"""Turns TIA Portal Openness XML exports (SimaticML, LAD networks) into readable logic.

Usage:  /usr/bin/python3 read_ladder.py <export folder>/PLC_1  > OLD_PROGRAM_LOGIC.txt
Reads Blocks/*.xml (OB, FC, DB) and Tags/*.xml. Only reads files; changes nothing.
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

OUT_PINS = {"out", "eno", "Q", "ET", "out1", "out2", "NDR", "DR", "ERROR", "STATUS", "ENO", "RET_VAL"}


def strip(tag):
    return tag.split("}", 1)[-1]


def kids(el, name):
    return [c for c in el if strip(c.tag) == name]


def kid(el, name):
    for c in el:
        if strip(c.tag) == name:
            return c
    return None


def component_text(comp):
    name = comp.get("Name")
    idx = [access_text(a) for a in kids(comp, "Access")]
    return name + ("[" + ",".join(idx) + "]" if idx else "")


def access_text(acc):
    scope = acc.get("Scope")
    sym = kid(acc, "Symbol")
    if sym is not None:
        comps = [component_text(c) for c in kids(sym, "Component")]
        if len(comps) == 1:
            return '"' + comps[0] + '"'
        return '"' + comps[0] + '".' + ".".join('"' + c + '"' if " " in c else c for c in comps[1:])
    const = kid(acc, "Constant")
    if const is not None:
        if const.get("Name"):
            return const.get("Name")
        val = kid(const, "ConstantValue")
        return val.text if val is not None else "?"
    addr = kid(acc, "Address")
    if addr is not None:
        area, typ, num, bit = addr.get("Area"), addr.get("Type"), addr.get("BlockNumber"), int(addr.get("BitOffset", "0"))
        size = {"Word": "W", "Byte": "B", "DWord": "D", "Int": "W", "Bool": "X"}.get(typ, typ)
        if area == "DB":
            if size == "X":
                return f"%DB{num}.DBX{bit // 8}.{bit % 8}"
            return f"%DB{num}.DB{size}{bit // 8}"
        return f"%{area}{size}{bit // 8}"
    return f"<{scope}>"


class Net:
    def __init__(self, flg):
        self.access, self.parts, self.calls = {}, {}, {}
        parts = kid(flg, "Parts")
        for el in parts:
            t, uid = strip(el.tag), el.get("UId")
            if t == "Access":
                self.access[uid] = access_text(el)
            elif t == "Part":
                neg = {n.get("Name") for n in kids(el, "Negated")}
                inst = kid(el, "Instance")
                inst_txt = None
                if inst is not None:
                    inst_txt = '"' + '"."'.join(c.get("Name") for c in kids(inst, "Component")) + '"'
                tv = {t2.get("Name"): t2.text for t2 in kids(el, "TemplateValue")}
                self.parts[uid] = dict(name=el.get("Name"), neg=neg, inst=inst_txt, tv=tv)
            elif t == "Call":
                ci = kid(el, "CallInfo")
                self.calls[uid] = dict(name=ci.get("Name"), type=ci.get("BlockType"))
                self.parts[uid] = dict(name="CALL " + ci.get("Name"), neg=set(), inst=None, tv={})
        self.wires = []
        for w in kid(flg, "Wires"):
            ends = []
            for e in w:
                t = strip(e.tag)
                if t == "Powerrail":
                    ends.append(("RAIL", None, None))
                elif t == "NameCon":
                    ends.append(("PIN", e.get("UId"), e.get("Name")))
                elif t == "IdentCon":
                    ends.append(("IDENT", e.get("UId"), None))
                elif t == "OpenCon":
                    ends.append(("OPEN", e.get("UId"), None))
            self.wires.append(ends)

    def wire_of(self, uid, pin):
        for w in self.wires:
            if ("PIN", uid, pin) in w:
                return w
        return None

    def operand(self, uid, pin):
        w = self.wire_of(uid, pin)
        if not w:
            return None
        for kind, u, p in w:
            if kind == "IDENT":
                return self.access[u]
            if kind == "PIN" and (u, p) != (uid, pin) and p in OUT_PINS:
                return self.describe_out(u, p)
        return None

    def describe_out(self, uid, pin):
        part = self.parts[uid]
        who = part["inst"] or part["name"]
        return f"{who}.{pin}"

    def power_in(self, uid, pin, depth=0):
        w = self.wire_of(uid, pin)
        if not w:
            return "FALSE(not connected)"
        terms = []
        for kind, u, p in w:
            if kind == "RAIL":
                terms.append("RAIL")
            elif kind == "PIN" and (u, p) != (uid, pin) and p in OUT_PINS:
                terms.append(self.power_out(u, p, depth + 1))
        if not terms:
            return "FALSE(not connected)"
        return terms[0] if len(terms) == 1 else "(" + " OR ".join(terms) + ")"

    def power_out(self, uid, pin, depth=0):
        part = self.parts[uid]
        n = part["name"]
        if depth > 60:
            return "..."
        if n == "Contact":
            op = self.operand(uid, "operand")
            lit = ("NOT " + op) if "operand" in part["neg"] else op
            return and_(self.power_in(uid, "in", depth), lit)
        if n in ("Coil", "SCoil", "RCoil"):
            return self.power_in(uid, "in", depth)
        if n == "O":
            card = int(part["tv"].get("Card", "2"))
            return "(" + " OR ".join(self.power_in(uid, f"in{i}", depth) for i in range(1, card + 1)) + ")"
        if n in ("Eq", "Ne", "Gt", "Lt", "Ge", "Le"):
            sym = {"Eq": "==", "Ne": "<>", "Gt": ">", "Lt": "<", "Ge": ">=", "Le": "<="}[n]
            cmp_ = f"[{self.operand(uid, 'in1')} {sym} {self.operand(uid, 'in2')} ({part['tv'].get('SrcType', '')})]"
            return and_(self.power_in(uid, "pre", depth), cmp_)
        if n == "PBox":
            return f"RISING_EDGE({self.power_in(uid, 'in', depth)}, memory {self.operand(uid, 'bit')})"
        if n == "TON":
            return f"{part['inst']}.Q"
        if pin == "eno" or n.startswith("CALL"):
            return self.power_in(uid, "en", depth)
        return f"{self.describe_out(uid, pin)}"

    def actions(self):
        out = []
        for uid, part in self.parts.items():
            n = part["name"]
            if n in ("Coil", "SCoil", "RCoil"):
                op = self.operand(uid, "operand")
                cond = clean(self.power_in(uid, "in"))
                if n == "Coil":
                    neg = "NOT " if "operand" in part["neg"] else ""
                    out.append(f"{op} := {neg}{cond}")
                elif n == "SCoil":
                    out.append(f"SET   {op}   when {cond}")
                else:
                    out.append(f"RESET {op}   when {cond}")
            elif n == "Move":
                card = int(part["tv"].get("Card", "1"))
                dests = ", ".join(str(self.operand(uid, f"out{i}")) for i in range(1, card + 1))
                out.append(f"MOVE {self.operand(uid, 'in')} -> {dests}   when {clean(self.power_in(uid, 'en'))}")
            elif n == "Add":
                out.append(f"{self.operand(uid, 'out')} := {self.operand(uid, 'in1')} + {self.operand(uid, 'in2')}"
                           f"   ({part['tv'].get('SrcType', '')}) when {clean(self.power_in(uid, 'en'))}")
            elif n == "TON":
                out.append(f"TON {part['inst']}: IN = {clean(self.power_in(uid, 'IN'))}, PT = {self.operand(uid, 'PT')}")
            elif n == "PBox":
                pass  # shown inside the expression that uses it
            elif n.startswith("CALL"):
                out.append(f"{n}   when {clean(self.power_in(uid, 'en'))}")
            elif n not in ("Contact", "O", "Eq", "Ne", "Gt", "Lt", "Ge", "Le"):
                pins = sorted({p for w in self.wires for k, u, p in w if k == "PIN" and u == uid and p not in ("en",)})
                args = ", ".join(f"{p} = {self.operand(uid, p) if p not in OUT_PINS else '(output) ' + str(self.operand(uid, p))}"
                                 for p in pins)
                out.append(f"{n} {part['inst'] or ''} when {clean(self.power_in(uid, 'en'))}: {args}")
        return out


def and_(a, b):
    if a == "RAIL":
        return b
    return f"{a} AND {b}"


def clean(expr):
    return expr.replace("RAIL", "TRUE")


def text_of(unit, comp_name):
    for mt in unit.iter():
        if strip(mt.tag) == "MultilingualText" and mt.get("CompositionName") == comp_name:
            for t in mt.iter():
                if strip(t.tag) == "Text" and t.text:
                    return t.text.strip()
    return ""


def block_report(path):
    root = ET.parse(path).getroot()
    blk = next(e for e in root.iter() if strip(e.tag).startswith("SW.Blocks."))
    attrs = kid(blk, "AttributeList")
    num = kid(attrs, "Number").text if kid(attrs, "Number") is not None else "?"
    name = kid(attrs, "Name").text
    lines = [f"\n================ {name}  ({strip(blk.tag).replace('SW.Blocks.', '')} {num}) ================"]
    title = text_of(blk, "Title")
    if title:
        lines.append(f"Block title: {title}")
    iface = kid(attrs, "Interface")
    if strip(blk.tag) == "SW.Blocks.GlobalDB":
        lines += db_members(iface)
        return lines
    for i, unit in enumerate([u for u in blk.iter() if strip(u.tag) == "SW.Blocks.CompileUnit"], 1):
        uattr = kid(unit, "AttributeList")
        src = kid(uattr, "NetworkSource")
        lang = kid(uattr, "ProgrammingLanguage").text if kid(uattr, "ProgrammingLanguage") is not None else ""
        lines.append(f"\n--- Network {i}: {text_of(unit, 'Title') or '(no title)'}   [{lang}]")
        cmt = text_of(unit, "Comment")
        if cmt:
            lines.append(f"    comment: {cmt}")
        if src is None or len(src) == 0:
            lines.append("    (empty network)")
            continue
        flg = src[0]
        if strip(flg.tag) == "StructuredText":
            lines.append("    SCL:  " + scl_text(flg).replace("\n", "\n          "))
            continue
        if strip(flg.tag) != "FlgNet":
            lines.append("    (not a LAD/FBD network: " + strip(flg.tag) + ")")
            continue
        net = Net(flg)
        for a in net.actions():
            lines.append("    " + a)
    return lines


def scl_text(st):
    parts = []

    def walk(el):
        for c in el:
            t = strip(c.tag)
            if t == "Token":
                parts.append(c.get("Text"))
            elif t == "Blank":
                parts.append(" " * int(c.get("Num", "1")))
            elif t == "NewLine":
                parts.append("\n" * int(c.get("Num", "1")))
            elif t == "Component":
                quoted = any(strip(b.tag) == "BooleanAttribute" and b.get("Name") == "HasQuotes" and b.text == "true" for b in c)
                name = c.get("Name")
                parts.append('"' + name + '"' if quoted or " " in name else name)
            elif t == "ConstantValue":
                parts.append(c.text or "")
            elif t == "LineComment" or t == "Comment":
                parts.append("// " + "".join(x.text or "" for x in c.iter() if strip(x.tag) == "Text"))
            else:
                walk(c)
    walk(st)
    return "".join(parts)


def db_members(iface):
    lines = []
    if iface is None:
        return lines

    def walk(el, prefix):
        for m in el:
            if strip(m.tag) == "Member":
                start = None
                for s in m:
                    if strip(s.tag) == "StartValue":
                        start = s.text
                lines.append(f"    {prefix}{m.get('Name'):<28} {m.get('Datatype'):<14} start={start}")
                walk(m, prefix + "    ")
            elif strip(m.tag) in ("Section", "Sections"):
                walk(m, prefix)
    walk(iface, "")
    return lines


def tags_report(path):
    root = ET.parse(path).getroot()
    lines = [f"\n================ Tag table: {os.path.basename(path)[:-4]} ================"]
    for t in root.iter():
        if strip(t.tag) == "SW.Tags.PlcTag":
            a = kid(t, "AttributeList")
            g = lambda n: (kid(a, n).text if kid(a, n) is not None else "")
            lines.append(f"    {g('Name'):<32} {g('DataTypeName'):<8} {g('LogicalAddress')}")
    return lines


def main(plc_dir):
    order = ["Main", "FC_GENERAL", "FC_MANUAL", "FC_ALARMS", "FC_OUTPUTS", "FC_AUTO", "FC_TCP_IP"]
    files = sorted(glob.glob(os.path.join(plc_dir, "Blocks", "*.xml")),
                   key=lambda p: (order.index(os.path.basename(p)[:-4]) if os.path.basename(p)[:-4] in order else 99, p))
    for f in sorted(glob.glob(os.path.join(plc_dir, "Tags", "*.xml"))):
        print("\n".join(tags_report(f)))
    for f in files:
        print("\n".join(block_report(f)))


if __name__ == "__main__":
    main(sys.argv[1])

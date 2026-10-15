"""Turns TIA Portal Openness HMI exports (WinCC Basic: screens, templates, tags, text lists) into a readable listing.

Usage:  /usr/bin/python3 read_hmi.py <hmi export folder>/HMI_RT_1  > OLD_HMI.txt
Only reads files; changes nothing.
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

KEEP = ["Left", "Top", "Width", "Height", "BackColor", "ForeColor", "BorderColor", "BorderWidth", "Mode", "Visible",
        "ProcessValue", "TextListName", "Format", "DisplayDate", "DisplayTime", "TimeFormat", "Enabled", "FitToLargest",
        "HorizontalAlignment", "VerticalAlignment", "BackFillStyle", "UseDesignColorSchema", "TabIndex", "Radius",
        "ShowDate", "ShowTime", "AlarmClasses", "Number", "Height", "LineColor", "LineWidth"]


def strip(tag):
    return tag.split("}", 1)[-1]


def kids(el, name=None):
    return [c for c in el if name is None or strip(c.tag) == name]


def kid(el, name):
    for c in el:
        if strip(c.tag) == name:
            return c
    return None


def attrs(el):
    al = kid(el, "AttributeList")
    out = {}
    if al is not None:
        for a in al:
            if len(a) == 0:
                out[strip(a.tag)] = (a.text or "").strip()
    return out


def links(el):
    ll = kid(el, "LinkList")
    out = {}
    if ll is not None:
        for l in ll:
            n = kid(l, "Name")
            out[strip(l.tag)] = n.text if n is not None else l.get("TargetID")
    return out


def html_text(t):
    if t is None:
        return ""
    t = re.sub(r"<br\s*/?>", " / ", t)
    return re.sub(r"<[^>]+>", "", t).strip()


def texts(obj):
    out = {}
    ol = kid(obj, "ObjectList")
    if ol is None:
        return out
    for mt in ol:
        if strip(mt.tag) == "MultilingualText":
            for item in mt.iter():
                if strip(item.tag) == "Text":
                    raw = ET.tostring(item, encoding="unicode")
                    inner = re.sub(r"^<[^>]+>|</[^>]+>$", "", raw.strip())
                    txt = html_text(inner)
                    if txt:
                        out[mt.get("CompositionName")] = txt
    return out


def describe_dynamic(d):
    kind = strip(d.tag).replace("Hmi.Dynamic.", "")
    a = attrs(d)
    lines = []
    if kind == "TagConnectionDynamic":
        lines.append(f"tag connection: property {a.get('PropertyName', '?')} <- tag {links(d).get('Tag', '?')}")
    elif kind.endswith("Animation"):
        tag, ranges = None, []
        ol = kid(d, "ObjectList")
        for c in (ol if ol is not None else []):
            ct = strip(c.tag)
            if ct.endswith("Trigger"):
                tag = links(c).get("Tag")
            elif ct == "Hmi.Dynamic.Range" or ct.endswith("Range") or ct.endswith("Entry"):
                ra = attrs(c)
                ranges.append(", ".join(f"{k}={v}" for k, v in ra.items()))
        extra = {k: v for k, v in a.items() if k not in ("Name",)}
        lines.append(f"animation {a.get('Name', kind)}: tag {tag} {extra if extra else ''} ranges: " + " | ".join(ranges))
    else:
        lines.append(f"{kind}: {a} {links(d)}")
    return lines


def describe_event(ev):
    name = attrs(ev).get("Name", "?")
    funcs = []
    for fe in ev.iter():
        if strip(fe.tag) == "Hmi.Event.FunctionListEntry":
            fa = attrs(fe)
            params = []
            ol = kid(fe, "ObjectList")
            for p in (ol if ol is not None else []):
                if strip(p.tag) == "Hmi.Event.FunctionListEntryParameter":
                    pa, pl = attrs(p), links(p)
                    val = pl.get("Value") or pa.get("Value", "")
                    params.append(f"{pa.get('Name')}={val}")
            funcs.append(f"{fa.get('Name')}({', '.join(params)})")
    return f"event {name}: " + "; ".join(funcs)


def describe_item(item, indent="  "):
    kind = strip(item.tag).replace("Hmi.Screen.", "")
    a = attrs(item)
    name = a.get("ObjectName", "")
    pos = f"x={a.get('Left')} y={a.get('Top')} w={a.get('Width')} h={a.get('Height')}"
    lines = [f"{indent}[{kind}] {name}  {pos}"]
    t = texts(item)
    if t:
        lines.append(indent + "    texts: " + "; ".join(f"{k}='{v}'" for k, v in t.items() if k != "HelpText" or v))
    keep = {k: v for k, v in a.items() if k in KEEP and k not in ("Left", "Top", "Width", "Height")}
    if keep:
        lines.append(indent + "    props: " + ", ".join(f"{k}={v}" for k, v in keep.items()))
    lk = links(item)
    if lk:
        lines.append(indent + "    links: " + ", ".join(f"{k}={v}" for k, v in lk.items()))
    ol = kid(item, "ObjectList")
    for c in (ol if ol is not None else []):
        ct = strip(c.tag)
        if ct.startswith("Hmi.Dynamic."):
            lines += [indent + "    " + x for x in describe_dynamic(c)]
        elif ct == "Hmi.Event.Event":
            lines.append(indent + "    " + describe_event(c))
        elif ct.startswith("Hmi.Screen.") and ct != "Hmi.Screen.Property":
            lines += describe_item(c, indent + "    ")
        elif ct == "Hmi.Screen.Property":
            pa = attrs(c)
            pol = kid(c, "ObjectList")
            for dyn in (pol if pol is not None else []):
                for x in describe_dynamic(dyn):
                    lines.append(indent + f"    property {pa.get('Name')}: " + x)
    return lines


def screen_report(path):
    root = ET.parse(path).getroot()
    top = next(e for e in root.iter() if strip(e.tag) in ("Hmi.Screen.Screen", "Hmi.Screen.ScreenTemplate"))
    a, lk = attrs(top), links(top)
    lines = [f"\n================ {strip(top.tag).replace('Hmi.Screen.', '')}: {a.get('Name')}  ({os.path.relpath(path)}) ================",
             "  screen props: " + ", ".join(f"{k}={v}" for k, v in a.items() if k in ("Number", "BackColor", "Width", "Height", "Name")),
             "  links: " + ", ".join(f"{k}={v}" for k, v in lk.items())]
    ol = kid(top, "ObjectList")
    for c in (ol if ol is not None else []):
        ct = strip(c.tag)
        if ct == "Hmi.Screen.ScreenLayer":
            la = attrs(c)
            lines.append(f"  -- layer {la.get('Name', '')} (visible={la.get('VisibleES', la.get('Visible', ''))})")
            lol = kid(c, "ObjectList")
            for item in (lol if lol is not None else []):
                if strip(item.tag).startswith("Hmi.Screen."):
                    lines += describe_item(item, "    ")
        elif ct == "Hmi.Event.Event":
            lines.append("  screen " + describe_event(c))
    return lines


def tags_report(path):
    root = ET.parse(path).getroot()
    lines = [f"\n================ HMI tag table: {os.path.basename(path)[:-4]} ================"]
    for t in root.iter():
        if strip(t.tag) == "Hmi.Tag.Tag":
            a, lk = attrs(t), links(t)
            plc = lk.get("ControllerTag", "")
            lines.append(f"  {a.get('Name'):<28} type={lk.get('DataType', a.get('DataType', '')):<6} conn={lk.get('Connection', '')} "
                         f"plc_tag={plc} addr={a.get('LogicalAddress', '')} access={a.get('AddressAccessMode', '')} "
                         f"acq={a.get('AcquisitionTriggerMode', '')} cycle={lk.get('AcquisitionCycle', '')}")
    return lines


def textlist_report(path):
    root = ET.parse(path).getroot()
    top = next(e for e in root.iter() if strip(e.tag).startswith("Hmi.TextGraphicList."))
    a = attrs(top)
    lines = [f"\n================ Text list: {a.get('Name')}  (ListRange={a.get('ListRange')}) ================"]
    for e in top.iter():
        if strip(e.tag).endswith("TextListEntry"):
            ea = attrs(e)
            t = texts(e).get("Text", "")
            rng = ea.get('From', '') + ('' if ea.get('From') == ea.get('To') else '..' + ea.get('To', ''))
            lines.append(f"  value {rng:<8} default={ea.get('DefaultEntry', '')}  '{t}'")
    return lines


def main(d):
    for f in sorted(glob.glob(os.path.join(d, "Tags", "*.xml"))):
        print("\n".join(tags_report(f)))
    for f in sorted(glob.glob(os.path.join(d, "TextLists", "*.xml"))):
        print("\n".join(textlist_report(f)))
    for f in sorted(glob.glob(os.path.join(d, "Templates", "**", "*.xml"), recursive=True)):
        print("\n".join(screen_report(f)))
    for f in sorted(glob.glob(os.path.join(d, "Screens", "**", "*.xml"), recursive=True)):
        print("\n".join(screen_report(f)))


if __name__ == "__main__":
    main(sys.argv[1])

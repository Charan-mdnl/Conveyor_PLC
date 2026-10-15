import csv, io, os, sys, contextlib, types
HERE = os.path.dirname(os.path.abspath(__file__))  # test outputs are written next to this file
sys.path.insert(0, HERE); sys.path.insert(0, "/home/charan/Documents/PLC/04_VFD")
sys.path.insert(0, "/home/charan/Documents/PLC/02_Guides_PDF/pdf_source")
import sim, write_new_vfd as W, read_vfd_parameters as rd
from vfd_el_params import PARAMS

OLD_CSV = "/home/charan/Documents/PLC/04_VFD/VFD_OLD_MACHINE/old_vfd_parameters.csv"
old = rd.load_csv(OLD_CSV)
# simulated NEW drive: old values replaced by the manual's factory values where known, small run time
new = dict(old)
for n, info in PARAMS.items():
    f = info[3]
    if f and n in new and f[0].isdigit():
        try:
            dec = info[1] or 0
            new[n] = int(round(float(f.split()[0]) * 10 ** dec))
        except ValueError: pass
new.update({"07.10": 345, "07.11": 0, "06.08": 0, "00.11": 0, "06.14": 0})
NEW_CSV = os.path.join(HERE, "sim_new.csv"); PLAN = os.path.join(HERE, "plan.csv")
with open(NEW_CSV, "w", newline="") as h:
    w = csv.writer(h); w.writerow(["parameter", "modbus_address", "raw_value", "raw_hex"])
    for k, v in new.items(): w.writerow([k, "", v, ""])

def run(argv):
    out = io.StringIO(); code = 0
    sys.argv = ["write_new_vfd.py"] + argv
    with contextlib.redirect_stdout(out):
        try: W.main()
        except SystemExit as e: code = e.code if isinstance(e.code, int) else (1 if e.code else 0)
    return code, out.getvalue()

ok = True
def check(cond, msg):
    global ok; print(("PASS " if cond else "FAIL ") + msg); ok &= cond

# 1. plan
code, out = run(["plan", "--old", OLD_CSV, "--new", NEW_CSV, "--out", PLAN, "--overload-protection"])
plan = W.load_plan(PLAN); names = [p[0] for p in plan]
check(code == 0 and plan[0][0] == "01.00" and plan[0][2] == 5000, "plan: 01.00 first, value 5000")
check(dict((p[0], p[2]) for p in plan).get("07.00") == 16, "plan: 07.00 = 16 (1.6 A)")
check(dict((p[0], p[2]) for p in plan).get("06.06") == 0, "plan: 06.06 = 0 with --overload-protection")
check(not any(n in W.NEVER or n.startswith(("09.", "12.")) for n in names), "plan: no forbidden parameter (00.02, 09.xx, counters, group 12)")
check("00.11" in out and "decide by hand" in out, "plan: unknown EL-W parameter 00.11 listed as NOT written")
print(out)

def drive(params, **kw): return sim.SimDrive(params, **kw)
base = ["write", "--plan", PLAN, "--timeout", "0.5"]

# 2. dry run
d = drive(new); code, out = run(base + ["--port", d.path])
check(code == 0 and "DRY RUN" in out and not any(f == 6 for f, _ in d.seen), "dry run: passes checks, sends no write")

# 3. old drive refused
d = drive(old); code, out = run(base + ["--port", d.path, "--yes"])
check(code == 2 and not any(f == 6 for f, _ in d.seen), "old drive (633 min) refused, nothing written")

# 4. running refused
d = drive(new, status=3, outfreq=4500); code, out = run(base + ["--port", d.path, "--yes"])
check(code == 2 and "not stopped" in out and not any(f == 6 for f, _ in d.seen), "running drive refused, nothing written")

# 5. different drive refused
other = dict(new); other["01.09"] = 123
d = drive(other); code, out = run(base + ["--port", d.path, "--yes"])
check(code == 2 and "not the drive that was read" in out and not any(f == 6 for f, _ in d.seen), "unexpected drive refused, nothing written")

# 6. drive rejects a value -> stop at once
d = drive(new, refuse={"02.00"}); code, out = run(base + ["--port", d.path, "--yes", "--result", os.path.join(HERE, "res_fail.csv")])
writes = [a for f, a in d.seen if f == 6]
check(code == 3 and 0x0200 in writes and all(a <= 0x0200 or a == 0x0100 for a in writes) and "STOPPED" in out, "refused value: stops at that parameter")

# 7. real write, then resume run is harmless, then verify
d = drive(new); code, out = run(base + ["--port", d.path, "--yes", "--result", os.path.join(HERE, "res.csv")])
check(code == 0 and all(d.params[n] == t for n, _, t, _ in plan), f"write: all {len(plan)} parameters written and read back")
seen_fn = {f for f, _ in d.seen}; seen_addr = {a for f, a in d.seen if f == 6}
check(seen_fn <= {3, 6} and not any(0x2000 <= a <= 0x20FF for _, a in d.seen), "only functions 03/06, never the command registers 2000H-2002H")
check(all(f"{a >> 8:02d}.{a & 0xFF:02d}" in W.ALLOWED for a in seen_addr), "every written address is on the allow-list")
d2 = drive(d.params); code, out = run(base + ["--port", d2.path, "--yes"])
check(code == 0 and "already" in out and not any(f == 6 for f, _ in d2.seen), "second run on the same drive: everything 'already' set, nothing broken")
after = os.path.join(HERE, "after.csv")
with open(after, "w", newline="") as h:
    w = csv.writer(h); w.writerow(["parameter", "modbus_address", "raw_value", "raw_hex"])
    for k, v in d.params.items(): w.writerow([k, "", v, ""])
code, out = run(["verify", "--plan", PLAN, "--readout", after])
check(code == 0, "verify: all planned parameters present")
check(run(["verify", "--plan", PLAN, "--readout", NEW_CSV])[0] == 4, "verify detects values that are not stored")

# 8. frame builder refuses forbidden things directly
for name in ("00.02", "09.04", "07.04", "07.10"):
    try: W.build_write("ascii", 1, name, 9); check(False, f"builder refuses {name}")
    except RuntimeError: check(True, f"builder refuses {name}")
try: W.build_status_read("ascii", 1, 0x2000); check(False, "status reader refuses 2000H")
except RuntimeError: check(True, "status reader refuses 2000H (command register)")
# checksum against the manual example: write 6000 (1770H) to 0100H, address 1 -> ':010601001770' + LRC 71
check(W.build_write("ascii", 1, "01.00", 6000) == b":010601001770" + b"71\r\n", "frame matches the Delta manual example (LRC 71)")
print("\nALL PASS" if ok else "\nSOME TESTS FAILED")

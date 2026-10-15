"""READ ONLY watcher for the Delta VFD: MI input status (04.26) and drive status (2101H-2103H). Function 03 only."""
import sys, time
sys.path.insert(0, "/home/charan/Documents/PLC/04_VFD")
import read_vfd_parameters as rd, write_new_vfd as W
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 0
found = rd.find_drive("/dev/ttyUSB0", 1, 0.5, [9600], [("ascii", 7, "N", 2)])
if not found: sys.exit("drive did not answer")
port, mode, desc = found
def p(n): return rd.read_words(port, mode, 1, W.name_to_address(n))[0]
def st():
    s = W.read_status(port, mode, 1, 0x2101); mi = p("04.26")
    run = ["STOP", "decel", "standby", "RUN"][s & 3]; d = ["FWD", "REV->FWD", "FWD->REV", "REV"][(s >> 3) & 3]
    return f"04.26={mi:3d} bits(MI6..MI1)={mi:06b}  drive={run:7} dir={d:8} Fcmd={W.read_status(port, mode, 1, 0x2102)/100:6.2f}  Fout={W.read_status(port, mode, 1, 0x2103)/100:6.2f}  err={W.read_status(port, mode, 1, 0x2100)}"
with port:
    print(desc, "| settings:", {n: p(n) for n in ["02.01", "02.04", "04.04", "04.05", "04.09", "01.00", "07.00", "06.06"]})
    prev = st(); print(time.strftime("%H:%M:%S"), prev, flush=True)
    end = time.time() + secs
    while time.time() < end:
        now = st()
        if now != prev: print(time.strftime("%H:%M:%S"), now, flush=True)
        prev = now
    print("done")

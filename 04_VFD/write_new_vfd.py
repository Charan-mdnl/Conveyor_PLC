#!/usr/bin/env python3
"""
Copy the settings of the OLD conveyor drive into the NEW drive (Delta VFD-EL / VFD-EL-W), safely.

This is the only tool in the project that WRITES to a drive. It has three steps, and only step 2 writes:

  1. plan    Make the list of what to write. Needs no drive. Uses the old readout and the new readout
             (both made with read_vfd_parameters.py) plus the new-machine changes:
               01.00 = 50.00 Hz and 04.02 = 74.8 % (new motor + gearbox + 100 mm roller: same belt speed,
                                                   knob fully clockwise = 37.4 Hz)
               07.00 = 1.6 A    (new motor nameplate, 240 V delta)
               06.06 = 0        (motor overload protection ON) only with --overload-protection
  2. write   Write the plan into the NEW drive, one parameter at a time, reading each one back.
             Without --yes it only shows what it would do (dry run).
  3. verify  After switching the drive off and on, compare a fresh readout with the plan.

Safety locks (all checked before anything is written):
  * Refuses the OLD drive: stops if the drive has >= 633 minutes of motor run time in total (07.11 days,
    07.10 minutes; the old drive had 633 on 7 Oct and the counter only goes up) or has the old drive's settings.
  * The drive must be the one that was read: every parameter in the plan must still have the value of the
    new readout (or already the target value, when a stopped run is resumed). Otherwise nothing is written.
  * The drive must be stopped (status register 2101H = stop, output frequency 2103H = 0).
  * Only parameters on a fixed allow-list can be written (settings listed in the Delta VFD-EL manual).
    Never written: 00.02 (parameter reset), group 09 (communication), 07.04 (auto-tuning, moves the motor),
    read-only values, fault records, counters, and EL-W parameters that the manual does not describe.
  * Only Modbus function 06 (write one parameter) and 03 (read) are ever sent. No run / stop / reset command
    (registers 2000H - 2002H) can be sent: the frame builder refuses those addresses.
  * Stops at the first problem (no reply, refused value, read-back mismatch). Everything is logged.

Usage (from the PLC folder):
  python3 04_VFD/write_new_vfd.py plan --old OLD.csv --new NEW.csv --out PLAN.csv [--overload-protection]
  python3 04_VFD/write_new_vfd.py write --plan PLAN.csv --port /dev/ttyUSB0 --log FRAMES.txt          (dry run)
  python3 04_VFD/write_new_vfd.py write --plan PLAN.csv --port /dev/ttyUSB0 --log FRAMES.txt --yes    (writes)
  python3 04_VFD/write_new_vfd.py verify --plan PLAN.csv --readout AFTER.csv
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_vfd_parameters as rd  # noqa: E402  (same folder: port handling, checksums, parameter reads)

WRITE_SINGLE = 0x06
STATUS_REGISTERS = {0x2100: "error code", 0x2101: "drive status", 0x2102: "frequency command",
                    0x2103: "output frequency", 0x2104: "output current"}

# New-machine values (README 5.2): new motor Transtech TM71 B4 (1400 rpm, 240 V delta 1.6 A) on a helical
# gearbox i = 16.67 with a 100 mm drive roller. OLD MACHINE: 70 Hz, motor 1385 rpm, worm gearbox i = 18, roller 58.34 mm
# -> old belt 19.74 m/min. Same belt speed needs 64.13 x 58.34 / 100 = 37.41 Hz (15 Oct 2026).
# 01.00 cannot go below 50 Hz, so: 01.00 = 50.00 Hz and keypad knob gain 04.02 = 74.8 % -> knob fully clockwise = 37.4 Hz.
NEW_MACHINE = {"01.00": (5000, "new motor + gearbox + 100 mm roller: maximum 50 Hz (lowest allowed)"),
               "04.02": (748, "knob gain 74.8 %: knob fully clockwise = 37.4 Hz = old belt speed 19.74 m/min"),
               "07.00": (16, "new motor nameplate current 1.6 A (240 V delta)")}
OVERLOAD_ON = {"06.06": (0, "motor overload protection ON (standard motor)")}

# Settings that the Delta VFD-EL manual (2017-06, chapter 4.1) lists as writable. Everything else is refused.
ALLOWED = set()
ALLOWED |= {"00.03", "00.04", "00.05", "00.10", "00.12", "00.13", "00.14"}
ALLOWED |= {f"01.{n:02d}" for n in range(0, 36)}
ALLOWED |= {f"02.{n:02d}" for n in range(0, 16)} | {"02.18"}
ALLOWED |= {"03.00", "03.02", "03.03", "03.04", "03.05", "03.06", "03.07", "03.08", "03.11", "03.12", "03.14"}
ALLOWED |= {f"04.{n:02d}" for n in range(0, 19)} | {"04.27", "04.28"} | {f"04.{n:02d}" for n in range(29, 35)}
ALLOWED |= {f"05.{n:02d}" for n in range(0, 15)}
ALLOWED |= {f"06.{n:02d}" for n in range(0, 8)}
ALLOWED |= {"07.00", "07.01", "07.02", "07.03", "07.05", "07.06", "07.07", "07.08", "07.09"} | {f"07.{n:02d}" for n in range(12, 18)}
ALLOWED |= {f"08.{n:02d}" for n in range(0, 25)} - {"08.19"}
ALLOWED |= {f"10.{n:02d}" for n in range(0, 27)} | {f"10.{n:02d}" for n in range(35, 46)} | {"10.49", "10.50"}
# 04.19 is "Reserved" in the VFD-EL manual, but on the VFD-EL-W it is the start / stop control mode:
# 0 = RUN / STOP by MI1 only (MI2 is a multi-function input), 1 = 2-wire / 3-wire control with MI1, MI2, MI3
# (Delta VFD-EL-W catalogue 2022-02). The OLD MACHINE has 1; without it MI2 (PLC Q0.1) cannot reverse. Found 15 Oct 2026.
ALLOWED |= {"04.19"}

# Known parameters that must never be written, with the reason shown in the plan.
NEVER = {"00.00": "read only", "00.01": "read only", "00.02": "PARAMETER RESET - would erase all settings",
         "00.06": "read only", "00.08": "password", "00.09": "password",
         "02.16": "read only", "02.17": "read only", "02.19": "read only", "03.13": "read only", "04.26": "read only",
         "07.04": "auto-tuning - would move the motor", "07.10": "run-time counter", "07.11": "run-time counter",
         "08.25": "read only"}
NEVER.update({f"06.{n:02d}": "fault record" for n in range(8, 13)})
NEVER.update({f"09.{n:02d}": "communication setting - the link would break" for n in range(0, 9)})

# The old drive had 0 days 633 minutes of motor run time (07.11 / 07.10) on 7 Oct 2026. The counter only goes up,
# so any drive with >= 633 minutes in total could be the old one and is refused. (The new drive had 345 on 15 Oct.)
OLD_DRIVE_RUN_MINUTES = 633


def name_to_address(name):
    group, number = (int(x) for x in name.split("."))
    return (group << 8) | number


def load_readout(path):
    return rd.load_csv(path)


# ---------------------------------------------------------------- step 1: plan
def make_plan(old, new, overload_protection):
    """Returns (writes, skipped). writes: list of (param, from_value, to_value, reason)."""
    targets = {}
    for name in sorted(set(old) | set(new)):
        if name not in old or name not in new or old[name] == new[name]:
            continue
        targets[name] = (old[name], "same as the old drive")
    extra = dict(NEW_MACHINE)
    if overload_protection:
        extra.update(OVERLOAD_ON)
    for name, (value, reason) in extra.items():
        targets[name] = (value, reason)

    writes, skipped = [], []
    for name, (value, reason) in sorted(targets.items()):
        if name.startswith("12."):
            continue  # group 12 is the drive's own table of group sizes
        if name in NEVER:
            skipped.append((name, old.get(name), new.get(name), NEVER[name]))
        elif name not in ALLOWED:
            skipped.append((name, old.get(name), new.get(name),
                            "EL-W parameter not described in the VFD-EL manual - not written, decide by hand"))
        elif name not in new:
            skipped.append((name, old.get(name), None, "not present on the new drive"))
        elif new[name] == value:
            continue
        else:
            writes.append((name, new[name], value, reason))
    order = {"01.00": 0}  # maximum frequency first: other frequencies must not exceed it
    writes.sort(key=lambda w: (order.get(w[0], 1), w[0]))
    return writes, skipped


def save_plan(path, writes):
    with open(path, "w", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["parameter", "modbus_address", "new_drive_now", "write_value", "reason"])
        for name, frm, to, reason in writes:
            out.writerow([name, f"0x{name_to_address(name):04X}", frm, to, reason])


def load_plan(path):
    with open(path, newline="") as handle:
        return [(r["parameter"], int(r["new_drive_now"]), int(r["write_value"]), r["reason"]) for r in csv.DictReader(handle)]


def print_plan(writes, skipped):
    print(f"\nWRITE PLAN: {len(writes)} parameter(s) will be written to the NEW drive (raw values, no decimal point):\n")
    print(f"   {'param':6} {'new drive now':>14} {'will become':>12}   reason")
    for name, frm, to, reason in writes:
        print(f"   {name:6} {frm:>14} {to:>12}   {reason}")
    if skipped:
        print(f"\nNOT written ({len(skipped)}): different from the old drive, but excluded on purpose:\n")
        for name, o, n, why in skipped:
            print(f"   {name:6} old={'-' if o is None else o:>6}  new={'-' if n is None else n:>6}   {why}")


# ---------------------------------------------------------------- frames
def build_write(mode, slave, name, value):
    if name not in ALLOWED or name in NEVER:
        raise RuntimeError(f"SAFETY STOP: parameter {name} is not on the allow-list. Nothing was sent.")
    address = name_to_address(name)
    if not 1 <= slave <= 254 or not 0 <= address <= 0x0FFF or not 0 <= value <= 0xFFFF:
        raise RuntimeError("SAFETY STOP: address or value out of range. Nothing was sent.")
    body = bytes([slave, WRITE_SINGLE, address >> 8, address & 0xFF, value >> 8, value & 0xFF])
    if mode == "ascii":
        return b":" + (body + bytes([rd.lrc(body)])).hex().upper().encode() + b"\r\n"
    c = rd.crc16(body)
    return body + bytes([c & 0xFF, c >> 8])


def build_status_read(mode, slave, address):
    if address not in STATUS_REGISTERS:
        raise RuntimeError("SAFETY STOP: only the status registers 2100H - 2104H may be read here.")
    body = bytes([slave, rd.READ_HOLDING, address >> 8, address & 0xFF, 0, 1])
    if mode == "ascii":
        return b":" + (body + bytes([rd.lrc(body)])).hex().upper().encode() + b"\r\n"
    c = rd.crc16(body)
    return body + bytes([c & 0xFF, c >> 8])


def exchange(port, mode, request, expected_rtu_len):
    """Send one frame, return the reply body (slave, function, data...) without checksum."""
    function = request[1] if mode == "rtu" else int(request[3:5], 16)
    if function not in (rd.READ_HOLDING, WRITE_SINGLE):
        raise RuntimeError("SAFETY STOP: only functions 03 and 06 may be sent.")
    port.reset_input_buffer()
    port.write(request)
    port.flush()
    rd.log_frame("TX", request)
    if mode == "ascii":
        for _ in range(3):
            line = port.read_until(b"\n")
            rd.log_frame("RX", line)
            if not line:
                raise rd.NoReply("no reply")
            if line.strip() == request.strip() and function == rd.READ_HOLDING:
                continue  # adapter echo of a read request
            start = line.find(b":")
            if start < 0:
                continue
            try:
                raw = bytes.fromhex(line[start + 1:].strip().decode("ascii"))
            except (ValueError, UnicodeDecodeError):
                raise rd.NoReply("garbled reply")
            if len(raw) < 4 or rd.lrc(raw[:-1]) != raw[-1]:
                raise rd.NoReply("checksum error")
            return raw[:-1]
        raise rd.NoReply("no reply")
    raw = port.read(expected_rtu_len)
    rd.log_frame("RX", raw)
    if len(raw) >= 5 and raw[1] & 0x80:
        raw = raw[:5]
    if len(raw) < 5 or rd.crc16(raw[:-2]) != (raw[-2] | (raw[-1] << 8)):
        raise rd.NoReply("no reply or checksum error")
    return raw[:-2]


def read_status(port, mode, slave, address):
    body = exchange(port, mode, build_status_read(mode, slave, address), 7)
    return rd.parse_body(body, slave, 1)[0]


def write_param(port, mode, slave, name, value):
    request = build_write(mode, slave, name, value)
    body = exchange(port, mode, request, 8)
    if body[0] != slave:
        raise rd.NoReply("reply from a different address")
    if body[1] == WRITE_SINGLE | 0x80:
        raise rd.DriveError(body[2])
    # Delta answers a 06 write with an exact echo of the request (manual 3.3 (2)).
    expected = bytes.fromhex(request[1:-2].decode())[:-1] if mode == "ascii" else request[:-2]
    if body != expected:
        raise rd.NoReply("the drive did not echo the write correctly")


# ---------------------------------------------------------------- step 2: write
def safety_checks(port, mode, slave, plan):
    """Returns a list of problems (empty = safe). Reads only."""
    problems = []
    run_minutes = rd.read_words(port, mode, slave, name_to_address("07.10"))[0]
    run_days = rd.read_words(port, mode, slave, name_to_address("07.11"))[0]
    print(f"   motor run time on this drive: {run_days} days {run_minutes} minutes")
    if run_days * 1440 + run_minutes >= OLD_DRIVE_RUN_MINUTES:
        problems.append(f"this drive has {run_days} d {run_minutes} min of run time: it could be the OLD drive (633 min on 7 Oct)")
    old_signature = {"02.00": 4, "04.07": 5, "04.08": 14, "01.00": 7000}
    live_sig = {n: rd.read_words(port, mode, slave, name_to_address(n))[0] for n in old_signature}
    if live_sig == old_signature:
        problems.append("this drive already has the old drive's settings (02.00=4, 04.07=5, 04.08=14, 01.00=70 Hz)")

    status = read_status(port, mode, slave, 0x2101)
    out_freq = read_status(port, mode, slave, 0x2103)
    error = read_status(port, mode, slave, 0x2100)
    print(f"   status 2101H = 0x{status:04X}, output frequency = {out_freq / 100:.2f} Hz, error code = {error}")
    if status & 0b11 != 0 or out_freq != 0:
        problems.append("the drive is not stopped (RUN status or output frequency is not 0)")
    if error:
        print(f"   NOTE: the drive shows error code {error}. Writing parameters is still possible; clear it later.")

    for name, frm, to, _ in plan:
        if name not in ALLOWED or name in NEVER:
            problems.append(f"{name} is not on the allow-list")
            continue
        live = rd.read_words(port, mode, slave, name_to_address(name))[0]
        if live not in (frm, to):
            problems.append(f"{name} is {live} now, but the readout said {frm}: this is not the drive that was read")
    return problems


def do_write(args):
    plan = load_plan(args.plan)
    if not plan:
        sys.exit("The plan is empty: nothing to write.")
    if args.log:
        rd.LOG = open(args.log, "a")
    port_name = args.port or rd.pick_port()
    fmt = [f for f in rd.FORMATS if f"{f[0]}-{f[1]}{f[2]}{f[3]}".lower() == args.format.lower()]
    if not fmt:
        sys.exit("Unknown --format")
    print(f"Looking for the drive on {port_name} (address {args.address}, {args.format}, {args.baud} baud) ...")
    found = rd.find_drive(port_name, args.address, args.timeout, [args.baud], fmt)
    if not found:
        sys.exit("The drive did not answer. Nothing was written.")
    port, mode, description = found
    with port:
        print(f"Drive found: {description}\nSafety checks (read only):")
        problems = safety_checks(port, mode, args.address, plan)
        if problems:
            print("\nSTOPPED. Nothing was written, because:")
            for p in problems:
                print(f"   - {p}")
            sys.exit(2)
        print("   all safety checks passed")
        todo = [(n, f, t, r) for n, f, t, r in plan]
        if not args.yes:
            print(f"\nDRY RUN: {len(todo)} parameter(s) would be written:")
            for n, f, t, r in todo:
                print(f"   {n}: {f} -> {t}   ({r})")
            print("\nNothing was written. Add --yes to write.")
            return
        print(f"\nWriting {len(todo)} parameter(s) ...")
        done = []
        for n, f, t, r in todo:
            live = rd.read_words(port, mode, args.address, name_to_address(n))[0]
            if live == t:
                print(f"   {n}: already {t}, skipped")
                done.append((n, f, t, live))
                continue
            try:
                write_param(port, mode, args.address, n, t)
                time.sleep(0.05)
                back = rd.read_words(port, mode, args.address, name_to_address(n))[0]
            except (rd.NoReply, rd.DriveError) as exc:
                print(f"   {n}: FAILED ({exc}). STOPPED here; parameters before this one are written.")
                save_result(args.result, done)
                sys.exit(3)
            if back != t:
                print(f"   {n}: wrote {t} but read back {back}. STOPPED here.")
                save_result(args.result, done + [(n, f, t, back)])
                sys.exit(3)
            print(f"   {n}: {f} -> {t}  OK (read back {back})")
            done.append((n, f, t, back))
    save_result(args.result, done)
    print(f"\nAll {len(done)} parameter(s) written and read back. Result saved to {args.result}.")
    print("Now switch the drive OFF, wait until the display is dark, switch it ON, and run the verify step.")


def save_result(path, done):
    if not path:
        return
    with open(path, "w", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["parameter", "before", "target", "read_back", "ok"])
        for n, f, t, b in done:
            out.writerow([n, f, t, b, "yes" if b == t else "NO"])


# ---------------------------------------------------------------- step 3: verify
def do_verify(args):
    plan = load_plan(args.plan)
    now = load_readout(args.readout)
    bad = [(n, t, now.get(n)) for n, _, t, _ in plan if now.get(n) != t]
    if bad:
        print(f"{len(bad)} parameter(s) are NOT as planned after the power cycle:")
        for n, t, v in bad:
            print(f"   {n}: planned {t}, drive has {v}")
        sys.exit(4)
    print(f"All {len(plan)} planned parameter(s) are stored in the drive (checked after the power cycle).")


def main():
    parser = argparse.ArgumentParser(description="Copy the old conveyor drive's settings into the NEW drive (safe, logged).")
    sub = parser.add_subparsers(dest="step", required=True)
    p = sub.add_parser("plan", help="make the write list (no drive needed)")
    p.add_argument("--old", required=True, help="readout of the OLD drive (CSV)")
    p.add_argument("--new", required=True, help="readout of the NEW drive before writing (CSV)")
    p.add_argument("--out", required=True, help="plan CSV to create")
    p.add_argument("--overload-protection", action="store_true", help="also set 06.06 = 0 (motor overload protection ON)")
    w = sub.add_parser("write", help="write the plan into the NEW drive (dry run without --yes)")
    w.add_argument("--plan", required=True)
    w.add_argument("--port")
    w.add_argument("--address", type=int, default=1)
    w.add_argument("--baud", type=int, default=9600)
    w.add_argument("--format", default="ascii-7N2")
    w.add_argument("--timeout", type=float, default=0.5)
    w.add_argument("--log", help="append every raw frame to this file")
    w.add_argument("--result", default=None, help="CSV with before / target / read-back of every write")
    w.add_argument("--yes", action="store_true", help="really write (only after the user has approved the plan)")
    v = sub.add_parser("verify", help="check a fresh readout (after power OFF / ON) against the plan")
    v.add_argument("--plan", required=True)
    v.add_argument("--readout", required=True)
    args = parser.parse_args()

    if args.step == "plan":
        writes, skipped = make_plan(load_readout(args.old), load_readout(args.new), args.overload_protection)
        print_plan(writes, skipped)
        save_plan(args.out, writes)
        print(f"\nPlan saved to {args.out}. Nothing was sent to any drive.")
    elif args.step == "write":
        do_write(args)
    else:
        do_verify(args)


if __name__ == "__main__":
    main()

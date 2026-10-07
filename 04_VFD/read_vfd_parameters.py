#!/usr/bin/env python3
"""
Read all parameters from a Delta VFD (VFD-EL / VFD-EL-W family) and save them to a CSV file.

READ ONLY: this tool only uses Modbus function 03 (read). It never writes to the drive,
never sends run / stop / reset commands and never uses the broadcast address 0.
Parameter address rule (Delta manual, "Address list"): parameter GG.nn = register GGnn hex.

What you need
    * A USB-to-RS485 adapter (for example Delta IFD6500, or any generic USB-RS485 stick).
    * The RJ45 socket on the drive is RS-485, NOT Ethernet. Never plug it into a laptop
      network port.
    * Two wires: drive SG+ to adapter A / D+, drive SG- to adapter B / D-.
      On the VFD-EL-W, SG+ and SG- are screw terminals on the control terminal strip, and the
      same signals are on the RJ45 socket (pin 5 = SG+, pin 4 = SG-, pin 3 = GND).
      If the drive does not answer, swap the two wires and try again (this does no harm).
    * Python package "pyserial" (pip install pyserial).

How to use
    1. Old drive powered ON and connected:   python3 read_vfd_parameters.py --out old_vfd.csv
    2. New drive powered ON and connected:   python3 read_vfd_parameters.py --out new_vfd.csv
    3. See what must be changed on the new:  python3 read_vfd_parameters.py --compare old_vfd.csv new_vfd.csv

Values are the raw numbers stored in the drive. A value shown on the keypad as 10.0 is
stored as 100, and 50.00 is stored as 5000. Compare raw with raw.
"""
import argparse
import csv
import json
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("The package 'pyserial' is missing. Install it with:  pip install pyserial")

READ_HOLDING = 0x03
BAUDS = [9600, 19200, 38400, 4800]
# (mode, data bits, parity, stop bits). The first entry is the Delta factory setting.
FORMATS = [
    ("ascii", 7, "N", 2), ("ascii", 7, "E", 1), ("ascii", 7, "O", 1),
    ("rtu", 8, "N", 2), ("rtu", 8, "E", 1), ("rtu", 8, "O", 1), ("rtu", 8, "N", 1),
    ("ascii", 7, "N", 1), ("ascii", 7, "E", 2), ("ascii", 7, "O", 2),
    ("rtu", 8, "E", 2), ("rtu", 8, "O", 2),
]


LOG = None  # open file for raw frames when --log is used


def log_frame(direction, data):
    if LOG:
        LOG.write(f"{time.strftime('%H:%M:%S')} {direction} {data.hex(' ')}\n")


class NoReply(Exception):
    pass


class DriveError(Exception):
    """The drive answered with a Modbus exception code."""

    def __init__(self, code):
        super().__init__(f"drive exception code {code}")
        self.code = code


def lrc(data: bytes) -> int:
    return (-sum(data)) & 0xFF


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def build_request(mode: str, slave: int, address: int, count: int) -> bytes:
    if not 1 <= slave <= 254 or not 1 <= count <= 4 or not 0 <= address <= 0x0FFF:
        raise ValueError("refused: request outside the read-only parameter area")
    body = bytes([slave, READ_HOLDING, address >> 8, address & 0xFF, count >> 8, count & 0xFF])
    if mode == "ascii":
        return b":" + (body + bytes([lrc(body)])).hex().upper().encode() + b"\r\n"
    c = crc16(body)
    return body + bytes([c & 0xFF, c >> 8])


def send_read_only(port, mode, frame):
    """The only place that writes to the serial port. Refuses anything that is not function 03."""
    function = frame[1] if mode == "rtu" else int(frame[3:5], 16)
    if function != READ_HOLDING:
        raise RuntimeError("SAFETY STOP: tried to send a non-read Modbus frame. Nothing was sent.")
    port.write(frame)
    port.flush()


def parse_body(body: bytes, slave: int, count: int):
    """body = slave, function, payload (check bytes already removed). Returns a list of words."""
    if len(body) < 3 or body[0] != slave:
        raise NoReply("reply from a different address")
    if body[1] == READ_HOLDING | 0x80:
        raise DriveError(body[2])
    if body[1] != READ_HOLDING or body[2] != 2 * count or len(body) < 3 + 2 * count:
        raise NoReply("unexpected reply")
    return [(body[3 + 2 * i] << 8) | body[4 + 2 * i] for i in range(count)]


def read_ascii(port, slave, address, count):
    request = build_request("ascii", slave, address, count)
    port.reset_input_buffer()
    send_read_only(port, "ascii", request)
    log_frame("TX", request)
    for _ in range(3):  # an adapter may echo our own request first
        line = port.read_until(b"\n")
        log_frame("RX", line)
        if not line:
            raise NoReply("no reply")
        if line.strip() == request.strip():
            continue
        start = line.find(b":")
        if start < 0:
            continue
        try:
            raw = bytes.fromhex(line[start + 1:].strip().decode("ascii"))
        except (ValueError, UnicodeDecodeError):
            raise NoReply("garbled reply")
        if len(raw) < 4 or lrc(raw[:-1]) != raw[-1]:
            raise NoReply("checksum error")
        return parse_body(raw[:-1], slave, count)
    raise NoReply("no reply")


def read_rtu(port, slave, address, count):
    request = build_request("rtu", slave, address, count)
    port.reset_input_buffer()
    send_read_only(port, "rtu", request)
    log_frame("TX", request)
    expected = 5 + 2 * count
    raw = port.read(expected)
    log_frame("RX", raw)
    if raw.startswith(request):  # adapter echo
        raw = raw[len(request):] + port.read(len(request))
    if len(raw) >= 5 and raw[1] == READ_HOLDING | 0x80:
        raw = raw[:5]
    if len(raw) < 5:
        raise NoReply("no reply")
    if crc16(raw[:-2]) != (raw[-2] | (raw[-1] << 8)):
        raise NoReply("checksum error")
    return parse_body(raw[:-2], slave, count)


def read_words(port, mode, slave, address, count=1, retries=2):
    reader = read_ascii if mode == "ascii" else read_rtu
    last = None
    for _ in range(retries + 1):
        try:
            return reader(port, slave, address, count)
        except NoReply as exc:
            last = exc
            time.sleep(0.05)
    raise last


def open_port(name, baud, bits, parity, stop, timeout):
    return serial.Serial(name, baudrate=baud, bytesize=bits, parity=parity,
                         stopbits=stop, timeout=timeout, write_timeout=1)


def find_drive(port_name, slave, timeout, bauds=BAUDS, formats=FORMATS):
    """Try the usual settings until the drive answers. Returns (open port, mode, description) or None."""
    for baud in bauds:
        for mode, bits, parity, stop in formats:
            try:
                port = open_port(port_name, baud, bits, parity, stop, timeout)
            except PermissionError:
                raise
            except (serial.SerialException, OSError, ValueError):
                continue
            try:
                time.sleep(0.05)
                read_words(port, mode, slave, 0x0000, 1, retries=0)
            except DriveError:
                pass  # it answered, so the settings are right
            except (NoReply, serial.SerialException, OSError):
                port.close()
                continue
            return port, mode, f"Modbus {mode.upper()}, {baud} baud, {bits}{parity}{stop}"
    return None


def pick_port():
    ports = [p for p in list_ports.comports() if p.device]
    usb = [p for p in ports if "USB" in p.device or "ACM" in p.device or "COM" in p.device.upper()]
    candidates = usb or ports
    if not candidates:
        sys.exit("No serial port found. Plug in the USB-RS485 adapter and try again.")
    if len(candidates) > 1:
        print("Several serial ports found:")
        for p in candidates:
            print(f"   {p.device}   {p.description}")
        print(f"Using {candidates[0].device}. Choose another one with --port.")
    return candidates[0].device


def read_all(port, mode, slave, max_group, max_param):
    rows = []
    for group in range(max_group + 1):
        missing = 0
        found = 0
        for number in range(max_param + 1):
            address = (group << 8) | number
            try:
                value = read_words(port, mode, slave, address, 1)[0]
            except (DriveError, NoReply):
                missing += 1
                if missing >= 20:  # Delta groups have gaps of up to 6 numbers; 20 in a row = end of group
                    break
                continue
            missing = 0
            found += 1
            rows.append((f"{group:02d}.{number:02d}", f"0x{address:04X}", value))
        print(f"   group {group:02d}: {found} parameters")
    return rows


def save_json(path, rows, description):
    with open(path, "w") as handle:
        json.dump({"read_at": time.strftime("%Y-%m-%d %H:%M:%S"), "communication": description,
                   "parameters": {name: value for name, _, value in rows}}, handle, indent=1)


def save_csv(path, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["parameter", "modbus_address", "raw_value", "raw_hex"])
        for name, address, value in rows:
            writer.writerow([name, address, value, f"0x{value:04X}"])


def load_csv(path):
    with open(path, newline="") as handle:
        return {row["parameter"]: int(row["raw_value"]) for row in csv.DictReader(handle)}


def compare(old_path, new_path):
    old, new = load_csv(old_path), load_csv(new_path)
    different = [(k, old.get(k), new.get(k)) for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
    if not different:
        print("No differences. Both drives have the same parameter values.")
        return
    print(f"{len(different)} parameters are different.")
    print("Set these on the NEW drive to the OLD value (raw numbers, see the note at the top of this file):\n")
    print(f"   {'parameter':10} {'OLD drive':>10} {'NEW drive':>10}")
    for name, a, b in different:
        print(f"   {name:10} {'-' if a is None else a:>10} {'-' if b is None else b:>10}")


def main():
    parser = argparse.ArgumentParser(description="Read all parameters of a Delta VFD-EL family drive (read only).")
    parser.add_argument("--port", help="serial port, for example /dev/ttyUSB0 or COM3 (default: auto)")
    parser.add_argument("--address", type=int, default=1, help="drive communication address, parameter 09.00 (default 1)")
    parser.add_argument("--out", default="vfd_parameters.csv", help="CSV file to write")
    parser.add_argument("--max-group", type=int, default=12, help="highest parameter group to try (default 12)")
    parser.add_argument("--max-param", type=int, default=99, help="highest parameter number to try in a group")
    parser.add_argument("--timeout", type=float, default=0.3, help="reply timeout in seconds")
    parser.add_argument("--baud", type=int, choices=BAUDS, help="use only this baud rate (parameter 09.01); default: try all")
    parser.add_argument("--format", help="use only this format, for example ascii-7N2 or rtu-8N2 (parameter 09.04); default: try all")
    parser.add_argument("--log", help="write every raw frame sent and received to this text file")
    parser.add_argument("--probe", action="store_true",
                        help="first test: read only 00.00, 00.01, 00.06 and 09.00 - 09.07, print them, save nothing")
    parser.add_argument("--compare", nargs=2, metavar=("OLD.csv", "NEW.csv"), help="compare two saved files and exit")
    args = parser.parse_args()

    if args.compare:
        compare(*args.compare)
        return

    if not 1 <= args.address <= 254:
        sys.exit("The address must be 1 to 254. Address 0 (broadcast) is never used by this tool.")
    bauds = [args.baud] if args.baud else BAUDS
    formats = FORMATS
    if args.format:
        wanted = args.format.lower().replace("_", "-")
        formats = [f for f in FORMATS if f"{f[0]}-{f[1]}{f[2]}{f[3]}".lower() == wanted]
        if not formats:
            sys.exit("Unknown --format. Use one of: " + ", ".join(f"{f[0]}-{f[1]}{f[2]}{f[3]}" for f in FORMATS))
    global LOG
    if args.log:
        LOG = open(args.log, "w")

    port_name = args.port or pick_port()
    print(f"Looking for the drive on {port_name} (address {args.address}) ...")
    try:
        found = find_drive(port_name, args.address, args.timeout, bauds, formats)
    except PermissionError:
        sys.exit(f"No permission to open {port_name}. On Linux run:  sudo usermod -aG dialout $USER  then log out and in.")
    if not found:
        sys.exit("The drive did not answer. Check: drive powered ON, SG+ / SG- not swapped, "
                 "correct port, and the address in parameter 09.00 (use --address).")
    port, mode, description = found
    print(f"Drive found: {description}")

    if args.probe:
        with port:
            for name in ["00.00", "00.01", "00.06"] + [f"09.{n:02d}" for n in range(8)]:
                group, number = (int(x) for x in name.split("."))
                try:
                    print(f"   {name} = {read_words(port, mode, args.address, (group << 8) | number, 1)[0]}")
                except DriveError as exc:
                    print(f"   {name} : not available ({exc})")
                except NoReply as exc:
                    print(f"   {name} : no reply ({exc})")
        print("Probe finished. Nothing was written to the drive.")
        return

    with port:
        rows = read_all(port, mode, args.address, args.max_group, args.max_param)
    if not rows:
        sys.exit("The drive answered but no parameter could be read.")
    save_csv(args.out, rows)
    json_path = args.out.rsplit(".", 1)[0] + ".json"
    save_json(json_path, rows, description)
    print(f"\n{len(rows)} parameters saved to {args.out} and {json_path}   (READ ONLY: nothing was written to the drive)")


if __name__ == "__main__":
    main()

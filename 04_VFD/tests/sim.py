"""Simulated Delta drive on a pty: Modbus ASCII, functions 03 and 06. Logs every function/address it receives."""
import csv, os, pty, sys, threading, json

def lrc(b): return (-sum(b)) & 0xFF

class SimDrive:
    def __init__(self, params, status=0, outfreq=0, refuse=None):
        self.params = dict(params); self.status = status; self.outfreq = outfreq
        self.refuse = refuse or set(); self.seen = []
        self.master, slave = pty.openpty()
        self.path = os.ttyname(slave)
        threading.Thread(target=self.loop, daemon=True).start()
    def reply(self, body):
        os.write(self.master, b":" + (body + bytes([lrc(body)])).hex().upper().encode() + b"\r\n")
    def loop(self):
        buf = b""
        while True:
            try: buf += os.read(self.master, 256)
            except OSError: return
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                s = line.find(b":")
                if s < 0: continue
                raw = bytes.fromhex(line[s+1:].strip().decode())
                body = raw[:-1]; slave, fn = body[0], body[1]; addr = (body[2] << 8) | body[3]
                self.seen.append((fn, addr))
                if fn == 3:
                    if addr == 0x2101: v = self.status
                    elif addr == 0x2103: v = self.outfreq
                    elif addr in (0x2100, 0x2102, 0x2104): v = 0
                    else:
                        name = f"{addr >> 8:02d}.{addr & 0xFF:02d}"
                        if name not in self.params: self.reply(bytes([slave, 0x83, 2])); continue
                        v = self.params[name]
                    self.reply(bytes([slave, 3, 2, v >> 8, v & 0xFF]))
                elif fn == 6:
                    name = f"{addr >> 8:02d}.{addr & 0xFF:02d}"; v = (body[4] << 8) | body[5]
                    if name in self.refuse or name not in self.params: self.reply(bytes([slave, 0x86, 3])); continue
                    self.params[name] = v; self.reply(body)
                else:
                    self.reply(bytes([slave, fn | 0x80, 1]))

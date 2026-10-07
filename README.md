# Conveyor + Camera Machine: copy of the old machine (new build)

**Master notes file.** Every time something is done in this project, this file is updated.
Read this file first before doing any work on the project.

Last updated: **7 Oct 2026**

---

## 1. Goal

We have an **old machine** (conveyor + QR camera + PLC + HMI + VFD). Someone else built it and wrote its programs.
We are building a **second, identical machine** with the same components, copying:

- the **panel wiring**: from the old panel, the hand drawings and the BOM;
- the **PLC + HMI program**: the same TIA Portal project, uploaded unchanged;
- the **VFD settings**: read from the old drive, then entered on the new drive;
- the **camera settings**;
- the **PC program** (Lux WMS app).

---

## 2. How the machine works (confirmed 6 Oct 2026)

| Device | Model | IP address |
|---|---|---|
| PLC | Siemens S7-1200 CPU 1214C DC/DC/DC, 6ES7214-1AG40-0XB0 | 192.168.0.40 |
| HMI | Siemens KTP700 Basic, 6AV2123-2GB03-0AX0 | 192.168.0.41 |
| PC with the "Lux WMS" program | (from `conveyor_automation-main`) | 192.168.0.77 |
| Camera (code reader) | HIKROBOT MV-ID6200M-00C-NNG | 192.168.0.78 |
| VFD | Delta VFD-EL-W, VFD004EL21W-1 (230 V 1-ph in, 0.4 kW, 2.5 A) | RS-485, address 1 |
| Motor | Bonfiglioli BE 71B 4, 0.37 kW | - |

- The **IR sensor is wired to the camera trigger, NOT to the PLC**. PLC input I0.0 is empty.
- The camera reads the QR codes and sends them to the PC (TCP 2002). It uploads pictures to the PC by FTP (port 2005).
- The PC program writes PLC Modbus register **40001** (= `DB_CAMERA.DATA1`, DB5): **0 = run, 1 = stop**.
- **AUTO mode:** START/STOP latch. The conveyor runs while the cycle is active and `DATA1 = 0`.
- **MANUAL mode:** jog forward/reverse from the HMI.

PLC inputs and outputs:

| PLC | Connected to | Meaning |
|---|---|---|
| I0.0 | nothing | (sensor logic exists but is switched off on purpose) |
| I0.1 | Auto/Manual selector (NO) | ON = AUTO |
| I0.2 | START, green (NO) | pressed = ON |
| I0.3 | STOP (NC) | normal = ON |
| I0.4 | Emergency stop (NC) | normal = ON |
| I0.5 | VFD relay RA | ON = VFD fault |
| I0.6 | joint only | not used |
| Q0.0 | VFD MI1 | forward |
| Q0.1 | VFD MI2 | reverse |
| Q0.2 | (VFD reset, only if wired on the old panel) | fault reset |
| Q0.3 / Q0.4 / Q0.5 | tower light green / red / amber | auto running / fault / manual |

The full details are in `02_Guides_PDF/Conveyor_Panel_Rebuild_Guide.pdf`.

---

## 3. Folder map

```
PLC/
├── README.md                     <- THIS FILE (master notes)
├── 01_Old_Project_AS_RECEIVED/   <- original files from the old machine. DO NOT EDIT.
│   ├── latest plc (2)/           TIA Portal V21 project "latest plc" (PLC + HMI program to upload)
│   ├── latest plc (2).zip        same, zipped as received
│   ├── SIMPLE FINEL TCPIP START STOP PROSS111.backup/(.zip)   older backup: HMI compile data only, no PLC logic
│   └── conveyor_automation-main/ PC program (Frontend = Lux WMS app + backend) and old camera config files
├── 02_Guides_PDF/
│   ├── Conveyor_Panel_Rebuild_Guide.pdf          how to build/wire/load the new machine (Rev 2, 14 pages)
│   ├── Conveyor_Program_From_Scratch_TIA_V21.pdf  learn to write the same PLC program yourself (Rev 2, 16 pages)
│   └── pdf_source/                                Python scripts that generate the two PDFs
├── 03_Wiring_Photos/             hand drawings of the old panel wiring (5 Oct 2026)
├── 04_VFD/
│   ├── read_vfd_parameters.py    READ-ONLY tool: reads all VFD parameters over RS-485
│   ├── old_vfd_2026-10-07/       readout of the OLD drive (csv, json, txt, frame logs). Locked, read-only
│   └── OLD_VFD_BACKUP_2026-10-07/ second copy of the same readout (backup)
├── 05_Camera/
│   └── final.mfa                 camera settings file (HIKROBOT, IP 192.168.0.78), added 7 Oct 2026
└── 06_BOM_and_Purchases/
    ├── Conveyor_BOM_New_Build.xlsx   NEW BOM: old BOM + what was bought, invoice sheets
    ├── make_bom.py                   script that builds the xlsx (edit it to add new bills)
    ├── original_BOM/                 the original BOM xlsx (unchanged)
    └── invoices/                     photos of the purchase bills
```

---

## 4. What has been done (history)

| Date | Done |
|---|---|
| 5 Oct 2026 | Decoded the old TIA project (binary, no text source). Checked the hand drawings and the BOM. Made the 2 PDFs (Rev 1). |
| 6 Oct 2026 | User explained how the machine really works (sensor → camera, PC stops the belt via 40001). Both PDFs corrected → **Rev 2**. |
| 6 Oct 2026 | Wrote `read_vfd_parameters.py` (read-only Modbus tool) and tested it on a simulated drive. |
| 6–7 Oct 2026 | **HMI firmware mismatch fixed.** The panel had image 16.x, the project needed 17.0.0.0, and TIA V21 lacked the V17 panel image. Fix: Siemens entry 109825750, `109825750_Panel_Images.zip`, replaced `...\Portal V21\Data\Hmi\Transfer\17.0`, then downloaded with "Upgrade" ticked. **Done successfully.** |
| 7 Oct 2026 | The tool was checked again and hardened: a lock means only function 03 (read) can ever be sent; fixed a gap bug that would skip parameters. |
| 7 Oct 2026 | **Old VFD read successfully** (only the VFD was powered). See section 5. |
| 7 Oct 2026 | Folder reorganised (section 3). README created. New BOM made from the two purchase bills. |
| 7 Oct 2026 | Also pushed to the company repo **https://github.com/charanxp/Conveyor_PLC** (public). |
| 7 Oct 2026 | Whole project pushed to GitHub **https://github.com/Charan-mdnl/Conveyor_PLC** (branch `main`). The repo is **public**: the user chose to include everything, the bills too. |

---

## 5. VFD readout of the OLD drive (7 Oct 2026)

- **Adapter:** Sharvi ISO-B-RS485-A (FTDI, isolated), `/dev/ttyUSB0` on this Linux laptop.
- **Wiring:** adapter **A+ → VFD SG+**, **B- → VFD SG-**, GND not connected. The terminal strip reads `MI1 MI2 MI3 DCM SG+ SG-`. Connected with the power OFF.
- **Communication found:** Modbus **ASCII, 9600 baud, 7N2, address 1** (factory settings; the drive confirms 09.00 = 1, 09.01 = 1, 09.04 = 0).
- 09.02 = 3 and 09.03 = 0, so there is no communication time-out alarm.
- **Read:** 306 parameters, groups 00–10 (group 11 does not exist: exception 02; group 12 = the drive's own table of the last parameter number in each group, which matches what was read).
- **Safety:** all 579 frames sent were function 03 (read). Nothing was written.
- **Check:** all 17 group 00 values match the keypad notebook. ChatGPT also checked the text file; its wording suggestions were added to the file header.
- **Raw values:** values are raw integers (2.5 A is stored as 25). Some are option numbers, not decimals.
- **Files:** `04_VFD/old_vfd_2026-10-07/old_vfd_parameters.txt` (to share), `.csv`, `.json`, `old_vfd_frames.txt` (raw log), `probe_frames.txt`.
- 03.00 = 8 (relay output function). The rebuild guide expects the relay to work as "fault indication". Check that 8 = fault indication in the Delta VFD-EL manual.

### How to run the tool (from the PLC folder)

The commands use `/usr/bin/python3`.

```
# probe: reads 11 values only, saves nothing
/usr/bin/python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --probe
# full read
/usr/bin/python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --address 1 --baud 9600 --format ascii-7N2 \
    --out 04_VFD/new_vfd_<date>/new_vfd_parameters.csv --log 04_VFD/new_vfd_<date>/new_vfd_frames.txt
# compare old and new
/usr/bin/python3 04_VFD/read_vfd_parameters.py --compare 04_VFD/old_vfd_2026-10-07/old_vfd_parameters.csv 04_VFD/new_vfd_<date>/new_vfd_parameters.csv
```

---

## 6. BOM and purchases (7 Oct 2026)

`06_BOM_and_Purchases/Conveyor_BOM_New_Build.xlsx`:

- **Columns A–H:** the original BOM, unchanged.
- **Columns I–N:** what was bought, from which bill, the quantity, the rate and a note.
- **Extra rows:** items bought that were not in the old BOM.
- **Two more sheets:** both bills, line by line.

Bills received so far:

- **Pavitra Electricals, invoice 7964/2026-27, 03-10-2026:** 35 lines, ₹14,145 + GST = **₹16,691**. The transcription was checked: the line amounts add up to the printed total, and the quantities add up to 175.
- **Nanologic Automation, invoice NA/SL/26-27/225, 05-10-2026:** 2× PLC 6ES7214-1AG40-0XB0 and 2× HMI 6AV2123-2GB03-0AX0, total ₹1,37,411.
  - **Only 1 PLC + 1 HMI are for this machine.** The second set is extra and is NOT in the BOM.
  - PLC serials: SC-U6M113QV, SC-U6M1CXK4.
  - HMI serials: SC-T3JK1131, SC-T1GD2473.

Items to CHECK (yellow in the xlsx):

1. **Tower light: the bill says "3TIER 220V AC".** The PLC outputs Q0.3–Q0.5 give **24 V DC**, so a 220 V AC light will not light from the PLC. Check the voltage on the OLD tower light. If it is 24 V DC, exchange the new one.
2. **"2 P SWITCH" for ₹25** (Manual/Auto selector). Check that it is a 22 mm 2-position panel selector, not a small toggle switch.
3. **"ILPB"** (health lamp). Check that it is green and **24 V DC**.
4. **MCBs** are "SPN" (old ones are Schneider 2-pole). Check they are C-curve.
5. **DIN rail:** 2 m bought, while 4 m was planned. **Terminal blocks:** 60 bought, 70 planned, and no earth (PE) terminals. **Ferrules:** the 0.5 sq mm ones are not on the bill.

Not on any bill yet (bought at other shops, according to the user; details still to be given):

- VFD
- Ethernet switch
- camera, light, lens
- motor
- sensor and reflector
- back plate, markers, black gland, contact blocks, mounting hardware
- RS-485 converter

---

## 7. Pending / next steps

1. **Read the NEW VFD** (read-only, same tool, same wiring, only the VFD powered). Compare it with the old readout. Then decide which parameters to set (by keypad, or a separate verified write tool, only with the user's OK).
   - Do NOT copy blindly.
   - Leave out the read-only/info values (00.00, 00.01, 00.06), 00.02 (parameter reset!) and group 12.
2. **Tower light voltage** (section 6, item 1). Check before wiring.
3. **Remaining bills / component list** from other shops. Add them to `make_bom.py` and rebuild the xlsx.
4. **Red button reverses the conveyor in MANUAL?** The user says so, but the saved program has reverse only on the HMI REV JOG button. Test it on the old machine. If it is true, upload the program from the old PLC (the PLC may hold a newer version than the file).
5. **Q0.2 wire** (VFD fault reset). Look on the old panel to see whether Q0.2 goes to a VFD input.
6. **Camera:** confirm where `05_Camera/final.mfa` came from (an export from the old camera?). Load it into the new camera with HIKROBOT MVS / IDMVS, and set IP 192.168.0.78.
7. **Rebuild guide, section 7** still says the VFD tool "was not tried on the real drive". Update it with the real result (see `pdf_source`; the rebuild steps are in the memory notes).
8. **GitHub tokens:** two tokens (Charan-mdnl and charanxp) were pasted in chat on 7 Oct. Revoke both on GitHub (Settings → Developer settings → Personal access tokens) and make new ones when needed.

---

## 8. Safety rules (always)

- **VFD:** only READ (Modbus function 03). Never write, reset, start/stop or change frequency on the **old** drive.
- Never touch or move terminals while they are powered. Wire the adapter with the power OFF.
- Keep the conveyor stopped while reading (on 7 Oct, everything except the VFD was switched off).
- `01_Old_Project_AS_RECEIVED/` is the original. Never edit it; work on copies.
- Old VFD readout files are locked read-only. Keep the backup copy.

---

## 9. Change log of this README

- 2026-10-07: pushed to the company repo charanxp/Conveyor_PLC too.
- 2026-10-07: pushed to GitHub (public, by the user's choice).
- 2026-10-07: created. Folder reorganised, VFD readout recorded, BOM updated from the Pavitra + Nanologic bills.

---

## 10. GitHub

- Two copies, both public, branch `main`, same content:
  - personal: https://github.com/Charan-mdnl/Conveyor_PLC  (git remote `origin`)
  - company:  https://github.com/charanxp/Conveyor_PLC     (git remote `company`)
- The local folder `PLC/` is the git working copy. After each change push to BOTH: `git push origin main` and `git push company main`.
- To upload changes: `git add -A && git commit -m "..." && git push`. Pushing needs a token or SSH key; never put the token in a file.

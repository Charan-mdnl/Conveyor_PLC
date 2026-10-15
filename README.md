# Conveyor + Camera Machine: copy of the old machine (new build)

**Master notes file.** Every time something is done in this project, this file is updated.
Read this file first before doing any work on the project.

Last updated: **15 Oct 2026**

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

## 1b. Names of the machines and control boxes (use these names everywhere)

| Name | What it is | VFD files |
|---|---|---|
| **OLD MACHINE** | The existing, working conveyor built by someone else (the original). Its VFD was only ever READ | `04_VFD/VFD_OLD_MACHINE/` (+ `VFD_OLD_MACHINE_BACKUP/`) |
| **NEW CONTROL BOX 1** (CB1) | First of the two new control panels for the new conveyor. Not programmed yet | `04_VFD/VFD_NEW_CONTROL_BOX_1/` (empty so far) |
| **NEW CONTROL BOX 2** (CB2) | Second new control panel. VFD read and programmed on 15 Oct 2026 | `04_VFD/VFD_NEW_CONTROL_BOX_2/` |

File names start with the box code: `CB1_...`, `CB2_...`. **Tip:** put a sticker "CONTROL BOX 1" / "CONTROL BOX 2" on each panel and on its VFD, so they can never be mixed up. The VFD's run-time counter (07.10) also tells them apart: the OLD MACHINE had 633 min on 7 Oct, CB2 had 345 min as received.

## 2. How the whole system works (told by the user on 6 Oct 2026, checked against the programs)

### 2.1 The idea of the machine, as the user explained it

- The operator puts a **set of boxes side by side** (5 or 6 in a row) on the conveyor. Each box has a QR code.
- The conveyor is started in **AUTO** mode and runs continuously.
- The **IR sensor** sees the boxes and triggers the **camera directly**. The trigger wire goes to the camera, **not to the PLC**.
- The camera waits for a set **delay**, so the boxes are in the middle of the belt. Then it takes one picture, reads the QR codes and the PC counts them.
- **All boxes there:** the conveyor keeps moving. **A box missing (or extra):** the conveyor stops.
- With the PLC on and in AUTO, the **PC program (front GUI)** can also switch the conveyor on and off remotely.
- In **MANUAL** mode the remote control from the PC does **not** work.
- After an **Emergency stop**, releasing the button is not enough: **FAULT RESET** must be pressed on the HMI, or the machine will not run.
- The camera has no program to copy, only settings (config file).

### 2.2 The devices

| Device | Model | IP address | Job |
|---|---|---|---|
| IR sensor | (model not known yet) | - | Sees the boxes, triggers the camera |
| Camera (code reader) | HIKROBOT MV-ID6200M-00C-NNG | 192.168.0.78 | Takes the picture, reads up to 6 QR codes |
| PC with the "Lux WMS" program | (from `conveyor_automation-main`) | 192.168.0.77 | Counts the codes, decides run / stop, operator screen |
| PLC | Siemens S7-1200 CPU 1214C DC/DC/DC, 6ES7214-1AG40-0XB0 | 192.168.0.40 | Modes, start/stop memory, alarms, outputs |
| HMI | Siemens KTP700 Basic, 6AV2123-2GB03-0AX0 | 192.168.0.41 | Screens: auto status, manual jog, alarms, I/O status |
| VFD | Delta VFD-EL-W, VFD004EL21W-1 (230 V 1-ph in, 0.4 kW, 2.5 A) | RS-485, address 1 (only used to read parameters) | Drives the motor forward / reverse |
| Motor | Bonfiglioli BE 71B 4, 0.37 kW | - | Moves the belt |
| Ethernet switch | Teltonika TSW010 | - | Joins PLC, HMI, camera and PC |

Programming laptop: any free address, for example 192.168.0.100. Subnet mask for all: 255.255.255.0.

### 2.3 How the devices communicate

```
IR sensor --(trigger wire)--> Camera --(Ethernet)--> PC --(Ethernet, Modbus)--> PLC --(wires)--> VFD --> Motor
                                                                                 ^
                                              HMI <--(Ethernet)-->---------------+
                              Buttons, selector, Emergency --(wires)-------------+
```

| From | To | How | What is sent |
|---|---|---|---|
| IR sensor | Camera | One wire to the camera's trigger input | "A box is here": take a picture after the delay |
| Camera | PC (192.168.0.77) | Ethernet, TCP port **2002** (the PC connects to the camera) | The QR codes, separated by `;`. "NoRead" when nothing is read |
| Camera | PC (192.168.0.77) | Ethernet, FTP port **2005** (the PC is the FTP server; user "User") | The pictures (ok / ng folders) |
| PC | PLC (192.168.0.40) | Ethernet, **Modbus TCP port 502**, function 06, register **40001** | **0 = conveyor may run, 1 = stop** |
| HMI | PLC | Ethernet, Siemens S7 connection (`HMI_Connection_1`) | Jog and reset buttons to the PLC; mode, status, alarms and I/O state to the HMI |
| Buttons, selector, Emergency | PLC | Wires to inputs I0.1 - I0.4 | Operator commands |
| VFD relay | PLC | Wire to input I0.5 | Drive fault |
| PLC | VFD | Wires from Q0.0 / Q0.1 (/ Q0.2) to MI1 / MI2 | Run forward, run reverse, (reset) |
| PLC | Tower light | Wires from Q0.3 / Q0.4 / Q0.5 | Green / red / amber |
| PC | Company cloud server | Internet | Login, orders, and each scanned code |

- Register 40001 is `DB_CAMERA.DATA1` (DB5) in the PLC.
- The **PLC never talks to the camera**, and the PLC does not read the QR codes. The PC decides, the PLC obeys.
- The VFD gets **no speed value** from the PLC. Speed is set in the VFD itself.

### 2.4 AUTO mode, step by step

1. Selector at **AUTO**, Emergency released, no fault. Press the green **START** button. Green lamp ON, conveyor runs forward.
2. The operator puts a row of boxes on the belt. The IR sensor triggers the camera.
3. After the trigger delay (3 seconds in the saved camera settings) the camera takes the picture and sends the codes to the PC.
4. The PC compares the number of codes with the **Stack Size**:
   - **same:** nothing happens, the conveyor keeps running;
   - **different:** the PC writes **1** to register 40001 and the PLC stops the conveyor. The green lamp stays ON.
5. The operator corrects the boxes and clicks **Rescan Stack** or **Start** on the PC. The PC writes **0**, the conveyor runs again.
6. The red **STOP** button or the **Emergency** button ends the cycle at any time.

### 2.5 MANUAL mode

- Selector at **MANUAL** (amber lamp ON), and open the **MANUAL** screen on the HMI.
- Hold **CONVEYOR FWD JOG** on the HMI, or hold the green START button: forward while held.
- Hold **CONVEYOR REV JOG** on the HMI: reverse while held.
- The PC program cannot run the conveyor in manual mode.

### 2.6 Faults

- **Emergency pressed** or **VFD fault**: everything stops, red lamp ON, alarm text on the HMI.
- Release the Emergency (or clear the drive fault), then press the yellow **FAULT RESET** on the HMI (bottom right on every screen).
- The auto cycle does not restart by itself: press START again.

### 2.7 All the options the operator has

| Where | Control | What it does |
|---|---|---|
| Panel door | Auto / Manual selector | Chooses the mode |
| Panel door | Green START | AUTO: starts the cycle. MANUAL: forward while held |
| Panel door | STOP (red) | AUTO: ends the cycle |
| Panel door | Emergency stop | Stops everything, raises an alarm |
| Panel door | VFD healthy lamp | ON while the drive has no fault (from the VFD relay, not from the PLC) |
| Panel door | Main isolator, panel socket | Power on / off; 230 V socket |
| Tower light | Green / amber / red | Auto cycle started / manual mode / fault |
| HMI, bottom of every screen | AUTO, MANUAL, ALARMS, IO STATUS | Open that screen |
| HMI, bottom of every screen | FAULT RESET (yellow) | Clears the alarms (hold it) |
| HMI, AUTO OPERATION screen | Status text | AUTO RUNNING / STOPPED |
| HMI, MANUAL OPERATION screen | CONVEYOR FWD JOG, CONVEYOR REV JOG | Jog forward / reverse while held |
| HMI, ALARMS screen | Alarm list | Emergency alarm, VFD fault alarm |
| HMI, INPUT / OUTPUT STATUS screens | Lamps | Live state of every PLC input and output |
| PC program, Scanning page | **Start** | Writes 0: conveyor may run |
| PC program, Scanning page | **Stop** | Writes 1: conveyor stops |
| PC program, Scanning page | **Stack Size** | How many boxes are expected: 2, 4, 6, 8, 10, 20 or a typed number (6 when the program starts) |
| PC program, Scanning page | **Rescan Stack** | After a wrong count: run again |
| PC program | Login, orders | From the company server (the PC needs internet) |
| Camera settings | Trigger delay | Time from sensor signal to picture (3 s saved) |
| Camera settings | Number of codes, exposure, gain | Up to 6 codes per picture; brightness |
| VFD keypad | Parameters | Speed, ramps, motor data (copied from the old drive, section 5) |

### 2.8 Points where the user's explanation and the saved files differ (to check on the old machine)

| The user said | The saved files say | What to do |
|---|---|---|
| In MANUAL, the **red** button runs the conveyor in **reverse** | Reverse comes only from the HMI button CONVEYOR REV JOG. The red button has no job in manual (confirmed by the TIA export, 12 Oct) | **User, 12 Oct:** it was wanted but never built. It should work as hold-to-run (reverse while held, stop on release) in MANUAL. Planned as a new feature: section 2.10 |
| "5 or 6" boxes | The camera reads up to 6 codes; Stack Size is 6 when the PC program starts | Use the Stack Size the operators really use |
| "Change to manual mode in the HMI" | The HMI has no mode switch: the selector decides. On the HMI you only open the MANUAL screen | Nothing to change |

### 2.10 New requirement: red-button reverse jog in MANUAL (12 Oct 2026, not in the old program)

- **Wanted behaviour:** in MANUAL, hold the red button and the belt runs in reverse; release it and the belt stops (same as HMI CONVEYOR REV JOG). In AUTO the red button stays STOP.
- **Recommended design (way A):**
  - **Wiring:** one extra **NO contact block** on the red button, wired +24 V → NO contact → spare input **I0.7**.
  - **Tags:** tag `DI_SPARE I0.7` is renamed `DI_REV JOG PB`.
  - **Program:** in FC_MANUAL network 1, a NO contact on I0.7 goes in parallel with the HMI REV JOG contact. An interlock goes in FC_OUTPUTS: NC `DO_CONVEYOR REV ON` before the FWD coil, and NC `DO_CONVEYOR FWD ON` before the REV coil.
  - **If a wire breaks:** nothing moves (safe).
- **Not recommended (way B):** using the existing NC STOP input I0.3 with an NC contact. A broken STOP wire would make the belt run in reverse by itself in MANUAL.
- **Order:** build and test the exact copy first, then add this as a change ("Save as" a new project first).
- **Where to find it:** tutorial Part 12 has the steps, drawing and tests.
- **BOM:** add 1 NO contact block for the red button.

### 2.9 PLC inputs and outputs

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

More detail: `02_Guides_PDF/Conveyor_Panel_Rebuild_Guide.pdf` (wiring, camera settings, PC program) and `02_Guides_PDF/Conveyor_Program_Explained.pdf` (the PLC program).

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
│   ├── Conveyor_Panel_Rebuild_Guide.pdf          how to build/wire/load the new machine (Rev 5 + 15 Oct corrections: EL-W 04.19, no MI5; Appendix C = all old VFD settings)
│   ├── Conveyor_Program_From_Scratch_TIA_V21.pdf  HOW: every click to write the PLC + HMI program yourself (Rev 3.2, 26 pages; exact TIA export; one row per item; every item marked NEEDED / USEFUL / NOT needed; FC_AUTO way A = 3 short networks)
│   ├── Conveyor_Program_Explained.pdf             WHY: meaning of tags/DBs/blocks/networks + design method from a problem statement (Rev 2, 18 pages)
│   └── pdf_source/                                Python scripts that generate the three PDFs (make_*.py, common.py, vfd_el_params.py = VFD parameter names/factory values)
├── 03_Wiring_Photos/             hand drawings of the old panel wiring (5 Oct 2026)
├── 04_VFD/
│   ├── VFD_OLD_MACHINE/          readout of the OLD MACHINE drive (7 Oct 2026). Locked, read-only
│   ├── VFD_OLD_MACHINE_BACKUP/   second copy of the same
│   ├── VFD_NEW_CONTROL_BOX_2/    CB2 drive: CB2_as_received_* (settings before any change, locked + backup/), CB2_write_plan.csv, CB2_write_result.csv, CB2_*_frames.txt logs
│   ├── VFD_NEW_CONTROL_BOX_1/    CB1 drive: not read yet
│   ├── read_vfd_parameters.py    READ-ONLY tool: reads all VFD parameters over RS-485
│   ├── write_new_vfd.py          WRITE tool for the NEW drive only: plan / write (dry run without --yes) / verify, with safety locks
│   ├── tests/                    simulated drive + 22 tests for the write tool (all pass, 15 Oct 2026)
│   ├── manual/                   Delta VFD-EL user manual (2017-06) + its parameter summary as text. Local only, not on GitHub
├── 05_Camera/
│   └── final.mfa                 camera settings file (HIKROBOT, IP 192.168.0.78), added 7 Oct 2026
├── 06_BOM_and_Purchases/
    ├── Conveyor_BOM_New_Build.xlsx   NEW BOM: old BOM + what was bought, invoice sheets
    ├── make_bom.py                   script that builds the xlsx (edit it to add new bills)
    ├── original_BOM/                 the original BOM xlsx (unchanged)
│   └── invoices/                     photos of the purchase bills
├── 08_Commissioning/            tests on the new control boxes: plc_io_read.ps1 (READ-ONLY Modbus read of PLC I/O, run on the Windows laptop), CB2_IO_test_2026-10-15.txt
└── 07_Old_Program_Export/        EXACT old PLC program, exported from TIA Portal V21 (12 Oct 2026)
    ├── old_export_20261012_170146/PLC_1/   Blocks/*.xml (OB1, 6 FCs, 5 DBs) + Tags/*.xml (DI, DO, Default) - SimaticML
    ├── old_export_20261012_170146.log      export log (12 blocks, 3 tag tables, copy closed without saving)
    ├── read_ladder.py                      turns the XML into readable logic (read-only)
    ├── OLD_PROGRAM_LOGIC.txt               the whole program as readable logic (output of read_ladder.py)
    ├── hmi_export_20261012_181543/HMI_RT_1/ HMI export: Screens (AUTO, MANUAL, ALARMS, IOs/INPUT STATUS, IOs/OUTPUT STATUS), Templates/MAIN, Tags (Default, IO, ALARMS), TextLists, Cycles
    ├── hmi_export_20261012_181543.log
    ├── read_hmi.py                         turns the HMI XML into a readable listing (read-only)
    └── OLD_HMI.txt                         every HMI object: position, size, texts, colours, events, animations, tags
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
| 7 Oct 2026 | Company repo **https://github.com/charanxp/Conveyor_PLC** added as git remote `company`. The push was blocked by Claude Code's safety check: **the user must run the push** (section 10). |
| 9 Oct 2026 | User: the how-to guide says what to click but not what it means. New PDF **Conveyor_Program_Explained.pdf** covers the scan cycle, a glossary, NO/NC buttons vs contacts, a 10-step design method from a problem statement (worked on this conveyor), why each tag/flag/DB/block exists and why this many, every network explained, signal stories, Modbus, HMI, exercises and fact vs inference. The tutorial (Rev 2.1) now points to it. |
| 9 Oct 2026 | Verified from the original file: OB1 call order = FC_AUTO, FC_ALARMS, FC_GENERAL, FC_MANUAL, FC_OUTPUTS, FC_TCP_IP. The PC writes 40001 with Modbus function 06, address 0 (server.py): 0/1 from its Start/Stop and 1 on a QR count mismatch. |
| 9 Oct 2026 | User's 2nd wiring photo (power distribution) checked against the rebuild guide: **matches** (main switch → C10 → VFD → motor; main switch → C6 → socket + 24 V supply → 2 A MCB → sensor, Ethernet switch, HMI, PLC). |
| 12 Oct 2026 | Remote TIA link set up (2nd Tailscale + SSH + Openness, section 7 item 9). **Old program exported from TIA itself** (copy of "latest plc" opened with Openness, closed without saving) → `07_Old_Program_Export/`. Compared with the earlier understanding: **section 11**. |
| 12 Oct 2026 | Guides corrected from the TIA export: **tutorial Rev 3** (3 tag tables, clock memory MB0, DB_TCP_IP optimized, exact network titles and layouts, FC_AUTO = real 6 networks, FC_MANUAL REV row on top, FC_TCP_IP real order, MB_SERVER V5.3, new **Part 12: red-button reverse jog**) and **Explained Rev 2**. Part 10 (HMI) still to be checked against the HMI export. |
| 12 Oct 2026 | **HMI exported from TIA** (copy, closed without saving) → `07_Old_Program_Export/hmi_export_...`, readable in `OLD_HMI.txt`. Compared: section 11.4. **All three PDFs corrected:** tutorial Rev 3 (Part 10 HMI now exact), Explained Rev 2 (HMI part), **Rebuild guide Rev 4** (red-button resolved, I0.7 wiring for the new reverse jog, HMI notes, tests, Appendix A program reference). |
| 13 Oct 2026 | User: the guides were confusing (rows squeezed together, vague VFD/connection parts). **Tutorial Rev 3.1:** every tag, DB row, MOVE row and lamp on its own row. **Rebuild guide Rev 5:** VFD section rewritten with exact meanings from the Delta VFD-EL manual (section 5.1 below), wiring table with reasons, PNP switch, the list of parameters to set, Appendix C. |
| 13 Oct 2026 | User: "why waste time on extra things". **Tutorial Rev 3.2:** every item marked needed / useful / not needed (overview in part 0, a "Needed?" column in all tag, DB and HMI tables, marks on FC_AUTO / FC_TCP_IP networks), plus a **minimum build** path (section 11.5). |
| 13 Oct 2026 | VS Code Remote-SSH from the Windows laptop to this PC is in daily use (pending 13 done). |
| 9 Oct 2026 | Rebuild guide → **Rev 3**: section 7 shows the real old-drive values; **07.00 corrected** (the old drive holds 25 = 2.5 A, not "about 1.82 A"); the VFD tool notes now say it was used on the real drive, with the new paths. |
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
- **Files:** `04_VFD/VFD_OLD_MACHINE/old_vfd_parameters.txt` (to share), `.csv`, `.json`, `old_vfd_frames.txt` (raw log), `probe_frames.txt`.
- 03.00 = 8 (relay output function). The rebuild guide expects the relay to work as "fault indication". Check that 8 = fault indication in the Delta VFD-EL manual.

### 5.1 What the old drive's settings mean (Delta VFD-EL manual, decoded 13 Oct 2026)

The manual is in `04_VFD/manual/`. It is the VFD-EL manual; the drive is the EL-W variant of the same family (same parameter numbers, plus a few extra parameters the manual does not list).

| Setting | Value | Meaning |
|---|---|---|
| 02.00 | 4 | **Speed comes from the knob (potentiometer) on the drive keypad.** The PLC sends no speed |
| 01.00 / 01.01 / 01.02 | 70.00 Hz / 50.00 Hz / 220.0 V | Max frequency (top of the knob range) / motor rated frequency / motor voltage |
| 01.09 / 01.10 | 5.0 s / 0.5 s | Acceleration / deceleration time |
| 02.01 | 1 | Run command from the **external terminals** (keypad STOP also works) |
| 04.04 | 0 | 2-wire control: **MI1 = forward/stop, MI2 = reverse/stop** |
| 04.05 / 04.06 | 0 / 0 | MI3, MI4: **no function** |
| 04.07 | 5 | **MI5 = external reset**, so Q0.2 (if wired) must go to MI5 |
| 04.08 | 14 | MI6 = external fault input |
| 03.00 | 8 | Relay RA/RB/RC = **fault indication** (matches the sketch: RA→I0.5, RB→healthy lamp) |
| 02.02 / 02.05 / 08.15 | 0 / 1 / 0 | Ramp to stop / no run at power-on / no auto restart |
| 06.06 / 07.00 | 2 / 2.5 A | Motor overload protection **disabled** (factory) / motor current = drive rating (the motor plate says 1.82 A) |
| 06.08–06.12, 07.10 | 0, 633 | No stored faults; 633 minutes total run time |
| 09.00–09.04 | 1, 1, 3, 0, 0 | Factory communication: address 1, 9600 baud, ASCII 7N2 |

- **Input mode:** the PLC outputs give +24 V, so the drive's inputs must be in **PNP** mode (switch on the drive; factory = NPN) with **DCM joined to the panel 0 V**.
- **Different from the manual's factory values** (the list to expect when the new drive is compared): 00.12, 01.00, 01.01, 01.09, 01.10, 01.12, 01.13, 02.00, 02.11, 02.12, 03.08, 04.05–04.08, 07.08.
- **Group 10 (PID)** is off (10.00 = 0).
- **Still to look at on the old panel:** a Q0.2 → MI5 wire (yes/no), and the NPN/PNP switch position.

### 5.2 New motor + gearbox (15 Oct 2026): what changes on the VFD

| | Old machine | New machine |
|---|---|---|
| Gearbox | Bonfiglioli **VF49 F1 18 P71 B5 B3** (worm, i = 18, hollow output shaft) | Inline helical, foot mounting, i = **16.67**, shaft Ø20, 84 rpm, 41 Nm, SF 2.6, frame 71 |
| Motor | Bonfiglioli BE 71B 4, 0.37 kW, **1385 rpm**, 230/400 V Δ/Y, 1.82 A (Δ) | **Transtech TM71 B4**, 0.37 kW, **1400 rpm**, **240 V Δ 1.6 A / 415 V Y 1.1 A**, 50 Hz, PF 0.74, IE2, IP55, class F, S1, B5 flange |
| Output speed at 50 Hz | 1385 / 18 = **76.9 rpm** | 1400 / 16.67 = **84.0 rpm** (matches the supplier's 84 rpm, so the ratio is confirmed) |

- **The new drive train is about 9 % faster per Hz.** For the same belt speed: **new frequency = 0.916 × old frequency** (old 50 Hz → 45.8 Hz; 60 → 55.0; 70 → 64.1). The speed comes from the keypad knob (02.00 = 4), so **no speed parameter changes**: read the old drive's F value while running, then turn the new knob to 0.916 × that value. Fine-tune by timing the belt over a fixed length on both machines. This assumes the same drum diameter.
- **Motor connection: DELTA** (240 V Δ), the same as the old motor.
- **Parameter changes:**
  - **07.00 = 1.6 A** (raw 16; the old drive had 2.5 A);
  - recommended **06.06 = 0** (motor overload protection on);
  - everything else stays as on the old drive (01.00 70 Hz, 01.01 50 Hz, 01.02 220 V, 00.12 = 1, ramps 5.0 / 0.5 s, V/F mode, compensation off, so 07.01 / 07.06 have no effect).
- **Old drive F value (photo, 15 Oct 2026): F 70.0, knob turned fully clockwise.** The old belt runs at the maximum frequency 01.00 = 70.00 Hz.
- **New drive: set 01.00 = 64.10 Hz (raw 6410) and turn the knob fully clockwise.** That gives 70 × 0.916 = 64.1 Hz, the same belt speed, and is exactly repeatable (no fiddly knob position).
- **Final changes on the new drive vs the old:** 01.00 = 64.10 Hz, 07.00 = 1.6 A, optional 06.06 = 0. Everything else is identical.
- **Still needed:** confirm the conveyor drum is the same as on the old machine.

### 5.3 Programming the NEW drive from the laptop (tool ready 15 Oct 2026, not used yet)

`04_VFD/write_new_vfd.py` is the only tool that writes. It writes only with `--yes`, and only after the user approved the printed plan.

**Safety locks (all tested on a simulated drive):**
- refuses a drive with ≥ 300 min run time (07.10; the old drive has 633) or with the old drive's signature settings;
- refuses if any planned parameter differs from the new readout, i.e. a different drive;
- refuses a running drive (2101H / 2103H);
- writes only parameters on an allow-list (writable settings in the VFD-EL manual). Never 00.02, group 09, 07.04, read-only, fault records, counters or unknown EL-W parameters;
- sends only functions 03 / 06, never the command registers 2000H–2002H;
- reads each write back and stops at the first problem; logs every frame.

**Run sequence** (new drive wired A+→SG+, B-→SG-, only the new drive powered, motor stopped; `D=04_VFD/VFD_NEW_CONTROL_BOX_<n>`):
1. `/usr/bin/python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --probe`
2. `/usr/bin/python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --address 1 --baud 9600 --format ascii-7N2 --out $D/new_before.csv --log $D/read_before_frames.txt`
3. `/usr/bin/python3 04_VFD/write_new_vfd.py plan --old 04_VFD/VFD_OLD_MACHINE/old_vfd_parameters.csv --new $D/new_before.csv --out $D/plan.csv [--overload-protection]` → show the plan to the user and wait for **YES**.
4. `/usr/bin/python3 04_VFD/write_new_vfd.py write --plan $D/plan.csv --port /dev/ttyUSB0 --log $D/write_frames.txt` (dry run, checks only)
5. Same command with `--yes --result $D/write_result.csv`
6. The user switches the drive OFF and ON → read again to `$D/new_after.csv` → `write_new_vfd.py verify --plan $D/plan.csv --readout $D/new_after.csv` → also `read_vfd_parameters.py --compare` against the old drive.

Expected extra values on top of "same as old": **01.00 = 6410 (64.10 Hz), 07.00 = 16 (1.6 A)**, and 06.06 = 0 only if the user wants overload protection.

**15 Oct 2026: NEW CONTROL BOX 2 (CB2) VFD read and programmed**
- **As received** (saved before any change, locked + `backup/`): `04_VFD/VFD_NEW_CONTROL_BOX_2/CB2_as_received_2026-10-15.csv/.json/.txt` (306 parameters; 567 frames, all function 03).
- **Not factory-new:** 345 min run time, and settings changed by someone before:
  - 02.01 = 0 (keypad run: the PLC could not start it);
  - 02.04 = 1 (reverse disabled);
  - 02.10 = 1;
  - 01.01 = 59.99 Hz;
  - MI4–MI6 different.
- The display showed F 60.0.
- The write tool's old-drive lock was changed from ≥ 300 to ≥ 633 total minutes (the OLD MACHINE's count on 7 Oct; counters only go up).
- **Written (user approved "after that write"), 15 parameters, all read back OK:**
  - 01.00 6000→**6410**, 01.01 5999→5000, 01.09 100→50, 01.10 100→5, 01.12 100→1, 01.13 10→1;
  - 02.01 0→**1**, 02.04 1→**0**, 02.10 1→0, 02.11 2580→5000, 02.12 6000→5000;
  - 04.06 1→0, 04.07 2→**5**, 04.08 3→14;
  - 07.00 25→**16**.
  - Log `CB2_write_frames.txt`: 70 frames, 55 × fn 03, 15 × fn 06, no command register. Result `CB2_write_result.csv`.
- **Not written:**
  - 06.06 (overload protection; the user did not decide, left = old machine: off);
  - 04.19 ("Reserved" in both Delta manuals; OLD 1, CB2 0);
  - read-only values, the counter.
- **Power cycle check (15 Oct):** the user switched it OFF/ON; the display shows **F 64.1** (knob fully clockwise). Read `CB2_after_write_power_cycled.csv`: **all 15 writes stored**. Compared with the OLD MACHINE, only 01.00 (6410 vs 7000), 07.00 (16 vs 25), 04.19 (reserved) and the counter differ.
- **06.06 = 0 written afterwards** (`CB2_write_plan_2_overload.csv`, `CB2_write_2_result.csv`, read back OK). The user's rule: the aim is to replicate the OLD MACHINE exactly (same speed, same behaviour), because the motor and gearbox are a different type; anything that does not change that may be set. Overload protection does not change speed or normal behaviour: it only trips the drive (fault → PLC alarm) on a long overload such as a jammed belt.
- **CB2 final = OLD MACHINE settings, except:** 01.00 = 64.10 Hz (same belt speed with the new motor and gearbox), 07.00 = 1.6 A (new motor), 06.06 = 0 (protection on), 04.19 untouched.
- **Still to do for CB2:** run the belt and time a mark over a fixed length on the OLD MACHINE and on CB2's conveyor, to confirm the same speed. Matters for the camera, whose trigger delay is 3 s.
- **15 Oct 2026, CB2 panel commissioning:**
  - Motor connected in **delta** (checked by the user).
  - HMI cable plugged straight into the PLC (no switch); the Windows laptop on the PLC port at 192.168.0.100.
  - **Fault found:** the Emergency alarm would not reset and no PLC input LED ever lit. Cause: **PLC terminal 1M was not connected to 0 V**. Fixed by the user (1M → 0 V).
  - Then a read-only I/O check over Modbus (`08_Commissioning/plc_io_read.ps1`): every input and output correct (I0.1 selector, I0.2 START, I0.3 STOP NC, I0.4 E-stop NC, FAULT RESET → Q0.2 pulse, HMI jogs → Q0.0 / Q0.1, AUTO + START → Q0.0 + green). I0.5 stayed 0.
  - **Still to check by eye:** the motor turns, the direction, the tower lamps really light (the bill says 220 V AC), the belt speed vs the OLD MACHINE.
- **15 Oct 2026, CB2: two more faults reported:**
  - (a) **Belt runs the wrong direction.** Expected: the new helical gearbox turns the opposite way to the old worm gearbox. Fix: power OFF, wait 5 min, swap two motor wires (U, V). Do not swap the PLC outputs or MI1 / MI2.
  - (b) **REV jog does nothing.** The PLC is fine (Q0.1 ON in the I/O test). The VFD settings are fine (02.04 = 0, 04.04 = 0, 04.09 = 0). So it is the Q0.1 → MI2 wire: probably on MI3 (no function, 04.05 = 0) or loose. Check 24 V between MI2 and DCM while REV JOG is held.
  - Waiting for the user's result.
- **15 Oct 2026, CB2 reverse fault solved (cause found by watching PLC + VFD together):**
  - The PLC sent Q0.1 and the drive saw MI2 (04.26 bit 1), but stayed STOP.
  - **Cause: 04.19.** On the **VFD-EL-W** it is the start / stop control mode (0 = RUN / STOP by MI1 only, MI2 = multi-function; 1 = 2-wire / 3-wire with MI1, MI2, MI3). Source: Delta VFD-EL-W catalogue 2022-02 (factory: MI1 Run/Stop, MI2 multi-step). The plain VFD-EL manual wrongly lists it as "Reserved", so it had been left out on purpose.
  - The OLD MACHINE has 04.19 = 1. **Written 04.19 = 1** (`CB2_write_plan_3_0419.csv`, `CB2_write_3_result.csv`, read back OK). 04.19 is now on the write tool's allow-list.
  - The forward direction was confirmed in the watch: the drive ran FWD to 64.10 Hz, but the belt moves the wrong way, so swap U / V at the motor.
- **CORRECTION (15 Oct 2026):** the VFD-EL-W control strip has only **MI1, MI2, MI3** (+ DCM, SG+, SG-), no MI5. Earlier notes and the Rebuild Guide Rev 5 (section 7) say "Q0.2 must go to MI5"; that is **not valid for the EL-W**. Where Q0.2 should go on the EL-W (if anywhere) is still open: check the OLD MACHINE panel. Fix the guide.
- **15 Oct 2026, CB2 works:** after 04.19 = 1, the power cycle and swapping two motor wires, **forward and reverse jog both run correctly** (confirmed by the user). The Rebuild Guide has the MI5 statements corrected (Q0.2 stays unwired; EL-W = MI1–MI3 only) and 04.19 added; vfd_el_params.py updated.
- **New finding (15 Oct): the new conveyor's drive roller is Ø100 mm** and the belt runs faster than the OLD MACHINE. The 64.10 Hz assumed the same roller as the old machine.
  - Formula: new Hz = 64.13 × (old roller Ø / 100 mm).
  - Needs the OLD MACHINE's drive roller diameter, or a timed belt-speed comparison.
  - If the result is below 50 Hz, 01.00 cannot go that low (minimum 50 Hz): keep 01.00 = 50.00 and limit with 01.07 (output upper limit, % of 01.00) instead.
- **Earthing (15 Oct):** the user measured ~70 V AC between earth and neutral in the workshop (the earth is not working) and disconnected the PLC earth terminal. Advice given: connect the PLC ⏚ to PE at the site, where the earth is proper. 70 V earth–N means no real earth (leakage through the VFD / SMPS filters), so the panel enclosure is not safe to touch. Have an electrician fix or verify the earth (earth–N should be a few volts at most) before running.
- **15 Oct 2026, roller speed correction (CB2):** the OLD MACHINE's drive roller is **Ø 58.34 mm** (from the user); the new one is Ø 100 mm.
  - Old belt = π × 0.05834 × (1385/18 × 70/50 = 107.7 rpm) = **19.74 m/min**.
  - New: π × 0.100 × (1400/16.67) × f/50 = 19.74 → **f = 37.41 Hz**. At 64.1 Hz the belt ran 33.8 m/min (1.71× too fast).
  - 01.00 cannot go below 50 Hz, so: **01.00 = 50.00 Hz (raw 5000) and 04.02 knob gain = 74.8 % (raw 748)**, knob fully clockwise.
  - Written and read back (`CB2_write_plan_4_roller_speed.csv`, `CB2_write_4_result.csv`). The drive's frequency command now reads **37.40 Hz** (the display should show **F 37.4**).
  - The write tool's NEW_MACHINE values were updated to 01.00 = 5000, 04.02 = 748, 07.00 = 16, for CB1.
  - **Confirmed by the user (15 Oct 2026): "perfect"**, the new conveyor now runs at the old machine's speed. Optional later check: time 2 m (about 6.1 s at 19.74 m/min).
- **CB2 final VFD = OLD MACHINE settings except:** 01.00 = 50.00 Hz, 04.02 = 74.8 %, 07.00 = 1.6 A, 06.06 = 0 (protection on). 04.19 = 1 like the old machine.
- **Next: NEW CONTROL BOX 1**, the same way (read and save as received first).

### How to run the tool (from the PLC folder)

The commands use `/usr/bin/python3`.

```
# probe: reads 11 values only, saves nothing
/usr/bin/python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --probe
# full read
/usr/bin/python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --address 1 --baud 9600 --format ascii-7N2 \
    --out 04_VFD/VFD_NEW_CONTROL_BOX_<n>/new_vfd_parameters.csv --log 04_VFD/VFD_NEW_CONTROL_BOX_<n>/new_vfd_frames.txt
# compare old and new
/usr/bin/python3 04_VFD/read_vfd_parameters.py --compare 04_VFD/VFD_OLD_MACHINE/old_vfd_parameters.csv 04_VFD/VFD_NEW_CONTROL_BOX_<n>/new_vfd_parameters.csv
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
5. **Q0.2 wire** (VFD fault reset). Look on the old panel: is there a wire from Q0.2 to drive terminal **MI5** (the only input set to reset)? Also note the **NPN/PNP switch** position on the old drive (expected: PNP).
6. **Camera:** confirm where `05_Camera/final.mfa` came from (an export from the old camera?). Load it into the new camera with HIKROBOT MVS / IDMVS, and set IP 192.168.0.78.
7. **GitHub push not done yet.** The local commits (7 Oct and 9 Oct) are not on either GitHub repo. The user must run `git push origin main` and `git push company main` (section 10).
8. **GitHub tokens:** two tokens (Charan-mdnl and charanxp) were pasted in chat on 7 Oct. Revoke both on GitHub (Settings → Developer settings → Personal access tokens) and make new ones when needed.

9. **Remote TIA Portal (12 Oct 2026, setup mostly done).** Windows 11 Home laptop `XP_Robotics`, user `xprobotics` (administrator). It has TIA Portal V21 + the Openness API (`C:\Program Files\Siemens\Automation\Portal V21\PublicAPI\V21\net48\`). Link: a **second Tailscale** for the user's own account charanxpwork@gmail.com runs on this PC in userspace mode (`/usr/sbin/tailscaled --tun=userspace-networking --statedir=~/.local/share/tailscale-xp --socket=~/.local/share/tailscale-xp/tailscaled.sock --port=41642`, autostart since 12 Oct 2026 as the user service `~/.config/systemd/user/tailscale-xp.service`, enabled at login; status: `systemctl --user status tailscale-xp`; remove: `systemctl --user disable --now tailscale-xp`). This PC = `charan-lenovo-xp` 100.74.159.40, laptop = `xp-robotics` 100.96.36.99. The company Tailscale (rockzz12344321, 100.80.182.55) is untouched. `ssh xp-robotics` works with this PC's key, no password (entry in ~/.ssh/config, backup ~/.ssh/config.bak-2026-10-12; key in C:\ProgramData\ssh\administrators_authorized_keys, ACL locked). Work folder on the laptop: `C:\Users\xprobotics\claude_work`. **Careful:** the user says the TIA Portal on the laptop is a third-party (unlicensed) install that cannot be reinstalled. Never touch the TIA program files, the Automation License Manager, licenses or updates; work only through Openness on test projects in claude_work. **Waiting for:** the user to add `xprobotics` to the 'Siemens TIA Openness' group and sign out/in (Claude was blocked from doing it). Openness group done (12 Oct). Openness V21 loads (main dll `Siemens.Engineering.Base.dll` + `Siemens.Engineering.Step7.dll`). **Finding:** over SSH the commands run in Windows session 0 (no desktop), and `new TiaPortal(WithoutUserInterface)` fails there with "Connection to TiaPortal failed". Openness must run in the user's desktop session. Test files are in claude_work: `TiaTest.cs`, `FC_Test.scl`, `run_test.ps1` (log -> `run_test_log.txt`), `RUN_TEST.bat` (the user double-clicks it), `cleanup_test_tia.ps1` (stops only non-desktop TIA processes). **Openness works in the desktop session** (12 Oct 16:56: test project created, SCL imported, compile 0 errors / 0 warnings). The old project was copied to `claude_work\old_project_copy\latest plc.ap21` (a copy; the original stays on this PC). `EXPORT_OLD_PROGRAM.bat` → `export_old.ps1` + `ExportOld.cs` opens that copy, exports all blocks, tag tables and types as XML to `claude_work\old_export_<time>\`, and closes WITHOUT saving. Goal: read the old ladder exactly (the user says the guide's ladder doesn't look like the original, and some logic was not mentioned). Waiting for: the user to double-click EXPORT_OLD_PROGRAM.bat.

10. **Correct the guides to match the real program (section 11.1)**. **Done 12 Oct for all three PDFs** (tutorial Rev 3 incl. HMI, Explained Rev 2, Rebuild guide Rev 4). Earlier plan:
    - Tutorial Rev 2.1 → Rev 3: 3 tag tables with spares; clock memory byte ON at MB0; DB_TCP_IP stays optimized; FC_AUTO drawn as the real 6 networks; network titles; MB_SERVER V5.3.
    - Explained PDF: fix "M0 left free" and "all DBs non-optimized".
11. ~~HMI not exported yet~~ **Done 12 Oct** (section 11.4). Still open: the **alarm views** and the **discrete alarm list** cannot be exported. They are taken from the Feb 2026 screen files. Check the ALARMS screen of the old panel.
12. **Real PLC vs file:** upload the program from the OLD PLC (TIA: Online → Upload device as new station) and export it the same way. This shows whether the PLC holds a newer program, for example the red-button reverse the user remembers.

13. **VS Code on the Windows laptop → this PC (Remote-SSH): WORKING since 12 Oct 2026.** The user works at the laptop, and Claude Code runs on this PC (logged in here, no OTP). The laptop key is `C:\Users\xprobotics\.ssh\id_ed25519`; the laptop's `~/.ssh/config` Host `charan-pc` → 100.74.159.40, user charan; the Remote-SSH extension is on the laptop. This PC: openssh-server installed and enabled; `~/.ssh/authorized_keys` allows the laptop key only from 127.0.0.1 / 100.64.0.0/10; linger on, so the user service `tailscale-xp` starts at boot (the hand-started copy is retired). Test `ssh charan-pc` from the laptop: OK. Use: VS Code on the laptop → bottom-left >< → Connect to Host → charan-pc → open /home/charan/Documents/PLC; install Claude Code "in SSH: charan-pc" once. SSH password login on this PC is OFF (`/etc/ssh/sshd_config.d/10-no-password.conf`, 12 Oct; checked: password refused, laptop key OK). Keep this PC on, charging, lid open.

---

## 8. Safety rules (always)

- **VFD:** only READ (Modbus function 03). Never write, reset, start/stop or change frequency on the **old** drive.
- Never touch or move terminals while they are powered. Wire the adapter with the power OFF.
- Keep the conveyor stopped while reading (on 7 Oct, everything except the VFD was switched off).
- `01_Old_Project_AS_RECEIVED/` is the original. Never edit it; work on copies.
- Old VFD readout files are locked read-only. Keep the backup copy.

---

## 9. Change log of this README

- 2026-10-12: autostart for the second Tailscale enabled (user asked). TIA on the laptop is unlicensed and cannot be reinstalled, so work with extra care.
- 2026-10-15: CB2 speed confirmed by the user; project committed for GitHub.
- 2026-10-15: roller Ø58.34 (old) vs Ø100 (new): CB2 set to 37.4 Hz (01.00 50 Hz + 04.02 74.8 %); the write tool updated for CB1.
- 2026-10-15: CB2 forward/reverse OK; guide corrected (04.19, MI5); roller Ø100 mm found (speed recalculation pending the old roller Ø); earthing advice.
- 2026-10-15: CB2 reverse fault: 04.19 (EL-W start/stop mode) written = 1 like the old machine; correction: the EL-W has no MI5.
- 2026-10-15: CB2 panel: 1M→0V fault found and fixed; full I/O test OK (08_Commissioning).
- 2026-10-15: CB2 verified after power cycle (all stored, F 64.1); 06.06 = 0 written (protection on, does not change speed).
- 2026-10-15: names fixed: OLD MACHINE / NEW CONTROL BOX 1 / NEW CONTROL BOX 2 (section 1b); VFD folders renamed (old_vfd_2026-10-07 → VFD_OLD_MACHINE, OLD_VFD_BACKUP_2026-10-07 → VFD_OLD_MACHINE_BACKUP); CB2 VFD saved as received and programmed (15 writes OK); power-cycle verify pending.
- 2026-10-15: write tool for the new drive (04_VFD/write_new_vfd.py) + tests ready; section 5.3 = run sequence. Not used on a drive yet.
- 2026-10-15: old F value = 70.0 Hz (knob at end), so the new drive gets 01.00 = 64.10 Hz with the knob at the end.
- 2026-10-15: 5.2 updated with the new motor nameplate (Transtech TM71 B4, 1400 rpm, 240 V Δ 1.6 A): factor 0.916, 07.00 = 1.6 A.
- 2026-10-15: section 5.2 added: new motor + helical gearbox (i 16.67) vs old VF49 i 18; speed factor 0.89; 07.00 to the new nameplate current.
- 2026-10-13: tutorial Rev 3.2 (needed / not needed marks, minimum build); section 11.5 added.
- 2026-10-13: tutorial Rev 3.1 (one row per item); Rebuild guide Rev 5 (exact VFD section + Appendix C); section 5.1 added (decoded VFD settings); Delta manual saved in 04_VFD/manual (git-ignored).
- 2026-10-12: Remote-SSH laptop → this PC working (pending 13 updated).
- 2026-10-12: pending 13 added: VS Code Remote-SSH from the laptop to this PC (laptop side done; sudo steps on this PC pending).
- 2026-10-12: HMI exported and compared (section 11.4); all three PDFs corrected (Rebuild guide Rev 4 added); pending 10 and 11 updated.
- 2026-10-12: guides corrected (tutorial Rev 3, Explained Rev 2); section 2.10 added (red-button reverse jog requirement and design); 2.8 updated.
- 2026-10-12: section 11 added: exact old program read from the TIA export, comparison table, correct logic. Folder 07_Old_Program_Export added. Pending items 10-12 added.
- 2026-10-12: remote link working (2nd Tailscale charanxpwork + SSH key); TIA V21 + Openness found on the laptop; Openness group still to be done by the user.
- 2026-10-12: pending item 9 added: remote TIA Portal over Tailscale + SSH + Openness (setup steps given, waiting for the user).
- 2026-10-09: section 2 rewritten with the user's full explanation of 6 Oct: how the system works, how the devices communicate, all operator options, points to check.
- 2026-10-09: new Explained PDF, tutorial Rev 2.1, rebuild guide Rev 3 (real VFD values, 07.00 fix); wiring photo 2 verified; OB1 order verified.
- 2026-10-07: company repo charanxp/Conveyor_PLC added as a remote (push still to be done by the user).
- 2026-10-07: pushed to GitHub Charan-mdnl/Conveyor_PLC (public, by the user's choice).
- 2026-10-07: created. Folder reorganised, VFD readout recorded, BOM updated from the Pavitra + Nanologic bills.

---

## 10. GitHub

- Two copies, both public, branch `main`, same content:
  - personal: https://github.com/Charan-mdnl/Conveyor_PLC  (git remote `origin`)
  - company:  https://github.com/charanxp/Conveyor_PLC     (git remote `company`)
- The local folder `PLC/` is the git working copy. After each change push to BOTH: `git push origin main` and `git push company main`.
- Claude Code's safety check blocks Claude from pushing, so **the user runs the push** in the VS Code terminal: username = the account name, password = that account's token.
- To upload changes: `git add -A && git commit -m "..." && git push`. Pushing needs a token or SSH key; never put the token in a file.

---

## 11. Old PLC program: exact logic (read from TIA Portal, 12 Oct 2026)

**Source:**
- A copy of "latest plc" was opened in TIA Portal V21 on the laptop through Openness.
- All blocks and tag tables were exported as XML, and the copy was closed without saving. The original project was never opened.
- The files are in `07_Old_Program_Export/`. The whole program as readable logic is in `07_Old_Program_Export/OLD_PROGRAM_LOGIC.txt`.
- This replaces the earlier understanding, which was decoded from the raw project file on 5–6 Oct.

**Limit:** this is the program in the **file** "latest plc". If the real old PLC holds a newer program, it can differ (pending item 12).

### 11.1 Earlier understanding vs. the real program

| # | Item | What I said before (tutorial Rev 2.1 / Explained Rev 1) | What the TIA export shows | Effect |
|---|---|---|---|---|
| 1 | PLC tag tables | One "Default tag table" with 19 own tags | **Three tables:** **DI** (14 tags: I0.0–I0.5 + spares `DI_SPARE I0.6` … `DI_SPARE I1.5`), **DO** (10 tags: Q0.0–Q0.5 + spares `DO_SPARE Q0.6` … `DO_SPARE Q1.1`), **Default tag table** (system + clock tags + the 7 flags M2.0–M2.6) | Logic the same. For an exact copy, make DI and DO tables with the spares |
| 2 | Clock memory byte | "Leave the clock memory byte unticked"; Explained PDF: "M0 is left free" | **Clock memory is switched ON at MB0** (Clock_10Hz M0.0 … Clock_0.5Hz M0.7). No network uses it | Tick it at address 0 to match |
| 3 | DB_TCP_IP | Untick "Optimized block access" on all DBs; offsets 14.0 / 18.0 / 22.0 | **DB_TCP_IP is OPTIMIZED.** DB_HMI, DB_ALARMS, DB_AUTO, DB_CAMERA are Standard (not optimized) ✔ | Leave DB_TCP_IP optimized (it has no offsets) |
| 4 | FC_AUTO layout | Part 8: 3 simplified networks, and the old-file order "start/stop, big network, reset, status, SCL, camera done" | **6 networks + 1 empty, in this order:** 1 AUTO ON, 2 STOP DELAY TIME (SCL), 3 CONVEYOR ON (run rung + the switched-off sensor cycle in one network), 4 CAMERA DONE, 5 CONVEYOR OFF RESET, 6 AUTO STATUS (10/20/30) | **Behaviour is the same** (the sensor cycle is blocked by `NOT AlwaysTRUE`), but the drawing must follow the real 6 networks to look like the original. My order in the tutorial's appendix was wrong |
| 5 | Network titles and empty networks | Not given | Every network has a title (list in 11.2). OB1 and every FC end with one **empty** network | Cosmetic; copy for an identical look |
| 6 | MB_SERVER version | Not stated | **MB_SERVER V5.3**, instance DB `MB_SERVER_DB` | When placing MB_SERVER, choose version 5.3 |
| 7 | OB1 call order | FC_AUTO, FC_ALARMS, FC_GENERAL, FC_MANUAL, FC_OUTPUTS, FC_TCP_IP | Same ✔ (+ empty network 7) | – |
| 8 | FC_GENERAL, FC_MANUAL, FC_ALARMS, FC_OUTPUTS, FC_TCP_IP logic | As drawn in the tutorial | Same ✔ | – |
| 9 | Red STOP button reverses in MANUAL (user's memory) | "Not in the file" | **Confirmed not in the file.** I0.3 (STOP) is used only in FC_AUTO. Reverse comes only from the HMI REV JOG | **Resolved 12 Oct:** the user says it was wanted but never built. It is now a new feature (section 2.10, tutorial Part 12) |
| 10 | PC "remote ON" (user's description) | PC writes 0 = run, 1 = stop | Same, and the PC **cannot start the cycle**: the belt runs only when `ACTIVE` (START pressed in AUTO) **and** DATA1 = 0. In MANUAL the PC has no effect | The PC can stop and release the belt, not start the cycle |
| 11 | Station name | PLC_1 | Device "S7-1200 station_1", PLC "PLC_1"; HMI "HMI_1" | Cosmetic |
| 12 | DB start values | All 0 | All default (0) ✔ | – |

### 11.2 The correct logic, block by block

**Main [OB1]**
- Calls, in order: FC_AUTO, FC_ALARMS, FC_GENERAL, FC_MANUAL, FC_OUTPUTS, FC_TCP_IP.
- Network 7 is empty.

**FC_GENERAL [FC1]**
1. *CONTROL ON:* `CONTROL ON FLAG (M2.0) := DI_EMERGENCY PB (I0.4)`
2. *MODE SELECTION:*
   - `MANUAL MODE SELECTED (M2.1) := AlwaysTRUE AND NOT DI_AUTO MANUAL SELECTION (I0.1)`
   - `AUTO MODE SELECTED (M2.2) := AlwaysTRUE AND DI_AUTO MANUAL SELECTION`
3. *FAULT RESET:* `FAULT RESET FLAG (M2.3) := "DB_HMI".FAULT RESET PB`
4. (empty)

**FC_MANUAL [FC2]**
1. *MOTOR FWD /REV ON:*
   - `MANUAL CONVEYOR FWD ON FLAG (M2.5) := CONTROL ON AND MANUAL MODE AND NOT FAULT BIT AND ("DB_HMI".MOTOR JOG FWD PB OR DI_CYCLE START PB (I0.2))`
   - `MANUAL CONVEYOR REV ON FLAG (M2.6) := CONTROL ON AND MANUAL MODE AND NOT FAULT BIT AND "DB_HMI".MOTOR JOG REV PB`
2. (empty)

**FC_ALARMS [FC3]**
1. *EMERGENCY PB PRESSED FAULT (I0.4):* SET `"DB_ALARMS".EMERGENCY PB PRESSED FAULT` when `NOT DI_EMERGENCY PB`
2. *CONVEYOR VFD FAULT (I0.5):* SET `"DB_ALARMS".VFD FAULT` when `DI_CONVEYOR VFD FAULT`
3. *FAULT RESET:* MOVE 0 → `%DB2.DBW0` (all 16 alarm bits) when `FAULT RESET FLAG`
4. *FAULT BIT:* `FAULT BIT (M2.4)` and `"DB_ALARMS".FAULT POP := (%DB2.DBW0 <> 0)` (CMP <> Word, IN1 = 0, IN2 = %DB2.DBW0)
5. (empty)

**FC_OUTPUTS [FC4]**
1. *CONVEYOR FWD ON:* `Q0.0 := MANUAL CONVEYOR FWD ON FLAG OR "DB_AUTO".CONVEYOR ON`
2. *CONVEYOR REV ON:* `Q0.1 := MANUAL CONVEYOR REV ON FLAG`
3. *FAULT RESET:* `Q0.2 := FAULT RESET FLAG`
4. *TL GREEN:* `Q0.3 := "DB_AUTO".ACTIVE`
5. *TL RED:* `Q0.4 := FAULT BIT`
6. *TL AMBER:* `Q0.5 := MANUAL MODE SELECTED`
7. (empty)

**FC_AUTO [FC5]**
1. *AUTO ON:* `"DB_AUTO".ACTIVE := CONTROL ON AND AUTO MODE AND NOT FAULT BIT AND (DI_CYCLE START PB OR "DB_AUTO".ACTIVE) AND DI_CYCLE STOP PB (I0.3, NC button)`. This is the latch.
2. *STOP DELAY TIME* (SCL network): `"DB_AUTO"."STOP DELAY TIMER".PT := "DB_HMI"."STOP TIME" * 1000;`
3. *CONVEYOR ON* (one big network; everything after the first rung is switched off):
   - `"DB_AUTO".CONVEYOR ON := AlwaysTRUE AND ACTIVE AND (NOT CONVEYOR OFF2 OR AlwaysTRUE) AND ("DB_CAMERA".DATA1 == 0)`. **This is the rung that runs the belt.** The OR with AlwaysTRUE makes the OFF2 contact have no effect.
   - Switched-off part, which starts with `AlwaysTRUE AND NOT AlwaysTRUE`, so it is never true:
     - TON `"DB_AUTO".SENSOR CHECK DELAY` (PT T#500MS) with IN = ACTIVE AND CONVEYOR ON;
     - then P_TRIG on `DI_PRODUCT SENSOR` (memory `"DB_AUTO".P_TRG`) → SET `CONVEYOR OFF1`.
   - `TON "DB_AUTO".STOP DELAY TIMER` (IN = CONVEYOR OFF1, PT = its own PT from network 2). When Q: RESET OFF1, MOVE 1 → `"DB_CAMERA".DATA1`, SET OFF2. This never happens, because OFF1 is never set.
4. *CAMERA DONE:* `"DB_AUTO".CAMERA DONE := CONVEYOR OFF2 AND ("DB_CAMERA".DATA1 == 0)`
5. *CONVEYOR OFF RESET:* RESET `CONVEYOR OFF1` and `CONVEYOR OFF2` when `AlwaysTRUE AND ((OFF2 AND ("DB_AUTO".CAMERA DONE OR "DB_HMI".CAMERA DONE)) OR NOT ACTIVE)`
6. *AUTO STATUS:*
   - MOVE 10 when ACTIVE AND NOT OFF2 (AUTO RUNNING);
   - MOVE 20 when NOT ACTIVE (STOPPED);
   - MOVE 30 when ACTIVE AND OFF2 (WAITING FOR CAMERA ACK, never happens now). All three start with AlwaysTRUE.
7. (empty)

**FC_TCP_IP [FC6]**
1. *Connection definition:* MOVE into `"DB_TCP_IP"."MY CONNECT DATA"`:
   - InterfaceId = Local~PROFINET_interface_1, ID = 1, ConnectionType = 11;
   - ActiveEstablished := NOT AlwaysTRUE (= 0);
   - RemoteAddress.ADDR[1..4] = 0, RemotePort = 0, LocalPort = 502.
2. *MB SERVER:* MB_SERVER V5.3, instance `MB_SERVER_DB`, DISCONNECT = AlwaysFALSE, MB_HOLD_REG = `P#DB5.DBX0.0 INT 10`, CONNECT = `"DB_TCP_IP"."MY CONNECT DATA"`.
3. *ERROR CHECK:*
   - `NO OF DONE := NO OF DONE + 1` (UDInt) when NDR OR DR;
   - `NO OF ERROR := NO OF ERROR + 1` when ERROR;
   - MOVE STATUS → ERROR STATUS when ERROR.

**Data blocks**

| DB | Optimized? | Contents |
|---|---|---|
| DB_HMI (DB1) | No (Standard) | FAULT RESET PB, MOTOR JOG FWD PB, MOTOR JOG REV PB (Bool), STOP TIME (DInt), CAMERA DONE (Bool) |
| DB_ALARMS (DB2) | No (Standard) | EMERGENCY PB PRESSED FAULT, VFD FAULT, SPARE1–SPARE14, FAULT POP, WARNING POP (all Bool) |
| DB_AUTO (DB3) | No (Standard) | ACTIVE, CONVEYOR ON, CONVEYOR OFF1, CONVEYOR OFF2, P_TRG, CAMERA DONE (Bool), AUTO STATUS (Int), STOP DELAY TIMER, SENSOR CHECK DELAY (IEC_TIMER) |
| DB_CAMERA (DB5) | No (Standard) | DATA1–DATA19 (Int); DATA1 = Modbus 40001 |
| DB_TCP_IP (DB12) | **Yes (Optimized)** | MY CONNECT DATA (TCON_IP_v4), NO OF DONE, NO OF ERROR, ERROR STATUS (UDInt) |
| MB_SERVER_DB (DB4) | instance | created by TIA for MB_SERVER V5.3 |

### 11.3 What the machine really does (from this logic)

- **AUTO:** START latches ACTIVE (green lamp). The belt runs while ACTIVE and DATA1 = 0. STOP, Emergency, a fault or switching to MANUAL drops ACTIVE.
- **PC:** writes DATA1 = 1 to stop the belt and 0 to let it run again. It cannot start the cycle; START on the panel must have been pressed.
- **MANUAL:** amber lamp. HMI FWD JOG or the green START runs forward while held; HMI REV JOG runs reverse while held. The red STOP button does nothing in manual (in this file).
- **Faults:** Emergency or VFD fault set alarms that stay latched, turn on the red lamp and stop everything. HMI FAULT RESET (held) clears them and pulses Q0.2. Then START must be pressed again.

### 11.4 HMI: earlier understanding vs. the TIA export

The source is `07_Old_Program_Export/OLD_HMI.txt`.

| # | Item | Tutorial Rev 2.1 said | TIA export shows |
|---|---|---|---|
| 1 | Template name | Template_1 | **MAIN**, background 182,182,182 |
| 2 | Screen names (numbers) | AUTO OPERATION, MANUAL OPERATION, ALARMS, INPUT STATUS, OUTPUT STATUS-1 | **AUTO (1), MANUAL (2), ALARMS (3), INPUT STATUS (10), OUTPUT STATUS (19)**. The last two are in the screen folder **IOs**. "AUTO OPERATION" and so on are only the title texts on the screens |
| 3 | HMI tag tables | One table, 12 tags | **3 tables:** Default (10 tags, including the internal Tag_ScreenNumber and the old-cycle tags DB_HMI_STOP TIME and DB_HMI_CAMERA DONE), **IO** (IB0, IB1, QB0, QB1), **ALARMS** (ALARM WORD). All tags: connection HMI_Connection_1, cycle 1 s |
| 4 | ALARM WORD | Word | **Int**, absolute %DB2.DBW0, acquisition **Continuous** (the others are "Visible" = cyclic in operation) |
| 5 | Text list name | AUTO_STATUS | **AUTO STATUS** (with a space): 10/20/30. MODE: bit 0 MANUAL, bit 1 AUTO ✔ |
| 6 | HMI buttons (JOG, FAULT RESET) | SetBit on Press + ResetBit on Release | **SetBitWhileKeyPressed on Press** (bit 0). The JOG buttons also turn **green** while pressed (appearance animation, value 1) |
| 7 | Navigation buttons | "Click" event | **Press** event → ActivateScreen (AUTO, MANUAL, ALARMS, INPUT STATUS) |
| 8 | AUTO screen layout | Text at 19,135; status field 177,123, 560×52 | Text "AUTO STATUS" at **304,117, 165×34**; status field at **116,182, 560×106**, border 3, **green at 10, red (white text) at 20** |
| 9 | I/O lamps | Grey = 0, green = 1 | **Red = 0, green = 1** (single-bit animation); grey 217 only in the editor |
| 10 | BACK button on OUTPUT STATUS | Goes to INPUT STATUS | **Points to OUTPUT STATUS itself, so it does nothing** (an original mistake). Tutorial 10.5 offers the fix |
| 11 | Grey strip button 0,61 800×30 | "purpose could not be read" | Decoration only, **no event** |
| 12 | Alarm views (template + ALARMS screen), discrete alarms | 2 alarm views on the template, 1 on ALARMS; alarms on bits 8/9 | **Not in the export** (TIA's export does not include them). Kept from the Feb 2026 files and marked CHECK |
| 13 | Everything else (template objects, MANUAL buttons, I/O table rows) | – | Same positions, sizes and texts ✔ |

### 11.5 Minimum build: what the machine really needs (13 Oct 2026)

Derived from the exported program: an item is "needed" only if a working network or the HMI uses it. The minimum build behaves exactly like the old machine.

| Part | Needed | Not needed (identical copy only) |
|---|---|---|
| Hardware | System memory byte at MB1 (AlwaysTRUE / AlwaysFALSE are used) | Clock memory byte MB0 (never used) |
| PLC tags | I0.1–I0.5, Q0.0–Q0.5, flags M2.0–M2.6 (one tag table is enough) | DI_PRODUCT SENSOR (I0.0), 8 DI_SPARE, 4 DO_SPARE, separate DI/DO tables |
| DB_HMI | FAULT RESET PB, MOTOR JOG FWD PB, MOTOR JOG REV PB | STOP TIME, CAMERA DONE (old sensor cycle) |
| DB_ALARMS | All 18 rows (the 14 spares fill the 16-bit word DBW0) | – (WARNING POP is never set) |
| DB_AUTO | ACTIVE, CONVEYOR ON, AUTO STATUS (offsets stay 0.0 / 0.1 / 2.0) | CONVEYOR OFF1, OFF2, P_TRG, CAMERA DONE, both timers (old sensor cycle) |
| DB_CAMERA | DATA1 (used) + DATA2–DATA10 (MB_HOLD_REG is INT 10) | DATA11–DATA19 |
| DB_TCP_IP | MY CONNECT DATA | NO OF DONE, NO OF ERROR, ERROR STATUS (fault finding) |
| FC_GENERAL, FC_MANUAL, FC_ALARMS, FC_OUTPUTS | Every network | Titles, empty last networks |
| FC_AUTO | 3 short networks: ACTIVE latch; `CONVEYOR ON := ACTIVE AND DATA1 == 0`; MOVE 10 / 20 → AUTO STATUS | The SCL network, the switched-off rows of network 3, networks 4 and 5, MOVE 30 |
| FC_TCP_IP | Network 1 (connection), network 2 (MB_SERVER) | Network 3 (counters) |
| HMI | Connection; FAULT / RESET, AUTO and MANUAL buttons; the two JOG buttons. Useful: mode field, status field, alarms | Date/time, title, bars, the two I/O status screens (24 lamps), exact colours |

Rule: "old sensor cycle only" items go together with FC_AUTO way B (the 6 original networks); leave them all out with way A.

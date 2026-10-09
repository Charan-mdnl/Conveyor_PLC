"""Builds Conveyor_Panel_Rebuild_Guide.pdf  (revision 2).

Run:  PYTHONPATH=<folder with reportlab> python3 make_rebuild_guide.py <output.pdf> <temp folder>
"""
import os
import sys

from PIL import Image as PILImage, ImageOps
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph

from common import BAD, CHK, GREY, OKC, ST, Diagram, Doc

OUT, TMP = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root (PLC folder)
PICS = os.path.join(ROOT, "03_Wiring_Photos")

d = Doc()
d.title("Conveyor + Camera Control Panel",
        "Rebuild guide, Revision 3 (9 October 2026): panel, PLC, HMI, VFD, camera and PC program.<br/>"
        "Based on the old TIA Portal project \"latest plc\", your hand drawings, your BOM, your explanation of how the "
        "machine works, and the PC and camera files in the folder conveyor_automation-main.")

d.box("<b>What changed in Revision 3.</b> Section 7 now shows the real values read from the old drive on 7 October 2026 "
      "(motor current 07.00 corrected: the old drive holds 2.5 A, not 1.82 A), and the VFD tool notes say it has been used on the real drive. "
      "Files are now in numbered folders (see README.md in the PLC folder).", OKC)
d.box("<b>What changed from Revision 1.</b><br/>"
      "1. The IR sensor is wired to the <b>camera</b>, not to the PLC. PLC input I0.0 stays empty. Revision 1 told you to "
      "wire the sensor to I0.0. That was wrong.<br/>"
      "2. The conveyor is stopped and started by the <b>PC program</b> through Modbus register 40001. This is the real design. "
      "Revision 1 called it a test left in the program. That was wrong too.<br/>"
      "3. The PC program and two camera setting files were found in your folder. New sections 8 and 12 describe them.<br/>"
      "4. The VFD relay wiring (I0.5, purple wire, health lamp) is now read from your sketch (section 4.2).<br/>"
      "5. New: three ways to copy the VFD parameters, with a ready tool (section 7).", OKC)

# ------------------------------------------------------------------ 1
d.h1("1. How the machine works")
g = Diagram(72)
g.box(2, 58, 30, 11, "IR sensor")
g.box(58, 58, 44, 11, "Camera\n192.168.0.78", OKC)
g.box(128, 58, 44, 11, "PC with Lux WMS program\n192.168.0.77", OKC)
g.arrow(32, 63.5, 58, 63.5)
g.label(45, 65.2, "trigger wire", "middle")
g.arrow(102, 63.5, 128, 63.5)
g.label(115, 68.2, "QR codes: TCP 2002", "middle")
g.label(115, 65.2, "pictures: FTP 2005", "middle")
g.box(58, 30, 44, 13, "PLC S7-1200\n192.168.0.40", OKC)
g.line(150, 58, 150, 36.5)
g.arrow(150, 36.5, 102, 36.5)
g.label(105, 41.6, "Modbus TCP port 502")
g.label(105, 38.6, "register 40001:  0 = run, 1 = stop")
g.box(2, 34, 34, 10, "HMI KTP700\n192.168.0.41", OKC)
g.arrow(36, 39, 58, 39)
g.arrow(58, 39, 36, 39)
g.box(2, 14, 34, 13, "START, STOP,\nEmergency,\nAuto / Manual switch")
g.line(36, 20.5, 52, 20.5)
g.line(52, 20.5, 52, 33)
g.arrow(52, 33, 58, 33)
g.label(37.5, 22.2, "I0.1 - I0.4")
g.box(58, 6, 44, 10, "Tower lamp\ngreen / red / amber")
g.arrow(80, 30, 80, 16)
g.label(82, 22, "Q0.3 - Q0.5")
g.box(118, 12, 26, 12, "Delta VFD")
g.box(152, 12, 20, 12, "Motor")
g.line(102, 32, 110, 32)
g.line(110, 32, 110, 18)
g.arrow(110, 18, 118, 18)
g.arrow(144, 18, 152, 18)
g.label(112, 28.5, "Q0.0 forward, Q0.1 reverse")
g.label(118, 8.2, "VFD relay back to I0.5 = fault")
d.add(g.d)
d.sp(4)
d.h2("AUTO (selector at AUTO)")
d.steps([
    "Emergency released, no fault. Press the green <b>START</b> button. The PLC remembers the start (\"ACTIVE\"), the green lamp "
    "is ON and the conveyor runs forward. It runs as long as register 40001 is 0.",
    "The operator puts a row of boxes on the belt. The IR sensor sees them and triggers the camera <b>directly</b> (the PLC is not involved).",
    "The camera waits for its trigger delay (3 seconds in the saved settings), so the boxes are in the middle. It takes one picture, "
    "reads up to 6 QR codes, and sends the codes and the picture to the PC.",
    "The PC program counts the codes. Count equal to the <b>Stack Size</b> chosen on the PC screen (6 when the program starts; "
    "you can pick 2, 4, 6, 8, 10, 20 or type a number): nothing happens, the conveyor keeps running. "
    "Count different: the PC writes <b>1</b> to register 40001 and the PLC stops the conveyor.",
    "The operator corrects the boxes and clicks <b>Rescan Stack</b> (or <b>Start</b>) on the PC screen. The PC writes <b>0</b> and the conveyor runs again.",
    "The red <b>STOP</b> button or the Emergency button stops the cycle at any time."])
d.h2("MANUAL (selector at MANUAL, amber lamp ON)")
d.bullets(["Open the <b>MANUAL</b> screen on the HMI. Hold <b>CONVEYOR FWD JOG</b>, or hold the green START button: the conveyor runs forward while you hold.",
           "Hold <b>CONVEYOR REV JOG</b> on the HMI: reverse while you hold.",
           "The PC program cannot run the conveyor in manual mode."])
d.h2("After an Emergency stop or a VFD fault")
d.p("The alarm stays stored. Release the Emergency button (or clear the VFD fault), then press the yellow <b>FAULT RESET</b> button "
    "on the HMI (bottom right on every screen). Only then will the machine start again.")

# ------------------------------------------------------------------ 2
d.h1("2. Result of my verification")
d.table(["Item", "Result", "What it means for you"], [
    ["Your explanation of how the machine works", "OK, 1 point to check",
     "It matches the saved PLC program, the PC program and the camera settings. One difference: you say the red button runs "
     "reverse in manual mode. In the saved PLC program reverse comes only from the HMI button. See section 3, item 1."],
    ["PLC and HMI part numbers in the BOM", "OK",
     "Exactly the same as in the old program (CPU 1214C DC/DC/DC 6ES7214-1AG40-0XB0, HMI KTP700 Basic 6AV2123-2GB03-0AX0)."],
    ["Power drawing (page dated 18 Aug)", "OK",
     "Matches the BOM. One wording fix: the \"DC-DC converter\" is really the 230 VAC to 24 VDC power supply."],
    ["PLC I/O drawing (page dated 19 Aug)", "OK",
     "Every signal matches the program. I0.0 with no wire is correct, because the sensor goes to the camera."],
    ["VFD relay, purple wire, health lamp", "CHECK",
     "Read from your sketch: RC = +24 V, RA to I0.5 and the purple lamp wire, RB to the health lamp. Confirm on the old panel (section 4.2)."],
    ["Q0.2 (fault reset wire to the VFD)", "CHECK", "The program switches Q0.2, but your sketch shows no wire. Look on the old panel."],
    ["PC program (Lux WMS)", "OK - found",
     "It is in conveyor_automation-main / Frontend. Three Python packages are used but not listed in its install file (section 12)."],
    ["Camera settings", "CHECK",
     "Two setting files are in your folder (saved 19 and 23 Feb 2026). The picture-upload port inside them (21 / 8080) is not the port "
     "the PC program uses (2005), so they are close but not the final settings. Best: export the settings again from the old camera (section 8)."],
    ["VFD parameter settings", "MISSING", "Not in any file. A new drive has factory settings. Copy them from the old drive (section 7)."],
    ["Power for camera and light", "CHECK", "Not on your drawing and \"not confirmed\" in the BOM. Find how the old camera and light get 24 V."],
], [44, 30, 100], status_col=1)
d.box("<b>Safety.</b> The panel contains 230 VAC. Mains wiring, the VFD and the motor must be wired and checked by a qualified electrician, "
      "with the main isolator OFF and locked. In this design the Emergency Stop only goes to a PLC input (software stop). "
      "It does not cut the power to the VFD by itself.", BAD)

# ------------------------------------------------------------------ 3
d.h1("3. Do this on the OLD machine before you buy or dismantle anything")
d.table(["#", "What", "How", "Why"], [
    ["1", "Reverse test in manual mode",
     "Selector at MANUAL. Press and hold the red STOP button. Does the conveyor run in reverse?<br/>"
     "<b>NO</b> (only the HMI REV JOG button reverses): the file \"latest plc\" is right. Use it.<br/>"
     "<b>YES</b>: the old PLC holds a newer program than the file. Read it out of the old PLC with TIA Portal V21 "
     "(<b>Online &gt; Upload device as new station</b>) and load that into the new PLC.",
     "This is the only point where your description and the saved program differ. The last change in the file is from 25 Feb 2026."],
    ["2", "VFD parameters", "See section 7 (keypad, or laptop with a USB-RS485 adapter and the tool in your folder). "
     "Also note the position of the small NPN / PNP switch on the drive.", "Without them the new drive will not run correctly."],
    ["3", "Camera", "Connect the HIKROBOT IDMVS software to the old camera and export its settings to a file. "
     "Photograph the camera cable: which wire carries the sensor signal, and where the camera and the light get their power.",
     "The saved setting files are a few days older than the final machine."],
    ["4", "Sensor, tower lamp, buttons", "Photograph the labels and the back of each button. Count the NO and NC contact blocks.",
     "The BOM lists these as \"type only\". STOP and Emergency must use NC contacts."],
    ["5", "Wire-by-wire photos", "Every PLC terminal, the VFD control terminals (RA, RB, RC, MI1, MI2, DCM, 24V) and the terminal strips.",
     "To settle the CHECK points of section 2."],
], [7, 30, 86, 51])
d.box("<b>Best extra protection:</b> even if the answer to item 1 is NO, do <b>Online &gt; Upload device as new station</b> once on the old PLC "
      "and keep the result. It is the only copy that is certain to be what the old machine runs.", OKC)

# ------------------------------------------------------------------ 4
d.page()
d.h1("4. Check of your hand drawings against the program")
d.h2("4.1 PLC inputs and outputs")
d.table(["PLC terminal", "Your drawing", "Program", "Result"], [
    ["I0.0", "Nothing", "Tag \"DI_PRODUCT SENSOR\" exists, but its logic is switched off", "OK - leave empty. The sensor goes to the camera."],
    ["I0.1", "Selector SW (AT)", "Auto / Manual selector. ON = AUTO, OFF = MANUAL", "OK"],
    ["I0.2", "PB Green", "Cycle START push button (NO contact)", "OK"],
    ["I0.3", "PB Red", "Cycle STOP push button (NC contact)", "OK - confirm the contact is NC"],
    ["I0.4", "Em switch", "Emergency stop (NC contact)", "OK - confirm the contact is NC"],
    ["I0.5", "To VFD relay RA", "VFD fault. Input ON = fault", "OK"],
    ["I0.6", "Joined to the I0.5 / RA wire, with the purple lamp wire", "Not used", "OK - the screw is only used as a joint. Copy it."],
    ["Q0.0", "To VFD", "Conveyor FORWARD", "OK"],
    ["Q0.1", "To VFD", "Conveyor REVERSE", "OK"],
    ["Q0.2", "Nothing", "Fault RESET signal to the VFD", "CHECK - look for a wire from Q0.2 to a VFD input. If there is none, "
     "the HMI reset clears the PLC alarm only, and the VFD must be reset at the drive."],
    ["Q0.3", "Lamp green", "Auto cycle started", "OK"],
    ["Q0.4", "Lamp red", "Fault", "OK"],
    ["Q0.5", "Lamp yellow", "Manual mode", "OK"],
    ["Q0.6", "Crossed out", "Not used", "OK"],
    ["Input common (top \"0V\")", "0 V", "1M = 0 V, because the switches give +24 V", "OK"],
    ["Output supply (\"+ -\")", "+24 V and 0 V", "3L+ = +24 V, 3M = 0 V", "OK"],
], [26, 38, 50, 60], status_col=3)
d.h2("4.2 VFD relay, as I read your sketch")
d.table(["VFD terminal", "Goes to", "What it does"], [
    ["RC (common)", "+24 V", "Feeds the relay contact"],
    ["RA (closes when the relay pulls in)", "PLC I0.5, with a link to the I0.6 screw, where the purple wire of the tower lamp is also connected",
     "On a VFD fault: the PLC gets the fault signal and the purple wire (buzzer or fourth light) gets 24 V"],
    ["RB (closed while the relay is at rest)", "The \"VFD healthy\" indicator lamp on the panel door (other lamp wire to 0 V)",
     "Lamp ON while the drive has no fault"],
], [44, 70, 60])
d.box("This works only when the VFD relay is set to <b>\"fault\"</b> (parameter 03.00 on Delta VFD-EL drives). Copy the value from the old drive. "
      "My reading of the words \"(Indicator) - RB\" and \"24V - RC\" on the sketch is not certain. Trace these three wires on the old panel.")
d.h2("4.3 Power drawing")
d.table(["Your drawing", "BOM part", "Result"], [
    ["Main power L, N to main switch", "Salzer 16 A rotary isolator", "OK"],
    ["MCB C10 to VFD to motor (U, V, W)", "Schneider A9N2P10C, Delta VFD004EL21W-1, Bonfiglioli BE 71B 4",
     "OK - the motor terminal box must be linked in DELTA (230 V). See section 7."],
    ["MCB C6 to socket and \"DC-DC converter\"", "Schneider A9N2P06CGN, Multispan PS24-5A-P", "OK - the converter is the 230 VAC / 24 VDC 5 A power supply"],
    ["24 V, 0 V to MCB 2A", "Schneider A9KF71202", "OK"],
    ["2A MCB to sensor, Ethernet switch, HMI, PLC", "Teltonika TSW010, KTP700, CPU 1214C", "OK"],
    ["Camera and light supply", "BOM: \"not confirmed\"", "CHECK - not on your drawing"],
], [62, 62, 50], status_col=2)
d.h2("4.4 BOM - items to add or settle")
d.bullets([
    "<b>Ethernet patch cables</b>: PLC, HMI and PC to the switch, plus one for the programming laptop. The switch has 5 ports: PLC, HMI, camera, PC and one free.",
    "<b>Camera cables</b>: the camera uses its own round-connector cables for network and for power / signals. Order the same ones as on the old machine.",
    "<b>PC for the Lux WMS program</b>, if the old PC stays with the old machine.",
    "<b>TIA Portal V21</b> (STEP 7 Basic + WinCC Basic). The project cannot be opened with an older version.",
    "<b>USB-to-RS485 adapter</b> (optional, low cost) to read the VFD parameters with the laptop. See section 7.",
    "<b>Contact blocks</b>: START 1 NO, STOP 1 NC, Emergency 1 NC, selector 1 NO.",
    "<b>Signal tower</b>: 24 VDC, red / amber / green plus the fourth (purple) wire, common 0 V.",
    "<b>Photoelectric sensor</b>: same model as the old one if readable. Its output must suit the camera trigger input, so copy the old type."])

# ------------------------------------------------------------------ 5
d.h1("5. Power wiring")
g = Diagram(92)
g.box(62, 80, 50, 9, "Mains 230 VAC  (L, N, PE)")
g.box(62, 66, 50, 9, "Main isolator 16 A")
g.line(87, 80, 87, 75)
g.line(87, 66, 87, 62); g.line(30, 62, 140, 62); g.line(30, 62, 30, 58); g.line(140, 62, 140, 58)
g.box(10, 49, 40, 9, "MCB 2P C10"); g.box(10, 35, 40, 9, "Delta VFD\nR/L1, S/L2 in")
g.box(10, 21, 40, 9, "Terminal block\nU, V, W + PE"); g.box(10, 7, 40, 9, "Motor 0.37 kW\n(DELTA 230 V)")
g.line(30, 49, 30, 44); g.line(30, 35, 30, 30); g.line(30, 21, 30, 16)
g.box(120, 49, 40, 9, "MCB 2P C6"); g.line(140, 49, 140, 45); g.line(100, 45, 150, 45); g.line(100, 45, 100, 42); g.line(150, 45, 150, 42)
g.box(84, 33, 32, 9, "Panel socket\n230 VAC"); g.box(132, 33, 38, 9, "24 VDC 5 A supply\n(Multispan)", OKC)
g.line(150, 33, 150, 29); g.box(132, 20, 38, 9, "MCB 2P 2 A\n(24 V and 0 V)", OKC); g.line(150, 20, 150, 16); g.line(66, 16, 164, 16)
for x, text in [(58, "Sensor"), (84, "Ethernet\nswitch"), (110, "HMI"), (136, "PLC L+ / M\n1M, 3L+, 3M")]:
    g.box(x, 2, 24, 9, text, OKC); g.line(x + 12, 16, x + 12, 11)
g.label(52, 46, "230 VAC side"); g.label(60, 18, "24 VDC side (green boxes)")
d.add(g.d)
d.sp(4)
d.table(["From", "To", "Note"], [
    ["Mains L, N, PE", "Incoming terminals, then isolator", "PE (earth) goes to the earth bar and to the mounting plate, VFD, motor, power supply and PLC earth terminals."],
    ["Isolator out L, N", "MCB C10 in and MCB C6 in", ""],
    ["MCB C10 out", "VFD R/L1 and S/L2", "Single-phase 230 V input drive."],
    ["VFD U/T1, V/T2, W/T3", "Terminal block, then motor U, V, W", "Use a screened motor cable if the old one is screened."],
    ["MCB C6 out", "Panel socket, and 24 V supply L, N", ""],
    ["24 V supply +V, -V", "MCB 2 A, then the +24 V and 0 V terminal rows", "Set the supply output to 24.0 V before connecting loads."],
    ["+24 V / 0 V terminals", "PLC, HMI, Ethernet switch, sensor, button common, VFD relay RC, health lamp", "See the next sections for the exact terminals."],
    ["Camera and light", "Copy from the old machine", "The camera needs 12 - 24 VDC (up to 12 W). The light has its own rating: read its label."],
], [42, 62, 70])

# ------------------------------------------------------------------ 6
d.h1("6. PLC wiring (CPU 1214C DC/DC/DC)")
d.h2("6.1 Supply and commons")
d.table(["PLC terminal", "Connect to", "Purpose"], [
    ["L+", "+24 V", "CPU supply"], ["M", "0 V", "CPU supply"], ["Earth terminal", "PE bar", "Functional earth"],
    ["1M (input common)", "0 V", "Inputs turn ON when +24 V arrives on them"],
    ["3L+", "+24 V", "Supply for the outputs"], ["3M", "0 V", "Output reference"],
], [42, 42, 90])
d.h2("6.2 Inputs (top terminal row)")
d.table(["Input", "Device", "Contact", "Wiring", "Input is ON when"], [
    ["I0.0", "Not connected", "-", "Leave empty", "-"],
    ["I0.1", "Auto / Manual selector", "NO", "+24 V - contact - I0.1", "Selector is at AUTO"],
    ["I0.2", "Cycle START (green)", "NO", "+24 V - contact - I0.2", "Button pressed"],
    ["I0.3", "Cycle STOP (red)", "NC", "+24 V - contact - I0.3", "Button NOT pressed (normal)"],
    ["I0.4", "Emergency stop", "NC", "+24 V - contact - I0.4", "Emergency NOT pressed (normal)"],
    ["I0.5", "VFD fault relay", "RA - RC", "+24 V - RC, RA - I0.5", "VFD has a fault"],
    ["I0.6", "Joint only", "-", "Wire link from I0.5, plus the purple lamp wire", "(not used by the program)"],
], [14, 40, 20, 58, 42])
d.box("With normal healthy conditions the PLC input LEDs must show: I0.3 ON, I0.4 ON, I0.5 OFF. "
      "If I0.3 or I0.4 is OFF the machine will never start. If I0.5 is ON the PLC shows VFD FAULT.")
d.h2("6.3 Outputs (bottom terminal row). Each output gives +24 V when ON")
d.table(["Output", "Goes to", "Function"], [
    ["Q0.0", "VFD forward run input (MI1 on Delta EL)", "Conveyor forward (auto and manual)"],
    ["Q0.1", "VFD reverse run input (MI2 on Delta EL)", "Conveyor reverse (manual only)"],
    ["Q0.2", "VFD fault reset input, only if wired on the old panel", "ON while the HMI FAULT RESET button is pressed"],
    ["Q0.3", "Signal tower GREEN", "Auto cycle started"],
    ["Q0.4", "Signal tower RED", "Fault present"],
    ["Q0.5", "Signal tower AMBER / yellow", "Manual mode selected"],
    ["Lamp common", "0 V", ""],
], [18, 76, 80])

# ------------------------------------------------------------------ 7
d.h1("7. VFD and motor")
d.bullets([
    "<b>Motor link plates:</b> the motor is 230 / 400 V (delta / star). The VFD gives 3-phase 230 V, so the motor terminal box must be connected in <b>DELTA</b>. Rated current in delta is 1.82 A.",
    "<b>Control wiring:</b> PLC Q0.0 to MI1 (forward), Q0.1 to MI2 (reverse). The PLC outputs give +24 V, so the VFD digital common (DCM) must be joined to the panel 0 V, "
    "and the drive NPN / PNP switch must be in the same position as on the old drive.",
    "<b>Relay:</b> RC, RA, RB as in section 4.2.",
    "<b>Speed:</b> find where the old drive gets its speed (keypad knob, fixed parameter or a potentiometer) and copy it. The PLC does not send a speed value."])
d.p("Parameters that matter for this machine, with the <b>raw values read from the old drive on 7 October 2026</b> "
    "(full list: 04_VFD/old_vfd_2026-10-07/old_vfd_parameters.txt). Raw values have no decimal point (5000 = 50.00 Hz). "
    "Option numbers (like 02.00 = 4) are codes: check their meaning in the Delta VFD-EL manual, but always set the <b>same value as the old drive</b>.")
d.table(["Parameter", "Meaning", "Old drive (raw)", "Note"], [
    ["01.00", "Maximum output frequency", "7000", "70.00 Hz"],
    ["01.01 / 01.02", "Motor rated frequency, motor rated voltage", "5000 / 2200", "50.00 Hz / 220.0 V"],
    ["01.09 / 01.10", "Acceleration / deceleration time", "50 / 5", "Copy exactly (0.1 s steps: 5.0 s / 0.5 s, check in manual)"],
    ["02.00", "Source of the speed command", "4", "Option code: copy exactly"],
    ["02.01", "Source of the run command", "1", "Option code: copy exactly (expected: external terminals)"],
    ["03.00", "Function of relay RA / RB / RC", "8", "Option code: copy exactly (expected: fault indication)"],
    ["04.04", "2-wire / 3-wire control mode", "0", "Option code: copy exactly"],
    ["04.05 / 04.06", "Function of further MI inputs", "0 / 0", "Copy exactly. Compare with the Q0.2 wire question (section 4.1)"],
    ["07.00", "Motor rated current", "25", "2.5 A. Copy this. (The motor plate says 1.82 A; setting 1.82 A would be a deliberate change from the old machine, for an electrician to decide.)"],
], [24, 52, 24, 74])
d.h2("How to copy the parameters from the old drive")
d.box("<b>Do not connect the drive to the laptop with an Ethernet cable.</b> The RJ45 socket on the drive looks like a network socket, "
      "but it is an <b>RS-485 serial</b> port. A laptop network port cannot talk to it, and one pin of that socket carries a supply voltage.", BAD)
d.table(["Way", "What you need", "Steps"], [
    ["A. Keypad", "Nothing. About 30 minutes.",
     "On the old drive press MODE until the parameter group shows, open each group (00, 01, 02 ...) and write down every value. "
     "Do the same on the new drive. Enter on the new drive every value that is different."],
    ["B. Laptop and the tool in your folder", "A USB-to-RS485 adapter (for example Delta IFD6500 or a generic one) and two wires.<br/>"
     "Drive terminal <b>SG+</b> to adapter A / D+, terminal <b>SG-</b> to adapter B / D-. "
     "The same two signals are on the RJ45 socket: pin 5 = SG+, pin 4 = SG-.",
     "1. Old drive: DONE on 7 Oct 2026, saved in 04_VFD/old_vfd_2026-10-07/.<br/>"
     "2. New drive ON, adapter connected:<br/><font face=\"DVM\">python3 04_VFD/read_vfd_parameters.py --port /dev/ttyUSB0 --out new_vfd.csv</font><br/>"
     "3. <font face=\"DVM\">python3 04_VFD/read_vfd_parameters.py --compare 04_VFD/old_vfd_2026-10-07/old_vfd_parameters.csv new_vfd.csv</font><br/>"
     "It prints only the parameters that differ. Enter those on the new drive with the keypad."],
    ["C. Delta PC software", "The same adapter and Delta's free VFDSoft program.",
     "It can save all parameters to a file and write them into the new drive. Check first that your VFDSoft version lists the VFD-EL-W."],
], [30, 56, 88])
d.bullets(["The tool <b>04_VFD/read_vfd_parameters.py</b> only reads and never writes to the drive (it refuses to send anything but Modbus function 03). "
           "It was used on the real old drive on 7 October 2026: Modbus ASCII 7N2, 9600 baud, address 1, 306 parameters, all group 00 values matching the keypad.",
           "Its numbers are raw: the drive stores 10.0 as 100 and 50.00 as 5000. Compare raw with raw.",
           "The SG+ / SG- screw terminals and the RJ45 pins (3 = GND, 4 = SG-, 5 = SG+) are from Delta's VFD-EL-W catalog. I could read only a summary of it, "
           "so look for the labels SG+ and SG- on the terminal strip of your drive before you connect. If you use the RJ45 socket, leave all other pins unconnected and insulated.",
           "Reading does not change the drive. Do it with the conveyor stopped, and do not remove any existing wire.",
           "If you connect the adapter to this laptop and tell me, I can run the tool with you and turn the result into a short setting list for the new drive."])

# ------------------------------------------------------------------ 8
d.h1("8. Sensor and camera")
d.p("The camera has no program to write. It only has <b>settings</b>, and the new camera needs the same settings as the old one.")
d.h2("8.1 Wiring")
d.table(["Wire", "Connect to", "Note"], [
    ["Sensor supply (+ and -)", "Panel +24 V and 0 V (after the 2 A MCB)", "As on your power drawing"],
    ["Sensor output", "The trigger input wire of the camera cable", "Copy the exact wire from the old machine (photo from section 3, item 3). It does not go to the PLC."],
    ["Camera power", "12 - 24 VDC, up to 12 W", "Copy from the old machine. If the camera has its own power supply, join its 0 V with the panel 0 V, otherwise the trigger signal has no return path."],
    ["Camera network", "Ethernet switch", ""],
    ["Light", "As on the old machine", "Read the voltage on the light's label"],
], [36, 62, 76])
d.h2("8.2 Settings found in the saved file")
d.p("From <font face=\"DVM\">conveyor_automation-main / backend_testing / config / camera_config / ftp-working-with-trigger-...mfa</font> "
    "(camera MV-ID6200M-00C-NNG, saved 23 Feb 2026). Only the values that differ from the factory settings are listed.")
d.table(["Setting", "Value in the file", "Note"], [
    ["IP address", "192.168.0.78, mask 255.255.255.0, gateway 192.168.0.254", "Fixed address. The PC program is written for this address."],
    ["Trigger mode", "ON", "One picture for each signal from the sensor"],
    ["Trigger delay", "3000000 (microseconds) = 3 seconds", "Time between sensor signal and picture. Depends on belt speed and sensor position."],
    ["Exposure time / gain", "100 / 150 (raw numbers in the file)", "Brightness. Fine-tune with the real light."],
    ["Number of 2D codes to read", "6", "Up to 6 QR codes in one picture"],
    ["Reading time limit", "5000 ms", ""],
    ["Result output", "TCP server, port 2002, format &lt;code_content&gt;; , text \"NoRead\" when nothing is read", "The PC program connects to this port and splits the codes at the \";\" sign."],
    ["Picture upload (FTP)", "To 192.168.0.77, user \"User\", password \"123456\", folder &lt;device_ip&gt;/&lt;image&gt;/ with ok and ng sub-folders",
     "The PC program is the FTP server."],
    ["FTP port", "8080 in the file (21 in another saved set)", "<b>Must be 2005.</b> The PC program listens on 2005, and its log of 24 Feb 2026 shows the camera connecting on 2005."],
], [40, 70, 64])
d.h2("8.3 Steps")
d.steps([
    "Mount the camera, the 12 mm lens and the light as on the old machine: same height, same angle, same sensor position.",
    "<b>Best way:</b> export the settings from the old camera with IDMVS and import that file into the new camera.",
    "<b>Other way:</b> import the saved file named in 8.2 into the new camera. Then check every row of the table in 8.2 and set the FTP port to 2005.",
    "Save the settings in the camera (a \"User Set\") and make that set the one loaded at power-on. If you skip this the settings are lost when the power is switched off.",
    "Test: block the sensor by hand. After the delay the light flashes and a picture is taken."])

# ------------------------------------------------------------------ 9
d.h1("9. Network")
d.p("All devices plug into the Teltonika 5-port switch. Subnet mask for all: 255.255.255.0.")
d.table(["Device", "IP address", "Where the value is set"], [
    ["PLC (PLC_1)", "192.168.0.40", "In the TIA project. Set automatically at download."],
    ["HMI (HMI_1)", "192.168.0.41", "In the TIA project. You also type it on the panel (section 11)."],
    ["PC with the Lux WMS program", "192.168.0.77", "Windows / Linux network settings. Must be exactly this: the program and the camera both use it."],
    ["Camera", "192.168.0.78", "In the camera settings (section 8)."],
    ["Laptop for programming", "192.168.0.100 (any free address)", "Network settings of the laptop."],
], [52, 44, 78])
d.table(["From", "To", "Port", "What"], [
    ["PC", "PLC 192.168.0.40", "502 (Modbus TCP)", "Write register 40001: 0 = conveyor may run, 1 = stop. Function 06, unit 1."],
    ["PC", "Camera 192.168.0.78", "2002 (TCP)", "The PC receives the QR codes"],
    ["Camera", "PC 192.168.0.77", "2005 (FTP)", "The camera uploads the pictures"],
    ["HMI", "PLC 192.168.0.40", "S7 connection", "HMI_Connection_1"],
], [22, 40, 34, 78])
d.p("In the PLC, register 40001 is the value <b>DATA1</b> of data block DB_CAMERA (DB5). Registers 40001 - 40010 are DATA1 - DATA10. Only DATA1 is used.")

# ------------------------------------------------------------------ 10 / 11
d.h1("10. Load the PLC program")
d.p("You need a Windows laptop with TIA Portal V21, an Ethernet cable, and the project folder <b>latest plc (2) / latest plc</b> "
    "(or the project you uploaded from the old PLC, if the reverse test in section 3 said YES).")
d.steps([
    "Finish and check all wiring. Switch on. A new PLC shows a yellow STOP light.",
    "Laptop: network adapter &gt; IPv4 &gt; IP 192.168.0.100, mask 255.255.255.0. Plug the laptop into the switch.",
    "Open TIA Portal V21. Open project: select the file <b>latest plc.ap21</b>.",
    "In the project tree click <b>PLC_1</b>. Menu <b>Online &gt; Extended download to device</b>.",
    "Type of PG/PC interface: <b>PN/IE</b>. PG/PC interface: your laptop network card. Tick <b>Show all compatible devices</b>. Click <b>Start search</b>.",
    "Select the PLC in the list and click <b>Load</b>. If TIA asks to assign an IP address, click Yes / OK.",
    "In the \"Load preview\" window accept the actions (Stop modules: \"Stop all\"; overwrite questions: accept). Click <b>Load</b>.",
    "In \"Load results\" tick <b>Start module</b> and click <b>Finish</b>. The PLC light turns green (RUN).",
    "Do not change anything in the program. Close without saving if TIA asks."])
d.box("If TIA says the firmware does not match: the project is made for CPU firmware <b>V4.4</b>. A new CPU with V4.4 or newer accepts it. "
      "If the new CPU has older firmware, update the CPU firmware first. Do not change the CPU type in the project.")
d.h1("11. Load the HMI screens")
d.steps([
    "On the KTP700 panel, at start-up press <b>Settings</b>. Open <b>Network Interface</b>: DHCP off, IP 192.168.0.41, mask 255.255.255.0.",
    "Open <b>Transfer Settings</b>: switch <b>Enable transfer</b> ON. Go back to the start screen.",
    "In TIA Portal click <b>HMI_1</b>. Menu <b>Online &gt; Extended download to device</b>, interface PN/IE, your network card, <b>Start search</b>, select the panel, <b>Load</b>.",
    "If TIA asks to update the panel operating system to match the project, accept. Do not switch off during the update.",
    "In the preview tick \"Overwrite all\", click <b>Load</b>. The panel restarts and shows the project screens.",
    "Check: the panel shows live values and no \"#####\" fields. \"#####\" means the HMI cannot reach the PLC."])

# ------------------------------------------------------------------ 12
d.h1("12. PC program (Lux WMS)")
d.p("The program is in <font face=\"DVM\">conveyor_automation-main / conveyor_automation-main / Frontend</font>. "
    "The folder <font face=\"DVM\">backend_testing</font> next to it holds earlier test versions and is not needed to run the machine.")
d.table(["Part", "File", "Job"], [
    ["PLC bridge", "backend / server.py (port 5000)", "Compares the number of codes with the Stack Size. Writes 0 or 1 to PLC register 40001."],
    ["Code receiver", "backend / tcp_client.py", "Receives the QR codes from the camera (192.168.0.78 : 2002). Also sends each code to the company cloud server."],
    ["Picture receiver", "backend / ftp_server.py (192.168.0.77 : 2005)", "Receives the pictures from the camera into backend / hik-camera-data."],
    ["Picture service", "backend / api_server.py (port 8000)", "Gives the newest picture to the screen."],
    ["Operator screen", "React web page (port 5173)", "Login, orders, and the Scanning page with Start, Stop, Stack Size and Rescan Stack."],
], [30, 62, 82])
d.h2("Install and start")
d.steps([
    "Give the PC the address <b>192.168.0.77</b>, mask 255.255.255.0, on the network card that goes to the machine switch. "
    "The PC also needs internet (for example by Wi-Fi), because login and orders come from the company server.",
    "Install <b>Python 3</b> and <b>Node.js</b>.",
    "In the folder <font face=\"DVM\">Frontend/backend</font> run:<br/><font face=\"DVM\">pip install -r requirements.txt</font><br/>"
    "<font face=\"DVM\">pip install flask flask-cors requests</font><br/>The second line is needed because the code uses these three packages but the list does not name them.",
    "In the folder <font face=\"DVM\">Frontend</font> run: <font face=\"DVM\">npm install</font>",
    "Switch on the PLC and the camera first. Then start everything: on Linux run <font face=\"DVM\">./start.sh</font> in the Frontend folder. "
    "On Windows run <font face=\"DVM\">python ..\\launcher.py</font> inside Frontend\\backend, and <font face=\"DVM\">npm run dev</font> inside Frontend.",
    "Open <b>http://localhost:5173</b> in the browser. Log in, choose the order, open the Scanning page. "
    "For a machine test only, the Scanning page is also reachable directly at http://localhost:5173/scan.",
    "On the Scanning page: <b>Start</b> writes 0 (run), <b>Stop</b> writes 1 (stop), <b>Stack Size</b> sets how many boxes are expected."])
d.box("<b>Quick test of the PC to PLC link without the screen:</b> one folder above Frontend, run <font face=\"DVM\">python3 backend_testing/test_plc_connection.py</font>. "
      "Type <b>w</b> then <b>1</b>: the conveyor stops. Type <b>w</b> then <b>0</b>: it runs. Type <b>r</b> to read the register back.", OKC)
d.bullets(["If the camera was off when the program started, the code receiver stops by itself. Restart the program after the camera is on.",
           "If the PC does not have the address 192.168.0.77, the picture receiver cannot start."])

# ------------------------------------------------------------------ 13
d.h1("13. Test step by step")
d.p("Do the tests in this order. Do not go to the next step until the present one is correct.")
d.table(["#", "Test", "Correct result"], [
    ["1", "Power off. Check with a multimeter: no short between +24 V and 0 V, and none between L and N.", "No continuity"],
    ["2", "Switch on isolator and MCBs, with the VFD MCB (C10) still OFF.", "24.0 V on the terminal row. PLC, HMI and switch powered."],
    ["3", "Look at the PLC input LEDs with nothing pressed.", "I0.3 ON, I0.4 ON, I0.5 OFF, I0.0 OFF"],
    ["4", "Turn the selector to AUTO, then MANUAL.", "I0.1 ON in AUTO. Amber lamp ON in MANUAL."],
    ["5", "Press START, then STOP, then Emergency (one at a time).", "I0.2 ON while pressed. I0.3 OFF while pressed. I0.4 OFF while Emergency is pushed in."],
    ["6", "After pushing Emergency: release it and press FAULT RESET on the HMI.", "Red lamp ON with the alarm text on the HMI. After reset the red lamp goes OFF."],
    ["7", "Switch ON the VFD MCB. Enter the VFD parameters (section 7).", "VFD display normal, no fault code. VFD healthy lamp ON."],
    ["8", "Selector MANUAL. Hold FWD JOG on the HMI (or the green START button).", "Q0.0 ON, conveyor runs forward. If the direction is wrong, power off and swap two motor wires (U and V)."],
    ["9", "Hold REV JOG on the HMI.", "Q0.1 ON, conveyor runs in reverse."],
    ["10", "Selector AUTO. Press START. The PC program is not needed for this step.", "Green lamp ON, conveyor runs forward."],
    ["11", "On the PC write 1 to register 40001 (Stop button, or the quick test of section 12). Then write 0.", "Conveyor stops at 1 (green lamp stays ON) and runs again at 0."],
    ["12", "Press STOP.", "Conveyor stops, green lamp OFF."],
    ["13", "Start again, then press Emergency while running.", "Conveyor stops, red lamp ON."],
    ["14", "Camera: block the sensor by hand.", "After the trigger delay a picture is taken. The PC screen shows the picture and the codes."],
    ["15", "Full test: run a correct row of boxes, then a row with one box missing.", "Correct row: conveyor keeps running. Missing box: conveyor stops and the PC shows a mismatch. Rescan Stack: it runs again."],
], [8, 92, 74])

# ------------------------------------------------------------------ 14
d.h1("14. Good to know")
d.bullets([
    "<b>Old sensor logic is still inside the PLC program, switched off.</b> The program contains a cycle \"sensor, delay, stop, wait for camera\". "
    "It is disabled by a contact that never passes. That is normal for this machine, because the sensor now goes to the camera.",
    "<b>If the PC stops the belt, the green START button does not restart it.</b> Use Rescan Stack or Start on the PC, which writes 0 again.",
    "<b>The HMI shows \"AUTO RUNNING\" also while the PC has stopped the belt.</b> The HMI text only looks at the START / STOP state.",
    "<b>When the PLC is switched on, register 40001 is 0.</b> So START runs the conveyor even when the PC program is not running. Nothing checks the boxes then.",
    "<b>Network.</b> Any device on this network can write the register, and can also switch PLC outputs through Modbus. Keep the machine network separate from the office network.",
    "<b>Alarms in the program:</b> \"EMERGENCY PB PRESSED FAULT (I0.4)\" and \"CONVEYOR VFD FAULT (I0.5)\". Both stay stored until FAULT RESET is pressed on the HMI."])

# ------------------------------------------------------------------ appendix
d.h1("Appendix A. Program reference")
d.table(["Block", "Job"], [
    ["Main (OB1)", "Runs the six blocks below, in this order, again and again"],
    ["FC_AUTO", "Start / stop memory; conveyor runs while started and register 40001 = 0; status number for the HMI (10 running, 20 stopped)"],
    ["FC_ALARMS", "Stores Emergency and VFD faults, makes the common FAULT signal"],
    ["FC_GENERAL", "Emergency healthy flag, Auto / Manual mode, fault reset from the HMI"],
    ["FC_MANUAL", "Jog forward / reverse in manual mode"],
    ["FC_OUTPUTS", "Drives Q0.0 - Q0.5"],
    ["FC_TCP_IP", "Modbus TCP server on port 502, counts good and bad messages"],
    ["DB_HMI (DB1), DB_ALARMS (DB2), DB_AUTO (DB3), DB_CAMERA (DB5), DB_TCP_IP (DB12), MB_SERVER_DB (DB4)", "Data used by the blocks, the HMI and Modbus"],
], [60, 114])
d.h1("Appendix B. Your hand drawings")
for k, (name, caption, width) in enumerate([
        ("WhatsApp Image 2026-10-05 at 3.38.34 PM.jpeg", "Power distribution (18 Aug page)", 105),
        ("WhatsApp Image 2026-10-05 at 3.38.31 PM.jpeg", "PLC inputs / outputs and VFD relay (19 Aug page)", 174)]):
    img = ImageOps.exif_transpose(PILImage.open(os.path.join(PICS, name))).convert("RGB")
    path = os.path.join(TMP, f"drawing_{k}.jpg")
    img.save(path, quality=85)
    w, h = img.size
    d.add(KeepTogether([Paragraph(caption, ST["h2"]), Image(path, width=width * mm, height=width * mm * h / w)]))
    d.sp(8)

d.build(OUT, "Conveyor + Camera Control Panel - rebuild guide, revision 3", "Conveyor + Camera Control Panel - Rebuild Guide (Rev 3)")
print("ok", OUT)

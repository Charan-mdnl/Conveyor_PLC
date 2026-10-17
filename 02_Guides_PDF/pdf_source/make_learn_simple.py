"""Builds Learn_PLC_Mini_Project.pdf: a small, story-style course (S7-1200 + KTP700, TIA Portal V21).

One tiny machine (a bottle filler) that uses every basic thing the real conveyor uses.
Run:  PYTHONPATH=<folder with reportlab> python3 make_learn_simple.py <output.pdf>
"""
import sys

from reportlab.platypus import KeepTogether, Paragraph, Spacer

from common import BAD, BOX, CHK, COIL, NC, NO, OKC, RST, SET, ST, Diagram, Doc

OUT = sys.argv[1]
d = Doc()
d.title("Learn PLC and HMI with One Small Machine",
        "A friendly, compact course for TIA Portal V21: S7-1200 CPU 1214C + KTP700 Basic. "
        "You build a tiny bottle filler and test it on the laptop, no hardware needed. Version 1, 17 October 2026.")

d.box("<b>How to read this.</b> Read it like a friend is sitting next to you. Each part is short: first the idea in plain words, "
      "then exactly what to click, then \"what you just learned\". Build it in a <b>new</b> project (never in the conveyor project). "
      "At the end, a table shows where the same idea is used in your real conveyor.", OKC)

# ------------------------------------------------------------------ 1
d.h1("1. The story: what we build")
d.p("Imagine a small table conveyor carrying empty bottles. A sensor sees each bottle. When a bottle arrives, the conveyor stops, "
    "a valve fills the bottle for a few seconds, then the conveyor runs again. After 6 bottles the box is full: the machine stops and a lamp blinks "
    "until someone presses RESET. There is a START and a STOP button, an Emergency button, three lamps and a touch panel.")
g = Diagram(40)
g.box(2, 24, 30, 12, "START, STOP,\nEmergency\nbuttons")
g.box(2, 6, 30, 12, "Bottle sensor")
g.box(64, 12, 46, 18, "PLC S7-1200\n(the brain)", OKC, bold_first=True)
g.box(140, 28, 32, 9, "Conveyor motor")
g.box(140, 17, 32, 9, "Fill valve")
g.box(140, 4, 32, 11, "Lamps: green,\nred, box full")
g.box(64, 33, 46, 7, "Touch panel (HMI)")
g.arrow(32, 30, 64, 24); g.arrow(32, 12, 64, 18)
g.arrow(110, 26, 140, 32); g.arrow(110, 21, 140, 21); g.arrow(110, 16, 140, 10)
g.line(87, 30, 87, 33)
d.add(g.d)
d.sp(3)
d.p("Every part of this machine is also in your conveyor: buttons, a sensor, a motor, lamps, an alarm, an HMI. "
    "So when you understand this one, the conveyor program will look easy.")

# ------------------------------------------------------------------ 2
d.h1("2. A PLC in one minute")
d.p("A PLC is a small computer that does the same three things again and again, about a thousand times per second:")
d.steps(["<b>Look</b>: read all inputs (buttons, sensor) and remember them as 0 or 1.",
         "<b>Think</b>: run your program from top to bottom, using those 0s and 1s.",
         "<b>Act</b>: switch the outputs (motor, valve, lamps) as the program decided."])
d.p("One round is a <b>scan</b>. Because it repeats so fast, it looks like the PLC reacts at once. Two rules come from this: "
    "write each output in <b>one place only</b> (the last writer wins), and remember that a push button is 1 only <b>while</b> the finger is on it.")

# ------------------------------------------------------------------ 3
d.h1("3. The words you need")
d.table(["Word", "Plain meaning", "In our machine"], [
    ["Input (I)", "A wire coming IN to the PLC", "%I0.0 START button"],
    ["Output (Q)", "A wire going OUT of the PLC", "%Q0.0 conveyor motor"],
    ["Memory bit (M)", "A switch inside the PLC, no wire. Used to remember a decision", "%M10.0 RUNNING"],
    ["Tag", "A name for an address, so you write START_PB instead of %I0.0", "All of section 5"],
    ["Bool / Int / DInt / Time", "Data types: 0-1 / whole number / big whole number / a time like T#3S", "FillTime_s is a DInt"],
    ["Data block (DB)", "A table of values inside the PLC, like a notebook page", "DB_Filler"],
    ["OB1 (Main)", "The block the PLC runs in every scan. Everything starts here", "Calls FC_Filler"],
    ["FC", "A block of program you write and call from OB1", "FC_Filler"],
    ["Network", "One drawing (rung) in a block. One network answers one question", "\"Should the motor run?\""],
    ["HMI tag", "The panel's window into a PLC value", "Bottle count on the screen"],
], [34, 86, 54])

# ------------------------------------------------------------------ 4
d.h1("4. Step 1: new project, CPU, simulator")
d.steps([
    "TIA Portal V21 &gt; <b>Create new project</b>, name <b>Learn_Filler</b> &gt; Create &gt; <b>Project view</b> (bottom left).",
    "<b>Add new device</b> &gt; Controllers &gt; SIMATIC S7-1200 &gt; CPU &gt; <b>CPU 1214C DC/DC/DC</b> &gt; 6ES7 214-1AG40-0XB0. OK.",
    "Double-click the CPU picture. Properties &gt; <b>System and clock memory</b>: tick <b>system memory byte</b> (address 1) and <b>clock memory byte</b> (address 0). "
    "You now get ready-made tags: <b>AlwaysTRUE</b> (always 1) and <b>Clock_1Hz</b> (blinks once per second).",
    "Save (Ctrl + S)."])
d.p("<b>What you just learned:</b> every project starts with the exact CPU. System and clock memory give free helper bits.")

# ------------------------------------------------------------------ 5
d.h1("5. Step 2: the tags (names for every signal)")
d.p("PLC_1 &gt; PLC tags &gt; <b>Default tag table</b>. Type each row: name, data type, address.")
d.table(["Name", "Type", "Address", "What it is", "Real button"], [
    ["START_PB", "Bool", "%I0.0", "Green START", "NO contact: 1 while pressed"],
    ["STOP_PB", "Bool", "%I0.1", "Red STOP", "<b>NC contact: 1 while NOT pressed</b>"],
    ["EMERGENCY_PB", "Bool", "%I0.2", "Emergency", "<b>NC contact: 1 while healthy</b>"],
    ["BOTTLE_SENSOR", "Bool", "%I0.3", "Sensor sees a bottle", "1 = bottle there"],
    ["CONVEYOR_MOTOR", "Bool", "%Q0.0", "Motor runs", ""],
    ["FILL_VALVE", "Bool", "%Q0.1", "Valve open", ""],
    ["LAMP_GREEN", "Bool", "%Q0.2", "Running lamp", ""],
    ["LAMP_RED", "Bool", "%Q0.3", "Alarm lamp", ""],
    ["LAMP_BOX_FULL", "Bool", "%Q0.4", "Box-full lamp (blinks)", ""],
    ["RUNNING", "Bool", "%M10.0", "Machine started (remembered)", ""],
    ["FILLING", "Bool", "%M10.1", "A bottle is being filled", ""],
    ["BOX_FULL", "Bool", "%M10.2", "6 bottles done", ""],
    ["ALARM_EMERGENCY", "Bool", "%M20.0", "Emergency happened (stays until reset)", ""],
    ["ALARM_WORD", "Word", "%MW20", "M20.0 - M21.7 as one word, for the HMI alarm", ""],
], [36, 14, 18, 56, 50])
d.box("<b>Why STOP and Emergency are NC.</b> If a wire breaks, an NC input becomes 0, which looks like \"STOP pressed\": the machine stops safely. "
      "That is why, on your real panel, I0.3 and I0.4 must be <b>ON</b> when nobody touches them (and why everything failed when 1M was not connected to 0 V).", CHK)

# ------------------------------------------------------------------ 6
d.h1("6. Step 3: the data block (the notebook)")
d.p("Program blocks &gt; <b>Add new block</b> &gt; Data block &gt; name <b>DB_Filler</b> &gt; OK. Add these rows. In the column <b>Start value</b> type the numbers shown.")
d.table(["Name", "Type", "Start value", "Used for"], [
    ["HMI_Start", "Bool", "", "START button on the panel"],
    ["HMI_Stop", "Bool", "", "STOP button on the panel"],
    ["HMI_Reset", "Bool", "", "RESET button on the panel"],
    ["FillTime_s", "DInt", "3", "Fill time in seconds, typed on the panel"],
    ["FillTime", "Time", "", "The same time in the format a timer needs"],
    ["BoxSize", "Int", "6", "Bottles per box, typed on the panel"],
    ["BottleCount", "Int", "", "Bottles filled so far, shown on the panel"],
    ["SensorMem", "Bool", "", "Memory for the edge detection (network 4)"],
], [36, 18, 22, 98])
d.p("<b>What you just learned:</b> a DB keeps values that belong together. The HMI can read and write them. "
    "(This DB stays <b>optimized</b>, the TIA default: we use names only. Your conveyor turns optimization off because it uses fixed addresses like DB2.DBW0.)")

# ------------------------------------------------------------------ 7
d.h1("7. Step 4: the program, one network at a time")
d.p("Program blocks &gt; Add new block &gt; <b>Function (FC)</b>, name <b>FC_Filler</b>, language <b>LAD</b>. Build the networks below in this order. "
    "For each: first read the sentence, then draw it. Contacts in a row = <b>AND</b>, one below the other = <b>OR</b>, the slashed contact = <b>NOT</b>.")

d.rung("Network 1: \"Was Emergency pressed?\"  (set coil)", [[NC("EMERGENCY_PB"), "-", SET("ALARM_EMERGENCY")]], ncols=3,
       explain="The input is 0 when Emergency is pressed, and the slashed contact passes on 0. <b>Set coil (S)</b>: once set, it stays 1 even after the button is released. "
               "That is how an alarm \"remembers\".")
d.rung("Network 2: \"Clear the alarm\"  (reset coil)", [[NO("\"DB_Filler\".\nHMI_Reset"), NO("EMERGENCY_PB"), RST("ALARM_EMERGENCY")]], ncols=3,
       explain="Reset works only if Emergency is released again (input back to 1). <b>Reset coil (R)</b> writes 0.")
d.rung("Network 3: \"Is the machine running?\"  (the latch)", [
    [NO("START_PB"), NO("STOP_PB"), NC("\"DB_Filler\".\nHMI_Stop"), NC("ALARM_\nEMERGENCY"), NC("BOX_FULL"), COIL("RUNNING")],
    [NO("\"DB_Filler\".\nHMI_Start"), None, None, None, None, None],
    [NO("RUNNING"), None, None, None, None, None]], links=[(1, 0, 2)],
    explain="Read it: (START <b>or</b> panel START <b>or</b> already RUNNING) <b>and</b> STOP not pressed <b>and</b> no panel STOP <b>and</b> no alarm <b>and</b> box not full. "
            "The RUNNING contact under START is the <b>latch</b>: after you release START, RUNNING keeps itself on. Any condition on the right breaks it. "
            "To draw the OR: select the wire before START, click <b>Open branch</b>, add the contact, drag the branch end back to the main line.")
d.rung("Network 4: \"Did a new bottle arrive?\"  (edge detection)", [
    [NO("RUNNING"), NO("BOTTLE_SENSOR"), BOX("", ["P_TRIG", "CLK      Q", "\"DB_Filler\".", "SensorMem"]), SET("FILLING")]], ncols=4,
    explain="The sensor stays 1 while the bottle stands there. <b>P_TRIG</b> gives 1 for <b>one scan only</b>, at the moment the sensor changes from 0 to 1, "
            "so each bottle counts once. It is in Basic instructions &gt; Bit logic. Type the memory bit under the box.")
d.add(KeepTogether([Paragraph("Network 5: \"Convert seconds to timer time\"  (an SCL line)", ST["h3"]),
                    Paragraph("Right-click the network title &gt; <b>Insert SCL network</b>, and type exactly:", ST["p"]),
                    Paragraph("\"DB_Filler\".FillTime := DINT_TO_TIME(\"DB_Filler\".FillTime_s * 1000);", ST["code"]),
                    Paragraph("A timer counts milliseconds. 3 seconds x 1000 = 3000 ms. DINT_TO_TIME changes the number into the Time type. "
                              "SCL is text programming: some things (maths) are shorter in text than in ladder.", ST["note"]), Spacer(1, 5)]))
d.rung("Network 6: \"Fill for a few seconds\"  (on-delay timer)", [
    [NO("FILLING"), BOX("T_Fill", ["TON  Time", "IN        Q", "PT: \"DB_Filler\".", "FillTime"]), "-", RST("FILLING")]], ncols=4,
    explain="Drag <b>TON</b> from Basic instructions &gt; Timer operations. When it asks \"Call options\", choose <b>Single instance</b> and name it <b>T_Fill</b>: "
            "TIA makes a small DB for the timer. While FILLING is 1, the timer counts. After PT, Q becomes 1 and resets FILLING: the conveyor runs again.")
d.rung("Network 7: \"Count the bottles\"  (counter)", [
    [NO("\"T_Fill\".Q"), BOX("C_Bottles", ["CTU  Int", "CU         Q", "R: \"DB_Filler\".HMI_Reset", "PV: \"DB_Filler\".BoxSize", "CV: \"DB_Filler\".BottleCount"]), "-", COIL("BOX_FULL")]], ncols=4,
    explain="<b>CTU</b> (count up) adds 1 each time CU goes from 0 to 1, so once per finished bottle. When the count reaches PV (6), Q = 1 = BOX_FULL. "
            "R (reset) sets the count back to 0. Single instance, name <b>C_Bottles</b>.")
d.rung("Network 8: \"Drive the motor and the valve\"  (outputs in one place)", [
    [NO("RUNNING"), NC("FILLING"), "-", COIL("CONVEYOR_MOTOR")],
    [NO("FILLING"), NC("ALARM_\nEMERGENCY"), "-", COIL("FILL_VALVE")]], ncols=4,
    explain="The motor runs while the machine is running and no bottle is being filled. The valve opens while filling, but never during an alarm (safety first).")
d.rung("Network 9: \"Which lamps are on?\"  (clock memory blink)", [
    [NO("RUNNING"), "-", COIL("LAMP_GREEN")],
    [NO("ALARM_EMERGENCY"), "-", COIL("LAMP_RED")],
    [NO("BOX_FULL"), NO("Clock_1Hz"), COIL("LAMP_BOX_FULL")]], ncols=3,
    explain="Clock_1Hz changes every half second by itself, so in series with BOX_FULL the lamp <b>blinks</b>.")
d.h2("Call it from OB1 and compile")
d.steps(["Open <b>Main [OB1]</b>. Drag <b>FC_Filler</b> from the project tree onto network 1.",
         "Click <b>PLC_1</b> &gt; <b>Compile</b>. The Info tab must say <b>Errors: 0</b>. A red line? Double-click it: usually a typing mistake in a name."])
d.add(Paragraph("Summary: the instructions you used", ST["h3"]))
d.table(["You used", "Instruction"], [
    ["Contact NO / NC", "-| |-  -|/|-"], ["Coil, set coil, reset coil", "-( )-  -(S)-  -(R)-"], ["AND / OR / latch", "series / branch / self-holding"],
    ["Edge detection", "P_TRIG"], ["Timer", "TON"], ["Counter", "CTU"], ["Maths and type change", "SCL: *, DINT_TO_TIME"], ["Blink", "Clock_1Hz"],
], [70, 104])

# ------------------------------------------------------------------ 8
d.h1("8. Step 5: the touch panel (HMI)")
d.steps([
    "<b>Add new device</b> &gt; HMI &gt; SIMATIC Basic Panel &gt; 7\" Display &gt; <b>KTP700 Basic</b> 6AV2 123-2GB03-0AX0. In the wizard: PLC connections &gt; Browse &gt; <b>PLC_1</b>. "
    "Untick the extra screens. Finish.",
    "Open the screen the wizard made (Screens &gt; <b>Root screen</b>). Drag objects from the <b>Toolbox</b> on the right, as in the table.",
    "For every object, the tag is picked with the \"...\" button: you can pick PLC tags and DB rows directly; TIA creates the HMI tag for you."])
d.table(["Object", "Text / settings", "Tag", "Event or animation"], [
    ["Button", "START", "DB_Filler.HMI_Start", "Events &gt; <b>Press</b> &gt; SetBitWhileKeyPressed"],
    ["Button", "STOP", "DB_Filler.HMI_Stop", "Press &gt; SetBitWhileKeyPressed"],
    ["Button", "RESET", "DB_Filler.HMI_Reset", "Press &gt; SetBitWhileKeyPressed"],
    ["I/O field", "Mode <b>Input</b>, format 99", "DB_Filler.FillTime_s", "The operator types the fill time"],
    ["I/O field", "Mode <b>Input</b>, format 99", "DB_Filler.BoxSize", "Bottles per box"],
    ["I/O field", "Mode <b>Output</b>, format 99", "DB_Filler.BottleCount", "Shows the count"],
    ["Circle", "\"Motor\" text next to it", "CONVEYOR_MOTOR", "Animations &gt; Appearance: 0 = grey, 1 = green"],
    ["Circle", "\"Valve\"", "FILL_VALVE", "Appearance: 0 = grey, 1 = blue"],
    ["Circle", "\"Box full\"", "BOX_FULL", "Appearance: 1 = yellow, flashing"],
    ["Alarm view", "Toolbox &gt; Controls", "-", "Shows the alarm texts"],
], [22, 46, 46, 60])
d.h2("The alarm text")
d.p("HMI_1 &gt; <b>HMI alarms</b> &gt; Discrete alarms: text <b>EMERGENCY STOP PRESSED</b>, trigger tag <b>ALARM_WORD</b>, trigger bit <b>8</b>.")
d.box("<b>Why bit 8 for M20.0?</b> In a Siemens word the first byte is the high half. MW20 = byte M20 (bits 8 - 15) + byte M21 (bits 0 - 7). "
      "So M20.0 is bit 8. Your conveyor uses the same trick: its two alarms are bits 8 and 9 of DB2.DBW0.", OKC)
d.p("<b>What you just learned:</b> buttons write bits, I/O fields read and write numbers, animations show bits, alarms watch bits of a word.")

# ------------------------------------------------------------------ 9
d.h1("9. Step 6: test it on the laptop (no hardware)")
d.steps([
    "Click PLC_1 &gt; toolbar <b>Start simulation</b> (PLCSIM). Load the program into the simulated PLC, choose RUN.",
    "In PLC_1 add a <b>Watch table</b> with START_PB, STOP_PB, EMERGENCY_PB, BOTTLE_SENSOR, RUNNING, FILLING and \"DB_Filler\".BottleCount. Switch monitoring on (glasses icon).",
    "<b>First set the NC inputs to 1</b>: STOP_PB = 1 and EMERGENCY_PB = 1 (modify value, lightning icon). Otherwise the machine never starts: just like your real panel without 1M.",
    "Click HMI_1 &gt; <b>Start simulation</b>. A panel window opens on the laptop."])
d.table(["#", "Do this", "You must see"], [
    ["1", "Press START on the simulated panel", "RUNNING = 1, motor circle green"],
    ["2", "Set BOTTLE_SENSOR = 1", "FILLING = 1, motor off, valve on"],
    ["3", "Wait 3 s, then set BOTTLE_SENSOR = 0", "Valve off, motor on, BottleCount = 1"],
    ["4", "Repeat 2-3 five more times", "BottleCount = 6, machine stops, box-full blinks"],
    ["5", "Press RESET", "Count 0, box-full off; START works again"],
    ["6", "Set EMERGENCY_PB = 0", "Alarm text, red lamp, machine stops"],
    ["7", "EMERGENCY_PB = 1, then RESET", "Alarm clears"],
    ["8", "Type 5 in the fill time field", "Next bottle fills 5 s"],
], [8, 80, 86])
d.p("Tip: open FC_Filler and switch on <b>monitoring</b> (glasses). Green lines = signal flows. Watching the rungs change is the fastest way to learn.")

# ------------------------------------------------------------------ 10
d.h1("10. Now look at your real conveyor")
d.table(["Idea in this course", "Where your conveyor uses it"], [
    ["NC buttons are 1 at rest", "I0.3 STOP and I0.4 Emergency (the 1M fault you fixed)"],
    ["Set / reset alarm", "FC_ALARMS networks 1 - 3"],
    ["Latch (self-holding)", "FC_AUTO network 1: START with ACTIVE in parallel"],
    ["Outputs written in one place", "FC_OUTPUTS: Q0.0 - Q0.5"],
    ["Edge, timer, SCL line", "The switched-off sensor cycle in FC_AUTO (P_TRIG, TON, SCL network 2)"],
    ["Compare instead of a sensor", "FC_AUTO network 3: run while register 40001 (DATA1) = 0"],
    ["HMI buttons SetBitWhileKeyPressed", "FWD JOG, REV JOG, FAULT RESET"],
    ["Alarm bit 8 of a word", "Alarms on bits 8 and 9 of DB2.DBW0"],
], [70, 104])
d.h2("Three small exercises")
d.bullets(["Add a second lamp output that is ON while the valve is open.",
           "Make the box-full lamp blink faster: use Clock_2Hz.",
           "Add a counter of all bottles ever filled (a second CTU without reset), and show it on the panel."])

d.build(OUT, "Learn PLC and HMI with one small machine - version 1", "Learn PLC and HMI with One Small Machine")
print("ok", OUT)

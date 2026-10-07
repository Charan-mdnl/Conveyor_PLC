"""Builds Conveyor_Program_From_Scratch_TIA_V21.pdf  (revision 2).

Run:  PYTHONPATH=<folder with reportlab> python3 make_tutorial.py <output.pdf>
"""
import sys

from reportlab.platypus import KeepTogether, Paragraph, Spacer

from common import BAD, BOX, CHK, COIL, NC, NO, OKC, RST, SET, ST, Doc

OUT = sys.argv[1]
d = Doc()
d.title("Write the Conveyor Program Yourself",
        "A to Z in TIA Portal V21, Revision 2 (6 October 2026): new project, hardware, tags, data blocks, ladder logic, "
        "Modbus, HMI, download and test.<br/>Every name, address and value is taken from the old project \"latest plc\".")

d.box("<b>What changed from Revision 1.</b><br/>"
      "1. Block <b>FC_AUTO</b> (part 8) now teaches the logic the real machine uses: the conveyor runs while the cycle is started "
      "and Modbus register 40001 is 0. Revision 1 taught a sensor-stop cycle as the main logic. On your machine that cycle is switched off, "
      "because the sensor goes to the camera. It is now in Appendix A as optional practice.<br/>"
      "2. The <b>HMI part</b> (part 10) now has the real screens, positions, texts and tags, read from the old project's screen files. "
      "Revision 1 had a \"Home\" screen, a STOP TIME field and a camera button; the final old panel has none of these.<br/>"
      "3. The test list (part 11) follows the real behaviour.", OKC)

# ------------------------------------------------------------------ 0
d.h1("0. How to use this guide")
d.bullets([
    "Work through the parts in order. Each part ends with something you can check.",
    "Type names <b>exactly</b> as shown, including spaces and capital letters. The HMI and Modbus depend on the names and addresses.",
    "The PLC part (parts 1 - 9) is exact: I read it out of the old project file.",
    "The HMI part (part 10): texts, tags and addresses are exact. Positions and sizes come from screen files made on 6 Feb 2026, "
    "so a later small move of an object would not show. Button actions and colour changes could not be read; I give the usual way to do them.",
    "I could not run TIA Portal myself, so a menu name may differ by a word or two in your V21 installation. The position in the menus is the same."])
d.table(["Part", "You build", "About"], [
    ["1", "New project and PLC hardware", "15 min"], ["2", "PLC tag table (inputs, outputs, flags)", "15 min"],
    ["3", "Five data blocks", "30 min"], ["4 - 8", "Six program blocks (FC) in ladder", "2 hours"],
    ["9", "Main block OB1, compile", "10 min"], ["10", "HMI panel", "2 hours"], ["11", "Download and test", "1 hour"]], [20, 110, 44])
d.h2("Ladder symbols used in this guide")
d.rung("", [[NO("normally open\ncontact"), NC("normally closed\ncontact"), BOX("instruction box", ["TON", "IN      Q", "PT     ET"]),
             COIL("coil"), SET("set coil"), RST("reset coil")]], ncols=6)
d.bullets([
    "<b>Normally open contact:</b> lets the signal pass when the tag is 1 (ON).",
    "<b>Normally closed contact:</b> lets the signal pass when the tag is 0 (OFF).",
    "<b>Coil:</b> the tag is 1 while signal arrives, 0 when it does not.",
    "<b>Set coil (S):</b> turns the tag ON and it stays ON. <b>Reset coil (R):</b> turns it OFF.",
    "Contacts in a line mean AND. Contacts one below the other (a branch) mean OR."])
d.p("In TIA Portal the symbols are in the toolbar above the network and in the <b>Instructions</b> panel on the right, under "
    "<b>Basic instructions &gt; Bit logic operations</b>. Drag a symbol onto the line. Then double-click the red <b>&lt;??.?&gt;</b> above it "
    "and type the tag name. To make a branch: select the line, click <b>Open branch</b> (arrow going down) in the toolbar, place the contact, "
    "then drag the end arrow of the branch up to the main line to close it.")

# ------------------------------------------------------------------ 1
d.h1("Part 1. New project and PLC hardware")
d.steps([
    "Start TIA Portal V21. Click <b>Create new project</b>. Project name: <b>Conveyor_New</b>. Click <b>Create</b>.",
    "Bottom left, click <b>Project view</b>.",
    "In the project tree (left) double-click <b>Add new device</b>.",
    "Click <b>Controllers</b>. Open <b>SIMATIC S7-1200 &gt; CPU &gt; CPU 1214C DC/DC/DC &gt; 6ES7 214-1AG40-0XB0</b>.",
    "On the right, <b>Version</b>: choose <b>V4.4</b> (the old project uses V4.4. If your new CPU has newer firmware, V4.4 still works). Device name stays <b>PLC_1</b>. Click <b>OK</b>.",
    "If a security wizard opens, keep the default choices or untick the protection options and finish. The old project has no PLC password.",
    "The device view opens. Double-click the picture of the CPU. The <b>Properties</b> window opens at the bottom, tab <b>General</b>.",
    "Click <b>PROFINET interface [X1] &gt; Ethernet addresses</b>. Click <b>Add new subnet</b> (it becomes PN/IE_1). Tick <b>Set IP address in the project</b>. "
    "IP address <b>192.168.0.40</b>, subnet mask <b>255.255.255.0</b>.",
    "Click <b>System and clock memory</b>. Tick <b>Enable the use of system memory byte</b>. Address of system memory byte: <b>1</b>. Leave the clock memory byte unticked.",
    "Click <b>DI 14/DQ 10 &gt; I/O addresses</b>. Check: input start address 0, output start address 0.",
    "Press <b>Ctrl + S</b> to save."])
d.box("<b>Why the system memory byte?</b> It creates ready-made tags. With address 1 you get <b>AlwaysTRUE = M1.2</b> and <b>AlwaysFALSE = M1.3</b>. "
      "The program uses both. If you choose another address, the names stay the same but the addresses change, and the M2.x flags could clash.", OKC)

# ------------------------------------------------------------------ 2
d.h1("Part 2. PLC tags")
d.steps([
    "Project tree: <b>PLC_1 &gt; PLC tags &gt; Default tag table</b> (double-click).",
    "You already see System_Byte, FirstScan, DiagStatusUpdate, AlwaysTRUE, AlwaysFALSE. Leave them.",
    "Click the first empty row (&lt;Add new&gt;). Type the name, choose data type <b>Bool</b>, type the address. Do this for every row of the table below."])
d.table(["Name", "Data type", "Address", "Meaning"], [
    ["DI_PRODUCT SENSOR", "Bool", "%I0.0", "Old sensor input. Nothing is wired to it now (the sensor goes to the camera). Keep the tag: the HMI shows it."],
    ["DI_AUTO MANUAL SELECTION", "Bool", "%I0.1", "1 = AUTO, 0 = MANUAL"],
    ["DI_CYCLE START PB", "Bool", "%I0.2", "Green start button (NO contact)"],
    ["DI_CYCLE STOP PB", "Bool", "%I0.3", "Red stop button (NC contact, so 1 = not pressed)"],
    ["DI_EMERGENCY PB", "Bool", "%I0.4", "Emergency (NC contact, so 1 = healthy)"],
    ["DI_CONVEYOR VFD FAULT", "Bool", "%I0.5", "1 = drive has a fault"],
    ["DO_CONVEYOR FWD ON", "Bool", "%Q0.0", "Drive: run forward"],
    ["DO_CONVEYOR REV ON", "Bool", "%Q0.1", "Drive: run reverse"],
    ["DO_FAULT RESET", "Bool", "%Q0.2", "Drive: reset fault"],
    ["DO_TL GREEN", "Bool", "%Q0.3", "Tower lamp green"],
    ["DO_TL RED", "Bool", "%Q0.4", "Tower lamp red"],
    ["DO_TL AMBER", "Bool", "%Q0.5", "Tower lamp amber"],
    ["CONTROL ON FLAG", "Bool", "%M2.0", "Emergency is healthy"],
    ["MANUAL MODE SELECTED", "Bool", "%M2.1", ""],
    ["AUTO MODE SELECTED", "Bool", "%M2.2", "Also shown on the HMI"],
    ["FAULT RESET FLAG", "Bool", "%M2.3", "Reset button on the HMI is pressed"],
    ["FAULT BIT", "Bool", "%M2.4", "Any alarm is present"],
    ["MANUAL CONVEYOR FWD ON FLAG", "Bool", "%M2.5", ""],
    ["MANUAL CONVEYOR REV ON FLAG", "Bool", "%M2.6", ""],
], [58, 20, 20, 76])

# ------------------------------------------------------------------ 3
d.h1("Part 3. Data blocks (DB)")
d.p("A data block is a table of values kept in the PLC. This project has five that you create by hand and one that TIA creates for you (in part 8b). "
    "The DB <b>numbers matter</b> because the HMI and Modbus use them.")
d.h2("How to create each DB")
d.steps([
    "Project tree: <b>PLC_1 &gt; Program blocks &gt; Add new block</b>.",
    "Click <b>Data block (DB)</b>. Type the <b>Name</b>. Type: <b>Global DB</b>. Number: choose <b>Manual</b> and type the number. Click <b>OK</b>.",
    "Before adding rows: in the project tree right-click the new DB &gt; <b>Properties &gt; Attributes</b>. <b>Untick \"Optimized block access\"</b>. Click OK and confirm the message.",
    "In the DB editor add the rows from the table. Type the name, then the data type. Leave the Start value as it is.",
    "Click <b>Compile</b> (toolbar, or right-click the DB &gt; Compile &gt; Software). The <b>Offset</b> column fills in. Compare it with the offsets in the tables below."])
d.box("<b>Do not skip step 3.</b> With \"Optimized block access\" ticked the values have no fixed address. Then Modbus cannot use DB_CAMERA, "
      "the alarm word DB2.DBW0 does not exist, and the HMI addresses below do not work. The old project has it unticked on all these DBs.", BAD)
d.p("Some rows belong to the old sensor cycle that is switched off on your machine. Create them anyway, so that every offset is the same as in the old PLC.")
d.h2("DB_HMI - number 1")
d.table(["Name", "Data type", "Offset", "Used for"], [
    ["FAULT RESET PB", "Bool", "0.0", "HMI fault reset button"], ["MOTOR JOG FWD PB", "Bool", "0.1", "HMI jog forward button"],
    ["MOTOR JOG REV PB", "Bool", "0.2", "HMI jog reverse button"],
    ["STOP TIME", "DInt", "2.0", "Old sensor cycle (delay in seconds). Not used on the machine now."],
    ["CAMERA DONE", "Bool", "6.0", "Old sensor cycle. Not used on the machine now."]], [44, 22, 18, 90])
d.h2("DB_ALARMS - number 2")
d.table(["Name", "Data type", "Offset", "Used for"], [
    ["EMERGENCY PB PRESSED FAULT", "Bool", "0.0", "Alarm 1"], ["VFD FAULT", "Bool", "0.1", "Alarm 2"],
    ["SPARE1 ... SPARE14 (14 rows)", "Bool", "0.2 ... 1.7", "Free alarms. They fill the first 16 bits so that the alarms form one word, DBW0."],
    ["FAULT POP", "Bool", "2.0", "Tells the HMI that a fault exists"], ["WARNING POP", "Bool", "2.1", "Not used by the program"]], [58, 20, 26, 70])
d.h2("DB_AUTO - number 3")
d.table(["Name", "Data type", "Offset", "Used for"], [
    ["ACTIVE", "Bool", "0.0", "Auto cycle is started"], ["CONVEYOR ON", "Bool", "0.1", "Auto wants the conveyor to run"],
    ["CONVEYOR OFF1", "Bool", "0.2", "Old sensor cycle"], ["CONVEYOR OFF2", "Bool", "0.3", "Old sensor cycle"],
    ["P_TRG", "Bool", "0.4", "Old sensor cycle"], ["CAMERA DONE", "Bool", "0.5", "Old sensor cycle"],
    ["AUTO STATUS", "Int", "2.0", "10 / 20 / 30 for the HMI text"],
    ["STOP DELAY TIMER", "IEC_TIMER", "4.0", "Old sensor cycle (type the data type by hand)"],
    ["SENSOR CHECK DELAY", "IEC_TIMER", "20.0", "Old sensor cycle"]], [48, 24, 18, 84])
d.h2("DB_CAMERA - number 5")
d.p("19 rows named <b>DATA1</b> to <b>DATA19</b>, all data type <b>Int</b>. Offsets 0.0, 2.0, 4.0 ... 36.0. "
    "<b>DATA1 is Modbus register 40001</b>, the value the PC writes: 0 = run, 1 = stop. "
    "Tip: make DATA1, select the row, and drag the small square at the bottom-left corner of the row down; TIA numbers the copies for you.")
d.h2("DB_TCP_IP - number 12")
d.table(["Name", "Data type", "Offset", "Used for"], [
    ["MY CONNECT DATA", "TCON_IP_v4", "0.0", "Connection settings for Modbus. Type TCON_IP_v4 in the data type column by hand; it then opens into sub-rows."],
    ["NO OF DONE", "UDInt", "14.0", "Counter of good Modbus messages"], ["NO OF ERROR", "UDInt", "18.0", "Counter of failed messages"],
    ["ERROR STATUS", "UDInt", "22.0", "Last error code"]], [40, 24, 16, 94])

# ------------------------------------------------------------------ 4
d.h1("Part 4. Block FC_GENERAL (FC1) - mode and reset")
d.h2("How to create an FC (same for all six)")
d.steps([
    "<b>Program blocks &gt; Add new block</b>. Click <b>Function (FC)</b>.",
    "Name as given. Language: <b>LAD</b>. Number: <b>Manual</b>, type the number. Click <b>OK</b>.",
    "The editor opens with Network 1. To add a network: right-click a network title &gt; <b>Insert network</b>."])
d.rung("FC_GENERAL - Network 1: control ON", [[NO("DI_EMERGENCY PB"), "-", COIL("CONTROL ON FLAG")]], ncols=3,
       explain="Emergency healthy (input ON) gives CONTROL ON. Pushing Emergency drops it.")
d.rung("FC_GENERAL - Network 2: mode", [[NO("AlwaysTRUE"), NC("DI_AUTO MANUAL\nSELECTION"), COIL("MANUAL MODE\nSELECTED")],
                                        [None, NO("DI_AUTO MANUAL\nSELECTION"), COIL("AUTO MODE\nSELECTED")]], links=[(1, 0, 1)],
       explain="Selector OFF = manual, ON = auto. The AlwaysTRUE contact is only there so that two coils can share one network.")
d.rung("FC_GENERAL - Network 3: fault reset", [[NO("\"DB_HMI\".\nFAULT RESET PB"), "-", COIL("FAULT RESET FLAG")]], ncols=3,
       explain="To use a DB value, type <b>\"DB_HMI\".</b> and pick the row from the list that appears.")

# ------------------------------------------------------------------ 5
d.h1("Part 5. Block FC_MANUAL (FC2) - jog")
d.rung("FC_MANUAL - Network 1", [
    [NO("CONTROL ON\nFLAG"), NO("MANUAL MODE\nSELECTED"), NC("FAULT BIT"), NO("\"DB_HMI\".MOTOR\nJOG FWD PB"), COIL("MANUAL CONVEYOR\nFWD ON FLAG")],
    [None, None, None, NO("DI_CYCLE\nSTART PB"), None],
    [None, None, None, NO("\"DB_HMI\".MOTOR\nJOG REV PB"), COIL("MANUAL CONVEYOR\nREV ON FLAG")]],
    links=[(3, 0, 2), (4, 0, 1)],
    explain="In manual, with no fault: the HMI forward button OR the green START button runs forward. The HMI reverse button runs reverse. "
            "The motor runs only while the button is held.")
d.box("<b>Check this against your old machine.</b> You told me the red STOP button runs reverse in manual mode. In the saved file there is no such contact: "
      "reverse comes only from the HMI button, as drawn above. Test it on the old machine. If it really reverses with the red button, "
      "the old PLC holds a newer program than the file: read it out with <b>Online &gt; Upload device as new station</b> and copy FC_MANUAL from there, "
      "instead of guessing the contact.")

# ------------------------------------------------------------------ 6
d.h1("Part 6. Block FC_ALARMS (FC3) - alarms")
d.rung("FC_ALARMS - Network 1: emergency alarm", [[NC("DI_EMERGENCY PB"), "-", SET("\"DB_ALARMS\".EMERGENCY\nPB PRESSED FAULT")]], ncols=3)
d.rung("FC_ALARMS - Network 2: drive alarm", [[NO("DI_CONVEYOR\nVFD FAULT"), "-", SET("\"DB_ALARMS\".\nVFD FAULT")]], ncols=3,
       explain="Set coils: the alarm stays ON even after the cause has gone, until someone presses reset.")
d.rung("FC_ALARMS - Network 3: reset all alarms", [[NO("FAULT RESET FLAG"), BOX("", ["MOVE", "EN       ENO", "IN = 0", "OUT1 = %DB2.DBW0"]), None]], ncols=3,
       explain="MOVE is in <b>Basic instructions &gt; Move operations</b>. At IN type <b>0</b>. At OUT1 type <b>%DB2.DBW0</b>. "
               "DBW0 is the first 16 bits of DB_ALARMS = all 16 alarm bits together. Writing 0 clears them all at once.")
d.rung("FC_ALARMS - Network 4: common fault", [[BOX("", ["CMP <>", "Word", "IN1 = 0", "IN2 = %DB2.DBW0"]), "-", COIL("FAULT BIT")],
                                              [None, None, COIL("\"DB_ALARMS\".\nFAULT POP")]], links=[(2, 0, 1)],
       explain="Compare is in <b>Basic instructions &gt; Comparator operations &gt; CMP &lt;&gt;</b>. Click the <b>???</b> inside the box and choose <b>Word</b>. "
               "If any alarm bit is 1 the word is not 0, so FAULT BIT turns ON.")

# ------------------------------------------------------------------ 7
d.h1("Part 7. Block FC_OUTPUTS (FC4) - outputs")
d.rung("FC_OUTPUTS - Network 1: forward", [[NO("MANUAL CONVEYOR\nFWD ON FLAG"), "-", COIL("DO_CONVEYOR\nFWD ON")],
                                          [NO("\"DB_AUTO\".\nCONVEYOR ON"), None, None]], links=[(1, 0, 1)])
d.p("Networks 2 to 6 are one contact and one coil each:")
d.table(["Network", "Contact (normally open)", "Coil"], [
    ["2", "MANUAL CONVEYOR REV ON FLAG", "DO_CONVEYOR REV ON"], ["3", "FAULT RESET FLAG", "DO_FAULT RESET"],
    ["4", "\"DB_AUTO\".ACTIVE", "DO_TL GREEN"], ["5", "FAULT BIT", "DO_TL RED"], ["6", "MANUAL MODE SELECTED", "DO_TL AMBER"]], [24, 80, 70])
d.box("<b>Good habit:</b> each physical output (Q) is written in one place only, here. Other blocks only set flags. "
      "This avoids two rungs fighting over one output.", OKC)

# ------------------------------------------------------------------ 8
d.h1("Part 8. Block FC_AUTO (FC5) - automatic cycle")
d.p("This is the heart of the machine, and it is short: remember START / STOP, run the conveyor while the PC allows it, and tell the HMI the state.")
d.rung("FC_AUTO - Network 1: start / stop memory", [
    [NO("CONTROL ON\nFLAG"), NO("AUTO MODE\nSELECTED"), NC("FAULT BIT"), NO("DI_CYCLE\nSTART PB"), NO("DI_CYCLE\nSTOP PB"), COIL("\"DB_AUTO\".\nACTIVE")],
    [None, None, None, NO("\"DB_AUTO\".\nACTIVE"), None, None]], links=[(3, 0, 1), (4, 0, 1)],
    explain="Press START: ACTIVE turns ON and holds itself through its own contact (a \"latch\"). It drops when STOP is pressed "
            "(the input goes OFF because the button is NC), on a fault, on Emergency, or when the selector leaves AUTO.")
d.rung("FC_AUTO - Network 2: conveyor run", [
    [NO("\"DB_AUTO\".\nACTIVE"), BOX("", ["CMP ==", "Int", "IN1 = \"DB_CAMERA\".DATA1", "IN2 = 0"]), "-", COIL("\"DB_AUTO\".\nCONVEYOR ON")]], ncols=4,
    explain="Compare is in <b>Basic instructions &gt; Comparator operations &gt; CMP ==</b>; choose <b>Int</b> inside the box. "
            "DATA1 is Modbus register 40001. The PC writes 1 to stop the conveyor and 0 to let it run. "
            "After the PLC is switched on DATA1 is 0, so START runs the conveyor.")
d.rung("FC_AUTO - Network 3: status number for the HMI", [
    [NO("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), BOX("", ["MOVE", "IN = 10", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])],
    [None, NC("\"DB_AUTO\".\nACTIVE"), BOX("", ["MOVE", "IN = 20", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])]], links=[(1, 0, 1)],
    explain="10 = started (HMI text AUTO RUNNING), 20 = not started (HMI text STOPPED).")
d.box("<b>How the old file looks.</b> These three networks do exactly what the old PLC does. The old file is longer only because the switched-off "
      "sensor cycle is still drawn in it: network 2 has three extra contacts that change nothing, network 3 has a third row for status 30, "
      "and there are more networks that can never become active. Appendix A shows all of it, if you want an exact copy or more practice.")

d.h1("Part 8b. Block FC_TCP_IP (FC6) - Modbus TCP server")
d.h2("Network 1: connection settings")
d.p("Insert ten MOVE boxes, each directly on the left rail (use <b>Open branch</b> for each new row). Type the IN and OUT1 values from the table. "
    "For OUT1 type <b>\"DB_TCP_IP\".\"MY CONNECT DATA\".</b> and pick the sub-row.")
d.table(["IN", "OUT1 = \"DB_TCP_IP\".\"MY CONNECT DATA\". ...", "Meaning"], [
    ["\"Local~PROFINET_interface_1\"", "InterfaceId", "Which Ethernet port. Pick this name from the list; it is created with the CPU (value 64)."],
    ["1", "ID", "Connection number"], ["11", "ConnectionType", "11 = TCP"],
    ["0", "RemoteAddress.ADDR[1]", "Remote IP 0.0.0.0 = accept any device"], ["0", "RemoteAddress.ADDR[2]", ""],
    ["0", "RemoteAddress.ADDR[3]", ""], ["0", "RemoteAddress.ADDR[4]", ""],
    ["0", "RemotePort", "Any port on the other side"], ["502", "LocalPort", "The Modbus port of the PLC"]], [52, 62, 60])
d.rung("Same network, last row: the PLC waits for the connection",
       [[NC("AlwaysTRUE"), "-", COIL("\"DB_TCP_IP\".\"MY CONNECT\nDATA\".ActiveEstablished")]], ncols=3,
       explain="This contact never passes, so ActiveEstablished is always 0 = the PLC is the passive side (server).")
d.h2("Network 2: the Modbus server")
d.steps([
    "Instructions panel: <b>Communication &gt; Others &gt; MODBUS TCP &gt; MB_SERVER</b>. Drag it onto the line.",
    "\"Call options\" opens. Choose <b>Single instance</b>. Name <b>MB_SERVER_DB</b>. Number <b>Manual</b>, <b>4</b>. Click <b>OK</b>. TIA creates DB4 by itself.",
    "Fill the inputs on the left of the box as in the table. Leave all outputs on the right empty."])
d.table(["Pin", "Type this", "Meaning"], [
    ["DISCONNECT", "AlwaysFALSE", "0 = keep listening for a connection"],
    ["MB_HOLD_REG", "P#DB5.DBX0.0 INT 10", "Registers 40001 - 40010 are the first 10 values of DB_CAMERA (DB5)"],
    ["CONNECT", "\"DB_TCP_IP\".\"MY CONNECT DATA\"", "The settings from network 1"]], [34, 60, 80])
d.rung("FC_TCP_IP - Network 3: message counters", [
    [NO("\"MB_SERVER_DB\".\nNDR"), BOX("", ["ADD  UDInt", "IN1 = NO OF DONE", "IN2 = 1", "OUT = NO OF DONE"]), None],
    [NO("\"MB_SERVER_DB\".\nDR"), None, None],
    [NO("\"MB_SERVER_DB\".\nERROR"), BOX("", ["ADD  UDInt", "IN1 = NO OF ERROR", "IN2 = 1", "OUT = NO OF ERROR"]),
     BOX("", ["MOVE", "IN = \"MB_SERVER_DB\".", "STATUS", "OUT1 = ERROR STATUS"])]],
    links=[(1, 0, 1)],
    explain="ADD is in <b>Math functions</b>; choose UDInt inside the box. NO OF DONE, NO OF ERROR and ERROR STATUS are in \"DB_TCP_IP\". "
            "These counters are only for fault finding: watch them go up when the PC talks to the PLC.")

# ------------------------------------------------------------------ 9
d.h1("Part 9. Main block OB1 and compile")
d.steps([
    "Open <b>Program blocks &gt; Main [OB1]</b>.",
    "Drag <b>FC_AUTO</b> from the project tree onto the line of Network 1. A box \"FC_AUTO\" appears.",
    "Insert five more networks and drag one block into each, in this order: <b>FC_ALARMS, FC_GENERAL, FC_MANUAL, FC_OUTPUTS, FC_TCP_IP</b>.",
    "In the project tree click <b>PLC_1</b>. Click <b>Compile</b> in the toolbar.",
    "Look at the <b>Info &gt; Compile</b> tab at the bottom. It must end with <b>Errors: 0</b>. Double-click any red line to jump to the mistake. "
    "Usual causes: a name typed differently, a contact left with &lt;??.?&gt;, or a DB still \"optimized\".",
    "Save with <b>Ctrl + S</b>."])
d.box("<b>Check the block list.</b> Program blocks must now show: Main [OB1], FC_GENERAL [FC1], FC_MANUAL [FC2], FC_ALARMS [FC3], FC_OUTPUTS [FC4], "
      "FC_AUTO [FC5], FC_TCP_IP [FC6], DB_HMI [DB1], DB_ALARMS [DB2], DB_AUTO [DB3], MB_SERVER_DB [DB4], DB_CAMERA [DB5], DB_TCP_IP [DB12].", OKC)

# ------------------------------------------------------------------ 10
d.page()
d.h1("Part 10. HMI panel (KTP700 Basic)")
d.p("The old panel has five screens and one template. The template holds everything that is the same on all screens: "
    "the title bar on top and the row of five buttons at the bottom. The screen is 800 x 480 points. "
    "Positions below are <b>x, y</b> of the top-left corner and <b>width x height</b>; type them under <b>Properties &gt; Layout</b>.")
d.h2("10.1 Add the panel and connect it to the PLC")
d.steps([
    "Project tree: <b>Add new device &gt; HMI &gt; SIMATIC Basic Panel &gt; 7\" Display &gt; KTP700 Basic &gt; 6AV2 123-2GB03-0AX0</b>. Device name <b>HMI_1</b>. "
    "Leave \"Start device wizard\" ticked. Click OK.",
    "Wizard page \"PLC connections\": click <b>Browse</b>, choose <b>PLC_1</b>. On the next pages untick the ready-made screens and system screens, and click <b>Finish</b>.",
    "Project tree: <b>Devices &amp; networks</b>. Double-click the HMI. Properties: <b>PROFINET Interface [X1] &gt; Ethernet addresses</b>: subnet PN/IE_1, "
    "IP <b>192.168.0.41</b>, mask 255.255.255.0.",
    "Check <b>HMI_1 &gt; Connections</b>: one row <b>HMI_Connection_1</b> to PLC_1 must exist."])
d.h2("10.2 HMI tags (exactly these twelve)")
d.p("Open <b>HMI_1 &gt; HMI tags &gt; Default tag table</b>. Connection is always <b>HMI_Connection_1</b>. For rows with a PLC name, click the \"...\" button in the "
    "<b>PLC tag</b> column and pick it; TIA fills the rest. For rows with only an address, choose Access mode <b>&lt;absolute access&gt;</b> and type the address.")
d.table(["HMI tag name", "Data type", "PLC tag or address", "Used for"], [
    ["AUTO MODE SELECTED", "Bool", "PLC tag AUTO MODE SELECTED (%M2.2)", "Mode text AUTO / MANUAL"],
    ["DB_ALARMS_FAULT POP", "Bool", "\"DB_ALARMS\".\"FAULT POP\" (%DB2.DBX2.0)", "Fault line in the title bar"],
    ["DB_ALARMS_WARNING POP", "Bool", "\"DB_ALARMS\".\"WARNING POP\" (%DB2.DBX2.1)", "Warning line (the PLC never sets it)"],
    ["IB0", "Byte", "%IB0 (absolute access)", "Input lamps I0.0 - I0.7"],
    ["IB1", "Byte", "%IB1 (absolute access)", "Input lamps I1.0 - I1.5"],
    ["QB0", "Byte", "%QB0 (absolute access)", "Output lamps Q0.0 - Q0.7"],
    ["QB1", "Byte", "%QB1 (absolute access)", "Output lamps Q1.0 - Q1.1"],
    ["ALARM WORD", "Word", "%DB2.DBW0 (absolute access). Acquisition mode: <b>Cyclic continuous</b>", "Alarm messages"],
    ["DB_HMI_FAULT RESET PB", "Bool", "\"DB_HMI\".\"FAULT RESET PB\" (%DB1.DBX0.0)", "FAULT RESET button"],
    ["DB_HMI_MOTOR JOG REV PB", "Bool", "\"DB_HMI\".\"MOTOR JOG REV PB\" (%DB1.DBX0.2)", "REV JOG button"],
    ["DB_AUTO_AUTO STATUS", "Int", "\"DB_AUTO\".\"AUTO STATUS\" (%DB3.DBW2)", "Status text"],
    ["DB_HMI_MOTOR JOG FWD PB", "Bool", "\"DB_HMI\".\"MOTOR JOG FWD PB\" (%DB1.DBX0.1)", "FWD JOG button"],
], [44, 18, 74, 38])
d.h2("10.3 Text lists and alarms")
d.table(["Where", "What to enter"], [
    ["<b>HMI_1 &gt; Text and graphic lists &gt; Text lists</b>", "List <b>AUTO_STATUS</b>, selection \"Value/Range\": 10 = <b>AUTO RUNNING</b>, 20 = <b>STOPPED</b>, 30 = <b>WAITING FOR CAMERA ACK</b>.<br/>"
     "List <b>MODE</b>, selection \"Bit (0, 1)\": 0 = <b>MANUAL</b>, 1 = <b>AUTO</b>."],
    ["<b>HMI_1 &gt; HMI alarms &gt; Discrete alarms</b>", "Row 1: alarm text <b>EMERGENCY PB PRESSED FAULT (I0.4)</b>, alarm class Errors, trigger tag <b>ALARM WORD</b>, trigger bit <b>8</b>.<br/>"
     "Row 2: <b>CONVEYOR VFD FAULT (I0.5)</b>, trigger tag ALARM WORD, trigger bit <b>9</b>."],
], [56, 118])
d.box("<b>Why bits 8 and 9, not 0 and 1?</b> In a Siemens word the first byte (DBB0) is the high half. So DBX0.0 is bit 8 of DBW0 and DBX0.1 is bit 9. "
      "TIA shows the matching address (DB2.DBX0.0) next to the trigger bit; use that to check.", OKC)
d.h2("10.4 The template (shown on every screen)")
d.p("Open <b>HMI_1 &gt; Screen management &gt; Templates &gt; Template_1</b>. Drag the objects from the <b>Toolbox</b> on the right.")
d.table(["Object", "x, y", "Size", "Settings"], [
    ["Rectangle (top bar)", "1, 1", "798 x 58", "Grey background"],
    ["Date/time field", "1, 1", "121 x 58", "Top left"],
    ["Date/time field", "677, 1", "121 x 58", "Top right"],
    ["Text field <b>CONVEYOR</b>", "225, 11", "327 x 39", "Dark grey background, white text. This is the title."],
    ["Alarm view, twice, one on top of the other", "124, 4", "550 x 53", "One with red background for alarm class Errors, one yellow for Warnings. They cover the title, "
     "so they are most likely made visible only while there is a fault: <b>Animations &gt; Display &gt; Visibility</b>, tag DB_ALARMS_FAULT POP (red one) and DB_ALARMS_WARNING POP (yellow one), visible at 1."],
    ["Button without text (grey strip behind the mode line)", "0, 61", "800 x 30", "Its purpose could not be read. A plain grey rectangle looks the same."],
    ["Text field <b>MODE :-</b>", "12, 64", "65 x 23", ""],
    ["Symbolic I/O field", "89, 61", "117 x 27", "Mode: Output. Tag AUTO MODE SELECTED. Text list MODE."],
    ["Rectangle (bottom bar)", "1, 406", "799 x 68", "Grey background"],
    ["Button <b>AUTO</b>", "6, 411", "151 x 60", "Events &gt; Click &gt; Add function &gt; Screens &gt; <b>ActivateScreen</b>: AUTO OPERATION"],
    ["Button <b>MANUAL</b>", "166, 411", "151 x 60", "ActivateScreen: MANUAL OPERATION"],
    ["Button <b>ALARMS</b>", "326, 411", "151 x 60", "ActivateScreen: ALARMS"],
    ["Button <b>IO STATUS</b>", "486, 411", "151 x 60", "ActivateScreen: INPUT STATUS"],
    ["Button <b>FAULT RESET</b> (two lines: FAULT / RESET)", "646, 411", "151 x 60", "Yellow background. Events &gt; <b>Press</b>: Edit bits &gt; <b>SetBit</b>, tag DB_HMI_FAULT RESET PB. "
     "Events &gt; <b>Release</b>: Edit bits &gt; <b>ResetBit</b>, same tag."],
], [44, 18, 20, 92])
d.h2("10.5 The five screens")
d.p("Create each with <b>HMI_1 &gt; Screens &gt; Add new screen</b>, give it the name shown, and check that its template is Template_1.")
d.table(["Screen", "Object", "x, y", "Size", "Settings"], [
    ["AUTO OPERATION", "Text field <b>AUTO OPERATION</b>", "308, 62", "181 x 27", "Screen title"],
    ["", "Text field <b>AUTO STATUS</b>", "19, 135", "155 x 29", ""],
    ["", "Symbolic I/O field", "177, 123", "560 x 52", "Mode: Output. Tag DB_AUTO_AUTO STATUS. Text list AUTO_STATUS. White background, text centred."],
    ["MANUAL OPERATION", "Text field <b>MANUAL OPERATION</b>", "308, 62", "210 x 27", "Screen title"],
    ["", "Button <b>CONVEYOR FWD JOG</b> (two lines)", "166, 194", "179 x 82", "Press: SetBit DB_HMI_MOTOR JOG FWD PB. Release: ResetBit, same tag."],
    ["", "Button <b>CONVEYOR REV JOG</b> (two lines)", "429, 190", "179 x 82", "Press: SetBit DB_HMI_MOTOR JOG REV PB. Release: ResetBit, same tag."],
    ["ALARMS", "Alarm view", "2, 92", "797 x 308", "Toolbox &gt; Controls &gt; Alarm view"],
    ["INPUT STATUS", "Text field <b>INPUT STATUS</b>", "308, 63", "147 x 27", "Screen title"],
    ["", "Lamp table (see 10.6)", "0, 94", "", "14 rows: I0.0 - I1.5"],
    ["", "Button <b>NEXT</b>", "644, 341", "151 x 60", "ActivateScreen: OUTPUT STATUS-1"],
    ["OUTPUT STATUS-1", "Text field <b>OUTPUT STATUS-1</b>", "308, 63", "184 x 27", "Screen title"],
    ["", "Lamp table (see 10.6)", "0, 94", "", "10 rows: Q0.0 - Q1.1"],
    ["", "Button <b>BACK</b>", "644, 341", "151 x 60", "ActivateScreen: INPUT STATUS"],
], [30, 48, 18, 18, 60])
d.p("<b>Start screen:</b> set <b>HMI_1 &gt; Runtime settings &gt; General &gt; Start screen</b> = AUTO OPERATION (it is the first screen of the old project, so most likely its start screen).")
d.h2("10.6 The lamp tables on the two status screens")
d.p("Each table is built from text fields and circles. There are two blocks side by side: the left block starts at x = 0, the right block at x = 401.")
d.table(["Piece", "Left block x / width", "Right block x / width", "Look"], [
    ["Header row at y = 94, height 26: <b>ADDRESS</b>, <b>STATUS</b>, <b>DESCRIPTION</b>", "0 / 84,  85 / 70,  156 / 241", "401 / 84,  486 / 70,  557 / 242", "Green background, white text"],
    ["Data rows, height 34, at y = 120, 155, 191, 227, 263, 299, 335, 371", "Same three columns", "Same three columns", "Dark grey background. Address in yellow text, description in white text. The STATUS cell stays empty."],
    ["Circle 23 x 23 in the STATUS column of each row", "x = 109", "x = 510", "y = row y + 6. Grey when the signal is 0."],
], [62, 36, 36, 40])
d.table(["Screen", "Left block (8 rows)", "Right block"], [
    ["INPUT STATUS", "I0.0 PRODUCT SENSOR, I0.1 AUTO MANUAL SELECTION, I0.2 CYCLE START PB, I0.3 CYCLE STOP PB, I0.4 EMERGENCY PB, I0.5 CONVEYOR VFD FAULT, I0.6 SPARE, I0.7 SPARE",
     "I1.0 - I1.5, all SPARE (6 rows)"],
    ["OUTPUT STATUS-1", "Q0.0 CONVEYOR FWD ON, Q0.1 CONVEYOR REV ON, Q0.2 FAULT RESET, Q0.3 TL GREEN, Q0.4 TL RED, Q0.5 TL AMBER, Q0.6 SPARE, Q0.7 SPARE",
     "Q1.0, Q1.1, both SPARE (2 rows)"],
], [34, 100, 40])
d.p("<b>Make a circle light up:</b> select the circle &gt; Properties &gt; <b>Animations &gt; Display &gt; Add new animation &gt; Appearance</b>. "
    "Tag: <b>IB0</b> for I0.x (IB1 for I1.x, QB0 for Q0.x, QB1 for Q1.x). Type: <b>Single bit</b>, and the bit number = the digit after the dot "
    "(I0.3 is bit 3). Then two rows: 0 = grey, 1 = green. Build one complete row, then copy and paste it and change only the address text, the description and the bit number.")
d.p("<b>Last step:</b> click <b>HMI_1</b> and <b>Compile</b>. Fix errors until it shows Errors: 0.")

# ------------------------------------------------------------------ 11
d.h1("Part 11. Download and test")
d.h2("11.1 Download")
d.steps([
    "Laptop network card: IP 192.168.0.100, mask 255.255.255.0. Connect laptop, PLC and HMI to the switch.",
    "Click <b>PLC_1</b>. Menu <b>Online &gt; Extended download to device</b>. Interface type <b>PN/IE</b>, choose your network card, tick <b>Show all compatible devices</b>, "
    "<b>Start search</b>, select the PLC, <b>Load</b>. Accept the questions, then <b>Load</b>, tick <b>Start module</b>, <b>Finish</b>.",
    "On the panel: Settings &gt; Network Interface: IP 192.168.0.41. Settings &gt; Transfer Settings: Enable transfer ON.",
    "Click <b>HMI_1</b>. <b>Online &gt; Extended download to device</b>, same choices, <b>Load</b>. Accept an operating system update if TIA asks."])
d.h2("11.2 Watch your logic working")
d.steps([
    "Open a block, for example FC_AUTO. Click the <b>Monitoring on/off</b> button (glasses icon) in the block toolbar.",
    "Green solid line = signal passes. Blue dotted line = no signal. This is the best way to learn: press a button on the machine and see which contact changes.",
    "For values, use <b>PLC_1 &gt; Watch and force tables &gt; Add new watch table</b>. Add \"DB_CAMERA\".DATA1, \"DB_AUTO\".\"AUTO STATUS\", \"DB_TCP_IP\".\"NO OF DONE\". "
    "Click the glasses icon. To change a value type it in <b>Modify value</b> and click the lightning icon."])
d.h2("11.3 Test list")
d.table(["#", "Do this", "You must see"], [
    ["1", "Nothing pressed, selector on MANUAL", "I0.3 and I0.4 ON. Amber lamp ON. HMI mode text MANUAL."],
    ["2", "Hold CONVEYOR FWD JOG on the HMI, then CONVEYOR REV JOG", "Q0.0 ON while held, then Q0.1 ON while held."],
    ["3", "Hold the green START button (still MANUAL)", "Q0.0 ON while held."],
    ["4", "Push Emergency", "Red lamp ON, alarm text on the HMI. Jog does not work."],
    ["5", "Release Emergency, press FAULT RESET on the HMI", "Alarm clears, red lamp OFF."],
    ["6", "Selector AUTO, press START", "Green lamp ON, Q0.0 ON, HMI status AUTO RUNNING."],
    ["7", "In the watch table write 1 to \"DB_CAMERA\".DATA1, then 0 (this is what the PC does)", "Q0.0 OFF at 1 (green lamp stays ON). Q0.0 ON again at 0."],
    ["8", "Press STOP", "Green lamp OFF, Q0.0 OFF, HMI status STOPPED."],
    ["9", "On the PC, inside the folder conveyor_automation-main / conveyor_automation-main, run <font face=\"DVM\">python3 backend_testing/test_plc_connection.py</font>. Type w, then 1. Type w, then 0.",
     "Conveyor stops, then runs. \"DB_TCP_IP\".\"NO OF DONE\" counts up."],
], [8, 92, 74])
d.box("<b>No hardware yet?</b> You can still practise parts 1 to 10 and compile. If S7-PLCSIM is installed, click PLC_1 and the <b>Start simulation</b> button in the toolbar "
      "to run the program on the laptop and switch inputs by hand. The Modbus part needs the real PLC.", OKC)
d.h1("Common mistakes")
d.table(["What you see", "Cause", "Fix"], [
    ["Machine never starts in AUTO", "I0.3 or I0.4 is OFF", "STOP and Emergency must be wired through NC contacts."],
    ["Green lamp ON but the conveyor does not run in AUTO", "Register 40001 (\"DB_CAMERA\".DATA1) is not 0", "The PC wrote 1. Click Rescan Stack or Start on the PC, or write 0 in the watch table."],
    ["Compile error at %DB2.DBW0 or at MB_HOLD_REG", "DB still has \"Optimized block access\" ticked", "Untick it (part 3, step 3) and compile again."],
    ["Compile error \"tag not defined\"", "Name typed differently in two places", "Pick names from the drop-down list instead of typing."],
    ["HMI shows #####", "No connection to the PLC", "Check both IP addresses, cables, and HMI_Connection_1."],
    ["Alarm text does not appear but the red lamp is ON", "Wrong trigger bit", "Use bits 8 and 9 (part 10.3)."],
    ["The PC cannot connect", "FC_TCP_IP not called in OB1, or wrong port", "Check part 9 step 3 and LocalPort = 502."],
], [50, 50, 74])

# ------------------------------------------------------------------ appendix
d.page()
d.h1("Appendix A. The switched-off sensor cycle in the old file (optional)")
d.p("The old program was first written for another way of working: the sensor was on PLC input I0.0, the PLC stopped the belt a set time after the sensor, "
    "wrote 1 to register 40001 as a signal, and waited until the other side wrote 0 back. When the sensor was moved to the camera, this cycle was switched off "
    "but left in the file. You do <b>not</b> need it. Build it only if you want your file to be an exact copy, or to practise timers, edge detection and set / reset.")
d.box("If you build it, also build the <b>normally closed AlwaysTRUE</b> contact at the start of A1 and A2. It never passes, and it is what keeps the cycle switched off. "
      "Without it the cycle would wake up as soon as something is wired to I0.0.", BAD)
d.rung("A1. Sensor settle time", [[NC("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), NO("\"DB_AUTO\".\nCONVEYOR ON"),
                                   BOX("\"DB_AUTO\".\nSENSOR CHECK DELAY", ["TON", "IN        Q", "PT = T#500ms", "ET"])]], ncols=4,
       explain="TON = on-delay timer, in <b>Basic instructions &gt; Timer operations</b>. Drag it in. A window \"Call options\" opens: click <b>Cancel</b>. "
               "Then double-click the <b>???</b> above the box and type <b>\"DB_AUTO\".\"SENSOR CHECK DELAY\"</b>. At PT type <b>T#500ms</b>.")
d.rung("A2. Product arrives", [[NC("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), NO("\"DB_AUTO\".\nCONVEYOR ON"), NO("\"DB_AUTO\".SENSOR\nCHECK DELAY.Q"),
                                NO("DI_PRODUCT\nSENSOR"), BOX("", ["P_TRIG", "CLK      Q", "\"DB_AUTO\".P_TRG"]), SET("\"DB_AUTO\".\nCONVEYOR OFF1")]],
       explain="P_TRIG (in Bit logic operations) gives a signal for one moment only, when the sensor changes from OFF to ON. "
               "Type <b>\"DB_AUTO\".P_TRG</b> under the box; it remembers the last state.")
d.rung("A3. Stop delay", [[NO("\"DB_AUTO\".\nCONVEYOR OFF1"), "-", BOX("\"DB_AUTO\".\nSTOP DELAY TIMER", ["TON", "IN        Q", "PT = \"DB_AUTO\".\"STOP", "DELAY TIMER\".PT"]), None]], ncols=4,
       explain="At PT type <b>\"DB_AUTO\".\"STOP DELAY TIMER\".PT</b>. The time itself is written by A6.")
d.rung("A4. Stop and signal", [[NO("\"DB_AUTO\".STOP\nDELAY TIMER.Q"), "-", RST("\"DB_AUTO\".\nCONVEYOR OFF1")],
                               [None, BOX("", ["MOVE", "IN = 1", "OUT1 = \"DB_CAMERA\".DATA1"]), None],
                               [None, "-", SET("\"DB_AUTO\".\nCONVEYOR OFF2")]], links=[(1, 0, 2)])
d.rung("A5. Continue", [[NO("\"DB_AUTO\".\nCONVEYOR OFF2"), NO("\"DB_AUTO\".\nCAMERA DONE"), "-", RST("\"DB_AUTO\".\nCONVEYOR OFF1")],
                        [None, NO("\"DB_HMI\".\nCAMERA DONE"), None, RST("\"DB_AUTO\".\nCONVEYOR OFF2")],
                        [NC("\"DB_AUTO\".\nACTIVE"), "-", None, None]], links=[(1, 0, 1), (2, 0, 2), (3, 0, 1)])
d.add(KeepTogether([Paragraph("A6. Delay time in seconds (SCL text)", ST["h3"]),
                    Paragraph("Right-click the network title &gt; <b>Insert SCL network</b>. Type this one line:", ST["p"]),
                    Paragraph("\"DB_AUTO\".\"STOP DELAY TIMER\".PT := \"DB_HMI\".\"STOP TIME\" * 1000;", ST["code"]),
                    Spacer(1, 2)]))
d.rung("A7. Camera done", [[NO("\"DB_AUTO\".\nCONVEYOR OFF2"), BOX("", ["CMP ==", "Int", "IN1 = \"DB_CAMERA\".DATA1", "IN2 = 0"]), "-", COIL("\"DB_AUTO\".\nCAMERA DONE")]], ncols=4)
d.h2("Where these sit in the old file, and the small differences in part 8")
d.bullets([
    "In the old file, part 8 network 2 and A1 to A4 are drawn together in <b>one</b> network that starts with a normally open AlwaysTRUE contact.",
    "Part 8 network 2 in the old file: between the ACTIVE contact and the compare there is a normally closed <b>\"DB_AUTO\".CONVEYOR OFF2</b> contact "
    "with a normally open <b>AlwaysTRUE</b> contact parallel to it. Because of the AlwaysTRUE, the pair always passes.",
    "Part 8 network 3 in the old file: the first row also has a normally closed CONVEYOR OFF2 contact, and there is a third row: "
    "ACTIVE and CONVEYOR OFF2 (normally open), MOVE 30 to AUTO STATUS (HMI text WAITING FOR CAMERA ACK). It never becomes true now.",
    "So the old FC_AUTO has six networks: start / stop memory, the big network, A5, the status network, A6 and A7."])

d.build(OUT, "Write the Conveyor Program Yourself - TIA Portal V21, revision 2", "Write the Conveyor Program Yourself - TIA Portal V21 (Rev 2)")
print("ok", OUT)

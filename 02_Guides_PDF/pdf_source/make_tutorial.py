"""Builds Conveyor_Program_From_Scratch_TIA_V21.pdf  (revision 2).

Run:  PYTHONPATH=<folder with reportlab> python3 make_tutorial.py <output.pdf>
"""
import sys

from reportlab.platypus import KeepTogether, Paragraph, Spacer

from common import BAD, BOX, CHK, COIL, NC, NO, OKC, RST, SET, ST, Doc

OUT = sys.argv[1]
d = Doc()
d.title("Write the Conveyor Program Yourself",
        "A to Z in TIA Portal V21, Revision 3.2 (13 October 2026): new project, hardware, tags, data blocks, ladder logic, "
        "Modbus, HMI, download and test.<br/>Every name, address, network and value is taken from the old project \"latest plc\", exported through TIA Portal itself.")

d.box("<b>New: read the companion guide \"Understand the Conveyor Program\"</b> (Conveyor_Program_Explained.pdf, same folder). "
      "This guide says <b>what to click</b>; the companion says <b>what each part means, why it is there</b> (tags, data blocks, every network) "
      "and how to design a program from a problem statement. Its first page shows which part to read with which part of this guide.", OKC)
d.box("<b>What changed in Revision 3.2.</b> Every item is now marked <b>needed</b> or <b>not needed</b>, so you do not spend time on things the machine never uses: "
      "an overview in part 0, a \"Needed?\" column in every tag, data block and HMI table, a mark on every FC_AUTO and FC_TCP_IP network, "
      "and a short 3-network version of FC_AUTO (part 8, way A) that behaves exactly like the original.", OKC)
d.box("<b>What changed in Revision 3.1.</b> No more shortened rows. Revision 3 squeezed several items into one table row "
      "(for example \"DI_SPARE I0.6, DI_SPARE I0.7 ... one row each\"), which was confusing. Now <b>every tag, every data block row, every MOVE row and every lamp "
      "has its own row</b> with its own name, address and position: parts 2, 3, 8b, 10.2 and 10.6.", OKC)
d.box("<b>What changed in Revision 3.</b> On 12 October 2026 the old project was opened in TIA Portal (a copy) and every block was exported by TIA itself. "
      "Revisions 1 and 2 were based on decoding the raw project file. Corrected now:<br/>"
      "1. Part 1: the <b>clock memory byte</b> is switched ON at address 0 in the old project.<br/>"
      "2. Part 2: the tags are in <b>three tag tables</b> (DI, DO, Default tag table), with spare tags.<br/>"
      "3. Part 3: <b>DB_TCP_IP is optimized</b>; only the other four DBs are non-optimized.<br/>"
      "4. Parts 4 - 8b: every network has its <b>real title</b> and <b>exact layout</b>. FC_MANUAL has the reverse row on top. "
      "<b>FC_AUTO is now the real six networks</b> (Revision 2 showed a shortened version). FC_TCP_IP: real row order, MB_SERVER <b>V5.3</b>.<br/>"
      "5. Part 10 (HMI) is now from the HMI export: template <b>MAIN</b>, screens <b>AUTO, MANUAL, ALARMS, INPUT STATUS, OUTPUT STATUS</b> with their numbers, "
      "three HMI tag tables, buttons with <b>SetBitWhileKeyPressed</b>, the green / red status field, red / green I/O lamps, and the BACK button that points to its own screen.<br/>"
      "6. New part 12: the red-button reverse jog you asked for. It is <b>not</b> in the old program and is added as a separate, optional step.", OKC)

# ------------------------------------------------------------------ 0
d.h1("0. How to use this guide")
d.bullets([
    "Work through the parts in order. Each part ends with something you can check.",
    "Type names <b>exactly</b> as shown, including spaces and capital letters. The HMI and Modbus depend on the names and addresses.",
    "The PLC part (parts 1 - 9) is exact: it was exported from the old project by TIA Portal itself (12 October 2026).",
    "The HMI part (part 10) is exact too, from the HMI export of 12 October 2026, except the alarm views and discrete alarms, which the export cannot include (marked CHECK).",
    "I could not run TIA Portal myself, so a menu name may differ by a word or two in your V21 installation. The position in the menus is the same."])
d.table(["Part", "You build", "About"], [
    ["1", "New project and PLC hardware", "15 min"], ["2", "Three PLC tag tables (inputs, outputs, flags)", "20 min"],
    ["3", "Five data blocks", "30 min"], ["4 - 8b", "Six program blocks (FC) in ladder", "2 hours"],
    ["9", "Main block OB1, compile", "10 min"], ["10", "HMI panel", "2 hours"], ["11", "Download and test", "1 hour"],
    ["12", "Optional, new: red-button reverse jog (not in the old program)", "30 min"]], [20, 110, 44])
d.h2("What is needed, and what is only for an identical copy")
d.p("You do not have to build everything. This guide marks every item:")
d.table(["Mark", "Meaning"], [
    ["YES / NEEDED", "The machine needs it. Without it the program does not compile or the machine does not work."],
    ["USEFUL", "The machine runs without it, but the operator loses information (a status text, an alarm text)."],
    ["NO / NOT needed", "Nothing uses it. Build it only if you want your project to look exactly like the old one."],
], [36, 138], status_col=0)
d.p("<b>Minimum build</b> = only the YES items (and the USEFUL ones you want). It behaves exactly like the old machine and takes about half the time:")
d.table(["Part", "Needed", "Not needed (identical copy only)"], [
    ["1. Hardware", "CPU, IP address, <b>system memory byte</b> at address 1", "Clock memory byte"],
    ["2. Tags", "5 inputs (I0.1 - I0.5), 6 outputs (Q0.0 - Q0.5), 7 flags (M2.0 - M2.6). One tag table is enough", "The I0.0 sensor tag, 8 spare input tags, 4 spare output tags, separate DI / DO tables"],
    ["3. Data blocks", "DB_HMI: 3 buttons. DB_ALARMS: all 18 rows. DB_AUTO: ACTIVE, CONVEYOR ON, AUTO STATUS. DB_CAMERA: DATA1 - DATA10. DB_TCP_IP: MY CONNECT DATA",
     "DB_HMI: STOP TIME, CAMERA DONE. DB_AUTO: 6 old-cycle rows. DB_CAMERA: DATA11 - DATA19. DB_TCP_IP: 3 counters"],
    ["4 - 7. FC_GENERAL, FC_MANUAL, FC_ALARMS, FC_OUTPUTS", "Every network", "Network titles, the empty last network"],
    ["8. FC_AUTO", "<b>Way A: 3 short networks</b>", "Way B: the 6 original networks with the switched-off sensor cycle"],
    ["8b. FC_TCP_IP", "Network 1 (connection settings), network 2 (MB_SERVER)", "Network 3 (message counters)"],
    ["9. OB1", "The six block calls, in order", "The empty network 7"],
    ["10. HMI", "Connection, FAULT / RESET button, AUTO and MANUAL buttons, the two JOG buttons. Useful: mode field, status field, alarms",
     "Date / time, title, coloured bars, the two I/O status screens with their 24 lamps, exact colours and positions"],
    ["12. Red-button reverse", "-", "Optional new feature"],
], [34, 76, 64])
d.box("If you choose the minimum build, keep it consistent: an item marked \"old sensor cycle only\" is needed by FC_AUTO way B and by nothing else. "
      "Way A + no old-cycle rows, or way B + all old-cycle rows.", CHK)
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
    "Click <b>System and clock memory</b>. Tick <b>Enable the use of system memory byte</b>, address <b>1</b>: this is <b>needed</b>. "
    "<b>Enable the use of clock memory byte</b>, address <b>0</b>: <b>not needed</b>, the program never uses it; tick it only for an identical copy.",
    "Click <b>DI 14/DQ 10 &gt; I/O addresses</b>. Check: input start address 0, output start address 0.",
    "Press <b>Ctrl + S</b> to save."])
d.box("<b>Why the system and clock memory bytes?</b> They create ready-made tags. The system memory byte at 1 gives <b>AlwaysTRUE = M1.2</b> and <b>AlwaysFALSE = M1.3</b>; "
      "the program uses both. The clock memory byte at 0 gives eight blinking bits, from Clock_10Hz (M0.0) to Clock_0.5Hz (M0.7); part 2 lists them all. The old program does not use them, "
      "but they are switched on in the old project, so copy that. With other addresses the M2.x flags could clash.", OKC)

# ------------------------------------------------------------------ 2
d.h1("Part 2. PLC tags")
d.p("The old project keeps its tags in <b>three tables</b>: <b>DI</b> (inputs), <b>DO</b> (outputs) and the <b>Default tag table</b> (system and clock tags, plus the 7 internal flags). "
    "The column <b>Needed?</b> tells you what the machine really uses. <b>Minimum:</b> type only the YES rows; you may put them all into the Default tag table "
    "(three tables are only tidier). <b>Identical copy:</b> type every row.")
d.steps([
    "Project tree: <b>PLC_1 &gt; PLC tags</b>. For the identical copy: double-click <b>Add new tag table</b>, right-click the new table &gt; <b>Rename</b> &gt; type <b>DI</b>; "
    "do the same again for <b>DO</b>. For the minimum: skip this step and use the Default tag table.",
    "Open the table. Click the first empty row (&lt;Add new&gt;), type the name, choose data type <b>Bool</b>, type the address.",
    "The Default tag table already holds the system tags made by part 1. Leave them, and add the 7 flags."])
d.h2("Inputs (tag table DI)")
d.table(["Name", "Data type", "Address", "Meaning", "Needed?"], [
    ["DI_PRODUCT SENSOR", "Bool", "%I0.0", "Old sensor input, nothing wired to it", "NO - old sensor cycle only"],
    ["DI_AUTO MANUAL SELECTION", "Bool", "%I0.1", "1 = AUTO, 0 = MANUAL", "YES"],
    ["DI_CYCLE START PB", "Bool", "%I0.2", "Green start button (NO contact)", "YES"],
    ["DI_CYCLE STOP PB", "Bool", "%I0.3", "Red stop button (NC contact, so 1 = not pressed)", "YES"],
    ["DI_EMERGENCY PB", "Bool", "%I0.4", "Emergency (NC contact, so 1 = healthy)", "YES"],
    ["DI_CONVEYOR VFD FAULT", "Bool", "%I0.5", "1 = drive has a fault", "YES"],
    ["DI_SPARE I0.6", "Bool", "%I0.6", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I0.7", "Bool", "%I0.7", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I1.0", "Bool", "%I1.0", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I1.1", "Bool", "%I1.1", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I1.2", "Bool", "%I1.2", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I1.3", "Bool", "%I1.3", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I1.4", "Bool", "%I1.4", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DI_SPARE I1.5", "Bool", "%I1.5", "Spare, used nowhere", "NO - only for an identical copy"]], [50, 16, 18, 52, 38], status_col=4)
d.h2("Outputs (tag table DO)")
d.table(["Name", "Data type", "Address", "Meaning", "Needed?"], [
    ["DO_CONVEYOR FWD ON", "Bool", "%Q0.0", "Drive: run forward", "YES"],
    ["DO_CONVEYOR REV ON", "Bool", "%Q0.1", "Drive: run reverse", "YES"],
    ["DO_FAULT RESET", "Bool", "%Q0.2", "Drive: reset fault", "YES"],
    ["DO_TL GREEN", "Bool", "%Q0.3", "Tower lamp green", "YES"],
    ["DO_TL RED", "Bool", "%Q0.4", "Tower lamp red", "YES"],
    ["DO_TL AMBER", "Bool", "%Q0.5", "Tower lamp amber", "YES"],
    ["DO_SPARE Q0.6", "Bool", "%Q0.6", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DO_SPARE Q0.7", "Bool", "%Q0.7", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DO_SPARE Q1.0", "Bool", "%Q1.0", "Spare, used nowhere", "NO - only for an identical copy"],
    ["DO_SPARE Q1.1", "Bool", "%Q1.1", "Spare, used nowhere", "NO - only for an identical copy"]], [50, 16, 18, 52, 38], status_col=4)
d.p("Type each name exactly, with the space: for example <b>DI_SPARE I0.6</b> (DI_SPARE, one space, I0.6).")
d.h2("Default tag table: rows that TIA makes by itself (do not type them)")
d.table(["Name", "Data type", "Address", "Made by", "Needed?"], [
    ["System_Byte", "Byte", "%MB1", "System memory byte", "YES"],
    ["FirstScan", "Bool", "%M1.0", "System memory byte", "NO - not used, but comes with the byte"],
    ["DiagStatusUpdate", "Bool", "%M1.1", "System memory byte", "NO - not used, but comes with the byte"],
    ["AlwaysTRUE", "Bool", "%M1.2", "System memory byte", "YES - used by the program"],
    ["AlwaysFALSE", "Bool", "%M1.3", "System memory byte", "YES - used by the program"],
    ["Clock_Byte", "Byte", "%MB0", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_10Hz", "Bool", "%M0.0", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_5Hz", "Bool", "%M0.1", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_2.5Hz", "Bool", "%M0.2", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_2Hz", "Bool", "%M0.3", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_1.25Hz", "Bool", "%M0.4", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_1Hz", "Bool", "%M0.5", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_0.625Hz", "Bool", "%M0.6", "Clock memory byte", "NO - only for an identical copy"],
    ["Clock_0.5Hz", "Bool", "%M0.7", "Clock memory byte", "NO - only for an identical copy"]], [38, 16, 18, 38, 64], status_col=4)
d.p("The first five rows appear when you tick the <b>system memory byte</b> (address 1) in part 1: this is needed. "
    "The clock rows appear only if you also tick the <b>clock memory byte</b> (address 0): the program does not use them.")
d.h2("Default tag table: add these 7 flags (all needed)")
d.table(["Name", "Data type", "Address", "Meaning", "Needed?"], [
    ["CONTROL ON FLAG", "Bool", "%M2.0", "Emergency is healthy", "YES"],
    ["MANUAL MODE SELECTED", "Bool", "%M2.1", "", "YES"],
    ["AUTO MODE SELECTED", "Bool", "%M2.2", "Also shown on the HMI", "YES"],
    ["FAULT RESET FLAG", "Bool", "%M2.3", "Reset button on the HMI is pressed", "YES"],
    ["FAULT BIT", "Bool", "%M2.4", "Any alarm is present", "YES"],
    ["MANUAL CONVEYOR FWD ON FLAG", "Bool", "%M2.5", "", "YES"],
    ["MANUAL CONVEYOR REV ON FLAG", "Bool", "%M2.6", "", "YES"]], [58, 16, 18, 62, 20], status_col=4)

# ------------------------------------------------------------------ 3
d.h1("Part 3. Data blocks (DB)")
d.p("A data block is a table of values kept in the PLC. This project has five that you create by hand and one that TIA creates for you (in part 8b). "
    "The DB <b>numbers matter</b> because the HMI and Modbus use them.")
d.h2("How to create each DB")
d.steps([
    "Project tree: <b>PLC_1 &gt; Program blocks &gt; Add new block</b>.",
    "Click <b>Data block (DB)</b>. Type the <b>Name</b>. Type: <b>Global DB</b>. Number: choose <b>Manual</b> and type the number. Click <b>OK</b>.",
    "Before adding rows: in the project tree right-click the new DB &gt; <b>Properties &gt; Attributes</b>. For <b>DB_HMI, DB_ALARMS, DB_AUTO and DB_CAMERA</b>: <b>untick \"Optimized block access\"</b>, click OK and confirm the message. For <b>DB_TCP_IP</b>: leave it <b>ticked</b> (optimized), as in the old project.",
    "In the DB editor add the rows from the table. Type the name, then the data type. Leave the Start value as it is.",
    "Click <b>Compile</b> (toolbar, or right-click the DB &gt; Compile &gt; Software). In the four non-optimized DBs the <b>Offset</b> column fills in. Compare it with the offsets in the tables below. (An optimized DB has no offsets.)"])
d.box("<b>Do not skip step 3.</b> With \"Optimized block access\" ticked the values have no fixed address. Then Modbus cannot use DB_CAMERA, "
      "the alarm word DB2.DBW0 does not exist, and the HMI addresses below do not work. The old project has it unticked on these four DBs. "
      "Only DB_TCP_IP is optimized: it is used only by name, so it needs no fixed addresses.", BAD)
d.p("The column <b>Needed?</b> shows what the machine uses. Rows marked \"old sensor cycle only\" are used only by the switched-off networks of FC_AUTO "
    "(part 8): leave them out in the minimum build, type them for the identical copy.")
d.h2("DB_HMI - number 1")
d.table(["Name", "Data type", "Offset", "Used for", "Needed?"], [
    ["FAULT RESET PB", "Bool", "0.0", "HMI fault reset button", "YES"],
    ["MOTOR JOG FWD PB", "Bool", "0.1", "HMI jog forward button", "YES"],
    ["MOTOR JOG REV PB", "Bool", "0.2", "HMI jog reverse button", "YES"],
    ["STOP TIME", "DInt", "2.0", "Delay in seconds of the old sensor cycle", "NO - old sensor cycle only"],
    ["CAMERA DONE", "Bool", "6.0", "Old sensor cycle", "NO - old sensor cycle only"]], [40, 18, 14, 60, 42], status_col=4)
d.h2("DB_ALARMS - number 2 (type all rows)")
d.table(["Name", "Data type", "Offset", "Used for", "Needed?"], [
    ["EMERGENCY PB PRESSED FAULT", "Bool", "0.0", "Alarm 1", "YES"],
    ["VFD FAULT", "Bool", "0.1", "Alarm 2", "YES"],
    ["SPARE1", "Bool", "0.2", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE2", "Bool", "0.3", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE3", "Bool", "0.4", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE4", "Bool", "0.5", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE5", "Bool", "0.6", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE6", "Bool", "0.7", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE7", "Bool", "1.0", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE8", "Bool", "1.1", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE9", "Bool", "1.2", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE10", "Bool", "1.3", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE11", "Bool", "1.4", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE12", "Bool", "1.5", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE13", "Bool", "1.6", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["SPARE14", "Bool", "1.7", "Free alarm bit", "YES - fills the 16-bit alarm word"],
    ["FAULT POP", "Bool", "2.0", "Tells the HMI that a fault exists", "YES"],
    ["WARNING POP", "Bool", "2.1", "Never set by the program", "NO - only for an identical copy"]], [52, 16, 14, 44, 48], status_col=4)
d.p("The 14 spare rows are needed even though no alarm uses them: they fill bytes 0 and 1, so that the alarms form one 16-bit word (DBW0) and FAULT POP lands at 2.0.")
d.h2("DB_AUTO - number 3")
d.table(["Name", "Data type", "Offset", "Used for", "Needed?"], [
    ["ACTIVE", "Bool", "0.0", "Auto cycle is started", "YES"],
    ["CONVEYOR ON", "Bool", "0.1", "Auto wants the conveyor to run", "YES"],
    ["CONVEYOR OFF1", "Bool", "0.2", "Old sensor cycle", "NO - old sensor cycle only"],
    ["CONVEYOR OFF2", "Bool", "0.3", "Old sensor cycle", "NO - old sensor cycle only"],
    ["P_TRG", "Bool", "0.4", "Old sensor cycle", "NO - old sensor cycle only"],
    ["CAMERA DONE", "Bool", "0.5", "Old sensor cycle", "NO - old sensor cycle only"],
    ["AUTO STATUS", "Int", "2.0", "10 / 20 / 30 for the HMI text", "YES"],
    ["STOP DELAY TIMER", "IEC_TIMER", "4.0", "Old sensor cycle (type the data type by hand)", "NO - old sensor cycle only"],
    ["SENSOR CHECK DELAY", "IEC_TIMER", "20.0", "Old sensor cycle", "NO - old sensor cycle only"]], [40, 20, 14, 58, 42], status_col=4)
d.p("In the minimum build (only ACTIVE, CONVEYOR ON, AUTO STATUS) the offsets are 0.0, 0.1 and 2.0: the same as in the full table.")
d.h2("DB_CAMERA - number 5")
d.p("All data type <b>Int</b>. Tip: make DATA1, select the row, and drag the small square at the bottom-left corner of the row down; TIA numbers the copies for you. "
    "Then check every row against this table.")
d.table(["Name", "Data type", "Offset", "Modbus register", "Needed?"], [
    ["DATA1", "Int", "0.0", "40001", "YES - the PC writes 0 = run, 1 = stop"],
    ["DATA2", "Int", "2.0", "40002", "YES - the Modbus block needs 10 values"],
    ["DATA3", "Int", "4.0", "40003", "YES - the Modbus block needs 10 values"],
    ["DATA4", "Int", "6.0", "40004", "YES - the Modbus block needs 10 values"],
    ["DATA5", "Int", "8.0", "40005", "YES - the Modbus block needs 10 values"],
    ["DATA6", "Int", "10.0", "40006", "YES - the Modbus block needs 10 values"],
    ["DATA7", "Int", "12.0", "40007", "YES - the Modbus block needs 10 values"],
    ["DATA8", "Int", "14.0", "40008", "YES - the Modbus block needs 10 values"],
    ["DATA9", "Int", "16.0", "40009", "YES - the Modbus block needs 10 values"],
    ["DATA10", "Int", "18.0", "40010", "YES - the Modbus block needs 10 values"],
    ["DATA11", "Int", "20.0", "-", "NO - only for an identical copy"],
    ["DATA12", "Int", "22.0", "-", "NO - only for an identical copy"],
    ["DATA13", "Int", "24.0", "-", "NO - only for an identical copy"],
    ["DATA14", "Int", "26.0", "-", "NO - only for an identical copy"],
    ["DATA15", "Int", "28.0", "-", "NO - only for an identical copy"],
    ["DATA16", "Int", "30.0", "-", "NO - only for an identical copy"],
    ["DATA17", "Int", "32.0", "-", "NO - only for an identical copy"],
    ["DATA18", "Int", "34.0", "-", "NO - only for an identical copy"],
    ["DATA19", "Int", "36.0", "-", "NO - only for an identical copy"]], [28, 20, 18, 30, 78], status_col=4)
d.h2("DB_TCP_IP - number 12 (optimized: leave \"Optimized block access\" ticked)")
d.table(["Name", "Data type", "Used for", "Needed?"], [
    ["MY CONNECT DATA", "TCON_IP_v4", "Connection settings for Modbus. Type TCON_IP_v4 in the data type column by hand; it then opens into sub-rows.", "YES"],
    ["NO OF DONE", "UDInt", "Counter of good Modbus messages", "NO - fault finding only"],
    ["NO OF ERROR", "UDInt", "Counter of failed messages", "NO - fault finding only"],
    ["ERROR STATUS", "UDInt", "Last error code", "NO - fault finding only"]], [36, 22, 76, 40], status_col=3)

# ------------------------------------------------------------------ 4
d.h1("Part 4. Block FC_GENERAL (FC1) - mode and reset")
d.h2("How to create an FC (same for all six)")
d.steps([
    "<b>Program blocks &gt; Add new block</b>. Click <b>Function (FC)</b>.",
    "Name as given. Language: <b>LAD</b>. Number: <b>Manual</b>, type the number. Click <b>OK</b>.",
    "The editor opens with Network 1. To add a network: right-click a network title &gt; <b>Insert network</b>.",
    "<b>Not needed, only for an identical look:</b> give every network the title shown in this guide (click the grey title line of the network, where it says \"Network 1:\", and type it).",
    "<b>Not needed:</b> the old blocks each end with one empty network. It does nothing."])
d.box("Every drawing in parts 4 - 8b was read from the old project through TIA Portal itself (export of 12 October 2026): same networks, same order, "
      "same contacts and branches as the original.", OKC)
d.rung("FC_GENERAL - Network 1: CONTROL ON", [[NO("DI_EMERGENCY PB"), "-", COIL("CONTROL ON FLAG")]], ncols=3,
       explain="Emergency healthy (input ON) gives CONTROL ON. Pushing Emergency drops it.")
d.rung("FC_GENERAL - Network 2: MODE SELECTION", [[NO("AlwaysTRUE"), NC("DI_AUTO MANUAL\nSELECTION"), COIL("MANUAL MODE\nSELECTED")],
                                        [None, NO("DI_AUTO MANUAL\nSELECTION"), COIL("AUTO MODE\nSELECTED")]], links=[(1, 0, 1)],
       explain="Selector OFF = manual, ON = auto. The AlwaysTRUE contact is only there so that two coils can share one network.")
d.rung("FC_GENERAL - Network 3: FAULT RESET", [[NO("\"DB_HMI\".\nFAULT RESET PB"), "-", COIL("FAULT RESET FLAG")]], ncols=3,
       explain="To use a DB value, type <b>\"DB_HMI\".</b> and pick the row from the list that appears. Network 4 is empty.")

# ------------------------------------------------------------------ 5
d.h1("Part 5. Block FC_MANUAL (FC2) - jog")
d.rung("FC_MANUAL - Network 1: MOTOR FWD /REV ON", [
    [NO("CONTROL ON\nFLAG"), NO("MANUAL MODE\nSELECTED"), NC("FAULT BIT"), NO("\"DB_HMI\".MOTOR\nJOG REV PB"), "-", COIL("MANUAL CONVEYOR\nREV ON FLAG")],
    [None, None, None, NO("\"DB_HMI\".MOTOR\nJOG FWD PB"), "-", COIL("MANUAL CONVEYOR\nFWD ON FLAG")],
    [None, None, None, NO("DI_CYCLE\nSTART PB"), None, None]],
    links=[(3, 0, 2), (4, 1, 2)],
    explain="Exactly as in the old block: after the three common contacts the network splits. The <b>top</b> row is the HMI reverse button to the REV flag. "
            "Below it, the HMI forward button <b>or</b> the green START button gives the FWD flag. The motor runs only while a button is held. Network 2 is empty.")
d.box("<b>Red button reverse:</b> the old file has <b>no</b> red-button reverse (confirmed from the TIA export). You told me it was wanted but never built. "
      "Build this block exactly as above first. Part 12 shows how to add the red-button reverse jog safely, as a separate step.", CHK)

# ------------------------------------------------------------------ 6
d.h1("Part 6. Block FC_ALARMS (FC3) - alarms")
d.rung("FC_ALARMS - Network 1: EMERGENCY PB PRESSED FAULT (I0.4)", [[NC("DI_EMERGENCY PB"), "-", SET("\"DB_ALARMS\".EMERGENCY\nPB PRESSED FAULT")]], ncols=3)
d.rung("FC_ALARMS - Network 2: CONVEYOR VFD FAULT (I0.5)", [[NO("DI_CONVEYOR\nVFD FAULT"), "-", SET("\"DB_ALARMS\".\nVFD FAULT")]], ncols=3,
       explain="Set coils: the alarm stays ON even after the cause has gone, until someone presses reset.")
d.rung("FC_ALARMS - Network 3: FAULT RESET", [[NO("FAULT RESET FLAG"), BOX("", ["MOVE", "EN       ENO", "IN = 0", "OUT1 = %DB2.DBW0"]), None]], ncols=3,
       explain="MOVE is in <b>Basic instructions &gt; Move operations</b>. At IN type <b>0</b>. At OUT1 type <b>%DB2.DBW0</b>. "
               "DBW0 is the first 16 bits of DB_ALARMS = all 16 alarm bits together. Writing 0 clears them all at once.")
d.rung("FC_ALARMS - Network 4: FAULT BIT", [[BOX("", ["CMP <>", "Word", "IN1 = 0", "IN2 = %DB2.DBW0"]), "-", COIL("FAULT BIT")],
                                              [None, None, COIL("\"DB_ALARMS\".\nFAULT POP")]], links=[(2, 0, 1)],
       explain="Compare is in <b>Basic instructions &gt; Comparator operations &gt; CMP &lt;&gt;</b>. Click the <b>???</b> inside the box and choose <b>Word</b>. "
               "If any alarm bit is 1 the word is not 0, so FAULT BIT turns ON. The compare box sits directly on the left rail. Network 5 is empty.")

# ------------------------------------------------------------------ 7
d.h1("Part 7. Block FC_OUTPUTS (FC4) - outputs")
d.rung("FC_OUTPUTS - Network 1: CONVEYOR FWD ON", [[NO("MANUAL CONVEYOR\nFWD ON FLAG"), "-", COIL("DO_CONVEYOR\nFWD ON")],
                                          [NO("\"DB_AUTO\".\nCONVEYOR ON"), None, None]], links=[(1, 0, 1)])
d.p("Networks 2 to 6 are one contact and one coil each. Network 7 is empty.")
d.table(["Network", "Title", "Contact (normally open)", "Coil"], [
    ["2", "CONVEYOR REV ON", "MANUAL CONVEYOR REV ON FLAG", "DO_CONVEYOR REV ON"], ["3", "FAULT RESET", "FAULT RESET FLAG", "DO_FAULT RESET"],
    ["4", "TL GREEN", "\"DB_AUTO\".ACTIVE", "DO_TL GREEN"], ["5", "TL RED", "FAULT BIT", "DO_TL RED"], ["6", "TL AMBER", "MANUAL MODE SELECTED", "DO_TL AMBER"]],
    [18, 34, 66, 56])
d.box("<b>Good habit:</b> each physical output (Q) is written in one place only, here. Other blocks only set flags. "
      "This avoids two rungs fighting over one output.", OKC)

# ------------------------------------------------------------------ 8
d.h1("Part 8. Block FC_AUTO (FC5) - automatic cycle")
d.p("The old block has <b>six networks</b>. Only three of them do any work on your machine; the others are an old sensor cycle that is "
    "<b>switched off</b> by a normally closed AlwaysTRUE contact (it can never pass). So there are two ways to build this block, and <b>both behave exactly the same</b>:")
d.table(["Way", "What you build", "Time"], [
    ["<b>A. Minimum (recommended if you only want a working machine)</b>", "The 3 short networks drawn just below", "15 minutes"],
    ["<b>B. Identical copy of the old block</b>", "All 6 networks, drawn after that, with the switched-off rows", "1 hour"],
], [70, 80, 24])
d.h2("Way A: the minimum FC_AUTO (3 networks, all needed)")
d.rung("FC_AUTO short - Network 1: AUTO ON  [NEEDED]", [
    [NO("CONTROL ON\nFLAG"), NO("AUTO MODE\nSELECTED"), NC("FAULT BIT"), NO("DI_CYCLE\nSTART PB"), NO("DI_CYCLE\nSTOP PB"), COIL("\"DB_AUTO\".\nACTIVE")],
    [None, None, None, NO("\"DB_AUTO\".\nACTIVE"), None, None]], links=[(3, 0, 1), (4, 0, 1)],
    explain="Press START: ACTIVE turns ON and holds itself (a \"latch\"). It drops on STOP, a fault, Emergency, or when the selector leaves AUTO.")
d.rung("FC_AUTO short - Network 2: CONVEYOR ON  [NEEDED]", [
    [NO("\"DB_AUTO\".\nACTIVE"), BOX("", ["CMP ==  Int", "IN1 = \"DB_CAMERA\".DATA1", "IN2 = 0"]), "-", COIL("\"DB_AUTO\".\nCONVEYOR ON")]], ncols=4,
    explain="The belt runs while the cycle is started and register 40001 is 0. This is row 1 of the old network 3 without its two contacts that change nothing.")
d.rung("FC_AUTO short - Network 3: AUTO STATUS  [NEEDED for the HMI status text]", [
    [NO("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), BOX("", ["MOVE", "IN = 10", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])],
    [None, NC("\"DB_AUTO\".\nACTIVE"), BOX("", ["MOVE", "IN = 20", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])]], links=[(1, 0, 1)],
    explain="10 = AUTO RUNNING, 20 = STOPPED. With way A you can leave out all \"old sensor cycle only\" rows of part 2 and part 3, and the SCL network.")
d.box("If you built way A, <b>skip the rest of part 8</b> and go on to part 8b.", OKC)
d.h2("Way B: the identical copy (6 networks)")
d.p("Network 3 is large: its first row is the rung that really runs the belt; the other rows are the switched-off cycle. Each title below says whether the machine needs it.")
d.rung("FC_AUTO - Network 1: AUTO ON  [NEEDED]", [
    [NO("CONTROL ON\nFLAG"), NO("AUTO MODE\nSELECTED"), NC("FAULT BIT"), NO("DI_CYCLE\nSTART PB"), NO("DI_CYCLE\nSTOP PB"), COIL("\"DB_AUTO\".\nACTIVE")],
    [None, None, None, NO("\"DB_AUTO\".\nACTIVE"), None, None]], links=[(3, 0, 1), (4, 0, 1)],
    explain="Press START: ACTIVE turns ON and holds itself through its own contact (a \"latch\"). It drops when STOP is pressed "
            "(the input goes OFF because the button is NC), on a fault, on Emergency, or when the selector leaves AUTO.")
d.add(KeepTogether([Paragraph("FC_AUTO - Network 2: STOP DELAY TIME (an SCL network)  [NOT needed: old sensor cycle]", ST["h3"]),
                    Paragraph("Right-click the title of network 1 &gt; <b>Insert SCL network</b> (this network is text, not ladder). Type this one line:", ST["p"]),
                    Paragraph("\"DB_AUTO\".\"STOP DELAY TIMER\".PT := \"DB_HMI\".\"STOP TIME\" * 1000;", ST["code"]),
                    Paragraph("It turns STOP TIME (seconds, from the HMI) into the timer preset in milliseconds. It belongs to the switched-off sensor cycle.", ST["note"]),
                    Spacer(1, 5)]))
d.rung("FC_AUTO - Network 3: CONVEYOR ON  [row 1 NEEDED; rows 2 - 8 NOT needed: old sensor cycle]", [
    [NO("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), NC("\"DB_AUTO\".\nCONVEYOR OFF2"), BOX("", ["CMP ==  Int", "IN1:", "\"DB_CAMERA\".", "DATA1", "IN2: 0"]), "-", "-", "-", COIL("\"DB_AUTO\".\nCONVEYOR ON")],
    [None, None, NO("AlwaysTRUE"), None, None, None, None, None],
    [None, NC("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), NO("\"DB_AUTO\".\nCONVEYOR ON"), NO("\"DB_AUTO\".SENSOR\nCHECK DELAY.Q"), NO("DI_PRODUCT\nSENSOR"), BOX("", ["P_TRIG", "CLK     Q", "\"DB_AUTO\".", "P_TRG"]), SET("\"DB_AUTO\".\nCONVEYOR OFF1")],
    [None, None, None, None, BOX("\"DB_AUTO\".SENSOR\nCHECK DELAY", ["TON  Time", "IN      Q", "PT:", "T#500MS", "ET"]), None, None, None],
    [None, NO("\"DB_AUTO\".\nCONVEYOR OFF1"), BOX("\"DB_AUTO\".STOP\nDELAY TIMER", ["TON  Time", "IN      Q", "PT:", "\"DB_AUTO\".", "\"STOP DELAY", "TIMER\".PT"]), None, None, None, None, None],
    [None, NO("\"DB_AUTO\".STOP\nDELAY TIMER.Q"), "-", "-", "-", "-", "-", RST("\"DB_AUTO\".\nCONVEYOR OFF1")],
    [None, None, BOX("", ["MOVE", "IN: 1", "OUT1:", "\"DB_CAMERA\".", "DATA1"]), None, None, None, None, None],
    [None, None, "-", "-", "-", "-", "-", SET("\"DB_AUTO\".\nCONVEYOR OFF2")]],
    links=[(1, 0, 5), (2, 0, 1), (3, 0, 1), (4, 2, 3), (2, 5, 7)], ncols=8,
    explain="<b>Row 1 runs the belt:</b> AlwaysTRUE, ACTIVE, then (NOT OFF2 <b>or</b> AlwaysTRUE), then DATA1 = 0. The AlwaysTRUE branch makes the OFF2 contact "
            "have no effect, so: <b>belt runs while ACTIVE and register 40001 is 0.</b> "
            "The other rows hang from the first AlwaysTRUE contact. The row with the <b>normally closed AlwaysTRUE</b> never passes, so the sensor timer, "
            "P_TRIG and OFF1 never switch; therefore the stop-delay timer, the MOVE 1 and OFF2 never switch either.")
d.p("<b>How to place the boxes:</b> CMP == is in <b>Comparator operations</b> (choose <b>Int</b>). TON is in <b>Timer operations</b>: when \"Call options\" opens, click "
    "<b>Cancel</b>, then type the instance above the box (for example <b>\"DB_AUTO\".\"SENSOR CHECK DELAY\"</b>). P_TRIG is in <b>Bit logic operations</b>; "
    "type <b>\"DB_AUTO\".P_TRG</b> under it. Each new row is a branch: select the wire after AlwaysTRUE (or after the STOP DELAY TIMER.Q contact), "
    "click <b>Open branch</b>, place the elements, and leave the row ending in its own coil or box.")
d.rung("FC_AUTO - Network 4: CAMERA DONE  [NOT needed: old sensor cycle]", [[NO("\"DB_AUTO\".\nCONVEYOR OFF2"), BOX("", ["CMP ==  Int", "IN1 = \"DB_CAMERA\".", "DATA1", "IN2 = 0"]), "-", COIL("\"DB_AUTO\".\nCAMERA DONE")]], ncols=4,
       explain="Part of the switched-off cycle (OFF2 is never ON).")
d.rung("FC_AUTO - Network 5: CONVEYOR OFF RESET  [NOT needed: old sensor cycle]", [
    [NO("AlwaysTRUE"), NO("\"DB_AUTO\".\nCONVEYOR OFF2"), NO("\"DB_AUTO\".\nCAMERA DONE"), "-", RST("\"DB_AUTO\".\nCONVEYOR OFF1")],
    [None, None, NO("\"DB_HMI\".\nCAMERA DONE"), None, RST("\"DB_AUTO\".\nCONVEYOR OFF2")],
    [None, NC("\"DB_AUTO\".\nACTIVE"), "-", None, None]],
    links=[(1, 0, 2), (2, 0, 1), (3, 0, 2), (4, 0, 1)], ncols=5,
    explain="Resets OFF1 and OFF2 when the camera step is done (from the PLC or from the HMI) or when the cycle is not active. Part of the switched-off cycle.")
d.rung("FC_AUTO - Network 6: AUTO STATUS  [rows 10 and 20 NEEDED; row 30 NOT needed]", [
    [NO("AlwaysTRUE"), NO("\"DB_AUTO\".\nACTIVE"), NC("\"DB_AUTO\".\nCONVEYOR OFF2"), BOX("", ["MOVE", "IN = 10", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])],
    [None, NC("\"DB_AUTO\".\nACTIVE"), "-", BOX("", ["MOVE", "IN = 20", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])],
    [None, NO("\"DB_AUTO\".\nACTIVE"), NO("\"DB_AUTO\".\nCONVEYOR OFF2"), BOX("", ["MOVE", "IN = 30", "OUT1 = \"DB_AUTO\".", "\"AUTO STATUS\""])]],
    links=[(1, 0, 2)], ncols=4,
    explain="10 = started (HMI text AUTO RUNNING), 20 = not started (STOPPED), 30 = waiting for camera (never happens now, because OFF2 stays OFF). Network 7 is empty.")

d.h1("Part 8b. Block FC_TCP_IP (FC6) - Modbus TCP server")
d.h2("Network 1: Connection definition  [NEEDED]")
d.p("Nine MOVE boxes and one contact with a coil (10 rows), <b>each row starting directly at the left rail</b> (use <b>Open branch</b> for each new row), in this order. "
    "For OUT1 type <b>\"DB_TCP_IP\".\"MY CONNECT DATA\".</b> and pick the sub-row.")
d.table(["Row", "Element", "IN", "OUT1 / coil = \"DB_TCP_IP\".\"MY CONNECT DATA\". ...", "Meaning"], [
    ["1", "MOVE", "\"Local~PROFINET_interface_1\"", "InterfaceId", "Which Ethernet port. Pick this name from the list; it is created with the CPU (value 64)."],
    ["2", "MOVE", "1", "ID", "Connection number"], ["3", "MOVE", "11", "ConnectionType", "11 = TCP"],
    ["4", "Normally closed contact <b>AlwaysTRUE</b>, then coil", "-", "ActiveEstablished", "Never passes, so 0 = the PLC waits (server)"],
    ["5", "MOVE", "0", "RemoteAddress.ADDR[1]", "Remote IP 0.0.0.0 = accept any device"],
    ["6", "MOVE", "0", "RemoteAddress.ADDR[2]", ""],
    ["7", "MOVE", "0", "RemoteAddress.ADDR[3]", ""],
    ["8", "MOVE", "0", "RemoteAddress.ADDR[4]", ""],
    ["9", "MOVE", "0", "RemotePort", "Any port on the other side"], ["10", "MOVE", "502", "LocalPort", "The Modbus port of the PLC"]], [12, 30, 40, 50, 42])
d.h2("Network 2: MB SERVER  [NEEDED]")
d.steps([
    "Instructions panel: <b>Communication &gt; Others &gt; MODBUS TCP</b>. In the <b>Version</b> column of the MODBUS TCP line choose <b>V5.3</b> "
    "(the old project uses MB_SERVER V5.3; TIA may offer a newer version by default).",
    "Drag <b>MB_SERVER</b> onto the line. \"Call options\" opens. Choose <b>Single instance</b>. Name <b>MB_SERVER_DB</b>. Number <b>Manual</b>, <b>4</b>. Click <b>OK</b>. TIA creates DB4 by itself.",
    "Fill the inputs on the left of the box as in the table. Leave all outputs on the right empty."])
d.table(["Pin", "Type this", "Meaning"], [
    ["DISCONNECT", "AlwaysFALSE", "0 = keep listening for a connection"],
    ["MB_HOLD_REG", "P#DB5.DBX0.0 INT 10", "Registers 40001 - 40010 are the first 10 values of DB_CAMERA (DB5)"],
    ["CONNECT", "\"DB_TCP_IP\".\"MY CONNECT DATA\"", "The settings from network 1"]], [34, 60, 80])
d.rung("FC_TCP_IP - Network 3: ERROR CHECK  [NOT needed: counters for fault finding only]", [
    [NO("\"MB_SERVER_DB\".\nNDR"), BOX("", ["ADD  UDInt", "IN1 = NO OF DONE", "IN2 = 1", "OUT = NO OF DONE"]), None],
    [NO("\"MB_SERVER_DB\".\nDR"), None, None],
    [NO("\"MB_SERVER_DB\".\nERROR"), BOX("", ["ADD  UDInt", "IN1 = NO OF ERROR", "IN2 = 1", "OUT = NO OF ERROR"]), None],
    [None, BOX("", ["MOVE", "IN = \"MB_SERVER_DB\".", "STATUS", "OUT1 = ERROR STATUS"]), None]],
    links=[(1, 0, 1), (1, 2, 3)], ncols=3,
    explain="ADD is in <b>Math functions</b>; choose UDInt inside the box. NO OF DONE, NO OF ERROR and ERROR STATUS are in \"DB_TCP_IP\". "
            "After the ERROR contact the line splits: ADD and MOVE sit on two parallel branches. "
            "These counters are only for fault finding: watch them go up when the PC talks to the PLC.")

# ------------------------------------------------------------------ 9
d.h1("Part 9. Main block OB1 and compile")
d.steps([
    "Open <b>Program blocks &gt; Main [OB1]</b>.",
    "Drag <b>FC_AUTO</b> from the project tree onto the line of Network 1. A box \"FC_AUTO\" appears.",
    "Insert five more networks and drag one block into each, in this order: <b>FC_ALARMS, FC_GENERAL, FC_MANUAL, FC_OUTPUTS, FC_TCP_IP</b>. "
    "(The old OB1 also has an empty network 7. Not needed.)",
    "In the project tree click <b>PLC_1</b>. Click <b>Compile</b> in the toolbar.",
    "Look at the <b>Info &gt; Compile</b> tab at the bottom. It must end with <b>Errors: 0</b>. Double-click any red line to jump to the mistake. "
    "Usual causes: a name typed differently, a contact left with &lt;??.?&gt;, or one of the four DBs still \"optimized\".",
    "Save with <b>Ctrl + S</b>."])
d.box("<b>Check the block list.</b> Program blocks must now show: Main [OB1], FC_GENERAL [FC1], FC_MANUAL [FC2], FC_ALARMS [FC3], FC_OUTPUTS [FC4], "
      "FC_AUTO [FC5], FC_TCP_IP [FC6], DB_HMI [DB1], DB_ALARMS [DB2], DB_AUTO [DB3], MB_SERVER_DB [DB4], DB_CAMERA [DB5], DB_TCP_IP [DB12].", OKC)

# ------------------------------------------------------------------ 10
d.page()
d.h1("Part 10. HMI panel (KTP700 Basic)")
d.p("Everything in this part was exported from the old project by TIA Portal itself (12 October 2026): screen names and numbers, positions, sizes, texts, colours, "
    "tags, text lists, button functions and animations. The panel has <b>five screens</b> and one <b>template called MAIN</b>. The template holds the title bar "
    "and the row of five buttons at the bottom. The screen is 800 x 480 points. Positions are <b>x, y</b> of the top-left corner and <b>width x height</b>; "
    "type them under <b>Properties &gt; Layout</b>. Colours are given as red, green, blue numbers (Properties &gt; Appearance).")
d.box("<b>Two things the export cannot show:</b> alarm views and the discrete alarm list (TIA's export does not include them). They are given in 10.3 and 10.4 "
      "from older screen files of the same project (6 February 2026), marked <b>CHECK</b>. Look at the ALARMS screen of the old panel to confirm.", CHK)
d.h2("10.1 Add the panel and connect it to the PLC")
d.steps([
    "Project tree: <b>Add new device &gt; HMI &gt; SIMATIC Basic Panel &gt; 7\" Display &gt; KTP700 Basic &gt; 6AV2 123-2GB03-0AX0</b>. Device name <b>HMI_1</b>. "
    "Leave \"Start device wizard\" ticked. Click OK. (Its runtime is called HMI_RT_1, the TIA default.)",
    "Wizard page \"PLC connections\": click <b>Browse</b>, choose <b>PLC_1</b>. On the next pages untick the ready-made screens and system screens, and click <b>Finish</b>.",
    "Project tree: <b>Devices &amp; networks</b>. Double-click the HMI. Properties: <b>PROFINET Interface [X1] &gt; Ethernet addresses</b>: subnet PN/IE_1, "
    "IP <b>192.168.0.41</b>, mask 255.255.255.0.",
    "Check <b>HMI_1 &gt; Connections</b>: one row <b>HMI_Connection_1</b> to PLC_1 must exist."])
d.h2("10.2 HMI tags: three tag tables")
d.p("Open <b>HMI_1 &gt; HMI tags</b>. Double-click <b>Add new tag table</b> twice and rename the new tables <b>IO</b> and <b>ALARMS</b>. "
    "Connection is always <b>HMI_Connection_1</b>, acquisition cycle <b>1 s</b>. For rows with a PLC name, click the \"...\" button in the <b>PLC tag</b> column and pick it. "
    "For rows with an address, choose Access mode <b>&lt;absolute access&gt;</b> and type the address.")
d.table(["Table", "HMI tag name", "Data type", "PLC tag or address", "Used for", "Needed?"], [
    ["Default", "Tag_ScreenNumber", "UInt", "(internal, made by the wizard; no connection)", "Leave it", "NO - made by the wizard"],
    ["Default", "AUTO MODE SELECTED", "Bool", "PLC tag AUTO MODE SELECTED (%M2.2)", "Mode text AUTO / MANUAL", "USEFUL - mode text"],
    ["Default", "DB_ALARMS_FAULT POP", "Bool", "\"DB_ALARMS\".\"FAULT POP\"", "Red alarm line", "USEFUL - alarm line"],
    ["Default", "DB_ALARMS_WARNING POP", "Bool", "\"DB_ALARMS\".\"WARNING POP\"", "Warning line (the PLC never sets it)", "NO - never set"],
    ["Default", "DB_HMI_FAULT RESET PB", "Bool", "\"DB_HMI\".\"FAULT RESET PB\"", "FAULT / RESET button", "YES"],
    ["Default", "DB_HMI_MOTOR JOG FWD PB", "Bool", "\"DB_HMI\".\"MOTOR JOG FWD PB\"", "FWD JOG button", "YES"],
    ["Default", "DB_HMI_MOTOR JOG REV PB", "Bool", "\"DB_HMI\".\"MOTOR JOG REV PB\"", "REV JOG button", "YES"],
    ["Default", "DB_AUTO_AUTO STATUS", "Int", "\"DB_AUTO\".\"AUTO STATUS\"", "Status text on the AUTO screen", "USEFUL - status text"],
    ["Default", "DB_HMI_STOP TIME", "DInt", "\"DB_HMI\".\"STOP TIME\"", "Old sensor cycle; on no screen", "NO - on no screen"],
    ["Default", "DB_HMI_CAMERA DONE", "Bool", "\"DB_HMI\".\"CAMERA DONE\"", "Old sensor cycle; on no screen", "NO - on no screen"],
    ["IO", "IB0", "Byte", "%IB0 (absolute)", "Lamps I0.0 - I0.7", "NO - only for the I/O screens"],
    ["IO", "IB1", "Byte", "%IB1 (absolute)", "Lamps I1.0 - I1.5", "NO - only for the I/O screens"],
    ["IO", "QB0", "Byte", "%QB0 (absolute)", "Lamps Q0.0 - Q0.7", "NO - only for the I/O screens"],
    ["IO", "QB1", "Byte", "%QB1 (absolute)", "Lamps Q1.0 - Q1.1", "NO - only for the I/O screens"],
    ["ALARMS", "ALARM WORD", "<b>Int</b>", "%DB2.DBW0 (absolute). Acquisition mode: <b>Cyclic continuous</b>", "Alarm messages", "USEFUL - alarm texts"]], [18, 36, 13, 48, 30, 29], status_col=5)
d.p("All tags except ALARM WORD use acquisition mode <b>Cyclic in operation</b> (the default).")
d.h2("10.3 Text lists and alarms")
d.p("<b>Needed?</b> The two text lists are needed by the mode field and the status field (if you build those fields). "
    "The discrete alarms are <b>useful</b>: without them the red lamp still works, but the panel does not say which alarm it is.")
d.table(["Where", "What to enter"], [
    ["<b>HMI_1 &gt; Text and graphic lists &gt; Text lists</b>", "List <b>AUTO STATUS</b> (with a space), selection \"Value/Range\": 10 = <b>AUTO RUNNING</b>, 20 = <b>STOPPED</b>, 30 = <b>WAITING FOR CAMERA ACK</b>.<br/>"
     "List <b>MODE</b>, selection \"Bit (0, 1)\": 0 = <b>MANUAL</b>, 1 = <b>AUTO</b>."],
    ["<b>HMI_1 &gt; HMI alarms &gt; Discrete alarms</b> (CHECK, see the box above)", "Row 1: alarm text <b>EMERGENCY PB PRESSED FAULT (I0.4)</b>, alarm class Errors, trigger tag <b>ALARM WORD</b>, trigger bit <b>8</b>.<br/>"
     "Row 2: <b>CONVEYOR VFD FAULT (I0.5)</b>, trigger tag ALARM WORD, trigger bit <b>9</b>."],
], [56, 118])
d.box("<b>Why bits 8 and 9, not 0 and 1?</b> In a Siemens word the first byte (DBB0) is the high half. So DBX0.0 is bit 8 of DBW0 and DBX0.1 is bit 9. "
      "TIA shows the matching address (DB2.DBX0.0) next to the trigger bit; use that to check.", OKC)
d.h2("10.4 The template MAIN (shown on every screen)")
d.p("Open <b>HMI_1 &gt; Screen management &gt; Templates</b>. Rename Template_1 to <b>MAIN</b> (right-click &gt; Rename). Background colour <b>182, 182, 182</b>. "
    "Drag the objects from the <b>Toolbox</b> on the right. Buttons: on <b>Properties &gt; Events &gt; Press</b> click &lt;Add function&gt; and choose the function shown.")
d.table(["Object", "x, y", "Size", "Settings", "Needed?"], [
    ["Rectangle (top bar)", "1, 1", "798 x 58", "Background 192, 192, 192", "NO - looks only"],
    ["Date/time field (time only)", "1, 1", "121 x 58", "Mode Output; show time ON, date OFF", "NO - looks only"],
    ["Date/time field (date only)", "677, 1", "121 x 58", "Mode Output; show date ON, time OFF", "NO - looks only"],
    ["Text field <b>CONVEYOR</b>", "225, 11", "327 x 39", "Background 112, 112, 112, text white, centred. This is the title.", "NO - looks only"],
    ["Button without text (dark strip behind the mode line)", "0, 61", "800 x 30", "Background 99, 101, 113 with vertical gradient; no event. It is only decoration.", "NO - looks only"],
    ["Text field <b>MODE :-</b>", "12, 64", "65 x 23", "Transparent background", "USEFUL"],
    ["Symbolic I/O field", "89, 61", "117 x 27", "Mode <b>Output</b>, process tag <b>AUTO MODE SELECTED</b>, text list <b>MODE</b>, white background", "USEFUL - shows the mode"],
    ["Rectangle (bottom bar)", "1, 406", "799 x 68", "Background 198, 195, 198", "NO - looks only"],
    ["Button <b>AUTO</b>", "6, 411", "151 x 60", "Event <b>Press</b>: Screens &gt; <b>ActivateScreen</b>, screen AUTO", "YES - to open the screen"],
    ["Button <b>MANUAL</b>", "166, 411", "151 x 60", "Press: ActivateScreen, MANUAL", "YES - to open the screen"],
    ["Button <b>ALARMS</b>", "326, 411", "151 x 60", "Press: ActivateScreen, ALARMS", "USEFUL"],
    ["Button <b>IO STATUS</b>", "486, 411", "151 x 60", "Press: ActivateScreen, INPUT STATUS", "NO - only with the I/O screens"],
    ["Button <b>FAULT / RESET</b> (two lines)", "646, 411", "151 x 60", "Background <b>yellow 255, 255, 0</b>. Event <b>Press</b>: Edit bits &gt; <b>SetBitWhileKeyPressed</b>, tag DB_HMI_FAULT RESET PB, bit 0", "YES - without it an alarm can never be cleared"],
    ["CHECK: alarm view(s) for the red / yellow alarm line", "124, 4", "550 x 53", "Not in the export. The February screen files had two alarm views here (Errors red, Warnings yellow), made visible by DB_ALARMS_FAULT POP / WARNING POP. Copy what the old panel shows.", "USEFUL - shows the alarm line"]], [40, 15, 17, 72, 30], status_col=4)
d.p("All five navigation and reset buttons have a blue border (0, 0, 255, width 3) and grey background 218, 218, 218, except the yellow FAULT / RESET button.")
d.box("<b>SetBitWhileKeyPressed</b> sets the bit while the finger is on the button and clears it when the finger is lifted. It needs only the <b>Press</b> event. "
      "(Revision 2 told you to use SetBit on Press and ResetBit on Release. That also works, but the old project uses SetBitWhileKeyPressed.)", OKC)
d.h2("10.5 The five screens")
d.p("Create each with <b>HMI_1 &gt; Screens &gt; Add new screen</b>, give it the name and number shown (Properties &gt; General), and check that its template is <b>MAIN</b>. "
    "In the old project INPUT STATUS and OUTPUT STATUS are in a screen folder called <b>IOs</b> (right-click Screens &gt; Add group).")
d.table(["Screen (number)", "Object", "x, y", "Size", "Settings", "Needed?"], [
    ["AUTO (1), background white", "Text field <b>AUTO OPERATION</b>", "308, 62", "181 x 27", "Screen title", "NO - looks only"],
    ["", "Text field <b>AUTO STATUS</b>", "304, 117", "165 x 34", "", "NO - looks only"],
    ["", "Symbolic I/O field", "116, 182", "560 x 106", "Mode Output. Process tag DB_AUTO_AUTO STATUS. Text list AUTO STATUS. Border 3. Animation <b>Appearance</b>, tag DB_AUTO_AUTO STATUS: value 10 = background <b>green</b> (0, 255, 0), text black; value 20 = background <b>red</b> (255, 0, 0), text white", "USEFUL - shows running / stopped"],
    ["MANUAL (2), background white", "Text field <b>MANUAL OPERATION</b>", "308, 62", "210 x 27", "Screen title", "NO - looks only"],
    ["", "Button <b>CONVEYOR / FWD JOG</b> (two lines)", "166, 194", "179 x 82", "Font Tahoma 19. Press: <b>SetBitWhileKeyPressed</b> DB_HMI_MOTOR JOG FWD PB, bit 0. Animation Appearance, same tag: value 1 = background green (0, 255, 0)", "USEFUL - the green START button does the same"],
    ["", "Button <b>CONVEYOR / REV JOG</b> (two lines)", "429, 190", "179 x 82", "Same, with DB_HMI_MOTOR JOG REV PB", "YES - the only way to reverse"],
    ["ALARMS (3), background 182, 182, 182", "Text field <b>ALARMS</b>", "372, 62", "84 x 27", "Screen title", "NO - looks only"],
    ["", "CHECK: Alarm view", "2, 92", "797 x 308", "Not in the export; from the February files. Toolbox &gt; Controls &gt; Alarm view", "USEFUL - shows which alarm"],
    ["INPUT STATUS (10), folder IOs, background 181, 182, 181", "Text field <b>INPUT STATUS</b>", "308, 63", "147 x 27", "Screen title", "NO - fault finding only"],
    ["", "Lamp table (10.6)", "0, 94", "", "14 rows, listed one by one in 10.6", "NO - fault finding only"],
    ["", "Button <b>NEXT</b>", "644, 341", "151 x 60", "Press: ActivateScreen, OUTPUT STATUS", "NO - fault finding only"],
    ["OUTPUT STATUS (19), folder IOs, background 181, 182, 181", "Text field <b>OUTPUT STATUS-1</b>", "308, 63", "184 x 27", "Screen title (the text ends in -1; the screen name does not)", "NO - fault finding only"],
    ["", "Lamp table (10.6)", "0, 94", "", "10 rows, listed one by one in 10.6", "NO - fault finding only"],
    ["", "Button <b>BACK</b>", "644, 341", "151 x 60", "Press: ActivateScreen. <b>In the old project it points to OUTPUT STATUS itself, so BACK does nothing.</b> Choose INPUT STATUS to make it work (a small fix).", "NO - fault finding only"]], [28, 38, 15, 16, 50, 27], status_col=5)
d.p("<b>Start screen:</b> set <b>HMI_1 &gt; Runtime settings &gt; General &gt; Start screen</b> = AUTO (screen number 1; the export does not include runtime settings).")
d.h2("10.6 The lamp tables on the two status screens  [NOT needed to run the machine]")
d.box("<b>These two screens are not needed.</b> They only show which input and output is ON, which helps when you look for a wiring fault. "
      "They are also the slowest part of the HMI: 24 lamps, about one hour. In the minimum build skip all of 10.6, the IO tag table (IB0, IB1, QB0, QB1) "
      "and the IO STATUS button. You can add them later at any time.", CHK)
d.p("Each table is built from text fields and circles. There are two blocks side by side: the left block starts at x = 0, the right block at x = 401.")
d.table(["Piece", "Left block x / width", "Right block x / width", "Look"], [
    ["Header row at y = 94, height 26: <b>ADDRESS</b>, <b>STATUS</b>, <b>DESCRIPTION</b>", "0 / 84,  85 / 70,  156 / 241", "401 / 84,  486 / 70,  557 / 242", "Green background (0, 128, 0), white text"],
    ["Data rows, height 34 (y of each row: tables below)", "Same three columns", "Same three columns", "Dark grey background (51, 51, 51). Address in yellow text, description in white text. The STATUS cell stays empty."],
    ["Circle 23 x 23 in the STATUS column of each row", "x = 109", "x = 510", "Position of each circle: tables below. Grey 217, 217, 217 in the editor."],
], [62, 36, 36, 40])
d.add(Paragraph("INPUT STATUS: all 14 rows", ST["h3"]))
d.table(["Address text", "Description text", "Block", "Row y", "Circle x, y", "Circle tag", "Bit"], [
    ["I0.0", "PRODUCT SENSOR", "Left", "120", "109, 126", "IB0", "0"],
    ["I0.1", "AUTO MANUAL SELECTION", "Left", "155", "109, 161", "IB0", "1"],
    ["I0.2", "CYCLE START PB", "Left", "191", "109, 197", "IB0", "2"],
    ["I0.3", "CYCLE STOP PB", "Left", "227", "109, 233", "IB0", "3"],
    ["I0.4", "EMERGENCY PB", "Left", "263", "109, 269", "IB0", "4"],
    ["I0.5", "CONVEYOR VFD FAULT", "Left", "299", "109, 305", "IB0", "5"],
    ["I0.6", "SPARE", "Left", "335", "109, 341", "IB0", "6"],
    ["I0.7", "SPARE", "Left", "371", "109, 377", "IB0", "7"],
    ["I1.0", "SPARE", "Right", "120", "510, 126", "IB1", "0"],
    ["I1.1", "SPARE", "Right", "155", "510, 161", "IB1", "1"],
    ["I1.2", "SPARE", "Right", "191", "510, 197", "IB1", "2"],
    ["I1.3", "SPARE", "Right", "227", "510, 233", "IB1", "3"],
    ["I1.4", "SPARE", "Right", "263", "511, 269", "IB1", "4"],
    ["I1.5", "SPARE", "Right", "299", "511, 304", "IB1", "5"]], [22, 52, 16, 16, 26, 22, 20])
d.add(Paragraph("OUTPUT STATUS: all 10 rows", ST["h3"]))
d.table(["Address text", "Description text", "Block", "Row y", "Circle x, y", "Circle tag", "Bit"], [
    ["Q0.0", "CONVEYOR FWD ON", "Left", "121", "109, 127", "QB0", "0"],
    ["Q0.1", "CONVEYOR REV ON", "Left", "156", "109, 162", "QB0", "1"],
    ["Q0.2", "FAULT RESET", "Left", "192", "109, 198", "QB0", "2"],
    ["Q0.3", "TL GREEN", "Left", "228", "109, 234", "QB0", "3"],
    ["Q0.4", "TL RED", "Left", "264", "109, 270", "QB0", "4"],
    ["Q0.5", "TL AMBER", "Left", "300", "109, 306", "QB0", "5"],
    ["Q0.6", "SPARE", "Left", "336", "109, 342", "QB0", "6"],
    ["Q0.7", "SPARE", "Left", "372", "109, 378", "QB0", "7"],
    ["Q1.0", "SPARE", "Right", "121", "510, 127", "QB1", "0"],
    ["Q1.1", "SPARE", "Right", "156", "510, 162", "QB1", "1"]], [22, 52, 16, 16, 26, 22, 20])
d.p("Each row is three text fields (address, empty status cell, description) at the x positions of its block, and one circle. "
    "Example, row I0.3: text <b>I0.3</b> at x = 0, y = 227; empty cell at x = 85, y = 227; text <b>CYCLE STOP PB</b> at x = 156, y = 227; circle at 109, 233 with tag IB0, bit 3.")
d.p("<b>Make a circle light up:</b> select the circle &gt; Properties &gt; <b>Animations &gt; Display &gt; Add new animation &gt; Appearance</b>. "
    "Tag: <b>IB0</b> for I0.x (IB1 for I1.x, QB0 for Q0.x, QB1 for Q1.x). Type: <b>Single bit</b>, and the bit number = the digit after the dot "
    "(I0.3 is bit 3). Then two rows: <b>0 = red</b> (255, 0, 0) and <b>1 = green</b> (0, 255, 0), background and foreground. "
    "So a lamp is red when the signal is OFF and green when it is ON. Build one complete row, then copy and paste it and change only the address text, the description and the bit number.")
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

# ------------------------------------------------------------------ 12
d.page()
d.h1("Part 12. New: red-button reverse jog in MANUAL (not in the old program)")
d.p("You told me (12 October 2026): in MANUAL mode, holding the <b>red</b> button should run the belt in <b>reverse</b>, and releasing it should stop the belt, "
    "like the HMI REV JOG button. The old program does not do this. Build and test parts 1 - 11 first (an exact copy). Then add this change.")
d.table(["Way", "Wiring", "Program", "If a wire breaks"], [
    ["<b>A (recommended)</b>", "Clip one extra <b>NO</b> contact block onto the red button. Wire: +24 V - new NO contact - spare input <b>I0.7</b>.",
     "Normally open contact on I0.7", "Reverse simply does not work. Safe."],
    ["B (not recommended)", "No new wire: use the existing NC STOP contact on I0.3.",
     "Normally closed contact on I0.3", "A broken or loose STOP wire looks like \"red button held\": in MANUAL the belt would run in <b>reverse by itself</b>."]],
    [28, 62, 38, 46])
d.h2("Steps for way A")
d.steps([
    "Panel (power OFF): fit a NO contact block on the red button. Wire +24 V to one side, and the other side to PLC input <b>I0.7</b>.",
    "Tag table <b>DI</b>: rename <b>DI_SPARE I0.7</b> to <b>DI_REV JOG PB</b> (address %I0.7 stays).",
    "FC_MANUAL network 1: below the contact <b>\"DB_HMI\".MOTOR JOG REV PB</b> add a parallel branch with a normally open contact <b>DI_REV JOG PB</b>, "
    "joined again before the coil MANUAL CONVEYOR REV ON FLAG (drawing below).",
    "Interlock, so forward and reverse can never be ON together: FC_OUTPUTS network 1, add a <b>normally closed</b> contact <b>DO_CONVEYOR REV ON</b> just before the coil; "
    "network 2, add a normally closed contact <b>DO_CONVEYOR FWD ON</b> just before the coil.",
    "HMI, INPUT STATUS screen: change the description text of I0.7 from SPARE to <b>REV JOG PB</b> (optional).",
    "Compile (Errors: 0), download, and test as in the table below."])
d.rung("FC_MANUAL - Network 1 after the change", [
    [NO("CONTROL ON\nFLAG"), NO("MANUAL MODE\nSELECTED"), NC("FAULT BIT"), NO("\"DB_HMI\".MOTOR\nJOG REV PB"), "-", COIL("MANUAL CONVEYOR\nREV ON FLAG")],
    [None, None, None, NO("DI_REV JOG PB\n(I0.7, new)"), None, None],
    [None, None, None, NO("\"DB_HMI\".MOTOR\nJOG FWD PB"), "-", COIL("MANUAL CONVEYOR\nFWD ON FLAG")],
    [None, None, None, NO("DI_CYCLE\nSTART PB"), None, None]],
    links=[(3, 0, 3), (4, 0, 1), (4, 2, 3)])
d.table(["#", "Do this", "You must see"], [
    ["1", "MANUAL. Hold the red button, then release it", "Q0.1 ON while held, OFF when released"],
    ["2", "MANUAL. Hold green and red together", "Only one of Q0.0 / Q0.1 ON (forward wins)"],
    ["3", "AUTO, cycle running. Press red", "The cycle stops, as before. The belt does not reverse"],
    ["4", "MANUAL. Disconnect the I0.7 wire, hold red", "Nothing moves (way A is safe)"]], [8, 86, 80])
d.box("Keep this change out of the exact-copy project until the copy is tested. Save the project first under a new name (Project &gt; Save as) "
      "so you can go back to the exact copy at any time.", CHK)

# ------------------------------------------------------------------ appendix
d.h1("Appendix A. What the switched-off part of FC_AUTO was for")
d.p("The old program was first written for another way of working: the sensor was on PLC input I0.0. After the sensor saw a box, the PLC waited STOP TIME seconds "
    "(set on the HMI), stopped the belt, wrote 1 to register 40001 as a signal to the PC, and waited until 0 came back (CAMERA DONE) before running on. "
    "The HMI showed WAITING FOR CAMERA ACK (status 30) meanwhile.")
d.p("When the sensor was moved to the camera, the author did not delete this cycle. A <b>normally closed AlwaysTRUE</b> contact was put at its start "
    "(FC_AUTO network 3, third row) so that it can never become active, and an <b>AlwaysTRUE</b> branch was put parallel to the NOT OFF2 contact in the first row, "
    "so that it can never stop the belt. That is why network 3 looks complicated but works like a simple rule: <b>belt runs while ACTIVE and register 40001 = 0</b>.")
d.box("Do not remove the normally closed AlwaysTRUE contact. Without it the old cycle would wake up as soon as something is wired to I0.0.", BAD)

d.build(OUT, "Write the Conveyor Program Yourself - TIA Portal V21, revision 3.2", "Write the Conveyor Program Yourself - TIA Portal V21 (Rev 3.2)")
print("ok", OUT)

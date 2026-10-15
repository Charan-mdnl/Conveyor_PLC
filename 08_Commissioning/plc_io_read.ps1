# READ ONLY: reads PLC inputs (Modbus fn 02), outputs (fn 01) and register 40001 (fn 03) from the S7-1200 MB_SERVER.
# Never sends a write function. -Seconds N: watch for N seconds and print every change.
param([int]$Seconds = 0)
$ErrorActionPreference = "Stop"
$names = @{ 0="I0.0 (empty)"; 1="I0.1 AUTO/MANUAL selector"; 2="I0.2 START green"; 3="I0.3 STOP (NC)"; 4="I0.4 EMERGENCY (NC)";
            5="I0.5 VFD fault relay"; 6="I0.6 (joint only)"; 7="I0.7 spare"; 8="I1.0 spare"; 9="I1.1 spare"; 10="I1.2 spare";
            11="I1.3 spare"; 12="I1.4 spare"; 13="I1.5 spare" }
$onames = @{ 0="Q0.0 VFD FWD"; 1="Q0.1 VFD REV"; 2="Q0.2 VFD RESET"; 3="Q0.3 lamp GREEN"; 4="Q0.4 lamp RED"; 5="Q0.5 lamp AMBER"; 6="Q0.6"; 7="Q0.7"; 8="Q1.0"; 9="Q1.1" }
$client = New-Object System.Net.Sockets.TcpClient
$client.ReceiveTimeout = 2000; $client.SendTimeout = 2000
$client.Connect("192.168.0.40", 502)
$stream = $client.GetStream()
$script:tid = 0
function Req([byte]$fn, [int]$addr, [int]$count) {
    if ($fn -notin 1,2,3) { throw "SAFETY: only read functions 01, 02, 03 are allowed" }
    $script:tid++
    $f = [byte[]]@(($script:tid -shr 8), ($script:tid -band 255), 0, 0, 0, 6, 1, $fn, ($addr -shr 8), ($addr -band 255), ($count -shr 8), ($count -band 255))
    $stream.Write($f, 0, $f.Length)
    $buf = New-Object byte[] 260
    $n = $stream.Read($buf, 0, 260)
    if ($buf[7] -band 0x80) { throw "PLC answered exception $($buf[8]) for function $fn" }
    return ,$buf[9..($n - 1)]
}
function Bits($data, $count) { $r = @(); for ($i = 0; $i -lt $count; $i++) { $r += (($data[[math]::Floor($i / 8)] -shr ($i % 8)) -band 1) }; return ,$r }
function Snapshot { $i = Bits (Req 2 0 14) 14; $q = Bits (Req 1 0 10) 10; $h = Req 3 0 1; return @{ I = $i; Q = $q; R = ($h[0] * 256 + $h[1]) } }
try {
    $s = Snapshot
    "INPUTS (1 = LED on):"; for ($k = 0; $k -lt 14; $k++) { "   {0,-28} {1}" -f $names[$k], $s.I[$k] }
    "OUTPUTS:"; for ($k = 0; $k -lt 10; $k++) { "   {0,-28} {1}" -f $onames[$k], $s.Q[$k] }
    "Register 40001 (PC run/stop) = $($s.R)"
    if ($Seconds -gt 0) {
        "`nWATCHING for $Seconds s - press the buttons now, one at a time:"
        $end = (Get-Date).AddSeconds($Seconds); $prev = $s
        while ((Get-Date) -lt $end) {
            Start-Sleep -Milliseconds 150; $now = Snapshot
            for ($k = 0; $k -lt 14; $k++) { if ($now.I[$k] -ne $prev.I[$k]) { "{0}  INPUT  {1,-28} {2} -> {3}" -f (Get-Date -Format "HH:mm:ss.f"), $names[$k], $prev.I[$k], $now.I[$k] } }
            for ($k = 0; $k -lt 10; $k++) { if ($now.Q[$k] -ne $prev.Q[$k]) { "{0}  OUTPUT {1,-28} {2} -> {3}" -f (Get-Date -Format "HH:mm:ss.f"), $onames[$k], $prev.Q[$k], $now.Q[$k] } }
            $prev = $now
        }
        "done"
    }
} finally { $client.Close() }

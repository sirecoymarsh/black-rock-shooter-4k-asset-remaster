$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$exe=Join-Path $root 'workspace\runtime\ppsspp-1.20.4\PPSSPPWindows64.exe'
$iso='P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work\release_build\runtime_fix_iso_20260823_test_v2\BRS_Korean_v1.0.iso'
if((Get-FileHash -LiteralPath $iso -Algorithm SHA256).Hash.ToLowerInvariant() -ne '525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a'){throw 'ISO identity mismatch'}
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne '27d3edbb06dc623dab60877d3e3a975aef4034c7d4fac464e92fd4998864d2ec'){throw 'Emulator identity mismatch'}
$owned=@(Get-CimInstance Win32_Process -Filter "Name='PPSSPPWindows64.exe'" | Where-Object {$_.ExecutablePath -eq $exe})
if($owned.Count){Write-Output 'Independent game is already open. Existing progress preserved.';exit 0}
# Interactive game launch explicitly requested; always supply the fixed ISO.
Start-Process -FilePath $exe -ArgumentList @(('"'+$iso+'"'),'--windowed') -WorkingDirectory (Split-Path $exe -Parent) -WindowStyle Normal
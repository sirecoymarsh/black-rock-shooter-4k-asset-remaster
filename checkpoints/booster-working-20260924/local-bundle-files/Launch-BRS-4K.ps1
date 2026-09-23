$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$exe=Join-Path $root 'runtime\PPSSPPBRS4KTest.exe'
$iso=Join-Path $root 'BRS_4K_combined_test.iso'
$manifest=Get-Content -LiteralPath (Join-Path $root 'build-manifest.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.executable_sha256){throw 'Emulator hash mismatch'}
if((Get-FileHash -LiteralPath $iso -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.iso_sha256){throw 'ISO hash mismatch'}
if(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe}){throw 'This build is already running'}
if(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -eq 49324}){throw 'Port 49324 is already in use'}
[IO.File]::WriteAllText((Join-Path $root 'runtime\installed.txt'),(Join-Path $root 'memstick')+"`n",[Text.UTF8Encoding]::new($false))
$p=Start-Process -FilePath $exe -WorkingDirectory (Join-Path $root 'runtime') -ArgumentList @(('"'+$iso+'"'),'--windowed') -WindowStyle Normal -PassThru
@{pid=$p.Id;executable=$exe;iso=$iso;port=49324;launched=(Get-Date).ToString('o');savestate_loaded=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'launch-session.json') -Encoding utf8
Write-Output ('BRS combined build launched: '+$p.Id)

param([ValidateSet('reencoded','pgr')][string]$Variant='reencoded')
$ErrorActionPreference='Stop'
$proj='P:\AI\Codex\projects\black-rock-shooter-hd-retexture'
$testRoot=Join-Path $proj 'workspace\model_port\runtime_test'
$runtime=Join-Path $testRoot 'runtime'
$sourceRuntime=Join-Path $proj 'workspace\runtime\ppsspp-1.20.4'
$reference=Join-Path $proj 'workspace\sessions\S-20260922-151804-baseline-d7d8b6'
$exe=Join-Path $runtime 'PPSSPPModelPort.exe'
if(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe}){throw 'Model test already running.'}
if(Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -eq 49219}){throw 'Model test port in use.'}
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
if(!(Test-Path -LiteralPath $exe)){
 Copy-Item -LiteralPath "$sourceRuntime\PPSSPPWindows64.exe" -Destination $exe
 Copy-Item -LiteralPath "$sourceRuntime\assets" -Destination "$runtime\assets" -Recurse
}
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne '27d3edbb06dc623dab60877d3e3a975aef4034c7d4fac464e92fd4998864d2ec'){throw 'Runtime identity mismatch.'}
$sessionName=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$Variant
$session=Join-Path $testRoot $sessionName
New-Item -ItemType Directory -Path "$session\memstick\PSP\SYSTEM","$session\captures","$session\memstick\PSP\TEXTURES\NPUH10126\new" | Out-Null
Copy-Item -LiteralPath "$reference\memstick\PSP\SYSTEM\controls.ini" -Destination "$session\memstick\PSP\SYSTEM\controls.ini"
Copy-Item -LiteralPath "$reference\memstick\PSP\SAVEDATA" -Destination "$session\memstick\PSP\SAVEDATA" -Recurse
Copy-Item -LiteralPath "$reference\memstick\PSP\PPSSPP_STATE" -Destination "$session\memstick\PSP\PPSSPP_STATE" -Recurse
$ini=[IO.File]::ReadAllText("$reference\memstick\PSP\SYSTEM\ppsspp.ini")
$changes=@{RemoteISOPort='49219';WindowX='80';WindowY='80';WindowWidth='1056';WindowHeight='660';ReplaceTextures='False';GameVolume='0';InternalResolution='4';FullScreen='False'}
foreach($key in $changes.Keys){
 $pattern='(?m)^'+[regex]::Escape($key)+'\s*=.*$'
 if([regex]::Matches($ini,$pattern).Count -gt 1){throw "Duplicate setting: $key"}
 $ini=[regex]::Replace($ini,$pattern,($key+' = '+$changes[$key]))
}
[IO.File]::WriteAllText("$session\memstick\PSP\SYSTEM\ppsspp.ini",$ini,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText("$session\memstick\PSP\TEXTURES\NPUH10126\textures.ini","[options]`nhash = xxh64`nversion = 1`n[hashes]`n",[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText("$runtime\installed.txt","$session\memstick`n",[Text.UTF8Encoding]::new($false))
$isoName=if($Variant -eq 'reencoded'){'BRS_model_reencoded.iso'}else{'BRS_pgr_candidate.iso'}
$iso=Join-Path $proj "workspace\model_port\candidate_v1\$isoName"
$state=Join-Path $session 'memstick\PSP\PPSSPP_STATE\NPUH10126_1.01_0.ppst'
if((Get-FileHash -LiteralPath $state -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'e993964c615533dd5ef60b145a008f1d5db13a049c585c4ab048a37b71651b61'){throw 'State copy mismatch.'}
$p=Start-Process -FilePath $exe -WorkingDirectory $runtime -ArgumentList @(('"'+$iso+'"'),'--windowed',('--state="'+$state+'"')) -WindowStyle Normal -PassThru
$meta=@{variant=$Variant;path=$session;executable=$exe;pid=$p.Id;port=49219;iso=$iso;iso_sha256=(Get-FileHash -LiteralPath $iso -Algorithm SHA256).Hash.ToLowerInvariant();reference=$reference;state_before_costume_swap=$true;tested=$false;changes=$changes}
$meta | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$session\session.json" -Encoding utf8
$meta | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$testRoot\active_test.json" -Encoding utf8
$meta | ConvertTo-Json -Depth 6

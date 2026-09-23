param([switch]$Interactive,[switch]$SoftwareProbe,[switch]$StellaPreview)
$ErrorActionPreference='Stop'
if($SoftwareProbe -and $StellaPreview){throw 'Software probe cannot verify HD replacements.'}
$proj=Split-Path $PSScriptRoot -Parent
$envInfo=Get-Content -LiteralPath "$proj\qa\evidence\environment.json" -Raw | ConvertFrom-Json
$exe=$envInfo.runtime.path
$iso=$envInfo.iso.path
if((Get-FileHash -LiteralPath $iso -Algorithm SHA256).Hash.ToLowerInvariant() -ne $envInfo.iso.sha256){throw 'ISO identity differs from approved v1.0.1 baseline.'}
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $envInfo.runtime.sha256){throw 'PPSSPP executable identity changed.'}
$active=Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe}
if($active){throw 'The project PPSSPP is already running. Close it before starting another dump session.'}
$sessionId='S-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,6)
$sess=Join-Path $proj "workspace\sessions\$sessionId"
if(Test-Path -LiteralPath $sess){throw 'Session already exists.'}
New-Item -ItemType Directory -Path "$sess\memstick\PSP\SYSTEM","$sess\memstick\PSP\SAVEDATA","$sess\memstick\PSP\TEXTURES\NPUH10126\new","$sess\captures" | Out-Null
Copy-Item -LiteralPath "$PSScriptRoot\templates\ppsspp-dump.ini" -Destination "$sess\memstick\PSP\SYSTEM\ppsspp.ini"
Copy-Item -LiteralPath "$PSScriptRoot\templates\textures.ini" -Destination "$sess\memstick\PSP\TEXTURES\NPUH10126\textures.ini"
if($SoftwareProbe){
 $probeIni=Get-Content -LiteralPath "$sess\memstick\PSP\SYSTEM\ppsspp.ini" -Raw
 $probeIni=$probeIni.Replace("[Graphics]","[Graphics]`nSoftwareRenderer = True").Replace("GraphicsBackend = 3 (VULKAN)","GraphicsBackend = 0 (OPENGL)").Replace("SaveNewTextures = True","SaveNewTextures = False")
 [IO.File]::WriteAllText("$sess\memstick\PSP\SYSTEM\ppsspp.ini",$probeIni,[Text.UTF8Encoding]::new($false))
}
if($StellaPreview){
 $candidateRoot=Join-Path $proj 'workspace\stella_hd\corrected_v2'
 $candidateReport=Get-Content -LiteralPath "$candidateRoot\validation.json" -Raw | ConvertFrom-Json
 $candidateImage=Join-Path $candidateRoot 'qa_pack\PSP\TEXTURES\NPUH10126\stella\brs02_body_8x.png'
 if((Get-FileHash -LiteralPath $candidateImage -Algorithm SHA256).Hash.ToLowerInvariant() -ne $candidateReport.output_sha256){throw 'Candidate image hash mismatch.'}
 Copy-Item -LiteralPath "$candidateRoot\qa_pack\PSP\TEXTURES\NPUH10126\stella" -Destination "$sess\memstick\PSP\TEXTURES\NPUH10126\stella" -Recurse
 Copy-Item -LiteralPath "$candidateRoot\qa_pack\PSP\TEXTURES\NPUH10126\textures.ini" -Destination "$sess\memstick\PSP\TEXTURES\NPUH10126\textures.ini"
 $previewIni=Get-Content -LiteralPath "$sess\memstick\PSP\SYSTEM\ppsspp.ini" -Raw
 $previewIni=$previewIni.Replace('ReplaceTextures = False','ReplaceTextures = True').Replace('InternalResolution = 1','InternalResolution = 8')
 $previewIni=$previewIni.Replace('[General]',"[General]`nWindowX = 100`nWindowY = 80`nWindowWidth = 1152`nWindowHeight = 720`nWindowSizeState = 0")
 [IO.File]::WriteAllText("$sess\memstick\PSP\SYSTEM\ppsspp.ini",$previewIni,[Text.UTF8Encoding]::new($false))
}
Copy-Item -LiteralPath "$sess\memstick\PSP\SYSTEM\ppsspp.ini" -Destination "$sess\ppsspp.initial.ini"
Copy-Item -LiteralPath "$sess\memstick\PSP\TEXTURES\NPUH10126\textures.ini" -Destination "$sess\textures.initial.ini"
$saves=Join-Path $envInfo.legacy_memstick 'PSP\SAVEDATA\NPUH10126DATA00'
Copy-Item -LiteralPath $saves -Destination "$sess\memstick\PSP\SAVEDATA\NPUH10126DATA00" -Recurse
[IO.File]::WriteAllText((Join-Path (Split-Path $exe -Parent) 'installed.txt'),"$sess\memstick`n",[Text.UTF8Encoding]::new($false))
$meta=@{session_id=$sessionId;iso_sha256=$envInfo.iso.sha256;executable_sha256=$envInfo.runtime.sha256;hash_algorithm='xxh64';ignoreAddress=$true;replace_textures=[bool]$StellaPreview;stella_candidate=[bool]$StellaPreview;internal_resolution=$(if($StellaPreview){8}else{1});save_new_textures=(!$SoftwareProbe);muted=$true;backend=$(if($SoftwareProbe){'Software/OpenGL'}else{'Vulkan'});scene_status='unverified';interactive=[bool]$Interactive;ppsspp_ini_sha256=(Get-FileHash -LiteralPath "$sess\ppsspp.initial.ini" -Algorithm SHA256).Hash.ToLowerInvariant();textures_ini_sha256=(Get-FileHash -LiteralPath "$sess\textures.initial.ini" -Algorithm SHA256).Hash.ToLowerInvariant();source_save_files=@(Get-ChildItem -LiteralPath $saves -File -Recurse | ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}})}
$meta | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$sess\session.json" -Encoding utf8
@{session_id=$sessionId;path=$sess;port=49213} | ConvertTo-Json | Set-Content -LiteralPath "$proj\workspace\runtime\active_session.json" -Encoding utf8
$style=if($Interactive){'Normal'}else{'Hidden'}
$p=Start-Process -FilePath $exe -ArgumentList @(('"'+$iso+'"'),'--windowed') -WorkingDirectory (Split-Path $exe -Parent) -WindowStyle $style -PassThru
@{pid=$p.Id;start_time=$p.StartTime.ToString('o');executable=$exe;session=$sessionId} | ConvertTo-Json | Set-Content -LiteralPath "$sess\process.json" -Encoding utf8
Write-Output "Session: $sess"
Write-Output ('Audio disabled. ReplaceTextures='+[bool]$StellaPreview+'. Original ISO and save files are read-only inputs.')

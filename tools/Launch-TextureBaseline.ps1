param([string]$ReferenceSession='S-20260922-145156-354b41',[switch]$EnableReplacement,[switch]$ResumeLatest)
$ErrorActionPreference='Stop'
$proj=Split-Path $PSScriptRoot -Parent
if($ReferenceSession -notmatch '^S-[A-Za-z0-9-]+$'){throw 'Invalid reference session.'}
$reference=Join-Path $proj "workspace\sessions\$ReferenceSession"
$envInfo=Get-Content -LiteralPath "$proj\qa\evidence\environment.json" -Raw | ConvertFrom-Json
$exe=$envInfo.runtime.path
$iso=$envInfo.iso.path
foreach($identity in @($envInfo.iso,$envInfo.runtime)){
 if((Get-FileHash -LiteralPath $identity.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $identity.sha256){throw 'Baseline file identity changed.'}
}
$active=Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -eq $exe}
if($active){throw 'Project game is already running; preserve its progress before comparison.'}
$referenceMeta=Get-Content -LiteralPath "$reference\session.json" -Raw | ConvertFrom-Json
if($referenceMeta.iso_sha256 -ne $envInfo.iso.sha256 -or $referenceMeta.executable_sha256 -ne $envInfo.runtime.sha256){throw 'Reference session identity mismatch.'}
$before=[IO.File]::ReadAllText("$reference\memstick\PSP\SYSTEM\ppsspp.ini")
$pattern='(?m)^(ReplaceTextures\s*=\s*)(True|False)(?=\s*$)'
$matches=[regex]::Matches($before,$pattern)
if($matches.Count -ne 1){throw 'Reference must have exactly one replacement setting.'}
$previous=$matches[0].Groups[2].Value
$desired=if($EnableReplacement){'True'}else{'False'}
if($previous -eq $desired){throw 'Requested setting is already active in the reference.'}
# Retain every other setting, including rendering resolution and texture capture.
$after=[regex]::Replace($before,$pattern,('${1}'+$desired))
$reverse=[regex]::Replace($after,$pattern,('${1}'+$previous))
if($reverse -cne $before){throw 'Unexpected configuration differences.'}
$runLabel=if($EnableReplacement){'preview'}else{'baseline'}
$sessionId='S-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$runLabel+'-'+[guid]::NewGuid().ToString('N').Substring(0,6)
$sess=Join-Path $proj "workspace\sessions\$sessionId"
New-Item -ItemType Directory -Path "$sess\memstick\PSP\SYSTEM","$sess\memstick\PSP\TEXTURES\NPUH10126\new","$sess\captures" | Out-Null
foreach($item in (Get-ChildItem -LiteralPath "$reference\memstick\PSP\SYSTEM" | Where-Object {$_.Name -ne 'DUMP'})){
 Copy-Item -LiteralPath $item.FullName -Destination "$sess\memstick\PSP\SYSTEM" -Recurse
}
Copy-Item -LiteralPath "$reference\memstick\PSP\SAVEDATA" -Destination "$sess\memstick\PSP\SAVEDATA" -Recurse
foreach($item in (Get-ChildItem -LiteralPath "$reference\memstick\PSP\TEXTURES\NPUH10126" | Where-Object {$_.Name -ne 'new'})){
 Copy-Item -LiteralPath $item.FullName -Destination "$sess\memstick\PSP\TEXTURES\NPUH10126" -Recurse
}
[IO.File]::WriteAllText("$sess\memstick\PSP\SYSTEM\ppsspp.ini",$after,[Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath "$sess\memstick\PSP\SYSTEM\ppsspp.ini" -Destination "$sess\ppsspp.initial.ini"
Copy-Item -LiteralPath "$sess\memstick\PSP\TEXTURES\NPUH10126\textures.ini" -Destination "$sess\textures.initial.ini"
$sourceFiles=@(Get-ChildItem -LiteralPath "$reference\memstick\PSP\SAVEDATA" -File -Recurse | ForEach-Object {
 $relative=$_.FullName.Substring(("$reference\memstick\PSP\SAVEDATA").Length+1)
 $hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
 if((Get-FileHash -LiteralPath (Join-Path "$sess\memstick\PSP\SAVEDATA" $relative) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash){throw 'Save copy mismatch.'}
 @{path=$relative;sha256=$hash}
})
$stateInfo=$null
$launchArguments=@(('"'+$iso+'"'),'--windowed')
if($ResumeLatest){
 $stateRoot=Join-Path $reference 'memstick\PSP\PPSSPP_STATE'
 $latest=Get-ChildItem -LiteralPath $stateRoot -File | Where-Object {$_.Name -match '^NPUH10126_1\.01_[0-9]+\.ppst$'} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
 if(!$latest){throw 'No compatible save state exists.'}
 Copy-Item -LiteralPath $stateRoot -Destination "$sess\memstick\PSP\PPSSPP_STATE" -Recurse
 $stateCopy=Join-Path "$sess\memstick\PSP\PPSSPP_STATE" $latest.Name
 $stateHash=(Get-FileHash -LiteralPath $latest.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
 if((Get-FileHash -LiteralPath $stateCopy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $stateHash){throw 'State copy mismatch.'}
 $launchArguments+=('--state="'+$stateCopy+'"')
 $stateInfo=@{source=$latest.FullName;copy=$stateCopy;sha256=$stateHash;source_modified=$latest.LastWriteTime.ToString('o')}
}
if($EnableReplacement){
 $candidate=Join-Path $sess 'memstick\PSP\TEXTURES\NPUH10126\stella\brs02_body_8x.png'
 $expected=(Get-Content -LiteralPath "$proj\workspace\stella_hd\corrected_v2\validation.json" -Raw | ConvertFrom-Json).output_sha256
 if((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw 'Candidate image identity mismatch.'}
}
$meta=@{session_id=$sessionId;reference_session=$ReferenceSession;experiment='Toggle ReplaceTextures while retaining other settings';changed_settings=@{ReplaceTextures=@{before=($previous -eq 'True');after=[bool]$EnableReplacement}};all_other_ini_values_identical=$true;iso_sha256=$envInfo.iso.sha256;executable_sha256=$envInfo.runtime.sha256;replace_textures=[bool]$EnableReplacement;resume_state=$stateInfo;internal_resolution=8;save_new_textures=$true;muted=$true;backend='Vulkan';interactive=$true;scene_status='user_reproduction_pending';source_save_files=$sourceFiles;ppsspp_ini_sha256=(Get-FileHash -LiteralPath "$sess\ppsspp.initial.ini" -Algorithm SHA256).Hash.ToLowerInvariant()}
$meta | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$sess\session.json" -Encoding utf8
[IO.File]::WriteAllText((Join-Path (Split-Path $exe -Parent) 'installed.txt'),"$sess\memstick`n",[Text.UTF8Encoding]::new($false))
@{session_id=$sessionId;path=$sess;port=49213} | ConvertTo-Json | Set-Content -LiteralPath "$proj\workspace\runtime\active_session.json" -Encoding utf8
$p=Start-Process -FilePath $exe -ArgumentList $launchArguments -WorkingDirectory (Split-Path $exe -Parent) -WindowStyle Normal -PassThru
@{pid=$p.Id;start_time=$p.StartTime.ToString('o');executable=$exe;session=$sessionId} | ConvertTo-Json | Set-Content -LiteralPath "$sess\process.json" -Encoding utf8
@{session=$sessionId;path=$sess;pid=$p.Id;changed_setting=('ReplaceTextures: '+$previous+' -> '+$desired);resume_state=$stateInfo;same_iso=$true;save_copy_verified=$true} | ConvertTo-Json

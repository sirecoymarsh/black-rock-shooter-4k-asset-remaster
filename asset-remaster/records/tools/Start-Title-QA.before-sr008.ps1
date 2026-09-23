param(
  [ValidateSet('baseline','candidate')][string]$Variant='baseline',
  [ValidatePattern('^UIF-Q\d{3}-title-(baseline|candidate)$')][string]$SessionName,
  [switch]$InteractivePreview,
  [ValidateSet('VULKAN','DIRECT3D11')][string]$Backend='VULKAN'
)
$ErrorActionPreference='Stop'
$qaRoot='P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts'
$qaExe=Join-Path $qaRoot 'workspace\runtime\qa-ppsspp-1.20.4\PPSSPPWindows64.exe'
$qaIso='P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work\release_build\runtime_fix_iso_20260823_test_v2\BRS_Korean_v1.0.iso'
$qaName=if($SessionName){$SessionName}elseif($Variant -eq 'baseline'){'UIF-Q005-title-baseline'}else{'UIF-Q004-title-candidate'}
if(-not $qaName.EndsWith('-'+$Variant)){throw 'Session name must match variant'}
$qaSession=Join-Path $qaRoot ('workspace\sessions\'+$qaName)
$qaInstalled=Join-Path (Split-Path $qaExe -Parent) 'installed.txt'
if(Test-Path -LiteralPath $qaSession){throw 'Session already exists; inspect and resume explicitly.'}
if((Get-FileHash -LiteralPath $qaExe -Algorithm SHA256).Hash.ToLowerInvariant() -ne '27d3edbb06dc623dab60877d3e3a975aef4034c7d4fac464e92fd4998864d2ec'){throw 'Emulator identity mismatch'}
if((Get-FileHash -LiteralPath $qaIso -Algorithm SHA256).Hash.ToLowerInvariant() -ne '525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a'){throw 'ISO identity mismatch'}
$qaExisting=@(Get-CimInstance Win32_Process -Filter "Name='PPSSPPWindows64.exe'" | Where-Object {$_.ExecutablePath -eq $qaExe})
if($qaExisting.Count){throw 'QA executable already running; preserve existing session.'}
$qaListener=@(Get-NetTCPConnection -LocalPort 49322 -State Listen -ErrorAction SilentlyContinue)
if($qaListener.Count){throw 'QA port is already owned; do not replace.'}
$qaSystem=Join-Path $qaSession 'memstick\PSP\SYSTEM'
New-Item -ItemType Directory -Path $qaSystem -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $qaSession 'captures') -Force | Out-Null
$qaIni=Get-Content -LiteralPath (Join-Path $qaRoot 'workspace\sessions\UIF-Q001-font-baseline\memstick\PSP\SYSTEM\ppsspp.ini') -Raw
if($Backend -eq 'DIRECT3D11'){$qaIni=$qaIni.Replace('GraphicsBackend = 3 (VULKAN)','GraphicsBackend = 2 (DIRECT3D11)')}
if($Variant -eq 'candidate'){
  $qaIni=$qaIni.Replace('ReplaceTextures = False','ReplaceTextures = True')
  $qaTextures=Join-Path $qaSession 'memstick\PSP\TEXTURES'
  New-Item -ItemType Directory -Path $qaTextures -Force | Out-Null
  Copy-Item -LiteralPath (Join-Path $qaRoot 'workspace\local-sr\stage01-review-pack\PSP\TEXTURES\NPUH10126') -Destination $qaTextures -Recurse
}
[IO.File]::WriteAllText((Join-Path $qaSystem 'ppsspp.ini'),$qaIni,(New-Object Text.UTF8Encoding($false)))
Copy-Item -LiteralPath $qaInstalled -Destination (Join-Path $qaSession 'previous-installed.txt')
[IO.File]::WriteAllText($qaInstalled,(Join-Path $qaSession 'memstick'),(New-Object Text.UTF8Encoding($false)))
$qaMeta=[ordered]@{path=$qaSession;exe=$qaExe;iso=$qaIso;iso_sha256='525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a';port=49322;variant=$Variant;replace_textures=($Variant -eq 'candidate');created_utc=[DateTime]::UtcNow.ToString('o');save_data_copied=$false;state_copied=$false;windows_input_sent=$false}
$qaMeta.interactive_preview=[bool]$InteractivePreview
$qaMeta.graphics_backend=$Backend
$qaMeta.texture_pack=if($Variant -eq 'candidate'){'stage01-review-pack'}else{$null}
$qaWindowStyle=if($InteractivePreview){'Normal'}else{'Hidden'}
try {
  $qaProc=Start-Process -FilePath $qaExe -ArgumentList @(('"'+$qaIso+'"'),'--windowed') -WorkingDirectory (Split-Path $qaExe -Parent) -WindowStyle $qaWindowStyle -PassThru
} catch {
  Copy-Item -LiteralPath (Join-Path $qaSession 'previous-installed.txt') -Destination $qaInstalled -Force
  throw
}
$qaMeta.pid=$qaProc.Id
$qaMeta.start_time_utc=$qaProc.StartTime.ToUniversalTime().ToString('o')
$qaMeta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $qaSession 'session.json') -Encoding UTF8
$qaMeta | ConvertTo-Json -Depth 5

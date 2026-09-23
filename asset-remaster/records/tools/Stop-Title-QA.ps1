param([Parameter(Mandatory=$true)][ValidatePattern('^UIF-Q\d{3}-title-(baseline|candidate)$')][string]$SessionName)
$ErrorActionPreference='Stop'
$qaRoot='P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts'
$qaSession=Join-Path $qaRoot ('workspace\sessions\'+$SessionName)
$qaMetaPath=Join-Path $qaSession 'session.json'
$qaMeta=Get-Content -LiteralPath $qaMetaPath -Raw | ConvertFrom-Json
$qaExpected=Join-Path $qaRoot 'workspace\runtime\qa-ppsspp-1.20.4\PPSSPPWindows64.exe'
if($qaMeta.exe -ne $qaExpected -or $qaMeta.path -ne $qaSession){throw 'Foreign session'}
$qaProc=Get-Process -Id $qaMeta.pid -ErrorAction SilentlyContinue
if($null -ne $qaProc){
  $qaRecordedStart=([DateTime]$qaMeta.start_time_utc).ToUniversalTime()
  if($qaProc.Path -ne $qaExpected -or $qaProc.StartTime.ToUniversalTime().Ticks -ne $qaRecordedStart.Ticks){throw 'Process identity changed; will not stop'}
  Stop-Process -Id $qaMeta.pid
  Wait-Process -Id $qaMeta.pid -Timeout 10 -ErrorAction SilentlyContinue
}
$qaInstalled=Join-Path (Split-Path $qaExpected -Parent) 'installed.txt'
if((Get-Content -LiteralPath $qaInstalled -Raw).Trim() -ne (Join-Path $qaSession 'memstick')){throw 'QA routing changed; will not overwrite'}
Copy-Item -LiteralPath (Join-Path $qaSession 'previous-installed.txt') -Destination $qaInstalled -Force
$qaMeta | Add-Member -NotePropertyName stopped_utc -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force
$qaMeta | Add-Member -NotePropertyName previous_routing_restored -NotePropertyValue $true -Force
$qaMeta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $qaMetaPath -Encoding UTF8
Write-Output 'Owned QA process stopped; previous QA routing restored.'

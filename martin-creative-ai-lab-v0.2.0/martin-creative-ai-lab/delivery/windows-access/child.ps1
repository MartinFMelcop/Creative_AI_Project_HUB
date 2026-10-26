param([Parameter(Mandatory)][string]$Bundle,[Parameter(Mandatory)][string]$Launcher,[Parameter(Mandatory)][string]$Output,[Parameter(Mandatory)][string]$Shell)
$ErrorActionPreference='Stop'
function Write-Json($Path,$Value) { [IO.File]::WriteAllText($Path,($Value | ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false)) }
try {
    $Bundle=[IO.Path]::GetFullPath($Bundle);$Output=[IO.Path]::GetFullPath($Output)
    $runtime=Join-Path $Bundle 'runtime/dotnet.exe'
    $identity=Join-Path $Output 'token.json'
    & $runtime $Launcher '--identity' $identity
    if ($LASTEXITCODE -ne 0) { throw 'Actual child token identity probe failed.' }
    $token=Get-Content -Raw -LiteralPath $identity | ConvertFrom-Json
    if ($token.administrator -or -not $token.medium_integrity -or -not $token.administrator_sid_deny_only) { throw 'Child token does not meet the predeclared non-administrator/medium/deny-only boundary.' }
    $empty=Join-Path $Output 'empty PATH';[IO.Directory]::CreateDirectory($empty) | Out-Null
    $saves=Join-Path $Output 'child saves';[IO.Directory]::CreateDirectory($saves) | Out-Null
    $save=Join-Path $saves 'scene.json'
    if (Test-Path -LiteralPath $save) { throw 'Baseline requires a fresh separate save; never overwrite existing data.' }
    $port=[IO.File]::ReadAllText((Join-Path $Output 'port.txt')).Trim()
    $start=[Diagnostics.ProcessStartInfo]::new()
    $start.FileName=$Shell;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
    $start.WorkingDirectory=$Output;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    foreach($a in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $Bundle 'run-demo.ps1'),$port,'20')) { $start.ArgumentList.Add($a) }
    $start.Environment['PATH']=$empty;$start.Environment['NORTH_STAR_SAVE_DIR']=$saves
    $start.Environment['DOTNET_ROOT']='Z:\unavailable';$start.Environment['DOTNET_ROOT_X64']='Z:\unavailable';$start.Environment['DOTNET_MULTILEVEL_LOOKUP']='0'
    $process=[Diagnostics.Process]::new();$process.StartInfo=$start
    if (-not $process.Start()) { throw 'Unchanged recipient launcher did not start.' }
    Write-Json (Join-Path $Output 'child-start.json') @{ pid=$PID;launcher_pid=$process.Id;port=$port;save=$save;save_existed_before=$false;token_boundary_valid=$true }
    $recipientIdentity=Join-Path $Output 'recipient-launcher-token.json'
    & $runtime $Launcher '--identity-pid' ([string]$process.Id) $recipientIdentity
    $recipientIdentityCode=$LASTEXITCODE
    $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
    $finished=$process.WaitForExit(35000)
    if (-not $finished) { $process.Kill($true);$process.WaitForExit(); }
    $out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult()
    [IO.File]::WriteAllText((Join-Path $Output 'launcher.stdout.txt'),$out,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $Output 'launcher.stderr.txt'),$err,[Text.UTF8Encoding]::new($false))
    $exists=Test-Path -LiteralPath $save -PathType Leaf
    if ($exists) { [IO.File]::Copy($save,(Join-Path $Output 'saved-scene-after.json'),$false) }
    Write-Json (Join-Path $Output 'child-result.json') @{ status=$(if($finished){'completed'}else{'inconclusive'});recipient_identity_exit_code=$recipientIdentityCode;timed_out=(-not $finished);exit_code=$(if($finished){$process.ExitCode}else{$null});ready_line=$out.Contains('READY http://127.0.0.1:');save_existed_before=$false;save_exists_after=$exists;save_bytes_after=$(if($exists){(Get-Item -LiteralPath $save).Length}else{0});save_sha256_after=$(if($exists){(Get-FileHash -Algorithm SHA256 -LiteralPath $save).Hash.ToLowerInvariant()}else{$null});scope='Actual limited/restricted child token inherits into the unchanged recipient; no privilege, policy, account or URLACL change.' }
    if (-not $finished) { exit 2 };exit 0
} catch {
    Write-Json (Join-Path $Output 'child-failure.json') @{ status='inconclusive';error=$_.Exception.Message }
    [Console]::Error.WriteLine($_.Exception.Message);exit 2
}

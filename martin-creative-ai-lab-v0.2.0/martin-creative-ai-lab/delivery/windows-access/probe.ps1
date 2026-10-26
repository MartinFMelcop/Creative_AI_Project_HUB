param([Parameter(Mandatory)][string]$Bundle,[Parameter(Mandatory)][string]$Launcher,[Parameter(Mandatory)][string]$Output,[Parameter(Mandatory)][string]$Shell)
$ErrorActionPreference='Stop'
function Write-Json($Path,$Value) { [IO.File]::WriteAllText($Path,($Value | ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false)) }
if (-not $IsWindows) { throw 'Actual Windows is required; source compilation is insufficient.' }
$Bundle=[IO.Path]::GetFullPath($Bundle);$Launcher=[IO.Path]::GetFullPath($Launcher);$Output=[IO.Path]::GetFullPath($Output)
if (Test-Path -LiteralPath $Output) { throw 'Output directory must be new; preserve existing runs.' }
[IO.Directory]::CreateDirectory($Output) | Out-Null
$runtime=Join-Path $Bundle 'runtime/dotnet.exe'
$child=Join-Path $PSScriptRoot 'child.ps1'
$listener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0);$listener.Start();$port=$listener.LocalEndpoint.Port;$listener.Stop()
[IO.File]::WriteAllText((Join-Path $Output 'port.txt'),[string]$port)
$inputs=@{}
foreach($name in @('run-demo.ps1','payload.sha256','app/NorthStar.AuthoredScene.dll','runtime/dotnet.exe')) { $inputs[$name]=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Bundle $name)).Hash.ToLowerInvariant() }
$start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=$runtime;$start.UseShellExecute=$false;$start.WorkingDirectory=$Output
$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
foreach($a in @($Launcher,'--launch',$Shell,$child,$Bundle,$Output)) { $start.ArgumentList.Add($a) }
$process=[Diagnostics.Process]::new();$process.StartInfo=$start
if (-not $process.Start()) { throw 'Token launcher failed to start.' }
$stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
$handler=[Net.Http.HttpClientHandler]::new();$handler.UseProxy=$false
$http=[Net.Http.HttpClient]::new($handler);$http.Timeout=[TimeSpan]::FromMilliseconds(500)
$clock=[Diagnostics.Stopwatch]::StartNew()
$observed=$null;$networkErrors=[Collections.Generic.List[string]]::new()
try {
    while($clock.ElapsedMilliseconds -lt 30000) {
        try {
            $response=$http.GetAsync("http://127.0.0.1:$port/state").GetAwaiter().GetResult()
            if ($response.IsSuccessStatusCode) {
                $text=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
                $observed=$text | ConvertFrom-Json
                [IO.File]::WriteAllText((Join-Path $Output 'http-state.json'),$text,[Text.UTF8Encoding]::new($false));break
            }
        } catch { if ($networkErrors.Count -lt 5) { $networkErrors.Add($_.Exception.Message) } }
        if ($process.HasExited -or (Test-Path -LiteralPath (Join-Path $Output 'child-result.json')) -or (Test-Path -LiteralPath (Join-Path $Output 'child-failure.json'))) { break }
        Start-Sleep -Milliseconds 50
    }
    $remaining=[Math]::Max(1,55000-[int]$clock.ElapsedMilliseconds)
    $finished=$process.WaitForExit($remaining)
    if (-not $finished) { $process.Kill($true);$process.WaitForExit() }
    [IO.File]::WriteAllText((Join-Path $Output 'token-launcher.stdout.txt'),$stdout.GetAwaiter().GetResult(),[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $Output 'token-launcher.stderr.txt'),$stderr.GetAwaiter().GetResult(),[Text.UTF8Encoding]::new($false))
    $identityPath=Join-Path $Output 'token.json'
    $token=$(if(Test-Path -LiteralPath $identityPath){Get-Content -Raw -LiteralPath $identityPath | ConvertFrom-Json}else{$null})
    $parentPath=Join-Path $Output 'parent-token.json';$parent=$(if(Test-Path -LiteralPath $parentPath){Get-Content -Raw -LiteralPath $parentPath | ConvertFrom-Json}else{$null})
    $recipientPath=Join-Path $Output 'recipient-launcher-token.json';$recipient=$(if(Test-Path -LiteralPath $recipientPath){Get-Content -Raw -LiteralPath $recipientPath | ConvertFrom-Json}else{$null})
    $recipientValid=$null -ne $recipient -and $recipient.administrator -eq $false -and $recipient.medium_integrity -eq $true -and $recipient.administrator_sid_deny_only -eq $true -and $recipient.user_sid_sha256 -eq $parent.user_sid_sha256
    $valid=$recipientValid -and $null -ne $token -and $null -ne $parent -and -not $token.administrator -and $token.medium_integrity -and $token.administrator_sid_deny_only -and $token.user_sid_sha256 -eq $parent.user_sid_sha256
    $attemptPath=Join-Path $Output 'child-start.json';$attempt=$(if(Test-Path -LiteralPath $attemptPath){Get-Content -Raw -LiteralPath $attemptPath | ConvertFrom-Json}else{$null})
    $launchPath=Join-Path $Output 'launch-result.json';$launchResult=$(if(Test-Path -LiteralPath $launchPath){Get-Content -Raw -LiteralPath $launchPath | ConvertFrom-Json}else{$null})
    $childFailed=Test-Path -LiteralPath (Join-Path $Output 'child-failure.json')
    $stdoutPath=Join-Path $Output 'selected-child.stdout.txt';$stderrPath=Join-Path $Output 'selected-child.stderr.txt'
    $actualOut=$(if(Test-Path -LiteralPath $stdoutPath){[IO.File]::ReadAllText($stdoutPath)}else{''})
    $actualError=$(if(Test-Path -LiteralPath $stderrPath){[IO.File]::ReadAllText($stderrPath)}else{''})
    $save=Join-Path $Output 'child saves/scene.json';$saveExists=Test-Path -LiteralPath $save -PathType Leaf
    if($saveExists){[IO.File]::Copy($save,(Join-Path $Output 'saved-scene-after.json'),$false)}
    $normal=$finished -and $null -ne $launchResult -and $launchResult.status -eq 'completed'
    $child=@{status=$(if($normal){'completed'}else{'inconclusive'});normal_exit_observed=$normal;timed_out=((-not $finished) -or ($null -ne $launchResult -and $launchResult.status -eq 'inconclusive' -and $launchResult.reason -like 'Owned token child exceeded55seconds*'));exit_code=$(if($normal){$launchResult.child_exit_code}else{$null});ready_line=$actualOut.Contains('READY http://127.0.0.1:');attempt_marked=($null -ne $attempt);instrument_failure=$childFailed;save_existed_before=$false;save_exists_after=$saveExists;save_bytes_after=$(if($saveExists){(Get-Item -LiteralPath $save).Length}else{0});save_sha256_after=$(if($saveExists){(Get-FileHash -Algorithm SHA256 -LiteralPath $save).Hash.ToLowerInvariant()}else{$null})}
    Write-Json (Join-Path $Output 'child-result.json') $child
    $outcome='inconclusive'
    if($normal -and $valid -and $null -ne $attempt -and -not $childFailed -and (Test-Path -LiteralPath $stdoutPath) -and (Test-Path -LiteralPath $stderrPath)) {
        if($null -ne $observed -and $child.ready_line -and $child.exit_code -eq 0) { $outcome='baseline_started_and_expired' }
        elseif($null -eq $observed -and -not $child.ready_line -and $child.exit_code -is [long] -and $child.exit_code -ne 0) { $outcome='baseline_refused' }
        elseif($null -eq $observed -and -not $child.ready_line -and $child.exit_code -is [int] -and $child.exit_code -ne 0) { $outcome='baseline_refused' }
    }
    foreach($name in $inputs.Keys) { if((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Bundle $name)).Hash.ToLowerInvariant() -ne $inputs[$name]) { throw 'Original baseline identity changed during assessment.' } }
    Write-Json (Join-Path $Output 'baseline-result.json') @{ outcome=$outcome;token_boundary_valid=$valid;token=$token;parent_token=$parent;recipient_launcher_token=$recipient;http_observed=($null -ne $observed);child=$child;launcher_exit_code=$(if($finished){$process.ExitCode}else{$null});inputs_sha256=$inputs;network_errors=$networkErrors;scope='Actual hosted restricted/linked-limited same-user Windows token only; elevated flag is recorded unchanged. Actual restricted PowerShell invokes original script directly; native app token inheritance is inferred, not independently queried. No Windows10/11 physical device, independent participant or broad ordinary-user/non-elevated claim.' }
    Write-Output $outcome
    if($outcome -eq 'inconclusive'){exit 2};exit 0
} finally { $http.Dispose();$handler.Dispose();$process.Dispose() }

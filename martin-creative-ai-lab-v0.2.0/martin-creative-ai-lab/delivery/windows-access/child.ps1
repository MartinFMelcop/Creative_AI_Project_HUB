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
    if ($token.administrator -or -not $token.medium_integrity -or -not $token.administrator_sid_deny_only) { throw 'Child token does not meet the predeclared restricted non-administrator/medium/deny-only boundary.' }
    # Observe the actual PowerShell process that will invoke the unchanged script.
    & $runtime $Launcher '--identity-pid' ([string]$PID) (Join-Path $Output 'recipient-launcher-token.json')
    if ($LASTEXITCODE -ne 0) { throw 'Actual restricted PowerShell token query failed.' }
    $empty=Join-Path $Output 'empty PATH';[IO.Directory]::CreateDirectory($empty) | Out-Null
    $saveConfig=Join-Path $Output 'save-directory.txt'
    $saves=$(if(Test-Path -LiteralPath $saveConfig){[IO.Path]::GetFullPath([IO.File]::ReadAllText($saveConfig).Trim())}else{Join-Path $Output 'child saves'})
    [IO.Directory]::CreateDirectory($saves) | Out-Null
    $save=Join-Path $saves 'scene.json'
    if(Test-Path -LiteralPath (Join-Path $Output 'resume.flag')) {
        if(-not (Test-Path -LiteralPath $save -PathType Leaf)) { throw 'Explicit resume requires the existing actual save; never create a replacement.' }
    } elseif(Test-Path -LiteralPath $save) { throw 'Fresh attempt refuses existing data; use explicit resume.' }
    $port=[IO.File]::ReadAllText((Join-Path $Output 'port.txt')).Trim()
    $env:PATH=$empty;$env:NORTH_STAR_SAVE_DIR=$saves
    $env:DOTNET_ROOT='Z:\unavailable';$env:DOTNET_ROOT_X64='Z:\unavailable';$env:DOTNET_MULTILEVEL_LOOKUP='0'
    Write-Json (Join-Path $Output 'child-start.json') @{ pid=$PID;launcher_pid=$PID;port=$port;save=$save;save_existed_before=(Test-Path -LiteralPath $save);token_boundary_valid=$true;invocation='direct unchanged script in existing restricted PowerShell';scope='The actual PowerShell token is queried; nested native dotnet inherits through the unchanged direct invocation. Its token is not independently queried. Elevated flag is retained, never relabeled non-elevated.' }
    # Do not create another PowerShell or change any ACL/policy. The baseline owns exit.
    & (Join-Path $Bundle 'run-demo.ps1') $port '20'
    exit $LASTEXITCODE
} catch {
    Write-Json (Join-Path $Output 'child-failure.json') @{ status='inconclusive';error=$_.Exception.Message }
    [Console]::Error.WriteLine($_.Exception.Message);exit 2
}

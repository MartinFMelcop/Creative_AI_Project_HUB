param([string]$Port='8768', [string]$Seconds='300')
$ErrorActionPreference='Stop'
try {
    if ($args.Count -ne 0 -or $Port -notmatch '^[1-9][0-9]{3,4}$' -or [int]$Port -lt 1024 -or [int]$Port -gt 65535 -or $Seconds -notmatch '^[1-9][0-9]{0,2}$' -or [int]$Seconds -gt 600) { throw 'Usage: run-demo.ps1 [PORT 1024..65535] [SECONDS 1..600], without leading zeroes.' }
    function Assert-Unlinked([string]$Path) {
        $current=[IO.Path]::GetFullPath($Path)
        while ($current) {
            if (Test-Path -LiteralPath $current) {
                $item=Get-Item -Force -LiteralPath $current
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked or reparse paths are unsupported.' }
            }
            $parent=[IO.Path]::GetDirectoryName($current)
            if ($parent -eq $current) { break };$current=$parent
        }
    }
    $bundle=[IO.Path]::GetFullPath($PSScriptRoot)
    Assert-Unlinked $bundle
    $manifest=Join-Path $bundle 'payload.sha256'
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw 'Missing payload inventory.' }
    $declared=@{}
    foreach ($line in [IO.File]::ReadAllLines($manifest)) {
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') { throw 'Malformed payload inventory.' }
        $hash=$Matches[1];$name=$Matches[2]
        if ($name -match '[:\\]' -or $name.StartsWith('/') -or @($name.Split('/') | Where-Object { $_ -in @('','..','.') }).Count -gt 0) { throw 'Unsafe payload path.' }
        if ($name -eq 'payload.sha256' -or $declared.ContainsKey($name)) { throw 'Duplicate/recursive inventory.' }
        $declared[$name]=$hash
    }
    $observed=@{}
    # Enumerate one level at a time: never follow a reparse directory recursively.
    $pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($bundle)
    while ($pending.Count -gt 0) {
        foreach ($item in Get-ChildItem -Force -LiteralPath $pending.Dequeue()) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked payload is unsupported.' }
            if ($item.PSIsContainer) { $pending.Enqueue($item.FullName);continue }
            $name=$item.FullName.Substring($bundle.Length+1).Replace('\','/')
            if ($name -eq 'payload.sha256') { continue }
            $observed[$name]=(Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName).Hash.ToLowerInvariant()
        }
    }
    if ($observed.Count -ne $declared.Count) { throw 'Exact extracted inventory differs.' }
    foreach ($name in $declared.Keys) { if (-not $observed.ContainsKey($name) -or $observed[$name] -ne $declared[$name]) { throw "Missing or changed payload: $name" } }
    foreach ($name in @('runtime/dotnet.exe','runtime/LICENSE.txt','runtime/ThirdPartyNotices.txt','app/NorthStar.AuthoredScene.dll','web/index.html')) { if (-not $declared.ContainsKey($name)) { throw 'Required runtime/application/notices missing.' } }
    $saveDir=$env:NORTH_STAR_SAVE_DIR
    if ([string]::IsNullOrEmpty($saveDir)) { $saveDir=Join-Path ([IO.Directory]::GetParent($bundle).FullName) 'NorthStarWindowsSaves' }
    if (-not [IO.Path]::IsPathFullyQualified($saveDir)) { throw 'NORTH_STAR_SAVE_DIR must be fully qualified.' }
    $saveDir=[IO.Path]::GetFullPath($saveDir)
    if ($saveDir.Equals($bundle,[StringComparison]::OrdinalIgnoreCase) -or $saveDir.StartsWith($bundle+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Saves must remain outside the immutable payload.' }
    Assert-Unlinked $saveDir
    if (-not (Test-Path -LiteralPath $saveDir)) { [IO.Directory]::CreateDirectory($saveDir) | Out-Null }
    if (-not (Test-Path -LiteralPath $saveDir -PathType Container)) { throw 'Save path is not a directory.' }
    Assert-Unlinked $saveDir
    $save=Join-Path $saveDir 'scene.json';Assert-Unlinked $save
    $mode='--new'
    if (Test-Path -LiteralPath $save) { if (-not (Test-Path -LiteralPath $save -PathType Leaf)) { throw 'Save must be a regular file.' };$mode='--resume' }
    $env:DOTNET_ROOT=Join-Path $bundle 'runtime';$env:DOTNET_ROOT_X64=$env:DOTNET_ROOT
    $env:DOTNET_MULTILEVEL_LOOKUP='0';$env:DOTNET_ROLL_FORWARD='Disable';$env:DOTNET_EnableDiagnostics='0';$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
    & (Join-Path $bundle 'runtime/dotnet.exe') (Join-Path $bundle 'app/NorthStar.AuthoredScene.dll') '--serve' $Port (Join-Path $bundle 'web') '--seconds' $Seconds $mode $save
    exit $LASTEXITCODE
} catch { [Console]::Error.WriteLine('Cannot start demo: '+$_.Exception.Message);exit 1 }

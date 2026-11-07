$base = [System.IO.Path]::GetFullPath('C:/Users/arthu/Documents/Vlerick/1_Courses/MDP/group_assignment/data')
$manifest = Get-Content -LiteralPath (Join-Path (Split-Path $base) 'pipeline/source_manifest.json') -Raw | ConvertFrom-Json
foreach ($entry in $manifest) {
    $original = [System.IO.Path]::GetFullPath((Join-Path $base $entry.source))
    $snapshot = [System.IO.Path]::GetFullPath((Join-Path (Split-Path $base) $entry.bronze_raw))
    if (-not $original.StartsWith($base + [System.IO.Path]::DirectorySeparatorChar)) { throw 'Original outside data' }
    if (-not $snapshot.StartsWith((Join-Path $base 'bronze/raw') + [System.IO.Path]::DirectorySeparatorChar)) { throw 'Snapshot outside bronze/raw' }
    if (Test-Path -LiteralPath $original -PathType Leaf) {
        $a = (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash
        $b = (Get-FileHash -LiteralPath $snapshot -Algorithm SHA256).Hash
        if ($a -ne $b -or $b -ne $entry.sha256) { throw "Hash mismatch: $original" }
        Remove-Item -LiteralPath $original
    }
}
foreach ($name in @('Road accidents', 'Road casualties', 'Traffic accidents by type of vehicle')) {
    $folder = Join-Path $base $name
    if ((Test-Path -LiteralPath $folder) -and @(Get-ChildItem -LiteralPath $folder -Force).Count -eq 0) { Remove-Item -LiteralPath $folder }
}

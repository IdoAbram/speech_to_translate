# Verify that the candidate is unchanged before testing or publishing it.
param([string]$Directory = 'dist')
$ErrorActionPreference = 'Stop'
$checksum = Get-Content (Join-Path $Directory 'SHA256SUMS.txt') -Raw
if ($checksum -notmatch '^([a-fA-F0-9]{64})  SongWords\.exe\s*$') {
    throw 'Invalid release checksum file'
}
$expected = $Matches[1]
$actual = (Get-FileHash (Join-Path $Directory 'SongWords.exe') -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw 'SongWords.exe checksum mismatch' }
Write-Output "Verified SongWords.exe: $actual"

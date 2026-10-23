# Validate workflow syntax using a checksum-pinned actionlint release.
$ErrorActionPreference = 'Stop'
$version = '1.7.12'
$archive = Join-Path $env:RUNNER_TEMP 'actionlint.zip'
$destination = Join-Path $env:RUNNER_TEMP 'actionlint'
$url = "https://github.com/rhysd/actionlint/releases/download/v$version/actionlint_${version}_windows_amd64.zip"
Invoke-WebRequest $url -OutFile $archive
$expected = '6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9'
if ((Get-FileHash $archive -Algorithm SHA256).Hash -ne $expected) {
    throw 'actionlint download checksum mismatch'
}
Expand-Archive $archive -DestinationPath $destination -Force
& (Join-Path $destination 'actionlint.exe') -color
if ($LASTEXITCODE) { exit $LASTEXITCODE }

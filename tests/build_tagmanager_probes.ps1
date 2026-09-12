param([string]$TagManagerRoot = 'D:\github\TagManager')
$ErrorActionPreference = 'Stop'
$probeRoot = Split-Path -Parent $PSScriptRoot
$probeOut = Join-Path $probeRoot 'local\tagmanager-tests'
New-Item -ItemType Directory -Force -Path $probeOut | Out-Null
$compiler = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$tagRefs = Join-Path $TagManagerRoot 'TagManager\max_2025_dlls'
$wpfRefs = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF'
& $compiler /nologo "/out:$probeOut\ArchitecturePriorsTest.exe" "$PSScriptRoot\ArchitecturePriorsTest.cs" "$TagManagerRoot\TagManager\ArchitecturalSuggestions.cs"
if ($LASTEXITCODE -ne 0) { throw 'Geometry test compilation failed' }
& "$probeOut\ArchitecturePriorsTest.exe"
if ($LASTEXITCODE -ne 0) { throw 'Geometry tests failed' }
& $compiler /nologo /target:library "/out:$probeOut\FastTagLiveProbe.dll" "/r:$tagRefs\TagManager.dll" "/r:$tagRefs\dragonz.actb.dll" "/r:$tagRefs\Autodesk.Max.dll" "/r:$wpfRefs\PresentationFramework.dll" "/r:$wpfRefs\PresentationCore.dll" "/r:$wpfRefs\WindowsBase.dll" /r:System.Web.Extensions.dll /r:System.Xaml.dll "$PSScriptRoot\FastTagLiveProbe.cs"
if ($LASTEXITCODE -ne 0) { throw 'Live probe compilation failed' }
Write-Output "Live probe: $probeOut\FastTagLiveProbe.dll"

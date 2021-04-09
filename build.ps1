Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\' -Name 'LongPathsEnabled' -Value 1
New-Item -Path C:\tmp -ItemType directory
$env:TMPDIR = 'C:\tmp'

Install-PackageProvider -Name NuGet -Force
Install-Module -Name VcRedist -Force
Import-Module -Name VcRedist
$VcList = Get-VcList -Release 2019 -Architecture x64
Save-VcRedist -Path C:\tmp -VcList $VcList
Install-VcRedist -Path C:\tmp -VcList $VcList

pip install -r requirements.txt
pip install pyinstaller
pip install gooey
pyinstaller raw2aif_gui.spec
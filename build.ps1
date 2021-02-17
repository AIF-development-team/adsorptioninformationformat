Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\' -Name 'LongPathsEnabled' -Value 1

Install-PackageProvider -Name NuGet -Force
Install-Module -Name VcRedist -Force
Import-Module -Name VcRedist
New-Item -Path C:\VcRedist -ItemType directory
$VcList = Get-VcList -Release 2019 -Architecture x64
Save-VcRedist -Path C:\VcRedist -VcList $VcList
Install-VcRedist -Path C:\VcRedist -VcList $VcList

pip install -r requirements.txt
pip install pyinstaller
pip install gooey
pyinstaller raw2aif_gui.spec
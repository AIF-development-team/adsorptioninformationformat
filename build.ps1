Install-Module -Name VcRedist
Import-Module -Name VcRedist
$VcList = Get-VcList -Release 2019 -Architecture x64
Save-VcRedist -Path C:\Temp\VcRedist -VcList $VcList
Install-VcRedist -Path C:\Temp\VcRedist -VcList $VcList

pip install -r requirements.txt
pip install pyinstaller
pyinstaller raw2aif_gui.spec
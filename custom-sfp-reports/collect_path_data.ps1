#a connection to VPN is required for this script to run properly

$OneDrive = "C:\Users\$($env:USERNAME)\OneDrive - Government of BC"
$SavePath = "C:\Users\$($env:USERNAME)\OneDrive - Government of BC\Optimize"
$SaveName = "path_report_$(Get-Date -format yyyy-MM-dd_HHmm)"

if (Test-Path -Path $OneDrive) {

    # Create folder if does not exist
    if (!(Test-Path -Path $SavePath)) {
        $paramNewItem = @{
            Path     = $SavePath
            ItemType = 'Directory'
            Force    = $true
        }

        New-Item @paramNewItem
    }

    Write-Host "This script is intended to help collect data usage information from your chosen folder and store it in OneDrive, you must have a VPN connection and have OneDrive enabled/installed. Do you wish to proceed?" -NoNewline
    $proceed = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
    $proceed = Read-Host

    if ($proceed -eq 'y') {
        Do {
            $Path = Write-Host "Input pathname, including the drive letter or use full network path. If your pathname has spaces, put quotation marks around the entire path : " -NoNewline
            $Path = Read-Host

            # Loop if Path check fails
            if (!(Test-Path -Path $Path)) {
                do {
                    Write-Host -ForegroundColor Red "Could not connect to $Path. Path may not exist, VPN might be disconnected, or security groups could be restricting access."
                    $Path = Write-Host "Input pathname, including the drive letter or use full network path. If your pathname has spaces, put quotation marks around the entire path : " -NoNewline
                    $Path = Read-Host    
                } until (Test-Path -Path $Path)
            }
            
            Write-Host "You input the path name '$Path'. Is this correct?"
            $correct = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
            $correct = Read-Host
        }
        while ($correct -ne "y")

        Write-Host -ForegroundColor Yellow -BackgroundColor Black "`nCompiling data and writing it to a .csv file. This may take a few minutes or up to a few hours, depending on the folder size. Please keep this window running in the background until completed.`n"
        Get-ChildItem -Path $Path -Recurse -Force | Where-Object { !$_.PSIsContainer } | Select-Object DirectoryName, Name, Extension, Length, CreationTime, LastAccessTime, LastWriteTime | Export-Csv $SavePath\$SaveName.csv -En  UTF8 -NoType -Delim ','
        
        if ($lastexitcode -gt 0) {
            write-host "PowerShell exit code:" $lastexitcode
        }
        else {
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your folder report has been created and saved to OneDrive in the Optimize folder. Verify the file creation was successful, then send your .csv file for processing to IITD.Optimize@gov.bc.ca at your earliest convenience. Please remember to remove any transitory email attachments from your sent folder afterwards" 
        }
    }
}

Else { "Please enable OneDrive before running this script" }
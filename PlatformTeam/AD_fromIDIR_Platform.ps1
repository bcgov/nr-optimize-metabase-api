# You may need to install the Active Directory PowerShell module if you do not already have them. 
# Run as Administrator if you need to install modules and say "yes" to any prompts.
# After the modules are installed, you can put a "#" in front of the command line(s) to avoid installing them unnecessarily each time you run this code.

# Install-Module -Name ActiveDirectory
$PSDefaultParameterValues['*-AD*:Server'] = 'IDIR' # you absolutley need this line if you're using Windows 11, or the AD portion will fail

$SaveLocation = "C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\"
$SaveFile = "PlatformTeam_LookupTable"
$NameFile = Import-Csv "C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv" | Select -ExpandProperty "IDIR Account" | Sort-Object -unique 


function Get-ADNamebyIDIR {
    [alias ("gadi")]
    param (
        
        [String[]]$idirs
    )
    Import-Module ActiveDirectory
    foreach ($idir in $idirs) { 
        Write-Host -ForegroundColor Yellow "`nPulling AD info for $idir...`n"   
        Get-ADUser -filter {SamAccountName -eq $idir} -Properties * | 
        Select-Object -Property @{N='IDIR'; E={$_.SamAccountName}}, @{N='DisplayName'; E={$_.Name}}, @{N='Email'; E={$_.UserPrincipalName}} | 
        Sort-Object Name |
        Export-Csv -Path $SaveLocation\$SaveFile.csv -NoTypeInformation -Append
    }
}

# Function now runs against the variable of user names.  
gadi -idirs $NameFile

Write-Host -ForegroundColor Yellow "`nYour file $SaveFile has been saved to $SaveLocation. Thank you!`n"



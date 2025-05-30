# License Usage Analyzer

A web application that analyzes user license usage by identifying users who haven't logged in for 60 days or more.

## Features

- Upload CSV files containing user data
- Analyze user login activity
- Group results by license type
- Modern, responsive user interface
- Drag-and-drop file upload support

## CSV File Format

The application expects a CSV file with the following columns:
- UserPrincipalName
- DisplayName
- License
- LastLoginDate

Example CSV format:
```csv
UserPrincipalName,DisplayName,License,LastLoginDate
user1@example.com,John Doe,Office 365 E3,2024-01-01
user2@example.com,Jane Smith,Office 365 E5,2024-02-15
```
To generate report from Microsoft Azure AD using MgGraph:

Connect-MgGraph -Scopes "Directory.Read.All", "AuditLog.Read.All" --NoWelcome

$Users = Get-MgUser -All -Select "UserPrincipalName, DisplayName, SignInActivity"

$userReport = @()

foreach ($user in $Users) {
    $LastLoginDate = $user.SignInActivity.LastSignInDateTime

    $licenses = Get-MgUserLicenseDetail -UserId $user.Id
    $licenseNames = ($licenses.SkuPartNumber) -join "; "

    $userReport += [PSCustomObject]@{
        UserPrincipalName = $user.UserPrincipalName;
        DisplayName = $user.DisplayName;
        License = $licenseNames;
        LastLoginDate = $LastLoginDate;
    }
}

$userREport | Export-Csv -Path "C:\Users" -NoTypeInformation

## Setup

1. Install Python 3.8 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Prepare your CSV file with the required columns
2. Open the web application
3. Drag and drop your CSV file or click to select it
4. Click "Analyze Data" to process the file
5. View the results grouped by license type

## Security

- The application only accepts CSV files
- Uploaded files are automatically deleted after processing
- File names are sanitized before processing 
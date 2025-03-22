# S3Operations Module - Usage Guide

## Installation Instructions

### Method 1: Direct Import (Temporary)
1. Save both files (`S3Operations.psm1` and `S3Operations.psd1`) to the same directory
2. Import the module with:
```powershell
Import-Module -Path "C:\path\to\S3Operations.psd1" -Force
```

### Method 2: Install to PowerShell Modules Directory (Permanent)
1. Create a folder named "S3Operations" in one of your PSModulePath locations:
```powershell
# View your module paths
$env:PSModulePath -split ';'

# Create module directory (using the personal modules path as an example)
$modulePath = "$env:USERPROFILE\Documents\WindowsPowerShell\Modules\S3Operations"
New-Item -Path $modulePath -ItemType Directory -Force

# Copy files to the new directory
Copy-Item -Path "C:\path\to\S3Operations.psm1" -Destination $modulePath
Copy-Item -Path "C:\path\to\S3Operations.psd1" -Destination $modulePath
```

2. Import the module:
```powershell
Import-Module S3Operations
```

## Usage Examples

### List Objects in a Bucket
```powershell
$params = @{
    Endpoint = "s3-uat1.object.example.net:8443"
    BucketName = "my-bucket-name"
    AccessKey = "your-access-key"
    SecretKey = "your-secret-key"
    Region = "us-east-1"  # Optional, defaults to us-east-1
    Prefix = "folder/"    # Optional, defaults to empty (root)
}

$objects = Get-S3Object @params
$objects.Contents  # List all objects
```

### Download an Object
```powershell
$params = @{
    Endpoint = "s3-uat1.object.example.net:8443"
    BucketName = "my-bucket-name"
    ObjectKey = "folder/myfile.txt"
    OutputPath = "C:\Downloads\myfile.txt"
    AccessKey = "your-access-key"
    SecretKey = "your-secret-key"
}

Download-S3Object @params
```

### Upload an Object
```powershell
$params = @{
    Endpoint = "s3-uat1.object.example.net:8443"
    BucketName = "my-bucket-name"
    ObjectKey = "folder/newfile.txt"
    FilePath = "C:\Files\myfile.txt"
    AccessKey = "your-access-key"
    SecretKey = "your-secret-key"
    ContentType = "text/plain"  # Optional, defaults to application/octet-stream
}

Upload-S3Object @params
```

### Download All Objects in a Bucket
```powershell
# First, list all objects
$listParams = @{
    Endpoint = "s3-uat1.object.example.net:8443"
    BucketName = "my-bucket-name"
    AccessKey = "your-access-key"
    SecretKey = "your-secret-key"
}

$objects = Get-S3Object @listParams

# Then download each object
foreach ($object in $objects.Contents) {
    $objectKey = $object.Key
    $outputPath = "C:\Downloads\$($object.Key.Replace('/', '-'))"
    
    $downloadParams = @{
        Endpoint = $listParams.Endpoint
        BucketName = $listParams.BucketName
        ObjectKey = $objectKey
        OutputPath = $outputPath
        AccessKey = $listParams.AccessKey
        SecretKey = $listParams.SecretKey
    }
    
    Download-S3Object @downloadParams
}
```

## Notes
- All functions support the common parameter `-Verbose` for detailed logging.
- Ensure your PowerShell execution policy allows running scripts:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

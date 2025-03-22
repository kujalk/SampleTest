function Get-S3Object {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$Endpoint,

        [Parameter(Mandatory=$true)]
        [string]$BucketName,

        [Parameter(Mandatory=$true)]
        [string]$AccessKey,

        [Parameter(Mandatory=$true)]
        [string]$SecretKey,

        [Parameter(Mandatory=$false)]
        [string]$Region = "us-east-1",

        [Parameter(Mandatory=$false)]
        [string]$Prefix = ""
    )

    # Request details
    $httpMethod = "GET"
    $canonicalUri = "/$BucketName/"
    $canonicalQueryString = "delimiter=%2F&encoding-type=url&list-type=2&prefix=$Prefix"
    $service = "s3"
    
    # Create date and time strings
    $amzDate = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $dateStamp = $amzDate.Substring(0, 8)
    
    # Empty body hash for GET request
    $emptyBodyHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Create canonical headers
    $canonicalHeaders = "host:$Endpoint`n"
    $canonicalHeaders += "x-amz-content-sha256:$emptyBodyHash`n"
    $canonicalHeaders += "x-amz-date:$amzDate`n"
    
    # Create signed headers string
    $signedHeaders = "host;x-amz-content-sha256;x-amz-date"
    
    # Create canonical request
    $canonicalRequest = "$httpMethod`n$canonicalUri`n$canonicalQueryString`n$canonicalHeaders`n$signedHeaders`n$emptyBodyHash"
    
    # Create hashed canonical request
    $hashedCanonicalRequest = Get-SHA256Hash -Data $canonicalRequest
    
    # Create string to sign
    $algorithm = "AWS4-HMAC-SHA256"
    $credentialScope = "$dateStamp/$Region/$service/aws4_request"
    $stringToSign = "$algorithm`n$amzDate`n$credentialScope`n$hashedCanonicalRequest"
    
    # Calculate signature
    $kSecret = [System.Text.Encoding]::UTF8.GetBytes("AWS4$SecretKey")
    $kDate = Get-HMACSHA256 -Key $kSecret -Data $dateStamp
    $kRegion = Get-HMACSHA256 -Key $kDate -Data $Region
    $kService = Get-HMACSHA256 -Key $kRegion -Data $service
    $kSigning = Get-HMACSHA256 -Key $kService -Data "aws4_request"
    $signature = Get-HMACSHA256Hash -Key $kSigning -Data $stringToSign
    
    # Create authorization header
    $authHeader = "$algorithm Credential=$AccessKey/$dateStamp/$Region/$service/aws4_request, SignedHeaders=$signedHeaders, Signature=$signature"
    
    # Create URL with query parameters
    $uri = "https://$Endpoint/$BucketName/?$canonicalQueryString"
    
    # Set request headers
    $headers = @{
        "Host" = $Endpoint
        "X-Amz-Date" = $amzDate
        "X-Amz-Content-SHA256" = $emptyBodyHash
        "Authorization" = $authHeader
    }
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method $httpMethod
        return $response
    }
    catch {
        Write-Error "Error: $_"
        if ($_.Exception.Response) {
            $responseStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($responseStream)
            $responseBody = $reader.ReadToEnd()
            Write-Error "Response Body: $responseBody"
        }
        return $null
    }
}

function Download-S3Object {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$Endpoint,

        [Parameter(Mandatory=$true)]
        [string]$BucketName,

        [Parameter(Mandatory=$true)]
        [string]$ObjectKey,

        [Parameter(Mandatory=$true)]
        [string]$OutputPath,

        [Parameter(Mandatory=$true)]
        [string]$AccessKey,

        [Parameter(Mandatory=$true)]
        [string]$SecretKey,

        [Parameter(Mandatory=$false)]
        [string]$Region = "us-east-1"
    )

    # Request details
    $httpMethod = "GET"
    $canonicalUri = "/$BucketName/$ObjectKey"
    $canonicalQueryString = ""
    $service = "s3"
    
    # Create date and time strings
    $amzDate = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $dateStamp = $amzDate.Substring(0, 8)
    
    # Empty body hash for GET request
    $emptyBodyHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Create canonical headers
    $canonicalHeaders = "host:$Endpoint`n"
    $canonicalHeaders += "x-amz-content-sha256:$emptyBodyHash`n"
    $canonicalHeaders += "x-amz-date:$amzDate`n"
    
    # Create signed headers string
    $signedHeaders = "host;x-amz-content-sha256;x-amz-date"
    
    # Create canonical request
    $canonicalRequest = "$httpMethod`n$canonicalUri`n$canonicalQueryString`n$canonicalHeaders`n$signedHeaders`n$emptyBodyHash"
    
    # Create hashed canonical request
    $hashedCanonicalRequest = Get-SHA256Hash -Data $canonicalRequest
    
    # Create string to sign
    $algorithm = "AWS4-HMAC-SHA256"
    $credentialScope = "$dateStamp/$Region/$service/aws4_request"
    $stringToSign = "$algorithm`n$amzDate`n$credentialScope`n$hashedCanonicalRequest"
    
    # Calculate signature
    $kSecret = [System.Text.Encoding]::UTF8.GetBytes("AWS4$SecretKey")
    $kDate = Get-HMACSHA256 -Key $kSecret -Data $dateStamp
    $kRegion = Get-HMACSHA256 -Key $kDate -Data $Region
    $kService = Get-HMACSHA256 -Key $kRegion -Data $service
    $kSigning = Get-HMACSHA256 -Key $kService -Data "aws4_request"
    $signature = Get-HMACSHA256Hash -Key $kSigning -Data $stringToSign
    
    # Create authorization header
    $authHeader = "$algorithm Credential=$AccessKey/$dateStamp/$Region/$service/aws4_request, SignedHeaders=$signedHeaders, Signature=$signature"
    
    # Create URL - note the different URL format for downloading an object
    $uri = "https://$Endpoint/$BucketName/$ObjectKey"
    
    # Set request headers
    $headers = @{
        "Host" = $Endpoint
        "X-Amz-Date" = $amzDate
        "X-Amz-Content-SHA256" = $emptyBodyHash
        "Authorization" = $authHeader
    }
    
    Write-Host "Downloading $ObjectKey to $OutputPath..."
    
    try {
        # We need to use Invoke-WebRequest instead of Invoke-RestMethod to download the file
        $response = Invoke-WebRequest -Uri $uri -Headers $headers -Method $httpMethod -OutFile $OutputPath
        Write-Host "Download complete! File saved to $OutputPath"
        return $true
    }
    catch {
        Write-Error "Error downloading file: $_"
        if ($_.Exception.Response) {
            $responseStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($responseStream)
            $responseBody = $reader.ReadToEnd()
            Write-Error "Response Body: $responseBody"
        }
        return $false
    }
}

function Upload-S3Object {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$Endpoint,

        [Parameter(Mandatory=$true)]
        [string]$BucketName,

        [Parameter(Mandatory=$true)]
        [string]$ObjectKey,

        [Parameter(Mandatory=$true)]
        [string]$FilePath,

        [Parameter(Mandatory=$true)]
        [string]$AccessKey,

        [Parameter(Mandatory=$true)]
        [string]$SecretKey,

        [Parameter(Mandatory=$false)]
        [string]$Region = "us-east-1",

        [Parameter(Mandatory=$false)]
        [string]$ContentType = "application/octet-stream"
    )

    # Check if file exists
    if (-not (Test-Path $FilePath)) {
        Write-Error "File not found: $FilePath"
        return $false
    }

    # Read file content
    $fileContent = [System.IO.File]::ReadAllBytes($FilePath)
    
    # Request details
    $httpMethod = "PUT"
    $canonicalUri = "/$BucketName/$ObjectKey"
    $canonicalQueryString = ""
    $service = "s3"
    
    # Create date and time strings
    $amzDate = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $dateStamp = $amzDate.Substring(0, 8)
    
    # Calculate SHA256 hash of the file content
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $contentHash = [System.BitConverter]::ToString($sha256.ComputeHash($fileContent)).Replace("-", "").ToLower()
    
    # Create canonical headers
    $canonicalHeaders = "content-type:$ContentType`n"
    $canonicalHeaders += "host:$Endpoint`n"
    $canonicalHeaders += "x-amz-content-sha256:$contentHash`n"
    $canonicalHeaders += "x-amz-date:$amzDate`n"
    
    # Create signed headers string
    $signedHeaders = "content-type;host;x-amz-content-sha256;x-amz-date"
    
    # Create canonical request
    $canonicalRequest = "$httpMethod`n$canonicalUri`n$canonicalQueryString`n$canonicalHeaders`n$signedHeaders`n$contentHash"
    
    # Create hashed canonical request
    $hashedCanonicalRequest = Get-SHA256Hash -Data $canonicalRequest
    
    # Create string to sign
    $algorithm = "AWS4-HMAC-SHA256"
    $credentialScope = "$dateStamp/$Region/$service/aws4_request"
    $stringToSign = "$algorithm`n$amzDate`n$credentialScope`n$hashedCanonicalRequest"
    
    # Calculate signature
    $kSecret = [System.Text.Encoding]::UTF8.GetBytes("AWS4$SecretKey")
    $kDate = Get-HMACSHA256 -Key $kSecret -Data $dateStamp
    $kRegion = Get-HMACSHA256 -Key $kDate -Data $Region
    $kService = Get-HMACSHA256 -Key $kRegion -Data $service
    $kSigning = Get-HMACSHA256 -Key $kService -Data "aws4_request"
    $signature = Get-HMACSHA256Hash -Key $kSigning -Data $stringToSign
    
    # Create authorization header
    $authHeader = "$algorithm Credential=$AccessKey/$dateStamp/$Region/$service/aws4_request, SignedHeaders=$signedHeaders, Signature=$signature"
    
    # Create URL
    $uri = "https://$Endpoint/$BucketName/$ObjectKey"
    
    # Set request headers
    $headers = @{
        "Content-Type" = $ContentType
        "Host" = $Endpoint
        "X-Amz-Date" = $amzDate
        "X-Amz-Content-SHA256" = $contentHash
        "Authorization" = $authHeader
    }
    
    Write-Host "Uploading $FilePath to $ObjectKey..."
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method $httpMethod -Body $fileContent
        Write-Host "Upload complete! File uploaded to $ObjectKey"
        return $true
    }
    catch {
        Write-Error "Error uploading file: $_"
        if ($_.Exception.Response) {
            $responseStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($responseStream)
            $responseBody = $reader.ReadToEnd()
            Write-Error "Response Body: $responseBody"
        }
        return $false
    }
}

# Helper functions
function Get-SHA256Hash {
    param (
        [string]$Data
    )
    
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Data))
    return [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
}

function Get-HMACSHA256 {
    param (
        [byte[]]$Key,
        [string]$Data
    )
    
    $hmacsha = New-Object System.Security.Cryptography.HMACSHA256
    $hmacsha.Key = $Key
    return $hmacsha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Data))
}

function Get-HMACSHA256Hash {
    param (
        [byte[]]$Key,
        [string]$Data
    )
    
    $hmacsha = New-Object System.Security.Cryptography.HMACSHA256
    $hmacsha.Key = $Key
    $hash = $hmacsha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Data))
    return [System.BitConverter]::ToString($hash).Replace("-", "").ToLower()
}

# Export functions
Export-ModuleMember -Function Get-S3Object, Download-S3Object, Upload-S3Object

function Get-S3Object {
    param (
        [string]$Endpoint,
        [string]$BucketName,
        [string]$AccessKey,
        [string]$SecretKey,
        [string]$Region = "us-east-1",
        [string]$Prefix = ""
    )

    # Request details
    $httpMethod = "GET"
    $canonicalUri = "/"
    $canonicalQueryString = "list-type=2&prefix=$Prefix&delimiter=%2F&encoding-type=url"
    $service = "s3"
    
    # Create date and time strings
    $amzDate = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $dateStamp = [DateTime]::UtcNow.ToString("yyyyMMdd")
    
    # Create canonical headers
    $canonicalHeaders = "host:$Endpoint`n"
    $canonicalHeaders += "x-amz-content-sha256:$($emptyBodyHash)`n"
    $canonicalHeaders += "x-amz-date:$amzDate`n"
    
    # Create signed headers string
    $signedHeaders = "host;x-amz-content-sha256;x-amz-date"
    
    # Create payload hash (empty for GET)
    $emptyBodyHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Create canonical request
    $canonicalRequest = "$httpMethod`n$canonicalUri`n$canonicalQueryString`n$canonicalHeaders`n$signedHeaders`n$emptyBodyHash"
    
    # Create string to sign
    $algorithm = "AWS4-HMAC-SHA256"
    $credentialScope = "$dateStamp/$Region/$service/aws4_request"
    $stringToSign = "$algorithm`n$amzDate`n$credentialScope`n$((Get-FileHash -InputStream ([System.IO.MemoryStream]::new([System.Text.Encoding]::UTF8.GetBytes($canonicalRequest))) -Algorithm SHA256).Hash.ToLower())"
    
    # Calculate signature
    $kSecret = [System.Text.Encoding]::UTF8.GetBytes("AWS4$SecretKey")
    $kDate = Get-HMACSHA256 -Key $kSecret -Data $dateStamp
    $kRegion = Get-HMACSHA256 -Key $kDate -Data $Region
    $kService = Get-HMACSHA256 -Key $kRegion -Data $service
    $kSigning = Get-HMACSHA256 -Key $kService -Data "aws4_request"
    $signature = (Get-HMACSHA256Hash -Key $kSigning -Data $stringToSign).ToLower()
    
    # Create authorization header
    $authHeader = "$algorithm Credential=$AccessKey/$credentialScope, SignedHeaders=$signedHeaders, Signature=$signature"
    
    # Create and send request
    $uri = "https://$Endpoint/?$canonicalQueryString"
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
        Write-Error "Response: $($_.Exception.Response)"
        return $null
    }
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

# Example usage
$endpoint = "s3-uat1.object.nanw.net:8443"
$bucketName = "your-bucket-name"
$accessKey = "your-access-key"
$secretKey = "your-secret-key"
$region = "us-east-1"  # Use the appropriate region
$prefix = ""

Get-S3Object -Endpoint $endpoint -BucketName $bucketName -AccessKey $accessKey -SecretKey $secretKey -Region $region -Prefix $prefix

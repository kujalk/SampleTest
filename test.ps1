function Get-S3Object {
    param (
        [string]$Endpoint,
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
    
    # Create date and time strings - use EXACT format as seen in Postman
    # Instead of calculating current time, let's use the same timestamp from Postman for debugging
    $amzDate = "20250318T130404Z"  # Replace with current time in production
    $dateStamp = $amzDate.Substring(0, 8)  # Extract date portion
    
    # Empty body hash for GET request
    $emptyBodyHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Create canonical headers - EXACT order matters
    $canonicalHeaders = "host:$Endpoint`n"
    $canonicalHeaders += "x-amz-content-sha256:$emptyBodyHash`n"
    $canonicalHeaders += "x-amz-date:$amzDate`n"
    
    # Create signed headers string
    $signedHeaders = "host;x-amz-content-sha256;x-amz-date"
    
    # Create canonical request
    $canonicalRequest = "$httpMethod`n$canonicalUri`n$canonicalQueryString`n$canonicalHeaders`n$signedHeaders`n$emptyBodyHash"
    
    # Debug canonical request
    Write-Host "Canonical Request (for debugging):"
    Write-Host $canonicalRequest.Replace("`n", "\n")
    
    # Create hashed canonical request
    $hashedCanonicalRequest = Get-SHA256Hash -Data $canonicalRequest
    
    # Create string to sign
    $algorithm = "AWS4-HMAC-SHA256"
    $credentialScope = "$dateStamp/$Region/$service/aws4_request"
    $stringToSign = "$algorithm`n$amzDate`n$credentialScope`n$hashedCanonicalRequest"
    
    # Debug string to sign
    Write-Host "String to Sign (for debugging):"
    Write-Host $stringToSign.Replace("`n", "\n")
    
    # Calculate signature
    $kSecret = [System.Text.Encoding]::UTF8.GetBytes("AWS4$SecretKey")
    $kDate = Get-HMACSHA256 -Key $kSecret -Data $dateStamp
    $kRegion = Get-HMACSHA256 -Key $kDate -Data $Region
    $kService = Get-HMACSHA256 -Key $kRegion -Data $service
    $kSigning = Get-HMACSHA256 -Key $kService -Data "aws4_request"
    $signature = Get-HMACSHA256Hash -Key $kSigning -Data $stringToSign
    
    # Debug signature
    Write-Host "Calculated Signature: $signature"
    
    # Create authorization header - Match EXACTLY the format shown in Postman
    $authHeader = "$algorithm Credential=$AccessKey/$dateStamp/$Region/$service/aws4_request, SignedHeaders=$signedHeaders, Signature=$signature"
    
    # Debug full authorization header
    Write-Host "Authorization Header:"
    Write-Host $authHeader
    
    # Create and send request
    $uri = "https://$Endpoint/?$canonicalQueryString"
    $headers = @{
        "Host" = $Endpoint
        "X-Amz-Date" = $amzDate
        "X-Amz-Content-SHA256" = $emptyBodyHash
        "Authorization" = $authHeader
    }
    
    # Debug final request
    Write-Host "Request URI: $uri"
    Write-Host "Request Headers:"
    $headers | Format-Table -AutoSize
    
    try {
        # For initial debugging, don't send the request yet
        Write-Host "Ready to send request. Continue? (Y/N)"
        $continue = Read-Host
        if ($continue -eq "Y") {
            $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method $httpMethod
            return $response
        }
        else {
            Write-Host "Request aborted for debugging"
        }
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

# Example usage
$endpoint = "s3-uat1.object.nanw.net:8443"
$accessKey = "your-access-key"
$secretKey = "your-secret-key"
$region = "us-east-1"  # Make sure this matches what your server expects
$prefix = ""

Get-S3Object -Endpoint $endpoint -AccessKey $accessKey -SecretKey $secretKey -Region $region -Prefix $prefix

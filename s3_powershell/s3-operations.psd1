@{
    RootModule = 'S3Operations.psm1'
    ModuleVersion = '1.0.0'
    GUID = 'a123e543-7ccd-4506-9e2d-f1e8b8d3b456'
    Author = 'Module Author'
    Description = 'S3 Operations module for interacting with S3-compatible object storage'
    PowerShellVersion = '5.1'
    FunctionsToExport = @('Get-S3Object', 'Download-S3Object', 'Upload-S3Object')
    PrivateData = @{
        PSData = @{
            Tags = @('S3', 'AWS', 'Storage')
            ProjectUri = ''
        }
    }
}

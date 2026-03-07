$apiKey = '4651e7ff360e49688db9ef06bedaad51'
$headers = @{'x-api-key' = $apiKey}
$response = Invoke-RestMethod -Uri 'https://api-v3.mbta.com/vehicles?include=route,stop,trip' -Headers $headers
if ($response.data.Count -gt 0) {
  $response.data[0] | ConvertTo-Json -Depth 10
} else {
  Write-Output "No data returned"
}

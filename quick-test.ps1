# Quick API Test - Simple curl equivalent tests
$BaseURL = "http://localhost:8000/api/v1"
$Results = @()

function Quick-Test {
    param([string]$Name, [string]$Method, [string]$Endpoint, [hashtable]$Headers)
    
    $url = "$BaseURL$Endpoint"
    try {
        $params = @{Uri = $url; Method = $Method; ContentType = "application/json"; ErrorAction = "Stop"}
        if ($Headers) { $params['Headers'] = $Headers }
        $r = Invoke-WebRequest @params
        return "[PASS] $Name - HTTP $($r.StatusCode)"
    } catch {
        return "[FAIL] $Name - $($_.Exception.Message)"
    }
}

# Run tests
Write-Output "====== API ENDPOINT TESTS ======"
Write-Output ""

Write-Output "TEST 1: Health Check"
Quick-Test -Name "Health" -Method "GET" -Endpoint "/health/"

Write-Output ""
Write-Output "TEST 2: API Root"
Quick-Test -Name "API Root" -Method "GET" -Endpoint "/"

Write-Output ""
Write-Output "TEST 3: Hotels List"
Quick-Test -Name "Hotels" -Method "GET" -Endpoint "/hotels/"

Write-Output ""
Write-Output "TEST 4: Offers List"
Quick-Test -Name "Offers" -Method "GET" -Endpoint "/offers/"

Write-Output ""
Write-Output "TEST 5: User Registration"
$body = @{username="testuser"; email="test@test.com"; password="Pass123!@#"; first_name="Test"; last_name="User"} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$BaseURL/auth/register/" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Output "[PASS] Registration - HTTP $($r.StatusCode)"
    $user = $r.Content | ConvertFrom-Json
    Write-Output "  User ID: $($user.id)"
} catch {
    Write-Output "[FAIL] Registration - $($_.Exception.Message)"
}

Write-Output ""
Write-Output "====== TEST COMPLETE ======"

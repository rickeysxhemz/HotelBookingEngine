# Hotel Booking Engine API Test Suite
# Tests all critical endpoints with curl-equivalent PowerShell commands

$BaseURL = "http://localhost:8000/api/v1"
$TestResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    $FullURL = "$BaseURL$Endpoint"
    Write-Host "`n════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "TEST: $Name" -ForegroundColor Yellow
    Write-Host "URL: $Method $FullURL" -ForegroundColor Gray
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    try {
        $params = @{
            Uri = $FullURL
            Method = $Method
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Headers.Count -gt 0) {
            $params['Headers'] = $Headers
        }
        
        if ($Body -and @("POST", "PUT", "PATCH") -contains $Method) {
            $params['Body'] = $Body
        }
        
        $response = Invoke-WebRequest @params
        $statusCode = $response.StatusCode
        $content = $response.Content | ConvertFrom-Json
        
        Write-Host "Status: $statusCode [PASS]" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Green
        $content | ConvertTo-Json -Depth 3
        
        $TestResults += @{
            Name = $Name
            Status = "PASS"
            Code = $statusCode
        }
        
        return $content
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        $errorMsg = $_.Exception.Message
        Write-Host "Status: $statusCode [FAIL]" -ForegroundColor Red
        Write-Host "Error: $errorMsg" -ForegroundColor Red
        
        try {
            $errorBody = $_.Exception.Response | ConvertFrom-Json
            Write-Host "Response:" -ForegroundColor Red
            $errorBody | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "Response: $($_.Exception.Response.Content)" -ForegroundColor Red
        }
        
        $TestResults += @{
            Name = $Name
            Status = "FAIL"
            Code = $statusCode
            Error = $errorMsg
        }
        
        return $null
    }
}

# ============================================
# SECTION 1: ROOT & HEALTH ENDPOINTS
# ============================================
Write-Host "`n`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   SECTION 1: ROOT & HEALTH ENDPOINTS              ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Magenta

Test-Endpoint -Name "API Health Check" -Method "GET" -Endpoint "/health/"
Test-Endpoint -Name "API Root" -Method "GET" -Endpoint "/"

# ============================================
# SECTION 2: AUTHENTICATION ENDPOINTS
# ============================================
Write-Host "`n`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   SECTION 2: AUTHENTICATION                        ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Magenta

# Test registration
$registerBody = @{
    username = "testuser_$(Get-Random)"
    email = "test_$(Get-Random)@example.com"
    password = "TestPassword123!@#"
    first_name = "Test"
    last_name = "User"
} | ConvertTo-Json

$registerResult = Test-Endpoint -Name "User Registration" -Method "POST" -Endpoint "/auth/register/" -Body $registerBody
$testUsername = $registerResult.username
$testEmail = $registerResult.email
$testUserID = $registerResult.id

# Test login
if ($registerResult) {
    $loginBody = @{
        username = $testUsername
        password = "TestPassword123!@#"
    } | ConvertTo-Json
    
    $loginResult = Test-Endpoint -Name "User Login" -Method "POST" -Endpoint "/auth/login/" -Body $loginBody
    $authToken = $loginResult.access
    
    if ($authToken) {
        # Test profile retrieval
        $authHeaders = @{ Authorization = "Bearer $authToken" }
        Test-Endpoint -Name "Get User Profile" -Method "GET" -Endpoint "/auth/profile/" -Headers $authHeaders
    }
}

# ============================================
# SECTION 3: HOTELS & ROOMS ENDPOINTS
# ============================================
Write-Host "`n`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   SECTION 3: HOTELS & ROOMS                        ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Magenta

$hotelsResult = Test-Endpoint -Name "List All Hotels" -Method "GET" -Endpoint "/hotels/"

if ($hotelsResult -and $hotelsResult.results.Count -gt 0) {
    $hotelID = $hotelsResult.results[0].id
    Write-Host "`nUsing Hotel ID: $hotelID" -ForegroundColor Gray
    
    # Hotel details
    Test-Endpoint -Name "Get Hotel Details" -Method "GET" -Endpoint "/hotels/$hotelID/"
    
    # Hotel rooms
    Test-Endpoint -Name "List Hotel Rooms" -Method "GET" -Endpoint "/hotels/$hotelID/rooms/"
    
    # Hotel availability
    Test-Endpoint -Name "Check Hotel Availability" -Method "GET" -Endpoint "/hotels/$hotelID/availability/"
    
    # Hotel amenities
    Test-Endpoint -Name "Get Hotel Amenities" -Method "GET" -Endpoint "/hotels/$hotelID/amenities/"
    
    # Hotel reviews
    Test-Endpoint -Name "Get Hotel Reviews" -Method "GET" -Endpoint "/hotels/$hotelID/reviews/"
}

# Hotel search
Test-Endpoint -Name "Search Hotels" -Method "GET" -Endpoint "/hotels/search/?search=hotel"
Test-Endpoint -Name "Featured Hotels" -Method "GET" -Endpoint "/hotels/featured/"

# ============================================
# SECTION 4: BOOKINGS ENDPOINTS
# ============================================
Write-Host "`n`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   SECTION 4: BOOKINGS                              ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Magenta

# List bookings (requires auth)
if ($authToken) {
    $authHeaders = @{ Authorization = "Bearer $authToken" }
    Test-Endpoint -Name "List User Bookings" -Method "GET" -Endpoint "/bookings/" -Headers $authHeaders
}

# Create booking (requires hotel and room)
if ($hotelID -and $authToken) {
    # Get a room from the hotel
    $roomsResponse = Invoke-WebRequest -Uri "$BaseURL/hotels/$hotelID/rooms/" -Method GET -ContentType "application/json" -ErrorAction SilentlyContinue
    if ($roomsResponse.StatusCode -eq 200) {
        $rooms = $roomsResponse.Content | ConvertFrom-Json
        if ($rooms.results.Count -gt 0) {
            $roomID = $rooms.results[0].id
            
            $bookingBody = @{
                room = $roomID
                check_in_date = (Get-Date).AddDays(5).ToString("yyyy-MM-dd")
                check_out_date = (Get-Date).AddDays(7).ToString("yyyy-MM-dd")
                number_of_guests = 2
                guest_email = $testEmail
                guest_phone = "+966501234567"
                guest_name = "Test Guest"
                special_requests = "Test booking"
            } | ConvertTo-Json
            
            $authHeaders = @{ Authorization = "Bearer $authToken" }
            $bookingResult = Test-Endpoint -Name "Create Booking" -Method "POST" -Endpoint "/bookings/create/" -Body $bookingBody -Headers $authHeaders
            
            # If booking created successfully, test other booking endpoints
            if ($bookingResult -and $bookingResult.id) {
                $bookingID = $bookingResult.id
                Write-Host "`nUsing Booking ID: $bookingID" -ForegroundColor Gray
                
                # Get booking details
                Test-Endpoint -Name "Get Booking Details" -Method "GET" -Endpoint "/bookings/$bookingID/" -Headers $authHeaders
                
                # Get booking audit history
                Test-Endpoint -Name "Get Booking Audit History" -Method "GET" -Endpoint "/bookings/$bookingID/audit-history/" -Headers $authHeaders
                
                # Test confirmation
                Test-Endpoint -Name "Confirm Booking" -Method "POST" -Endpoint "/bookings/$bookingID/confirm/" -Headers $authHeaders
                
                # Test cancellation
                $cancelBody = @{
                    reason = "Guest requested cancellation for testing"
                } | ConvertTo-Json
                Test-Endpoint -Name "Cancel Booking with Refund" -Method "POST" -Endpoint "/bookings/$bookingID/cancel/" -Body $cancelBody -Headers $authHeaders
            }
        }
    }
}

# ============================================
# SECTION 5: OFFERS ENDPOINTS
# ============================================
Write-Host "`n`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   SECTION 5: OFFERS                                ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Magenta

$offersResult = Test-Endpoint -Name "List All Offers" -Method "GET" -Endpoint "/offers/"
Test-Endpoint -Name "Featured Offers" -Method "GET" -Endpoint "/offers/featured/"
Test-Endpoint -Name "Search Offers" -Method "GET" -Endpoint "/offers/search/?search=discount"

if ($offersResult -and $offersResult.results.Count -gt 0) {
    $offerID = $offersResult.results[0].id
    Test-Endpoint -Name "Get Offer Details" -Method "GET" -Endpoint "/offers/$offerID/"
}

# ============================================
# TEST SUMMARY
# ============================================
Write-Host "`n`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   TEST SUMMARY                                    ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Green

$passCount = ($TestResults | Where-Object {$_.Status -eq "PASS"}).Count
$failCount = ($TestResults | Where-Object {$_.Status -eq "FAIL"}).Count
$totalCount = $TestResults.Count

Write-Host "`nTotal Tests: $totalCount"
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red

Write-Host "`nDetailed Results:`n" -ForegroundColor Yellow
$TestResults | Format-Table -AutoSize -Property Name, Status, Code

if ($failCount -gt 0) {
    Write-Host "`nFailed Tests Details:" -ForegroundColor Red
    $TestResults | Where-Object {$_.Status -eq "FAIL"} | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Error)" -ForegroundColor Red
    }
}

Write-Host "`n[COMPLETE] API Testing Finished!" -ForegroundColor Green

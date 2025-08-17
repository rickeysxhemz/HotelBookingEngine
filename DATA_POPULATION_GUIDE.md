# Hotel Booking Engine - Data Population Guide

## Single Comprehensive Data Population Command

The hotel booking engine now has **one unified command** that handles all data population needs with comprehensive room data.

## Command: `populate_sample_data`

### Basic Usage
```bash
# Create comprehensive sample data (default - recommended)
python manage.py populate_sample_data

# Clear existing data and create fresh comprehensive data
python manage.py populate_sample_data --clear

# Create minimal data set (for testing or development)
python manage.py populate_sample_data --minimal

# Create multiple hotels with comprehensive data
python manage.py populate_sample_data --hotels 3
```

### Command Options

#### `--clear`
- **Purpose**: Clear all existing hotel and booking data before creating new data
- **Use case**: Starting fresh or resetting the database
- **What it clears**: Hotels, Room Types, Rooms, Bookings, Images, Amenities (keeps user accounts)

#### `--minimal`
- **Purpose**: Create a smaller dataset for quick testing
- **Creates**: 
  - 2 hotels with basic information
  - Standard room types without enhanced features
  - Fewer rooms per hotel
  - Basic extras and services
  - Sample bookings

#### `--comprehensive` (default)
- **Purpose**: Create full comprehensive data with all enhanced features
- **Creates**:
  - 1 luxury hotel with complete information
  - 5 comprehensive room types with 50+ amenity fields
  - 53 rooms with detailed features
  - Room images and multimedia content
  - Enhanced amenities and services
  - Seasonal pricing rules
  - Sample bookings with various statuses

#### `--hotels [number]`
- **Purpose**: Specify number of hotels to create
- **Default**: 1 for comprehensive mode, 3 for basic mode
- **Example**: `--hotels 5` creates 5 hotels

### What Gets Created

#### Comprehensive Mode (Default)
1. **Enhanced Hotel**:
   - Grand Plaza Hotel & Spa (5-star luxury)
   - Complete contact information and policies
   - Professional hotel management setup

2. **12 Room Amenities**:
   - Smart Home Controls, Gaming Console, Butler Service
   - Executive Workspace, Business Center Access
   - Child Safety Kit, Baby Amenities
   - In-Room Spa Services, Premium Linens, etc.

3. **5 Comprehensive Room Types**:
   - **Standard Queen Room** (20 rooms) - $149/night
   - **Deluxe King Room** (15 rooms) - $199/night  
   - **Executive Suite** (8 rooms) - $399/night
   - **Accessible Standard Room** (4 rooms) - $149/night
   - **Family Suite** (6 rooms) - $299/night

4. **53 Individual Rooms** with:
   - Detailed specifications (size, bed type, capacity)
   - View types (City, Ocean, Mountain, Garden, etc.)
   - Special features (corner rooms, connecting rooms)
   - Condition tracking and housekeeping status
   - Maintenance management

5. **Room Images**:
   - Multiple images per room type
   - Categorized by type (overview, bed area, bathroom, view)
   - Individual room photos for specific rooms

6. **Enhanced Features**:
   - 50+ amenity fields per room type
   - Accessibility compliance features
   - Family and child policies
   - Business traveler amenities
   - Seasonal pricing rules
   - Sample booking history

#### Minimal Mode
1. **2 Basic Hotels**:
   - Standard hotel information
   - Basic contact details

2. **6 Basic Room Types**:
   - Standard Single, Double, Family, Suite types
   - Basic amenity tracking
   - Standard pricing

3. **Fewer Rooms**:
   - 3 rooms per floor, 2 floors per hotel
   - Basic view types and features

4. **Basic Services**:
   - 3 essential extras per hotel
   - Basic seasonal pricing

### Sample Data Includes

#### Users
- 1 Admin user: `admin@hotel.com` / `admin123`
- 9 Guest users: `guest1@example.com` through `guest9@example.com` / `guest123`

#### Bookings
- Past bookings (checked out)
- Future bookings (confirmed)
- Current bookings (checked in)
- Various booking statuses and payment states

#### Pricing
- Base room prices by category
- Seasonal pricing multipliers
- Weekend premiums
- Holiday season rates

### Best Practices

#### For Development
```bash
# Start with comprehensive data for full feature testing
python manage.py populate_sample_data --clear

# Quick testing with minimal data
python manage.py populate_sample_data --minimal --clear
```

#### For Demonstration
```bash
# Create impressive demo data
python manage.py populate_sample_data --clear

# Multiple hotels for comparison
python manage.py populate_sample_data --hotels 3 --clear
```

#### For API Testing
```bash
# Full dataset for comprehensive API testing
python manage.py populate_sample_data --clear

# Then access via:
# http://localhost:8000/api/v1/hotels/
# http://localhost:8000/api/v1/rooms/
# http://localhost:8000/admin/
```

### Database Impact

The comprehensive mode creates:
- **Complete room data** ready for production-like testing
- **Realistic pricing** with seasonal variations
- **Professional content** suitable for demonstrations
- **Full amenity tracking** for filtering and search
- **Image galleries** for rich user interfaces
- **Booking history** for analytics and reporting

### Performance Notes

- **Comprehensive mode**: Takes 10-15 seconds, creates ~150 database records
- **Minimal mode**: Takes 3-5 seconds, creates ~50 database records
- **Database size**: Comprehensive data uses approximately 2-3 MB
- **Memory usage**: Minimal impact during creation, efficient for ongoing use

### Integration Ready

All data created is fully integrated with:
- ✅ Django Admin interface
- ✅ REST API endpoints
- ✅ Booking system
- ✅ Search and filtering
- ✅ Pricing calculations
- ✅ User authentication
- ✅ Frontend applications

This single command provides everything needed to test, demonstrate, and develop with the hotel booking engine.

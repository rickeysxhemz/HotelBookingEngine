#!/bin/bash
# Development server startup script

echo "Starting Hotel Booking Engine Development Server..."
echo "========================================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠ Virtual environment not found. Please create one with:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate  # Linux/Mac"
    echo "  venv\\Scripts\\activate    # Windows"
    exit 1
fi

# Install dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if needed
echo "Creating superuser (skip if already exists)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start development server
echo "Starting development server..."
echo "Server will be available at: http://127.0.0.1:8000"
echo "Admin panel: http://127.0.0.1:8000/admin"
echo "API Documentation: Check docs/ folder"
echo "========================================"

python manage.py runserver

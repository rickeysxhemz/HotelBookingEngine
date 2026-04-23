from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import time

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for production monitoring
    """
    start_time = time.time()
    status = {"status": "healthy", "timestamp": time.time()}
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
    
    # Check cache (if configured)
    try:
        cache.set('health_check', 'ok', 30)
        cache_result = cache.get('health_check')
        status["cache"] = "connected" if cache_result == 'ok' else "error"
    except Exception as e:
        status["cache"] = f"error: {str(e)}"
    
    # Response time
    status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Return appropriate status code
    status_code = 200 if status["status"] == "healthy" else 503
    
    return Response(status, status=status_code)

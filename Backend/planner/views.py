from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services.hos_engine import plan_hos_trip

@api_view(['POST'])
def plan_trip_view(request):
    data = request.data
    try:
        result = plan_hos_trip(data.get('current_location'), data.get('pickup_location'), data.get('dropoff_location'), float(data.get('cycle_used', 0.0)))
        return Response(result, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

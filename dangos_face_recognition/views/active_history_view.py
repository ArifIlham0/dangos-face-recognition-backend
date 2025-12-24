from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..serializers import ActiveHistorySerializer
from ..models import ActiveHistory
    
@api_view(["POST"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def create_active_history(request):
    try:
        operating_system = request.data.get('operating_system')
        model = request.data.get('model')

        user_histories = ActiveHistory.objects.filter(custom_user=request.user).order_by('updated_at')
        total_history = user_histories.count()

        if total_history >= 20:
            delete_count = total_history - 20 + 1
            histories_to_delete = user_histories[:delete_count]
            histories_to_delete.delete()

        serializer = ActiveHistorySerializer(
            data={
                'custom_user': request.user.id,
                'operating_system': operating_system,
                'model': model,
            }
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Active history recorded successfully",
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsSuperUser])
def fetch_active_histories(request):
    try:
        page = int(request.GET.get('page'))
        page_size = int(request.GET.get('page_size'))
        query_param = request.GET.get("query", "").strip()

        active_histories = ActiveHistory.objects.all()
        
        if query_param:
            active_histories = active_histories.filter(operating_system__icontains=query_param) | active_histories.filter(model__icontains=query_param)
        
        active_histories = active_histories.order_by('-updated_at')
        active_history_serializer = ActiveHistorySerializer(active_histories, many=True)
        data = active_history_serializer.data
        start = (page - 1) * page_size
        end = start + page_size
        data = data[start:end]

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Active histories fetched successfully.",
            "total_item": len(data),
            "page": page,
            "page_size": page_size,
            "total_page": (active_histories.count() + page_size - 1) // page_size,
            "data": data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["GET"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def fetch_active_history_by_users(request):
    try:
        page = int(request.GET.get('page'))
        page_size = int(request.GET.get('page_size'))
        query_param = request.GET.get("query", "").strip()

        active_histories = ActiveHistory.objects.filter(custom_user=request.user)
        
        if query_param:
            active_histories = active_histories.filter(operating_system__icontains=query_param) | active_histories.filter(model__icontains=query_param)
        
        active_histories = active_histories.order_by('-updated_at')
        active_history_serializer = ActiveHistorySerializer(active_histories, many=True)
        data = active_history_serializer.data
        start = (page - 1) * page_size
        end = start + page_size
        data = data[start:end]

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Active histories fetched successfully.",
            "total_item": len(data),
            "page": page,
            "page_size": page_size,
            "total_page": (active_histories.count() + page_size - 1) // page_size,
            "data": data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
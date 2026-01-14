from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, viewsets
from ..models import ActiveHistory
from ..middlewares.permissions import IsSuperUser
from ..serializers import ActiveHistorySerializer
from ..middlewares.authentications import BearerTokenAuthentication
    
class ActiveHistoryViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in []:
            permission_classes = [AllowAny]
        elif self.action in ["list"]:
            permission_classes = [IsSuperUser]
        elif self.action in ["create", "retrieve", "fetch_active_history_by_users"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def create(self, request):
        try:
            operating_system = request.data.get('operating_system')
            model = request.data.get('model')

            user_histories = ActiveHistory.objects.filter(custom_user=request.user).order_by('updated_at')
            total_history = user_histories.count()

            if total_history >= 12:
                delete_count = total_history - 12 + 1
                histories_to_delete = user_histories[:delete_count]
                pk_list = [h.pk for h in histories_to_delete]
                ActiveHistory.objects.filter(pk__in=pk_list).delete()

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

    def list(self, request):
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

    def retrieve(self, request, pk=None):
        try:
            try:
                active_history = ActiveHistory.objects.get(pk=pk)
            except ObjectDoesNotExist:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Active history not found.",
                }, status=status.HTTP_404_NOT_FOUND)
            
            active_history_serializer = ActiveHistorySerializer(active_history)
            data = active_history_serializer.data

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Active history fetched successfully.",
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["get"], url_path="fetch")
    def fetch_active_history_by_users(self, request):
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
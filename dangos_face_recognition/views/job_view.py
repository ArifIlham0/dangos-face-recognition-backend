from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets
from ..models import Job
from ..serializers import JobSerializer
from ..middlewares.permissions import IsSuperUser
from ..middlewares.authentications import BearerTokenAuthentication
    
class JobViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["list"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in []:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]


    def list(self, request):
        try:
            page = int(request.GET.get('page'))
            page_size = int(request.GET.get('page_size'))
            query_param = request.GET.get("query", "").strip()

            jobs = Job.objects.all()
            
            if query_param:
                jobs = jobs.filter(title__icontains=query_param)
            
            jobs = jobs.order_by('title')
            job_serializer = JobSerializer(jobs, many=True)
            data = job_serializer.data
            start = (page - 1) * page_size
            end = start + page_size
            data = data[start:end]

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Jobs fetched successfully.",
                "total_item": len(data),
                "page": page,
                "page_size": page_size,
                "total_page": (jobs.count() + page_size - 1) // page_size,
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
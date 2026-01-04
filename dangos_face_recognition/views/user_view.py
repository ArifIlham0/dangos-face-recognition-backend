from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status, viewsets
from ..serializers import UserSerializer
from ..models import UserToken, RefreshToken
from ..middlewares.permissions import IsSuperUser
from ..middlewares.authentications import BearerTokenAuthentication

class UserViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["create"]:
            permission_classes = [AllowAny]
        elif self.action in ["delete_users"]:
            permission_classes = [IsSuperUser]
        elif self.action in ["list", "retrieve", "update"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def create(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            job = request.data.get('job')
            password = request.data.get('password')
            request_data = request.data.copy()
            request_data['username'] = username
            request_data['password'] = password

            serializer = UserSerializer(data=request_data)

            if serializer.is_valid():
                user = serializer.save()
                user.set_password(password)
                user.save()

                access = UserToken.objects.create(user=user)
                refresh = RefreshToken.objects.create(user=user)
                user_serializer = UserSerializer(instance=user, context={'request': request})
                data = user_serializer.data
                data['access_token'] = access.key
                data['refresh_token'] = refresh.key

                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Register successful",
                    "data": data,
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

            User = get_user_model()
            users = User.objects.all()
            
            if query_param:
                users = users.filter(email__icontains=query_param) | users.filter(first_name__icontains=query_param)
            
            users = users.order_by('-date_joined')
            user_serializer = UserSerializer(users, many=True)
            data = user_serializer.data
            start = (page - 1) * page_size
            end = start + page_size
            data = data[start:end]

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Users fetched successfully.",
                "total_item": len(data),
                "page": page,
                "page_size": page_size,
                "total_page": (users.count() + page_size - 1) // page_size,
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        try:
            User = get_user_model()
            user = User.objects.get(pk=pk)
            user_serializer = UserSerializer(user, context={'request': request})
            data = user_serializer.data

            return Response({
                "status": status.HTTP_200_OK,
                "message": "User fetched successfully.",
                "data": data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, pk=None):
        try:
            User = get_user_model()
            
            try:
                user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            request_data = request.data.copy()
            first_name = request_data.get("first_name")
            if first_name and isinstance(first_name, str):
                parts = first_name.strip().split()
                if len(parts) > 1:
                    request_data["first_name"] = parts[0]
                    request_data["last_name"] = " ".join(parts[1:])
                    
            serializer = UserSerializer(user, data=request_data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                updated_user = serializer.save()
                user_serializer = UserSerializer(instance=updated_user, context={'request': request})
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "User updated successfully",
                    "data": user_serializer.data,
                }, status=status.HTTP_200_OK)
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
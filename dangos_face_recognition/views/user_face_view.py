import os
import numpy as np
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.decorators import  action
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from deepface import DeepFace
from ..serializers import UserFaceSerializer
from ..middlewares.permissions import IsSuperUser
from ..middlewares.authentications import BearerTokenAuthentication

class UserFaceViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in []:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["create", "update", "verify_face"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def create(self, request):
        try:
            User = get_user_model()
            user = User.objects.get(id=request.user.id)
            image_file = request.FILES.get('image')

            if not image_file:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Image file is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            temp_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_enroll.jpg")
            with open(temp_path, "wb+") as f:
                for chunk in image_file.chunks():
                    f.write(chunk)

            embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name='Facenet',
                enforce_detection=False
            )[0]
            embedding_vector = embedding_obj["embedding"]
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if hasattr(user, "user_faces"):
                serializer = UserFaceSerializer(
                    instance=user.user_faces,
                    data={'embedding': embedding_vector, 'image': image_file},
                    partial=True
                )
            else:
                serializer = UserFaceSerializer(
                    data={
                        'custom_user': user.id,
                        'embedding': embedding_vector,
                        'image': image_file,
                    }
                )

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Face enrolled successfully",
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid data",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="verify")
    def verify_face(self, request):
        try:
            User = get_user_model()
            user = User.objects.get(id=request.user.id)
            image_file = request.FILES.get('image')

            if not image_file:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Image file is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not hasattr(user, "user_faces"):
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User has no enrolled face yet"
                }, status=status.HTTP_404_NOT_FOUND)

            temp_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_verify.jpg")
            with open(temp_path, "wb+") as f:
                for chunk in image_file.chunks():
                    f.write(chunk)

            new_embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name='Facenet',
                enforce_detection=False
            )[0]

            new_embedding = np.array(new_embedding_obj["embedding"])
            if os.path.exists(temp_path):
                os.remove(temp_path)
            saved_embedding = np.array(user.user_faces.embedding)
            cos_sim = np.dot(saved_embedding, new_embedding) / (
                np.linalg.norm(saved_embedding) * np.linalg.norm(new_embedding)
            )

            verified = cos_sim > 0.7
            confidence = round(cos_sim * 100, 2)

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Face verification result",
                "data": {
                    "verified": bool(verified),
                    "confidence": confidence,
                    "image_url": request.build_absolute_uri(user.user_faces.image.url)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        try:
            User = get_user_model()
            user = User.objects.get(pk=pk)
            image_file = request.FILES.get('image')

            if not image_file:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Image file is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not hasattr(user, "user_faces"):
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User has no enrolled face. Please enroll first."
                }, status=status.HTTP_404_NOT_FOUND)

            temp_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_update.jpg")
            with open(temp_path, "wb+") as f:
                for chunk in image_file.chunks():
                    f.write(chunk)

            embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name='Facenet',
                enforce_detection=False
            )[0]

            embedding_vector = embedding_obj["embedding"]

            if os.path.exists(temp_path):
                os.remove(temp_path)

            user_face = user.user_faces
            serializer = UserFaceSerializer(
                instance=user_face,
                data={
                    "embedding": embedding_vector,
                    "image": image_file
                },
                partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Face updated successfully"
                }, status=status.HTTP_200_OK)

            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from ..serializers import UserFaceSerializer, UserSerializer
from ..middlewares.permissions import IsSuperUser
from ..middlewares.authentications import BearerTokenAuthentication
from ..models import UserToken, RefreshToken
from ..utils.image_util import crop_center_square

class UserFaceViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["verify_face_not_authenticated"]:
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

            cropped_content = crop_center_square(image_file)
            cropped_file = SimpleUploadedFile(
                name=image_file.name,
                content=cropped_content,
                content_type=image_file.content_type
            )
            temp_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_enroll.jpg")
            with open(temp_path, "wb+") as f:
                f.write(cropped_content)

            try:
                embedding_objs = DeepFace.represent(
                    img_path=temp_path,
                    model_name='Facenet',
                    enforce_detection=True 
                )
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "No face detected in the camera"
                }, status=status.HTTP_400_BAD_REQUEST)

            embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name='Facenet',
                enforce_detection=False
            )[0]
            embedding_vector = embedding_obj["embedding"]
            if os.path.exists(temp_path):
                os.remove(temp_path)

            users = User.objects.all()
            for other_user in users:
                if hasattr(other_user, "user_faces") and other_user.id != user.id:
                    saved_embedding = np.array(other_user.user_faces.embedding)
                    new_embedding = np.array(embedding_vector)
                    cos_sim = np.dot(saved_embedding, new_embedding) / (
                        np.linalg.norm(saved_embedding) * np.linalg.norm(new_embedding)
                    )
                    confidence = round(cos_sim * 100, 2)
                    if confidence >= 80:
                        return Response({
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "This face already registered",
                            "confidence": confidence,
                            "user_id": other_user.id
                        }, status=status.HTTP_400_BAD_REQUEST)

            if hasattr(user, "user_faces"):
                serializer = UserFaceSerializer(
                    instance=user.user_faces,
                    data={'embedding': embedding_vector, 'image': cropped_file},
                    partial=True
                )
            else:
                serializer = UserFaceSerializer(
                    data={
                        'custom_user': user.id,
                        'embedding': embedding_vector,
                        'image': cropped_file,
                    }
                )

            access = UserToken.objects.create(user=user)
            refresh = RefreshToken.objects.create(user=user)
            user_serializer = UserSerializer(user, context={'request': request})
            data = user_serializer.data
            data['access_token'] = access.key
            data['refresh_token'] = refresh.key

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Face enrolled successfully",
                    "data": {
                        "is_verified": True,
                        "user": data,
                    }
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
            
            cropped_content = crop_center_square(image_file)
            cropped_file = SimpleUploadedFile(
                name=image_file.name,
                content=cropped_content,
                content_type=image_file.content_type
            )
            temp_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_verify.jpg")
            with open(temp_path, "wb+") as f:
                f.write(cropped_content)

            try:
                embedding_objs = DeepFace.represent(
                    img_path=temp_path,
                    model_name='Facenet',
                    enforce_detection=True 
                )
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "No face detected in the camera"
                }, status=status.HTTP_400_BAD_REQUEST)

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

            access = UserToken.objects.create(user=user)
            refresh = RefreshToken.objects.create(user=user)
            user_serializer = UserSerializer(user, context={'request': request})
            data = user_serializer.data
            data['access_token'] = access.key
            data['refresh_token'] = refresh.key

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Face verification result",
                "data": {
                    "is_verified": bool(verified),
                    "confidence": confidence,
                    "user": data,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="verify-not-authenticated")
    def verify_face_not_authenticated(self, request):
        try:
            image_file = request.FILES.get('image')

            if not image_file:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Image file is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            cropped_content = crop_center_square(image_file)
            cropped_file = SimpleUploadedFile(
                name=image_file.name,
                content=cropped_content,
                content_type=image_file.content_type
            )
            temp_path = os.path.join(settings.MEDIA_ROOT, "temp_verify.jpg")
            with open(temp_path, "wb+") as f:
                f.write(cropped_content)

            try:
                embedding_objs = DeepFace.represent(
                    img_path=temp_path,
                    model_name='Facenet',
                    enforce_detection=True 
                )
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "No face detected in the camera"
                }, status=status.HTTP_400_BAD_REQUEST)

            new_embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name='Facenet',
                enforce_detection=False
            )[0]
            new_embedding = np.array(new_embedding_obj["embedding"])
            if os.path.exists(temp_path):
                os.remove(temp_path)

            User = get_user_model()
            users = User.objects.all()
            matched_user = None
            max_confidence = 0

            for user in users:
                if hasattr(user, "user_faces"):
                    saved_embedding = np.array(user.user_faces.embedding)
                    cos_sim = np.dot(saved_embedding, new_embedding) / (
                        np.linalg.norm(saved_embedding) * np.linalg.norm(new_embedding)
                    )
                    if cos_sim > 0.7 and cos_sim > max_confidence:
                        matched_user = user
                        max_confidence = cos_sim

            if matched_user:
                access = UserToken.objects.create(user=matched_user)
                refresh = RefreshToken.objects.create(user=matched_user)
                user_serializer = UserSerializer(matched_user, context={'request': request})
                data = user_serializer.data
                data['access_token'] = access.key
                data['refresh_token'] = refresh.key
                confidence = round(max_confidence * 100, 2)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Face verification successful",
                    "data": {
                        "is_verified": True,
                        "confidence": confidence,
                        "user": data,
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "No matching user found",
                    "data": {
                        "is_verified": False
                    }
                }, status=status.HTTP_404_NOT_FOUND)

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

            cropped_content = crop_center_square(image_file)

            temp_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_update.jpg")
            with open(temp_path, "wb") as f:
                f.write(cropped_content)

            embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name='Facenet',
                enforce_detection=False
            )[0]

            embedding_vector = embedding_obj["embedding"]

            if os.path.exists(temp_path):
                os.remove(temp_path)

            user_face = user.user_faces
            cropped_file = SimpleUploadedFile(
                name=image_file.name,
                content=cropped_content,
                content_type=image_file.content_type
            )
            serializer = UserFaceSerializer(
                instance=user_face,
                data={
                    "embedding": embedding_vector,
                    "image": cropped_file
                },
                partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Face updated successfully",
                    "data": {
                        "is_verified": True,
                    }
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
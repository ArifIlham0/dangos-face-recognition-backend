from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from dangos_face_recognition.views.job_view import JobViewSet
from dangos_face_recognition.views.user_view import UserViewSet
from dangos_face_recognition.views.user_face_view import UserFaceViewSet
from dangos_face_recognition.views.active_history_view import ActiveHistoryViewSet
from dangos_face_recognition.views.authentication_view import AuthenticationViewSet
from dangos_face_recognition.views.scrap_view import scrap_job

router = DefaultRouter()

router.register(r"api/dangos-face-recognition/v1/user", UserViewSet, basename="user")
router.register(r"api/dangos-face-recognition/v1/authentication", AuthenticationViewSet, basename="authentication")
router.register(r"api/dangos-face-recognition/v1/user-face", UserFaceViewSet, basename="user-face")
router.register(r"api/dangos-face-recognition/v1/job", JobViewSet, basename="job")
router.register(r"api/dangos-face-recognition/v1/active-history", ActiveHistoryViewSet, basename="active-history")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    # Scrap
    path('api/dangos-face-recognition/v1/scrap/fetch-jobs', scrap_job),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
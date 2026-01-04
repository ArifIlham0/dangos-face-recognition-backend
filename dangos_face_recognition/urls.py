from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from dangos_face_recognition.views.user_view import UserViewSet
from dangos_face_recognition.views.user_face_view import UserFaceViewSet
from dangos_face_recognition.views.authentication_view import AuthenticationViewSet
from dangos_face_recognition.views.job_view import fetch_jobs
from dangos_face_recognition.views.active_history_view import create_active_history, fetch_active_histories, fetch_active_history_by_users
from dangos_face_recognition.views.scrap_view import scrap_job

router = DefaultRouter()
router.register(r"api/dangos-face-recognition/v1/user", UserViewSet, basename="user")
router.register(r"api/dangos-face-recognition/v1/authentication", AuthenticationViewSet, basename="authentication")
router.register(r"api/dangos-face-recognition/v1/user-face", UserFaceViewSet, basename="user-face")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    # Jobs
    path('api/dangos-face-recognition/v1/job/fetch', fetch_jobs),
    # Active Histories
    path('api/dangos-face-recognition/v1/active-history/create', create_active_history),
    path('api/dangos-face-recognition/v1/active-history/fetch', fetch_active_histories),
    path('api/dangos-face-recognition/v1/active-history/fetch-by-user', fetch_active_history_by_users),
    # Scrap
    path('api/dangos-face-recognition/v1/scrap/fetch-jobs', scrap_job),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
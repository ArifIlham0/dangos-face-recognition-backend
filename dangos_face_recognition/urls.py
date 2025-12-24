from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from dangos_face_recognition.views.user_view import create_user, fetch_users, fetch_user, update_user
from dangos_face_recognition.views.authentication_view import login, logout, refresh_token, reset_password, activate_users
from dangos_face_recognition.views.user_face_view import enroll_face, verify_face, update_face
from dangos_face_recognition.views.job_view import fetch_jobs
from dangos_face_recognition.views.active_history_view import create_active_history, fetch_active_histories, fetch_active_history_by_users
from dangos_face_recognition.views.scrap_view import scrap_job

urlpatterns = [
    path('admin/', admin.site.urls),
    # Users
    path('api/dangos-face-recognition/v1/user/create', create_user),
    path('api/dangos-face-recognition/v1/user/fetch', fetch_users),
    path('api/dangos-face-recognition/v1/user/fetch-by-id/<int:id>', fetch_user),
    path('api/dangos-face-recognition/v1/user/update/<int:id>', update_user),
    # Authentication
    path('api/dangos-face-recognition/v1/authentication/login', login),
    path('api/dangos-face-recognition/v1/authentication/logout', logout),
    path('api/dangos-face-recognition/v1/authentication/refresh-token', refresh_token),
    path('api/dangos-face-recognition/v1/authentication/reset-password', reset_password),
    path('api/dangos-face-recognition/v1/authentication/active-users', activate_users),
    # User Faces
    path('api/dangos-face-recognition/v1/user-face/enroll', enroll_face),
    path('api/dangos-face-recognition/v1/user-face/verify', verify_face),
    path('api/dangos-face-recognition/v1/user-face/update/<int:id>', update_face),
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
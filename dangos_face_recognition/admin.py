from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserFace, Job, ActiveHistory

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_superuser', 'first_name', 'last_name', 'job', 'is_staff', 'is_active', 'date_joined')

class UserFaceAdmin(admin.ModelAdmin):
    list_display = ('custom_user', 'custom_user_id', 'embedding', 'created_at')

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')

class ActiveHistoryAdmin(admin.ModelAdmin):
    list_display = ('custom_user', 'custom_user_id', 'operating_system', 'model', 'created_at')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserFace, UserFaceAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(ActiveHistory, ActiveHistoryAdmin)
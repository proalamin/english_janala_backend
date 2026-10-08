from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'institute', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'phone', 'institute')

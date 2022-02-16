from django.contrib import admin
from .models import userPreferences
# Register your models here.


class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency']


admin.site.register(userPreferences, UserPreferenceAdmin)

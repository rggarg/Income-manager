from django.contrib import admin
from .models import UserIncome, Source
# Register your models here.


class UserIncomeAdmin(admin.ModelAdmin):
    list_display = ['amount', 'source', 'owner', 'date']
    list_filter = ['source', 'owner', 'date']


admin.site.register(UserIncome, UserIncomeAdmin)
admin.site.register(Source)

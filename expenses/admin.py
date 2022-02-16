from django.contrib import admin
from .models import Expense, Category
# Register your models here.


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['amount', 'category', 'owner', 'date']
    list_filter = ['category', 'owner', 'date']


admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Category)

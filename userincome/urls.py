from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt
urlpatterns = [
    path('', views.index, name="income"),
    path('add-income', views.add_income, name="add-income"),
    path('search-income', csrf_exempt(views.search_income),
         name="search-income"),
    path('income-edit/<int:id>', views.income_edit, name="income-edit"),
    path('income-delete/<int:id>', views.income_delete, name="income-delete"),
    path('income-stats', views.income_stats_view, name='income-stats'),
    path('income-category-summary', views.income_category_summary,
         name='income_category_summary'),
    path('export-income-csv', views.export_income_csv, name='export-income-csv'),
    path('export-income-excel', views.export_income_excel,
         name='export-income-excel'),
    path('export-income-pdf', views.export_income_pdf, name='export-income-pdf'),
]

from datetime import date
from django.core import paginator
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import Category, Expense
from userpreferences.models import userPreferences
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
import datetime
import csv
import xlwt
from django.template.loader import render_to_string
# from weasyprint import HTML
import tempfile
from django.db.models import Sum
# Create your views here.


@login_required(login_url='authentication/login')
def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user,) | Expense.objects.filter(
            date__icontains=search_str, owner=request.user,) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user,) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user,)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='authentication/login')
def index(request):
    categories = Category.objects.all()
    user = request.user
    currency = userPreferences.objects.get(user=user)
    expenses = Expense.objects.filter(
        owner=request.user).order_by('-date')
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': str(currency.currency)[:3]
    }
    return render(request, 'expenses/index.html', context)


@login_required(login_url='authentication/login')
def add_expense(request):
    categories = Category.objects.all()
    values = request.POST
    context = {
        'categories': categories,
        'values': values
    }
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        category = request.POST['category']
        date = request.POST['expense_date']

        if not amount:
            messages.error(request, 'Amount required!!!')
            return render(request, 'expenses/add_expense.html', context)
        if not description:
            messages.error(request, 'Description required!!!')
            return render(request, 'expenses/add_expense.html', context)
        if not category:
            messages.error(request, 'Category required!!!')
            return render(request, 'expenses/add_expense.html', context)
        if not date:
            messages.error(request, 'Date required!!!')
            return render(request, 'expenses/add_expense.html', context)

        s = Category.objects.filter(name=category)
        if not s:
            Category.objects.create(name=category)

        Expense.objects.create(owner=request.user,
                               amount=amount, description=description, category=category, date=date)
        messages.success(request, 'Expense added seccessfully...')
        return redirect('expenses')


@login_required(login_url='authentication/login')
def expense_edit(request, id):
    categories = Category.objects.all()
    expense = Expense.objects.get(pk=id)
    context = {
        'categories': categories,
        'expense': expense,
        'values': expense
    }
    if request.method == 'GET':
        print('data', expense.date)
        return render(request, 'expenses/edit_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        category = request.POST['category']
        date = request.POST['expense_date']

        if not amount:
            messages.error(request, 'Amount required!!!')
            return render(request, 'expenses/edit_expense.html', context)
        if not description:
            messages.error(request, 'Description required!!!')
            return render(request, 'expenses/edit_expense.html', context)
        if not category:
            messages.error(request, 'Category required!!!')
            return render(request, 'expenses/edit_expense.html', context)
        if not date:
            messages.error(request, 'Date required!!!')
            return render(request, 'expenses/edit_expense.html', context)

        expense.owner = request.user
        expense.amount = amount
        expense.description = description
        expense.category = category
        expense.date = date
        expense.save()
        messages.success(request, 'Expense updated seccessfully...')
        return redirect('expenses')


@login_required(login_url='authentication/login')
def expense_delete(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense deleted...')
    return redirect('expenses')


def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days=30*6)
    expenses = Expense.objects.filter(
        owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    final_rep = {}

    def get_category(expense):
        return expense.category

    categgory_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)
        for item in filtered_by_category:
            amount += item.amount
        return amount

    for x in expenses:
        for y in categgory_list:
            final_rep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': final_rep}, safe=False)


def stats_view(request):
    return render(request, 'expenses/stats.html')


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        str(datetime.datetime.now()) + '.csv'
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])
    expenses = Expense.objects.filter(owner=request.user)

    for expense in expenses:
        writer.writerow([expense.amount, expense.description,
                        expense.category, expense.date])

    return response


def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        str(datetime.datetime.now()) + '.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Expenses')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Amount', 'Description', 'Category', 'Date']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()
    rows = Expense.objects.filter(owner=request.user).values_list(
        'amount', 'description', 'category', 'date')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)
    return response


def export_pdf(request):
    pass
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename=Expenses' + \
    #     str(datetime.datetime.now()) + '.pdf'
    # response['Content-Transfer-Encoding'] = 'binary'
    # html_string = render_to_string(
    #     'expenses/pdf-output.html', {'expenses': [], 'total': 0})
    # html = HTML(string=html_string)
    # result = html.write_pdf()

    # with tempfile.NamedTemporaryFile(delete=True) as output:
    #     output.write(result)
    #     output.flush()

    #     output = open(output.name, 'rb')
    #     response.write(output.read())

    # return response

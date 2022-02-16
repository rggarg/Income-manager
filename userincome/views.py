from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import UserIncome, Source
from userpreferences.models import userPreferences
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from django.http.response import HttpResponse
import datetime
import csv
import xlwt
import tempfile
from django.db.models import Sum
# Create your views here.


@login_required(login_url='authentication/login')
def search_income(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        income = UserIncome.objects.filter(
            amount__istartswith=search_str, owner=request.user,) | UserIncome.objects.filter(
            date__icontains=search_str, owner=request.user,) | UserIncome.objects.filter(
            description__icontains=search_str, owner=request.user,) | UserIncome.objects.filter(
            source__icontains=search_str, owner=request.user,)
        data = income.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='authentication/login')
def index(request):
    sources = Source.objects.all()
    currency = userPreferences.objects.get(user=request.user)
    incomes = UserIncome.objects.filter(
        owner=request.user).order_by('-date')
    paginator = Paginator(incomes, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    context = {
        'incomes': incomes,
        'page_obj': page_obj,
        'currency': str(currency.currency)[:3]
    }
    return render(request, 'income/index.html', context)


@login_required(login_url='authentication/login')
def add_income(request):
    sources = Source.objects.all()
    values = request.POST
    context = {
        'sources': sources,
        'values': values
    }
    if request.method == 'GET':
        return render(request, 'income/add_income.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        source = request.POST['source']
        date = request.POST['income_date']

        if not amount:
            messages.error(request, 'Amount required!!!')
            return render(request, 'income/add_income.html', context)
        if not description:
            messages.error(request, 'Description required!!!')
            return render(request, 'income/add_income.html', context)
        if not source:
            messages.error(request, 'Source required!!!')
            return render(request, 'income/add_income.html', context)
        if not date:
            messages.error(request, 'Date required!!!')
            return render(request, 'income/add_income.html', context)
        s = Source.objects.filter(name=source)
        if not s:
            Source.objects.create(name=source)
        UserIncome.objects.create(owner=request.user,
                                  amount=amount, description=description, source=source, date=date)
        messages.success(request, 'Income added seccessfully...')
        return redirect('income')


@login_required(login_url='authentication/login')
def income_edit(request, id):
    sources = Source.objects.all()
    income = UserIncome.objects.get(pk=id)
    context = {
        'sources': sources,
        'income': income,
        'values': income
    }
    print('income', income.id)
    if request.method == 'GET':
        print('data', income.date)
        return render(request, 'income/edit_income.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        source = request.POST['source']
        date = request.POST['income_date']

        if not amount:
            messages.error(request, 'Amount required!!!')
            return render(request, 'income/edit_income.html', context)
        if not description:
            messages.error(request, 'Description required!!!')
            return render(request, 'income/edit_income.html', context)
        if not source:
            messages.error(request, 'Source required!!!')
            return render(request, 'income/edit_income.html', context)
        if not date:
            messages.error(request, 'Date required!!!')
            return render(request, 'income/edit_income.html', context)

        income.owner = request.user
        income.amount = amount
        income.description = description
        income.source = source
        income.date = date
        income.save()
        messages.success(request, 'Income updated seccessfully...')
        return redirect('income')


@login_required(login_url='authentication/login')
def income_delete(request, id):
    income = UserIncome.objects.get(pk=id)
    income.delete()
    messages.success(request, 'Income deleted...')
    return redirect('income')


def income_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days=30*6)
    incomes = UserIncome.objects.filter(
        owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    final_rep = {}

    def get_category(income):
        return income.source

    categgory_list = list(set(map(get_category, incomes)))

    def get_expense_category_amount(source):
        amount = 0
        filtered_by_category = incomes.filter(source=source)
        for item in filtered_by_category:
            amount += item.amount
        return amount

    for x in incomes:
        for y in categgory_list:
            final_rep[y] = get_expense_category_amount(y)

    print(final_rep)
    return JsonResponse({'income_category_data': final_rep}, safe=False)


def income_stats_view(request):
    return render(request, 'income/income_stats.html')


def export_income_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=Income' + \
        str(datetime.datetime.now()) + '.csv'
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Source', 'Date'])
    incomes = UserIncome.objects.filter(owner=request.user)

    for income in incomes:
        writer.writerow([income.amount, income.description,
                        income.source, income.date])

    return response


def export_income_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Income' + \
        str(datetime.datetime.now()) + '.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Income')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Amount', 'Description', 'Source', 'Date']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()
    rows = UserIncome.objects.filter(owner=request.user).values_list(
        'amount', 'description', 'source', 'date')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)
    return response


def export_income_pdf(request):
    pass

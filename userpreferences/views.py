from genericpath import exists
from django.contrib import messages
from django.shortcuts import render
import os
import json
from django.conf import settings
from .models import userPreferences
# Create your views here.


def index(request):
    exists = userPreferences.objects.filter(user=request.user).exists()
    user_prefernces = None
    if exists:
        user_prefernces = userPreferences.objects.get(user=request.user)
    currency_data = []
    file_path = os.path.join(settings.BASE_DIR, 'currencies.json')
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        for k, v in data.items():
            currency_data.append({'name': k, 'value': v})
    if request.method == 'GET':
        return render(request, 'preferences/index.html', {'currencies': currency_data, 'user_prefernces': user_prefernces})
    else:
        currency = request.POST['currency']
        if exists:
            user_prefernces.currency = currency
            user_prefernces.save()
        else:
            userPreferences.objects.create(
                user=request.user, currency=currency)
        messages.success(request, 'Changes saved successfully..')
        return render(request, 'preferences/index.html', {'currencies': currency_data, 'user_prefernces': user_prefernces})

from django.contrib.sites import requests
from django.shortcuts import redirect, render
from django.views import View
import json
from userpreferences.models import userPreferences
from django.http import JsonResponse
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import token_generator
from django.contrib import auth
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import threading


class EmailThread(threading.Thread):
    # to send the mail in back and speedup the front
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)


class RegisterationView(View):
    # to register the user and sending the user account activation link-mail
    def get(self, request):
        return render(request, 'authentication/register.html')

    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        context = {
            "fieldValues": request.POST
        }
        if len(username) == 0:
            messages.error(request, 'Username required!!!')
            return render(request, 'authentication/register.html', context)
        if len(email) == 0:
            messages.error(request, 'Email required!!!')
            return render(request, 'authentication/register.html', context)

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(username=username).exists():
                if len(password) < 6:
                    messages.error(request, 'Password too short!!!')
                    return render(request, 'authentication/register.html', context)

                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.is_active = False
                user.save()
                userPreferences.objects.create(
                    user=user, currency='INR - Indian National Rupee')
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(request).domain
                link = reverse('activate', kwargs={
                               'uidb64': uidb64, 'token': token_generator.make_token(user)})
                activate_link = 'http:/'+domain+link
                email_subject = 'Activate your account'
                email_body = 'Hi, ' + user.username + \
                    '\n Please use the below link to activate your account.\n' + activate_link
                email = EmailMessage(
                    email_subject,
                    email_body,
                    'noreply@semycolon.com',
                    [email],
                )
                EmailThread(email).start()
                # email.send(fail_silently=False)
                messages.success(request, 'Account created successfully...')

                return render(request, 'authentication/register.html')

        return render(request, 'authentication/register.html')


class LoginView(View):
    # to login the user and checking whether user is active or not
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        if username and password:
            user = auth.authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(
                        request, 'Hey! '+user.username+' Welcome to Income Manager')
                    return redirect('expenses')
            messages.error(
                request, 'Some issue!!!Please activate your account or try with another credentials..')
            return render(request, 'authentication/login.html')
        messages.error(request, 'Please fill all fields!!')
        return render(request, 'authentication/login.html')


def logout(request):
    # signing out the user
    auth.logout(request)
    messages.success(request, 'Signout Successfully..')
    return redirect('login')


class RequestPasswordResetEmail(View):
    # sending mail to user to reset the password of account
    def get(self, request):
        return render(request, 'authentication/reset-password.html')

    def post(self, request):
        email = request.POST['email']
        context = {
            'values': request.POST
        }
        if not validate_email(email):
            messages.error(request, 'Email not valid!! Please enter other.')
            return render(request, 'authentication/reset-password.html', context)

        current_site = get_current_site(request)
        user = User.objects.get(email=email)
        if user:
            print(user.pk)
            # user.is_active = True
            email_content = {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': PasswordResetTokenGenerator().make_token(user),
            }
            link = reverse('reset-user-password', kwargs={
                'uidb64': email_content['uid'], 'token': email_content['token']})
            reset_url = 'http:/'+current_site.domain+link
            email_subject = 'Reset your password'
            email_body = 'Hi, ' + user.username + \
                '\n Please use the below link to reset the password for your account.\n' + reset_url
            email = EmailMessage(
                email_subject,
                email_body,
                'noreply@semycolon.com',
                [email],
            )
            EmailThread(email).start()
            # email.send(fail_silently=False)
            messages.success(
                request, 'We have sent you an email..please check your inbox')
            return render(request, 'authentication/reset-password.html')
        else:
            messages.error(request, "User don't exists!! Please enter other.")
            return render(request, 'authentication/reset-password.html')


class CompletePasswordReset(View):
    # to check whether the user change the password with the link sent in mail
    # if yes then user a error otherwise got option to reset the password
    def get(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token,
        }
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            print('user_id---------', user_id)
            user = User.objects.get(pk=(user_id))
            print('user---', user, user.pk)
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(
                    request, 'Password link invalid!! Please request a new link')
                return render(request, 'authentication/reset-password.html')
        except Exception as e:
            print('e---', e)
            messages.info(request, 'Something went wrong,Please try again')
            return render(request, 'authentication/set-new-password.html', context)
        return render(request, 'authentication/set-new-password.html', context)

    def post(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token,
        }
        password = request.POST['password']
        password2 = request.POST['password2']
        if password != password2:
            messages.error(
                request, "Passwords don't match!! Please enter same")
            return render(request, 'authentication/set-new-password.html', context)
        if len(password) < 6:
            messages.error(request, "Password too short!!!")
            return render(request, 'authentication/set-new-password.html', context)

        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            messages.success(
                request, 'Password changed successfully..Login with new credentials.')
            return redirect('login')
        except Exception as e:
            messages.info(request, 'Something went wrong,Please try again')
            return render(request, 'authentication/set-new-password.html', context)


class VerificationView(View):
    # to active the account of user
    def get(self, request, uidb64, token):
        try:
            id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            if not token_generator.check_token(user, token):
                return redirect('login')

            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()
            messages.success(request, 'Account activated successfully..')
        except Exception as e:
            print('Error!', e)
        return redirect('login')


class UsernameValidationView(View):
    # validating the user by every letter entered in field
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        if len(username) < 6:
            return JsonResponse({'username_error': 'Username too short..Please choose another'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'username already exists,choose another..'}, status=409)
        return JsonResponse({'username_valid': True}, status=200)


class EmailValidationView(View):
    # validating the email by every letter entered in field
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'email is not valid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'email already exists,choose another..'}, status=409)
        return JsonResponse({'email_valid': True}, status=200)

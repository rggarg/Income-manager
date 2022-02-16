from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt
urlpatterns = [
    path('register', views.RegisterationView.as_view(), name="register"),
    path('login', views.LoginView.as_view(), name="login"),
    path('logout', views.logout, name="logout"),
    path('request-reset-link', views.RequestPasswordResetEmail.as_view(),
         name='request-password'),
    path('validate-username', csrf_exempt(views.UsernameValidationView.as_view()),
         name="validate-username"),
    path('validate-email', csrf_exempt(views.EmailValidationView.as_view()),
         name="validate-email"),
    path('activate/<uidb64>/<token>',
         views.VerificationView.as_view(), name='activate'),
    path('set-new-password/<uidb64>/<token>',
         views.CompletePasswordReset.as_view(), name='reset-user-password'),

]

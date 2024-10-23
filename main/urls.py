from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('results/', views.results, name='results'),
    path('register/', views.register, name="register"),
    path('verify/', views.verfiy_otp, name="verify"),

    path('logout/', views.logout_view, name='logout'),
    path('vote/', views.vote, name='vote'),
    path('send_opt_api/', views.send_opt_api, name='send_opt_api'),

    # path('verifyPassword/', views.login_password_verify, name="password_verify"),
    path('loginOtp/', views.loginOtp, name='loginOtp'),
    path('votelist/', views.voteList, name="voteList"),

    path('candidates/', views.candidates, name='candidates'),
    path('candidate/<int:id>/', views.candidate, name='candidate'),

    #----OTHERS----#
    path('forgotCwid/', views.forgotCwid, name='forgotCwid'),
]

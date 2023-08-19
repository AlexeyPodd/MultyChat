from django.urls import path

from .views import UserLoginView, logout_user, UserRegisterView


app_name = 'account'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', UserRegisterView.as_view(), name='register'),
]

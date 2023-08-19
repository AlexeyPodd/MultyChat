from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginUserForm, RegisterUserForm


class UserRegisterView(CreateView):
    """View for registering new user."""
    form_class = RegisterUserForm
    template_name = 'account/form.html'
    extra_context = {'title': 'Registration',
                     'button_label': 'Register'}

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('chat:home')


class UserLoginView(LoginView):
    """View for login page."""
    form_class = LoginUserForm
    template_name = 'account/form.html'
    extra_context = {'title': 'Login',
                     'button_label': 'Login'}

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url

        return reverse_lazy('chat:home')


def logout_user(request):
    logout(request)
    return redirect('chat:home')

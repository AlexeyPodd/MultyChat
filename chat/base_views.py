from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render

from account.models import User


def user_management_list_view(users_list_filed_name, title, bootstrap_btn_color, button_label, empty_phrase):
    def wrapper(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request):
            if request.method == 'POST':
                try:
                    excluding_user = User.objects.get(username=request.POST.get('username'))
                except ObjectDoesNotExist:
                    raise Http404

                try:
                    getattr(request.user, users_list_filed_name).remove(excluding_user)
                except AttributeError:
                    return

            managed_user_list = getattr(request.user, users_list_filed_name).all()
            return render(request,
                          'chat/manage_user_list.html',
                          {'title': title,
                           'bootstrap_btn_color': bootstrap_btn_color,
                           'button_label': button_label,
                           'empty_phrase': empty_phrase,
                           'user_list': managed_user_list})

        return wrapped
    return wrapper

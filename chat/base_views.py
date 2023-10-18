from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from account.models import User


def user_management_list_view(users_list_filed_name):
    """Base view decorator for managing some list of related users with current user (but not for banned users)"""
    def wrapper(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request):
            if request.method == 'POST':
                try:
                    excluding_user = User.objects.get(username=request.POST.get('username'))
                except ObjectDoesNotExist:
                    raise Http404

                getattr(request.user, users_list_filed_name).remove(excluding_user)

            managed_user_list = getattr(request.user, users_list_filed_name).all()
            return view_func(request, managed_user_list)

        return wrapped
    return wrapper

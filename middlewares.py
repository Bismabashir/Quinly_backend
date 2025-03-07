from django.http import JsonResponse
from functools import wraps


def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"message": "Authentication required."}, status=401)

        if not request.user.is_superuser:
            return JsonResponse({"message": "Superuser access required."}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper

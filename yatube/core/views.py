from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception):
    return render(
        request,
        'core/404.html',
        {'path': request.path},
        status=HTTPStatus.NOT_FOUND
    )


def permission_denied(request, exception):
    return render(
        request,
        'core/403.html',
        status=HTTPStatus.FORBIDDEN
    )

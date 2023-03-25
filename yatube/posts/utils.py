from django.conf import settings
from django.core.paginator import Paginator


def paginate(request, posts):
    page_number = request.GET.get('page')
    paginator = Paginator(posts, settings.MAX_LENGHT_POSTS)
    page_obj = paginator.get_page(page_number)
    return page_obj

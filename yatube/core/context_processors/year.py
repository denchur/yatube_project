from django.utils import timezone


def year(request):
    year = timezone.now().year
    return {
        'year': year
    }

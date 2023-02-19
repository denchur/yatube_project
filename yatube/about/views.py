from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about_title'] = 'О авторе'
        context['about_description'] = (
            'Django, Git, Python, Bootstrap, формы сложноваты или я глуп'
        )

        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about_title'] = 'О технологиях'
        context['about_description'] = (
            'Django, Git, Python, Bootstrap, формы сложноваты или я глуп'
        )

        return context

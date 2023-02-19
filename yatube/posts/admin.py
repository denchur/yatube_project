from django.contrib import admin

from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    search_fields = ('description',)
    empty_value_display = '-пусто-'
    list_filter = ('title',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)

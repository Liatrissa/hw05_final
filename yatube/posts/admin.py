from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    """ Модель админки """
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    list_editable = ('group',)
    # Настройка для изменения поля group в любом посте
    search_fields = ('text',)
    # Добавляем интерфейс для поиска по тексту постов
    list_filter = ('pub_date',)
    # Добавляем возможность фильтрации по дате
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    """ Модель комментариев """
    list_display = ('pk', 'text',
                    'author', 'post')
    search_fields = ('text',)
    list_filter = ('post',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment, CommentAdmin)

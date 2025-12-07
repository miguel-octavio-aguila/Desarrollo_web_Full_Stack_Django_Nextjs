from django.contrib import admin

from .models import Post, Category, Heading


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'parent', 'slug',)
    search_fields = ('name', 'title', 'description', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)
    ordering = ('name',)
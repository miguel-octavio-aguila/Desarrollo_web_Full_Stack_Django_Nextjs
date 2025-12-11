from django.contrib import admin
from django_ckeditor_5.widgets import CKEditor5Widget
from django import forms

from .models import Post, Category, Heading, PostAnalytics


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'parent', 'slug',)
    search_fields = ('name', 'title', 'description', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)
    ordering = ('name',)
    readonly_fields = ('id',)
    # list_editable = ('name', 'title',)

# Form for Post Admin
class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditor5Widget(config_name='default'))
    
    class Meta:
        model = Post
        fields = '__all__'

# Heading Inline Admin
class HeadingInline(admin.TabularInline):
    model = Heading
    extra = 1
    fields = ('title', 'level', 'order', 'slug',)
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)

# Post Admin
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'status', 'category', 'created_at', 'updated_at',)
    search_fields = ('title', 'description', 'content', 'slug', 'keywords',)
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('status', 'category', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at',)
    fieldsets = (
        ('General Information', {
            'fields': ('title', 'description', 'content', 'slug', 'keywords', 'category', 'thumbnail',)
        }),
        ('Status & Dates', {
            'fields': ('status', 'created_at', 'updated_at',)
        }),
    )
    inlines = [HeadingInline]

    class Media:
        css = {
            'all': ('admin/css/admin_custom.css',)
        }

# Heading Admin
# @admin.register(Heading)
# class HeadingAdmin(admin.ModelAdmin):
#     list_display = ('title', 'post', 'level', 'order',)
#     search_fields = ('title', 'post__title',)
#     list_filter = ('post', 'level',)
#     ordering = ('order', 'post',)
#     prepopulated_fields = {'slug': ('title',)}

@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('post_title', 'views', 'impressions', 'clicks', 'clicks_through_rate', 'avg_time_on_page')
    search_fields = ('post_title',)
    readonly_fields = ('post', 'views', 'impressions', 'clicks', 'clicks_through_rate', 'avg_time_on_page')
    
    def post_title(self, obj):
        return obj.post.title
    
    post_title.short_description = 'Post Title'

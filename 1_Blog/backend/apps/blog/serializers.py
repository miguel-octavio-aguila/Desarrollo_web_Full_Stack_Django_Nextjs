from rest_framework import serializers

from .models import Post, Category, Heading, PostViews


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug',]

class HeadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Heading
        fields = ['title', 'slug', 'level', 'order',]

class PostViewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostViews
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    headings = HeadingSerializer(many=True)
    post_views = PostViewsSerializer(many=True)
    view_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = '__all__'
    
    def get_view_count(self, obj):
        return obj.post_views.count()

class PostListSerializer(serializers.ModelSerializer):
    category = CategoryListSerializer()
    headings = HeadingSerializer(many=True)
    post_views = PostViewsSerializer(many=True)
    view_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'slug', 'category', 'thumbnail', 'headings', 'post_views', 'view_count',]
    
    def get_view_count(self, obj):
        return obj.post_views.count()

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Post, Heading, PostViews
from .serializers import PostListSerializer, PostSerializer, HeadingSerializer, PostViewsSerializer
from .utils import get_client_ip


# class PostListView(ListAPIView):
#     queryset = Post.post_published.all()
#     serializer_class = PostListSerializer

class PostListView(APIView):
    def get(self, request, *args, **kwargs):
        posts = Post.post_published.all()
        serialized_posts = PostListSerializer(posts, many=True).data
        
        return Response(serialized_posts)

# class PostDetailView(RetrieveAPIView):
#     queryset = Post.post_published.all()
#     serializer_class = PostSerializer
#     lookup_field = 'slug'

class PostDetailView(APIView):
    def get(self, request, slug, *args, **kwargs):
        post = Post.post_published.get(slug=slug)
        serialized_post = PostSerializer(post).data
        
        client_ip = get_client_ip(request)
        
        if PostViews.objects.filter(post=post, ip_address=client_ip).exists():
            return Response(serialized_post)
        
        PostViews.objects.create(post=post, ip_address=client_ip)
        
        return Response(serialized_post)

# class PostHeadingsView(ListAPIView):
#     serializer_class = HeadingSerializer
    
#     def get_queryset(self):
#         post_slug = self.kwargs.get("slug")
#         return Heading.objects.filter(post__slug=post_slug)

class PostHeadingsView(APIView):
    def get(self, request, slug, *args, **kwargs):
        headings = Heading.objects.filter(post__slug=slug)
        serialized_headings = HeadingSerializer(headings, many=True).data
        
        return Response(serialized_headings)

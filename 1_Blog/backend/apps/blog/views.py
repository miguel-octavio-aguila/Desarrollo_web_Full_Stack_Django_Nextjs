from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Post, Heading
from .serializers import PostListSerializer, PostSerializer, HeadingSerializer


class PostListView(ListAPIView):
    queryset = Post.post_published.all()
    serializer_class = PostListSerializer


class PostDetailView(RetrieveAPIView):
    queryset = Post.post_published.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'

class PostHeadingsView(ListAPIView):
    serializer_class = HeadingSerializer
    
    def get_queryset(self):
        post_slug = self.kwargs.get("slug")
        return Heading.objects.filter(post__slug=post_slug)
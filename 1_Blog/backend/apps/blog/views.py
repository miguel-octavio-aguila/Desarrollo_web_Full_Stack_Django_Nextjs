from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
from rest_framework import permissions

from .models import Post, Heading, PostViews, PostAnalytics
from .serializers import PostListSerializer, PostSerializer, HeadingSerializer, PostViewsSerializer
from .utils import get_client_ip
from .tasks import increment_post_impressions
from core.permissions import HasValidAPIKey

import redis
from django.conf import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)


# class PostListView(ListAPIView):
#     queryset = Post.post_published.all()
#     serializer_class = PostListSerializer

class PostListView(APIView):
    permission_classes = [HasValidAPIKey]
    
    def get(self, request, *args, **kwargs):
        try:
            posts = Post.post_published.all()
            
            if not posts.exists():
                raise NotFound(detail="Posts do not exist")
            
            serialized_posts = PostListSerializer(posts, many=True).data
            
            for post in posts:
                # Save the impressions on post id in redis
                redis_client.incr(f"post:impressions:{post.id}")
            
        except Post.DoesNotExist:
            raise NotFound(detail="Posts do not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
        
        return Response(serialized_posts)


# class PostDetailView(RetrieveAPIView):
#     queryset = Post.post_published.all()
#     serializer_class = PostSerializer
#     lookup_field = 'slug'

class PostDetailView(APIView):
    permission_classes = [HasValidAPIKey]
    
    def get(self, request, slug, *args, **kwargs):
        try:
            post = Post.post_published.get(slug=slug)
        except Post.DoesNotExist:
            raise NotFound(detail="Post does not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
        
        serialized_post = PostSerializer(post).data
        
        # Increment views count
        try:
            post_analytics = PostAnalytics.objects.get(post=post)
            post_analytics.increment_views(request)
        except PostAnalytics.DoesNotExist:
            raise NotFound(detail="Post analytics does not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred while updating post analytics: {str(e)}")
        
        return Response(serialized_post)


# class PostHeadingsView(ListAPIView):
#     serializer_class = HeadingSerializer
    
#     def get_queryset(self):
#         post_slug = self.kwargs.get("slug")
#         return Heading.objects.filter(post__slug=post_slug)

class PostHeadingsView(APIView):
    permission_classes = [HasValidAPIKey]
    
    def get(self, request, slug, *args, **kwargs):
        try:
            headings = Heading.objects.filter(post__slug=slug)
        except Heading.DoesNotExist:
            raise NotFound(detail="Headings do not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
        
        serialized_headings = HeadingSerializer(headings, many=True).data
        
        return Response(serialized_headings)


class IncrementPostClicksView(APIView):
    permission_classes = [HasValidAPIKey]
    
    def post(self, request):
        """
        Increment the number of clicks for a post based on the post slug
        """
        data = request.data
        try:
            post = Post.post_published.get(slug=data.get("slug"))
        except Post.DoesNotExist:
            raise NotFound(detail="Post does not exist")
        
        try:
            post_analytics = PostAnalytics.objects.get(post=post)
            post_analytics.increment_clicks()
            post_analytics.save()
        except PostAnalytics.DoesNotExist:
            raise NotFound(detail="Post analytics does not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred while updating post analytics: {str(e)}")
        
        return Response({
            "message": "Post clicks incremented successfully",
            "clicks": post_analytics.clicks 
        })
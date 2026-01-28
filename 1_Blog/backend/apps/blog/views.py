from rest_framework.generics import ListAPIView, RetrieveAPIView
# from rest_framework.views import APIView
from rest_framework_api.views import StandardAPIView
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
# Manual cache
from django.core.cache import cache
from .utils import get_client_ip
from .tasks import increment_post_views

redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)


# class PostListView(ListAPIView):
#     queryset = Post.post_published.all()
#     serializer_class = PostListSerializer

class PostListView(StandardAPIView):
    permission_classes = [HasValidAPIKey]
    
    # @method_decorator(cache_page(60 * 1)) # Cache for 1 minute
    
    def get(self, request, *args, **kwargs):
        try:
            # Verify if the posts are cached
            cached_data = cache.get("post_list")
            if cached_data:
                serialized_posts = cached_data["posts"]
                post_ids = cached_data["post_ids"]
                
                # Increment the impressions on post id in redis
                for post_id in post_ids:
                    redis_client.incr(f"post:impressions:{post_id}")
                
                return self.paginate_response_with_extra(request, serialized_posts, extra_data={"total_posts": len(serialized_posts)})
            
            # Get the posts if not cached
            posts = Post.post_published.all()
            
            if not posts.exists():
                raise NotFound(detail="Posts do not exist")
            
            # Serialize the posts
            serialized_posts = PostListSerializer(posts, many=True).data
            
            # Get post IDs for caching and impressions
            post_ids = list(posts.values_list("id", flat=True))
            
            # Set the serialized posts and IDs in cache
            cache.set("post_list", {"posts": serialized_posts, "post_ids": post_ids}, timeout=60 * 5)  # Cache for 5 minutes
            
            # Increment the impressions on post id in redis
            for post_id in post_ids:
                redis_client.incr(f"post:impressions:{post_id}")
            
        except Post.DoesNotExist:
            raise NotFound(detail="Posts do not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
        
        return self.paginate_response_with_extra(request, serialized_posts, extra_data={"total_posts": len(serialized_posts)})


# class PostDetailView(RetrieveAPIView):
#     queryset = Post.post_published.all()
#     serializer_class = PostSerializer
#     lookup_field = 'slug'

class PostDetailView(StandardAPIView):
    permission_classes = [HasValidAPIKey]
    
    def get(self, request):
        ip_address = get_client_ip(request)
        slug = request.query_params.get("slug")
        
        try:
            # Verify if the data is cached
            chached_post = cache.get(f"post_detail:{slug}")
            if chached_post:
                increment_post_views.delay(chached_post["slug"], ip_address)
                return self.response(chached_post)
            
            # Get the post if not cached from the db
            post = Post.post_published.get(slug=slug)
            
            if not post:
                raise NotFound(detail="Post does not exist")
            
            # Serialize the post
            serialized_post = PostSerializer(post).data
            
            # Set the post in cache
            cache.set(f"post_detail:{slug}", serialized_post, timeout=60 * 5) # Cache for 5 minutes
            
            # Increment views count
            increment_post_views.delay(slug, ip_address)
        except Post.DoesNotExist:
            raise NotFound(detail="Post does not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
        
        return self.response(serialized_post)


# class PostHeadingsView(ListAPIView):
#     serializer_class = HeadingSerializer
    
#     def get_queryset(self):
#         post_slug = self.kwargs.get("slug")
#         return Heading.objects.filter(post__slug=post_slug)

class PostHeadingsView(StandardAPIView):
    permission_classes = [HasValidAPIKey]
    
    def get(self, request):
        slug = request.query_params.get("slug")
        try:
            headings = Heading.objects.filter(post__slug=slug)
        except Heading.DoesNotExist:
            raise NotFound(detail="Headings not found")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
        
        serialized_headings = HeadingSerializer(headings, many=True).data
        
        return self.response(serialized_headings)


class IncrementPostClicksView(StandardAPIView):
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
        
        return self.response({
            "message": "Post clicks incremented successfully",
            "clicks": post_analytics.clicks 
        })
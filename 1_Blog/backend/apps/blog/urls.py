from django.urls import path

from .views import PostListView, PostDetailView, PostHeadingsView

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post-detail"),
    path("posts/<slug:slug>/headings/", PostHeadingsView.as_view(), name="post-headings"),
]

from django.urls import path

from .views import (
    PostListView, 
    PostDetailView, 
    PostHeadingsView, 
    IncrementPostClicksView
)

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/clicks/", IncrementPostClicksView.as_view(), name="increment-post-clicks"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post-detail"),
    path("posts/<slug:slug>/headings/", PostHeadingsView.as_view(), name="post-headings"),
]

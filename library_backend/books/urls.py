from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, PublisherViewSet, CategoryViewSet, TagViewSet, BookViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'books', BookViewSet, basename='book')

app_name = 'books'

urlpatterns = [
    path('', include(router.urls)),
]

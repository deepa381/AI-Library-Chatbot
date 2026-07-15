from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import FineViewSet

router = SimpleRouter()
router.register(r'fines', FineViewSet, basename='fine')

urlpatterns = [
    path('', include(router.urls)),
]

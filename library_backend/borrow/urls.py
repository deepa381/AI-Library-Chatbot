from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import BorrowViewSet

app_name = 'borrow'

router = SimpleRouter()
router.register(r'', BorrowViewSet, basename='borrow')

urlpatterns = [
    path('', include(router.urls)),
]

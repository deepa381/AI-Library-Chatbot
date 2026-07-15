from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ReservationViewSet

app_name = 'reservations'

router = SimpleRouter()
router.register(r'', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]

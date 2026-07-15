from django.urls import path
from recommendation.views import RecommendView

app_name = 'recommendation'

urlpatterns = [
    path('recommend/', RecommendView.as_view(), name='recommend'),
]

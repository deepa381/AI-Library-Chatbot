"""
URL configuration for library_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from books.dashboard_views import DashboardView
from books.report_views import (
    BorrowReportView,
    ReservationReportView,
    FineReportView,
    MemberActivityReportView,
    BookPopularityReportView
)

# Configure Swagger/OpenAPI documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Library Chatbot & Recommendation System API",
        default_version='v1',
        description="API documentation for the AI-powered Library Chatbot & Book Recommendation backend foundation.",
        contact=openapi.Contact(email="admin@librarychatbot.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Placeholder API Routes for modular apps
    path('api/auth/', include('accounts.urls', namespace='accounts')),
    path('api/', include('accounts.member_urls')),
    path('api/', include('books.urls', namespace='books')),
    path('api/borrow/', include('borrow.urls', namespace='borrow')),
    path('api/', include('borrow.fine_urls')),
    path('api/reservations/', include('reservations.urls', namespace='reservations')),
    path('api/', include('chatbot.urls', namespace='chatbot')),
    path('api/', include('recommendation.urls', namespace='recommendation')),

    
    # Dashboard & Reports
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/reports/borrow/', BorrowReportView.as_view(), name='report-borrow'),
    path('api/reports/reservation/', ReservationReportView.as_view(), name='report-reservation'),
    path('api/reports/fine/', FineReportView.as_view(), name='report-fine'),
    path('api/reports/member-activity/', MemberActivityReportView.as_view(), name='report-member-activity'),
    path('api/reports/book-popularity/', BookPopularityReportView.as_view(), name='report-book-popularity'),
    
    # Interactive API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve static/media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


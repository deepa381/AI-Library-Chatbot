"""
URL configuration for library_backend project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from books.dashboard_views import DashboardView
from books.report_views import (
    BorrowReportView,
    ReservationReportView,
    FineReportView,
    MemberActivityReportView,
    BookPopularityReportView,
)

# -----------------------------------------------------------------------------
# Home Endpoint
# -----------------------------------------------------------------------------

def home(request):
    return JsonResponse({
        "status": "success",
        "message": "AI Library Chatbot Backend is Running 🚀",
        "version": "1.0",
        "documentation": "/swagger/",
        "redoc": "/redoc/",
        "admin": "/admin/",
        "api": "/api/"
    })


# -----------------------------------------------------------------------------
# Swagger / OpenAPI Configuration
# -----------------------------------------------------------------------------

schema_view = get_schema_view(
    openapi.Info(
        title="Library Chatbot & Recommendation System API",
        default_version="v1",
        description="API documentation for the AI-powered Library Chatbot & Book Recommendation System.",
        contact=openapi.Contact(
            email="admin@librarychatbot.local"
        ),
        license=openapi.License(
            name="BSD License"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


# -----------------------------------------------------------------------------
# URL Patterns
# -----------------------------------------------------------------------------

urlpatterns = [

    # Home
    path("", home, name="home"),

    # Admin
    path("admin/", admin.site.urls),

    # Authentication
    path("api/auth/", include("accounts.urls", namespace="accounts")),

    # Member APIs
    path("api/", include("accounts.member_urls")),

    # Books
    path("api/", include("books.urls", namespace="books")),

    # Borrow
    path("api/borrow/", include("borrow.urls", namespace="borrow")),

    # Fine
    path("api/", include("borrow.fine_urls")),

    # Reservations
    path("api/reservations/", include("reservations.urls", namespace="reservations")),

    # Chatbot
    path("api/", include("chatbot.urls", namespace="chatbot")),

    # Recommendation
    path("api/", include("recommendation.urls", namespace="recommendation")),

    # Dashboard
    path(
        "api/dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),

    # Reports
    path(
        "api/reports/borrow/",
        BorrowReportView.as_view(),
        name="report-borrow",
    ),
    path(
        "api/reports/reservation/",
        ReservationReportView.as_view(),
        name="report-reservation",
    ),
    path(
        "api/reports/fine/",
        FineReportView.as_view(),
        name="report-fine",
    ),
    path(
        "api/reports/member-activity/",
        MemberActivityReportView.as_view(),
        name="report-member-activity",
    ),
    path(
        "api/reports/book-popularity/",
        BookPopularityReportView.as_view(),
        name="report-book-popularity",
    ),

    # Swagger Documentation
    path(
        "swagger<format>/",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),

    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),

    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]

# -----------------------------------------------------------------------------
# Static & Media Files (Development Only)
# -----------------------------------------------------------------------------

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
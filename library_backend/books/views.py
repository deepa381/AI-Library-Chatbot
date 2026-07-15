from rest_framework import viewsets, filters, permissions
from rest_framework.pagination import PageNumberPagination
from accounts.permissions import IsLibrarian
from .models import Author, Publisher, Category, Tag, Book
from .serializers import (
    AuthorSerializer,
    PublisherSerializer,
    CategorySerializer,
    TagSerializer,
    BookSerializer
)

class BookPagination(PageNumberPagination):
    """
    Standard pagination for library books: 10 items per page.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MetadataPagination(PageNumberPagination):
    """
    Standard pagination for metadata categories, tags, authors, and publishers.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseLibraryViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet to centralize permissions policy.
    Allows read-only access (list, retrieve) to anyone,
    but restricts write operations to librarians.
    """
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsLibrarian()]


class AuthorViewSet(BaseLibraryViewSet):
    """
    ViewSet for viewing and editing Author instances.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = MetadataPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'country']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name']


class PublisherViewSet(BaseLibraryViewSet):
    """
    ViewSet for viewing and editing Publisher instances.
    """
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    pagination_class = MetadataPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CategoryViewSet(BaseLibraryViewSet):
    """
    ViewSet for viewing and editing Category instances.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = MetadataPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class TagViewSet(BaseLibraryViewSet):
    """
    ViewSet for viewing and editing Tag instances.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = MetadataPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class BookViewSet(BaseLibraryViewSet):
    """
    ViewSet for viewing and editing Book instances.
    Features robust search, filtering, custom pagination, and N+1 query optimization.
    """
    serializer_class = BookSerializer
    pagination_class = BookPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'title',
        'isbn',
        'description',
        'authors__first_name',
        'authors__last_name',
        'publisher__name',
        'categories__name',
        'tags__name',
        'language',
        'publication_year',
        'shelf_location'
    ]
    ordering_fields = ['title', 'publication_year', 'average_rating', 'created_at', 'available_copies']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optimize database retrieval using select_related and prefetch_related,
        and dynamically apply request query filters.
        """
        queryset = Book.objects.all().select_related('publisher').prefetch_related(
            'authors', 'categories', 'tags'
        )

        # Apply filtering
        category = self.request.query_params.get('category')
        if category:
            if category.isdigit():
                queryset = queryset.filter(categories__id=category)
            else:
                queryset = queryset.filter(categories__slug=category)

        publisher = self.request.query_params.get('publisher')
        if publisher:
            queryset = queryset.filter(publisher_id=publisher)

        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language__iexact=language)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        publication_year = self.request.query_params.get('publication_year')
        if publication_year:
            queryset = queryset.filter(publication_year=publication_year)

        rating = self.request.query_params.get('rating')
        if rating:
            try:
                queryset = queryset.filter(average_rating__gte=float(rating))
            except ValueError:
                pass

        available = self.request.query_params.get('available')
        if available is not None:
            is_available = available.lower() in ('true', '1', 'yes')
            if is_available:
                queryset = queryset.filter(available_copies__gt=0)
            else:
                queryset = queryset.filter(available_copies=0)

        return queryset.distinct()

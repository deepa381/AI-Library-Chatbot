import re
import datetime
from rest_framework import serializers
from .models import Author, Publisher, Category, Tag, Book, BookLanguage, BookStatus

class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Author model.
    """
    class Meta:
        model = Author
        fields = [
            'id', 'first_name', 'last_name', 'biography', 
            'country', 'date_of_birth', 'website', 'is_active',
            'created_at', 'updated_at'
        ]


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for the Publisher model.
    """
    class Meta:
        model = Publisher
        fields = [
            'id', 'name', 'address', 'website', 'email', 
            'phone', 'is_active', 'created_at', 'updated_at'
        ]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tag model.
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at']


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for the Book model.
    Supports list of IDs for writing (POST/PUT/PATCH) and returns fully nested structures on reads (GET).
    """
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Author.objects.all(),
        help_text="IDs of the author(s) associated with this book."
    )
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        help_text="ID of the publisher associated with this book."
    )
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Category.objects.all(),
        help_text="IDs of the categories associated with this book."
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Tag.objects.all(),
        help_text="IDs of the tags associated with this book."
    )

    class Meta:
        model = Book
        fields = [
            'id', 'isbn', 'title', 'subtitle', 'description', 
            'publication_year', 'edition', 'language', 'pages', 
            'cover_image', 'total_copies', 'available_copies', 
            'average_rating', 'status', 'shelf_location', 
            'authors', 'publisher', 'categories', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['average_rating']

    def validate_isbn(self, value: str) -> str:
        """
        Normalize ISBN and ensure format and uniqueness constraints are met.
        """
        clean_value = re.sub(r'[-\s]', '', value).upper()
        if not re.match(r'^(?:\d{9}[\dX]|\d{13})$', clean_value):
            raise serializers.ValidationError("ISBN must be a valid 10 or 13-digit format (spaces/hyphens allowed).")

        queryset = Book.objects.filter(isbn=clean_value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A book with this ISBN already exists.")

        return clean_value

    def validate_publication_year(self, value: int) -> int:
        """
        Ensure publication year is within reasonable bounds and not in the future.
        """
        current_year = datetime.date.today().year
        if value < 800:
            raise serializers.ValidationError("Publication year cannot be earlier than 800 AD.")
        if value > current_year + 1:
            raise serializers.ValidationError(f"Publication year cannot be in the future (maximum allowed: {current_year + 1}).")
        return value

    def validate_pages(self, value: int) -> int:
        """
        Ensure page count is non-negative.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("Pages cannot be negative.")
        return value

    def validate_total_copies(self, value: int) -> int:
        """
        Ensure total copies are non-negative.
        """
        if value < 0:
            raise serializers.ValidationError("Total copies cannot be negative.")
        return value

    def validate_available_copies(self, value: int) -> int:
        """
        Ensure available copies are non-negative.
        """
        if value < 0:
            raise serializers.ValidationError("Available copies cannot be negative.")
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Object-level validation. Ensure available copies do not exceed total copies.
        """
        total_copies = attrs.get('total_copies', self.instance.total_copies if self.instance else 1)
        available_copies = attrs.get('available_copies', self.instance.available_copies if self.instance else 1)

        if available_copies > total_copies:
            raise serializers.ValidationError({
                "available_copies": "Available copies cannot exceed total copies owned."
            })

        return attrs

    def to_representation(self, instance: Book) -> dict:
        """
        Override default serializer representation to present fully nested object details on read.
        """
        # Inject detailed nested serializers for read representation
        self.fields['authors'] = AuthorSerializer(many=True, read_only=True)
        self.fields['publisher'] = PublisherSerializer(read_only=True)
        self.fields['categories'] = CategorySerializer(many=True, read_only=True)
        self.fields['tags'] = TagSerializer(many=True, read_only=True)
        return super().to_representation(instance)

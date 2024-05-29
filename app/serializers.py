from rest_framework import serializers
from .models import Book, ExtractedBook, Review

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['uid', 'title', 'author', 'genre', 'publication_date', 'frontal_page', 'book_file']

class ExtractedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedBook
        fields = ['uid', 'book', 'book_file']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['uid', 'book', 'reviewer_name', 'views', 'rating', 'comment']

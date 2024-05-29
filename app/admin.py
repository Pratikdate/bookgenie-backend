from django.contrib import admin
from .models import Book,ExtractedBook,Review

admin.site.register(Book)
admin.site.register(Review)
admin.site.register(ExtractedBook)

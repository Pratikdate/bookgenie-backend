from django.contrib import admin
from .models import Book, Bookmark,ExtractedBook,Review, UserProfile

admin.site.register(Book)
admin.site.register(Review)
admin.site.register(ExtractedBook)
admin.site.register(UserProfile)
admin.site.register(Bookmark)
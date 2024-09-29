from django.contrib import admin
from .models import Binding, BindingItem, Book, Bookmark, BookmarkID,ExtractedBook,Review, UserProfile ,VisitedActivity

admin.site.register(Book)
admin.site.register(Review)
admin.site.register(ExtractedBook)
admin.site.register(UserProfile)
admin.site.register(Bookmark)
admin.site.register(BookmarkID)
admin.site.register(Binding)
admin.site.register(BindingItem)
admin.site.register(VisitedActivity)
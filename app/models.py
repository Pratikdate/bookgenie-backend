# chat_app/models.py
from datetime import timezone
import uuid
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254)
    name = models.CharField(max_length=100)
    personal_info = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return self.user.username




class Book(models.Model):


     
    GENRE_CHOICES = [
        ('romance', 'Romance'),
        ('mystery', 'Mystery'),
        ('science_fiction', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('non_fiction', 'Non-Fiction'),
        ('biography', 'Biography'),
        ('self_help', 'Self-Help'),
        ('history', 'History'),
        ('horror', 'Horror'),
        ('adventure', 'Adventure'),
        ('young_adult', 'Young Adult'),
        ('children', 'Children’s Books'),
        ('cookbooks', 'Cookbooks'),
        ('travel', 'Travel'),
        ('science_nature', 'Science & Nature'),
        ('spiritual', 'Spiritual'),
        ('investing', 'Investing'),
        ('knowledge', 'Knowledge'),
    ]

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    title = models.CharField(max_length=100, unique=True)
    author = models.CharField(max_length=100)
    description = models.CharField(max_length=10000, blank=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES)
    views = models.IntegerField(default=0)
    star = models.IntegerField(default=0)
    publication_date = models.DateField()
    frontal_page = models.ImageField(upload_to='frontal_pages', null=True, blank=True)
    book_file = models.FileField(upload_to='books', null=True, blank=True)
    audiobook_file = models.FileField(upload_to='audiobooks/',null=True, blank=True)  # Store file path in the 'audiobooks' directory
    audiobook_duration = models.DurationField(null=True, blank=True) 

    def __str__(self):
        return str(self.title + " : " + str(self.uid))

class ExtractedBook(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    book = models.ForeignKey(Book, related_name='extracted_books', on_delete=models.CASCADE)
    book_file = models.FileField(upload_to='extracted_books', null=True, blank=True)

    def __str__(self):
        return str(self.book.title + " : " + str(self.book))

class Review(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    book = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField()
    comment = models.TextField()

    def __str__(self):
        return self.reviewer_name

class BookmarkID(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f'{self.user.username} - {self.book.title}'

class Bookmark(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    bookmarkId = models.ForeignKey(BookmarkID, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default=None)
    description = models.CharField(max_length=100, blank=True)
    page = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.bookmarkId} - {self.title}'


class Binding(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    title = models.CharField(max_length=255)
    book=models.ForeignKey(Book, on_delete=models.CASCADE,null=True,blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='bindings/',blank=True)  # Ensure to configure media settings
    date = models.DateField(auto_now_add=True)  # Automatically add the current date
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to User model

    def __str__(self):
        return self.title


class BindingItem(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('youtubevideo', 'YouTube Video'),
        ('notes', 'Notes'),
        ('web', 'Web'),
    ]

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True) # Automatically generated unique ID
    item_position = models.PositiveIntegerField()  # Position number of the item
    binding = models.ForeignKey(Binding, on_delete=models.CASCADE, related_name='items')  # Link to Binding model
    resource_type = models.CharField(
        max_length=100,
        choices=RESOURCE_TYPE_CHOICES,
        blank=True,
        default='web'  # Set a default value if needed
    )
    resource_link = models.URLField(max_length=500)  # URL link to the resource

    def __str__(self):
        return f"Item {self.item_position} in {self.binding.title}"



class VisitedActivity(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    visited_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-visited_at']  # Orders by most recent visits

    def __str__(self):
        return f'{self.book} visited at {self.visited_at}'



class Library(models.Model):
    uid=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    book=models.ForeignKey(Book, on_delete=models.CASCADE,null=True,blank=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    date_time=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.book} add by {self.user}'
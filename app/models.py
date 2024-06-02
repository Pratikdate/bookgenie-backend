# chat_app/models.py
import uuid
from django.db import models



class Book(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True,primary_key=True)
    title = models.CharField(max_length=100,unique=True)
    author = models.CharField(max_length=100)
    genre = models.CharField(max_length=50)
    views = models.IntegerField(default=0)
    publication_date = models.DateField()
    frontal_page = models.ImageField(upload_to='frontal_pages', null=True, blank=True)
    book_file = models.FileField(upload_to='books', null=True, blank=True)

    def __str__(self):
        return str(self.uid)

class ExtractedBook(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    book = models.ForeignKey(Book, related_name='extracted_books', on_delete=models.CASCADE,primary_key=True)
    book_file = models.FileField(upload_to='extracted_books', null=True, blank=True)

    def __str__(self):
        return str(self.book)

class Review(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    book = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField()
    comment = models.TextField()

    def __str__(self):
        return self.reviewer_name
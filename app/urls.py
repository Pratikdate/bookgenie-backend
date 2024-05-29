# chat_app/urls.py
from django.urls import path
from .views import home,BookList,ExtractBookDetail

urlpatterns = [
    path("",home.as_view()),
    path('books/', BookList.as_view(), name='book-list'),
    path('extractBooks/<str:pk>/', ExtractBookDetail.as_view(), name='book-detail'),
]
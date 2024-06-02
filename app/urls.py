# chat_app/urls.py
from django.urls import path
from .views import home,PopularBookList,ShelfBookList,ExtractBookDetail

urlpatterns = [
    path("",home.as_view()),
    path('popularbooks/', PopularBookList.as_view(), name='book-list'),
     path('shelfbooks/', ShelfBookList.as_view(), name='book-list'),
    path('extractBooks/<str:pk>/', ExtractBookDetail.as_view(), name='book-detail'),
]
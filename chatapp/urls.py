from django.urls import path
from .views import  ChatPDFView, Home
urlpatterns = [
    path("",Home.as_view()),
    path("chatpdf/<str:pk>",ChatPDFView.as_view(),name="chatpdf"),
]
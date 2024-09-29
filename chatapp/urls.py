from django.urls import path
from .views import  BindingSummaryAPIView, ChatPDFView, Home
urlpatterns = [
    path("",Home.as_view()),
    path("chatpdf/<str:pk>",ChatPDFView.as_view(),name="chatpdf"),
    path('binding-summary/<str:pk>/', BindingSummaryAPIView.as_view(), name='binding-summary'),
]
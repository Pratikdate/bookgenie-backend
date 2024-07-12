# chat_app/urls.py
from django.urls import path
from .views import BookmarkListView, BookmarkCreateView, UserProfileView, home,PopularBookList,ShelfBookList,ExtractBookDetail,RegisterView, LoginView, ForgotPasswordView,CheckAuthStatus,CustomAuthToken

urlpatterns = [
    path("",home.as_view()),
    path('check-auth-status/', CheckAuthStatus.as_view(), name='check_auth_status'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('bookmarks/<str:pk>', BookmarkCreateView.as_view(), name='bookmark-create'),
    path('bookmarks/', BookmarkListView.as_view(), name='bookmark-list-view'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('popularbooks/<int:pk>', PopularBookList.as_view(), name='book-list'),
     path('shelfbooks/<int:pk>', ShelfBookList.as_view(), name='book-list'),
    path('extractBooks/<str:pk>/', ExtractBookDetail.as_view(), name='book-detail'),
]
# chat_app/urls.py
from django.urls import path
from .views import AddToLibrary, BindingAPIView, BindingDetailAPIView, BindingItemAPIView, BindingItemDetailAPIView, BindingListCreateView, BookBindingDetailAPIView, BookSearchAPIView, BookmarkIDView, BookmarkListView, BookmarkCreateView, UserProfileView, VisitedActivityDetail, VisitedActivityList, home,PopularBookList,ShelfBookList,ExtractBookDetail,RegisterView, LoginView, ForgotPasswordView,CheckAuthStatus,CustomAuthToken,LogoutView

urlpatterns = [

    # Auths
    path("",home.as_view()),
    path('check-auth-status/', CheckAuthStatus.as_view(), name='check_auth_status'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('logout/',LogoutView.as_view(), name='logout'),


    #Bookmarks Handling
    path('bookmarks/<str:pk>', BookmarkCreateView.as_view(), name='bookmark-create'),
    path('bookmarksID/<str:pk>', BookmarkIDView.as_view(), name='bookmarkID-delete'),
    path('bookmarks/', BookmarkListView.as_view(), name='bookmark-list-view'),
    path('books/search/', BookSearchAPIView.as_view(), name='book-search-api'),

    # Handle Books
    
    path('books/genre/<str:genre>/<int:pk>/', PopularBookList.as_view(), name='book-list-on-genre'),
    path('popularbooks/<int:pk>', PopularBookList.as_view(), name='book-list'),
    path('shelfbooks/<int:pk>', ShelfBookList.as_view(), name='book-list'),
    path('extractBooks/<str:pk>/', ExtractBookDetail.as_view(), name='book-detail'),


    # Navigation 
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('visited-activities/', VisitedActivityList.as_view(), name='visited-activity-list'),
    path('visited-activities/<str:pk>/', VisitedActivityDetail.as_view(), name='visited-activity-detail'),
    path('bindings/', BindingAPIView.as_view(), name='binding-list'),
    path('bindings/<str:pk>/', BindingDetailAPIView.as_view(), name='binding-detail'),
    path('book-binding/<str:pk>/', BookBindingDetailAPIView.as_view(), name='book-binding-list'),

    # BindingItem API
    path('binding-items/', BindingItemAPIView.as_view(), name='bindingitem-list'),
    path('binding-items/<str:pk>/', BindingItemDetailAPIView.as_view(), name='bindingitem-detail'),
    path('binding/<str:binding_id>/item/<str:item_id>/', BindingItemDetailAPIView.as_view(), name='bindingitem-detail'),


    #library API's
    path('library-books/', AddToLibrary.as_view(), name='library-books-details'),
    path('library-books/<str:pk>/', AddToLibrary.as_view(), name='library-books'),

]

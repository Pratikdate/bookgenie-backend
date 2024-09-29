# chat_app/views.py
from django.utils import timezone
from django.db.models import Q
import json
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from marshmallow import ValidationError
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Binding, BindingItem, Book, Bookmark, BookmarkID,  ExtractedBook, UserProfile, VisitedActivity
from .serializers import BindingItemSerializer, BindingSerializer, BookSerializer, BookmarkIDSerializer, BookmarkSerializer, CustomAuthTokenSerializer, ExtractedBookSerializer, GetVisitedActivitySerializer, UserProfileSerializer, VisitedActivitySerializer #, VisitedActivitySerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from .serializers import UserSerializer, LoginSerializer
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.exceptions import NotFound



class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username=username)
            
        except UserModel.DoesNotExist:
            return None
        if user.password==password:
            return user
        return None




class home(APIView):
    def get(self,request):
        return HttpResponse("hello world")
    
    # def post(self, request, *args, **kwargs):


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)


    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = UserProfile(user=user)

        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookmarkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        bookmark_id = BookmarkID.objects.filter(user=request.user, book=pk)
        bookmarks = Bookmark.objects.filter(bookmarkId=bookmark_id.get()).values_list('uid','title','description','page','created_at')
        #berializer = BookmarkSerializer(bookmarks, many=True)
        return Response(bookmarks, status=status.HTTP_200_OK)

    def post(self, request, pk):
        bookmark_data = {
            'user': request.user.id,
            'book': pk
        }
        

        # Check if BookmarkID already exists
        try:
            bookmark_id_instance = BookmarkID.objects.get(user=request.user, book_id=pk)
        except BookmarkID.DoesNotExist:
            bookmark_id_serializer = BookmarkIDSerializer(data=bookmark_data)
            if bookmark_id_serializer.is_valid():
                bookmark_id_instance = bookmark_id_serializer.save()
            else:
                return Response(bookmark_id_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create or update Bookmark
        data = request.data.copy()
        data['bookmarkId'] = bookmark_id_instance.uid
        bookmark_serializer = BookmarkSerializer(data=data)
        if bookmark_serializer.is_valid():
            bookmark_serializer.save()
            return Response(bookmark_serializer.data, status=status.HTTP_201_CREATED)
        return Response(bookmark_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        try:
            bookmark = Bookmark.objects.get(pk=pk)
        except Bookmark.DoesNotExist:
            raise NotFound(detail="Bookmark not found", code=status.HTTP_404_NOT_FOUND)

        serializer = BookmarkSerializer(bookmark)
        bookmark.delete()

        return Response({"message": "Bookmark deleted successfully", "data": serializer.data}, status=status.HTTP_200_OK)



class BookmarkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookmarks = BookmarkID.objects.filter(user=request.user)
        serializer = BookmarkIDSerializer(bookmarks, many=True)
        
        dataList = []
        for data in serializer.data:
            # Retrieve book details and add bookmarkuid
            book_data = Book.objects.filter(uid=data['book']).values(
                'uid', 'title', 'author', 'views', 'genre', 
                'publication_date', 'frontal_page', 'book_file', 'description'
            ).first()

            if book_data:
                # Append bookmarkuid to the book data
                book_data['bookmarkuid'] = data['uid']
                dataList.append(book_data)

       
        return Response(dataList, status=status.HTTP_200_OK)
    
    

    

class CheckAuthStatus(APIView):
    authentication_classes = [TokenAuthentication]
    
    def get(self, request):
        return Response({'is_authenticated': True})


class CustomAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = EmailBackend().authenticate(request, username=email, password=password)
            
            if user is not None:
                return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Generate a password reset link and send it to the user
            reset_link = f"http://your-domain.com/reset-password?email={email}"
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                'from@example.com',
                [email],
                fail_silently=False,
            )
            return Response({"message": "Password reset email sent"}, status=status.HTTP_200_OK)
        return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)



class PopularBookList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, genre=None):
        # Filter books by the specified genre
        if genre:
            print(genre)
            books = Book.objects.filter(genre__iexact=genre).order_by('-views')  
        else:
            books = Book.objects.order_by('-views')

        print(books)

        # Check if enough books exist for pagination
        if books.count() >= pk + 1:
            try:
                # Slice the books based on the pk (pagination)
                books_ = books[(pk - 3):pk]
                serializer = BookSerializer(books_, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_204_NO_CONTENT)
        else:
            serializer = BookSerializer(books, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Return 204 if not enough books exist
        return Response(status=status.HTTP_204_NO_CONTENT)

                
            
    def post(self, request):
            serializer = BookSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ShelfBookList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,pk):
        books = Book.objects.order_by('publication_date')
       
        if(books.count()>=pk+1):
            try:
                books_=books[(pk-3):pk]

                serializer = BookSerializer(books_, many=True)
        
                return Response(serializer.data,status=status.HTTP_200_OK)


                
            except:
                return Response(status=status.HTTP_204_NO_CONTENT)
            
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookSearchAPIView(APIView):
    """
    API view to search for books by name or author.
    """
    
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', None)  # Get the search query from the query parameters
        
        if query:
            # Filter books by name or author using case-insensitive matching
            books = Book.objects.filter(
                Q(title__icontains=query) | Q(author__icontains=query)
            )
        else:
            # If no query is provided, return an empty result set
            books = Book.objects.none()

        # Serialize the filtered books
        serializer = BookSerializer(books, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

        

    
class BookmarkIDView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self,request,pk):
        try:
            bookmark = BookmarkID.objects.get(pk=pk)
        except Bookmark.DoesNotExist:
            raise NotFound(detail="Bookmark not found", code=status.HTTP_404_NOT_FOUND)

        serializer = BookmarkIDSerializer(bookmark)
        bookmark.delete()

        return Response({"message": "BookmarkID deleted successfully", "data": serializer.data}, status=status.HTTP_200_OK)




class ExtractBookDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return ExtractedBook.objects.get(pk=pk)
        except ExtractedBook.DoesNotExist:
            raise Http404  # type: ignore
        
    def setView(self,pk):
        try:
            book_id=Book.objects.get(pk=pk)
            book_id.views=int(book_id.views)+1
            book_id.save()
        except Book.DoesNotExist:
            raise Http404  # type: ignore
        


    def get(self, request, pk):
        book = self.get_object(pk)
        self.setView(pk)
        serializer = ExtractedBookSerializer(book)
        headers = {'UID': book.uid}
        return Response(serializer.data,headers=headers)

    def put(self, request, pk):
        book = self.get_object(pk)
        serializer = ExtractedBookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = self.get_object(pk)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class BindingListCreateView(APIView):
    """
    List all bindings or create a new binding.
    """

    def get(self, request):
        # Retrieve all binding instances
        bindings = Binding.objects.filter(user=request.user)
        serializer = BindingSerializer(bindings, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Create a new binding instance
        serializer = BindingSerializer(data=request.data)
        if serializer.is_valid():
            # Set the user from the request
            serializer.validated_data['user'] = request.user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    




# API for handling Binding objects
class BindingAPIView(APIView):

    def get(self, request, *args, **kwargs):
        """Handle GET requests to retrieve all bindings"""
        bindings = Binding.objects.filter(user=request.user)
        serializer = BindingSerializer(bindings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Handle POST requests to create a new binding"""
        data = request.data.copy()  # Create a mutable copy
        data["user"] = request.user.id  # Add user ID instead of user object

        serializer = BindingSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BookBindingDetailAPIView(APIView):

    def get(self, request, pk):
        """
        Retrieve  binding for the current user and a specific book.
        """
        bindings = Binding.objects.filter(user=request.user, book=pk)
        
        serializer = BindingSerializer(bindings, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        """Delete a binding"""
        binding = get_object_or_404(Binding, pk=pk)
        binding.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




# API for a specific binding (for retrieve, update, delete)
class BindingDetailAPIView(APIView):

    def get(self, request, pk, *args, **kwargs):
        """Retrieve a specific binding by its ID"""
        binding = get_object_or_404(Binding, pk=pk)
        serializer = BindingSerializer(binding)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        """Update an existing binding"""
        binding = get_object_or_404(Binding, pk=pk)
       
        serializer = BindingSerializer(binding, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        print(serializer.errors)  # Print errors to debug
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def delete(self, request, pk):
        try:
            binding = get_object_or_404(Binding, pk=pk)
            binding.delete()

            # Return a 204 No Content response, indicating successful deletion
            return Response(
                {"detail": "Visited activity successfully deleted."},
                status=status.HTTP_204_NO_CONTENT
            )

        except VisitedActivity.DoesNotExist:
            # If the VisitedActivity does not exist, return a 404 Not Found
            return Response({"error": "Visited activity not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Handle any other exceptions and return a 500 Internal Server Error
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API for handling BindingItem objects
class BindingItemAPIView(APIView):

    def get(self, request, *args, **kwargs):
        """Retrieve all binding items"""
        binding_items = BindingItem.objects.all()
        serializer = BindingItemSerializer(binding_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Create a new binding item"""
        serializer = BindingItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API for a specific binding item (retrieve, update, delete)
class BindingItemDetailAPIView(APIView):

    def get(self, request, pk, *args, **kwargs):
        """Retrieve a specific binding item"""
        binding_item = get_object_or_404(BindingItem, pk=pk)
        serializer = BindingItemSerializer(binding_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


    def put(self, request, binding_id, item_id):
        # Get the binding and the item to be updated
        binding = get_object_or_404(Binding, pk=binding_id)
        binding_item = get_object_or_404(BindingItem, pk=item_id)

        # Get the new position from the request data
        new_position = request.data.get('item_position')
        if new_position is None:
            raise ValidationError("item_position is required.")

        try:
            new_position = int(new_position)
        except ValueError:
            raise ValidationError("item_position must be an integer.")

        # Check the number of items in the binding
        total_items = BindingItem.objects.filter(binding=binding).count()

        if new_position < 1 or new_position > total_items:
            raise ValidationError(f"item_position must be between 1 and {total_items}.")

        # Get all items of this binding ordered by position
        all_items = BindingItem.objects.filter(binding=binding).order_by('item_position')

        # If the new position is different from the current one, rearrange the items
        if binding_item.item_position != new_position:
            if new_position < binding_item.item_position:
                # Shift positions down (move item up in the list)
                items_to_shift = all_items.filter(item_position__gte=new_position, item_position__lt=binding_item.item_position)
                for item in items_to_shift:
                    item.item_position += 1
                    item.save()

            elif new_position > binding_item.item_position:
                # Shift positions up (move item down in the list)
                items_to_shift = all_items.filter(item_position__lte=new_position, item_position__gt=binding_item.item_position)
                for item in items_to_shift:
                    item.item_position -= 1
                    item.save()

            # Update the selected item's position
            binding_item.item_position = new_position
            binding_item.save()

        serializer = BindingItemSerializer(binding_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    def delete(self, request, pk, *args, **kwargs):
        """Delete a binding item"""
        binding_item = get_object_or_404(BindingItem, pk=pk)
        binding_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VisitedActivityList(APIView):
    """
    List all visited activities or create a new visited activity.
    """
    def get(self, request):
        visited_activities = VisitedActivity.objects.filter(user=request.user)
    
        serializer = GetVisitedActivitySerializer(visited_activities, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()  # Create a copy of the request data

        # Get the book ID from the request data
        book_id = request.data.get('book')

        try:
            # Fetch the Book instance by the book ID
            book = Book.objects.get(uid=book_id)
            
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the VisitedActivity for this book and user already exists
        visited_activity = VisitedActivity.objects.filter(book=book, user=request.user).first()

        if visited_activity:
            # If it exists, update the visited_at timestamp
            visited_activity.visited_at = timezone.now()
            visited_activity.save()

            serializer = VisitedActivitySerializer(visited_activity)
            return Response(serializer.data, status=status.HTTP_200_OK)  # 200 for updated
        else:
            # If it doesn't exist, create a new VisitedActivity
            data['user'] = request.user.id  # Add the user ID to the data
            data['book'] = book.uid  # Set the book instance
            serializer = VisitedActivitySerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)  # 201 for created

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class VisitedActivityDetail(APIView):
    """
    Retrieve, update, or delete a specific visited activity.
    """
    def get_object(self, pk):
        try:
            return VisitedActivity.objects.get(pk=pk)
        except VisitedActivity.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        visited_activity = self.get_object(pk)
        serializer = VisitedActivitySerializer(visited_activity)
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            # Get the VisitedActivity object using the provided pk (primary key)
            visited_activity = self.get_object(pk)

            # Delete the object
            visited_activity.delete()

            # Return a 204 No Content response, indicating successful deletion
            return Response(
                {"detail": "Visited activity successfully deleted."},
                status=status.HTTP_204_NO_CONTENT
            )

        except VisitedActivity.DoesNotExist:
            # If the VisitedActivity does not exist, return a 404 Not Found
            return Response({"error": "Visited activity not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Handle any other exceptions and return a 500 Internal Server Error
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# chat_app/views.py
import json
from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Book, Bookmark, BookmarkID,  ExtractedBook, UserProfile
from .serializers import BookSerializer, BookmarkIDSerializer, BookmarkSerializer, CustomAuthTokenSerializer, ExtractedBookSerializer, UserProfileSerializer
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
        
        dataList=[Book.objects.filter(uid=data['book']).values_list('uid', 'title', 'author','views', 'genre', 'publication_date', 'frontal_page', 'book_file','description') for data in serializer.data ]
        
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
            print(request.data)
            
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

    def get(self, request,pk):
        books = Book.objects.order_by('-views')
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








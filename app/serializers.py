from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BindingItem, Book, Bookmark, BookmarkID,  ExtractedBook, Library, Review, UserProfile, Binding, VisitedActivity #VisitedActivity
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, get_user_model






class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'email', 'name', 'personal_info', 'image']

class BookmarkIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookmarkID
        fields = ['uid','user','book']

class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ['uid',"bookmarkId","title",'description','page','created_at']



class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField( trim_whitespace=False)

    

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            
            user = UserModel.objects.get(username=username)
            
        except UserModel.DoesNotExist:
            return None
        if user.password==password:
            return user
        return None




    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = self.authenticate(request=self.context.get('request'), username=email, password=password)

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}
            

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()



class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['uid', 'title', 'author','views',"description", 'genre', 'publication_date', 'frontal_page', 'book_file','audiobook_file',"audiobook_duration"]

class ExtractedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedBook
        fields = ['uid', 'book', 'book_file']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['uid', 'book', 'reviewer_name', 'rating', 'comment']

class BindingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BindingItem
        fields = ['uid', 'item_position', 'binding', 'resource_type','resource_link']


class BindingSerializer(serializers.ModelSerializer):
    items = BindingItemSerializer(many=True, read_only=True)  # Nested binding items

    class Meta:
        model = Binding
        fields = ['uid', 'title','book', 'description', 'image', 'date', 'user', 'items']

class VisitedActivitySerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)  # Remove 'many=True' since it's a single object

    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())  # Expect book ID as input


    class Meta:
        model = VisitedActivity
        fields = ['uid', 'book', 'user', 'visited_at']
        

class GetVisitedActivitySerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)  # This includes the complete book object

    class Meta:
        model = VisitedActivity
        fields = ['uid', 'book', 'user', 'visited_at']

class LibrarySerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    class Meta:
        model = Library
        fields = ['uid', 'book', 'user', 'date_time']
           
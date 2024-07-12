# chat_app/views.py
import json
from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, JsonResponse
from .models import Book, Bookmark, ExtractedBook, UserProfile
from .serializers import BookSerializer, BookmarkSerializer, CustomAuthTokenSerializer, ExtractedBookSerializer, UserProfileSerializer
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

    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        except UserProfile.DoesNotExist:
            serializer = UserProfileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BookmarkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,pk):
        bookmarks = Bookmark.objects.filter(user=request.user,book=pk)
        serializer = BookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request,pk):
        print(request.data)
        data = request.data.copy()
        data['user'] = request.user.id
        data['book'] = pk
        try:
            bookmark = Bookmark.objects.get(user=request.user,book=pk)
           
            serializer = BookmarkSerializer(bookmark, data=data, partial=True)
        except Bookmark.DoesNotExist:
            serializer = BookmarkSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class BookmarkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookmarks = Bookmark.objects.filter(user=request.user)
        serializer = BookmarkSerializer(bookmarks, many=True)
        dataList=[Book.objects.filter(uid=data['book']).values_list('uid', 'title', 'author','views', 'genre', 'publication_date', 'frontal_page', 'book_file') for data in serializer.data ]
        print(dataList)
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








# class MessageListCreateAPIView(generics.ListCreateAPIView):
#     queryset = Message.objects.all()
#     serializer_class = MessageSerializer
    

#     def post(self, request, *args, **kwargs):
#         # Extract the sender and text from the request data
        
#         text = request.data.get('text')
#         user = request.data.get('user')
#         pdf_docs=[]

#         # Validate the data
#         if not user or not text:
#             return Response({'error': 'Sender and text fields are required'}, status=400)

#         # Create the message instance
        
#         # Serialize the message instance
        
#         filepath = Document.objects.filter(user=user).values("file")[0]['file']
#         try:
#             pdf_docs.append(open(os.path.join(settings.MEDIA_ROOT+"/"+filepath), 'rb'))
#             pdf_name=os.path.basename(filepath)
            
#             raw_text=HandelChat.get_pdf_text(pdf_docs)
            
#             text_chunks =HandelChat.get_text_chunks(raw_text)
#             HandelChat.get_vector_store(text_chunks,pdf_name,user)
            

#             if text:
#                 response=HandelChat.user_input(text,pdf_name,user)
#                 print(response)
#                 message = Message.objects.create(user=user, text=text,response=response['output_text'])
#                 message.save()
#                 return Response(response, status=201)
            

#         except:
#             return Response({"msg":"Something wrong"}, status=400)

    
        

# class DocumentUploadAPIView(APIView):
#     parser_classes = (MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         # Extract the sender and text from the request data
#         file = request.data.get('file')
#         user = request.data.get('user')

        
#         user_id=json.load(user)["user_Id"]

#         # Validate the data
#         if not file:
#             return Response({'error': 'Sender and text fields are required'}, status=400)

#         # Create the message instance
#         message = Document.objects.create(user= user_id,name=os.path.basename(str(file)), file=file)

#         # Serialize the message instance
        
#         if message.DoesNotExist:
           
#             message.save()
#             return Response({"msg":"successs"}, status=201)
#         else:
#             return Response({"msg":"error"}, status=400)

        



# class HandelChat:
      
#     def get_pdf_text(pdf_docs):
#         text=""
#         for pdf in pdf_docs:
#             pdf_reader= PdfReader(pdf)
#             for page in pdf_reader.pages:
#                 text+= page.extract_text()
#         return  text



#     def get_text_chunks(text):
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
#         chunks = text_splitter.split_text(text)
#         return chunks


#     def get_vector_store(text_chunks,pdf_name,user):
        
#         embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
#         vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
#         vector_store.save_local(settings.MEDIA_ROOT+"/Vector_store"+f"/{user}/{pdf_name}")


#     def get_conversational_chain():

#         prompt_template = """
#         Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
#         provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
#         Context:\n {context}?\n
#         Question: \n{question}\n

#         Answer:
#         """

#         model = ChatGoogleGenerativeAI(model="gemini-pro",
#                                 temperature=0.3)

#         prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
#         chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

#         return chain



#     def user_input(user_question,pdf_name,user):
#         embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
        
#         new_db = FAISS.load_local(settings.MEDIA_ROOT+"/Vector_store"+f"/{user}/{pdf_name}", embeddings)
#         docs = new_db.similarity_search(user_question)

#         chain = HandelChat.get_conversational_chain()

        
#         response = chain(
#             {"input_documents":docs, "question": user_question}
#             , return_only_outputs=True)
#         return response
        

    

        


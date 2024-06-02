# chat_app/views.py
import json
from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from .models import Book, ExtractedBook
from .serializers import BookSerializer, ExtractedBookSerializer




class home(APIView):
    def get(self,request):
        return HttpResponse("hello world")
    
    # def post(self, request, *args, **kwargs):




class PopularBookList(APIView):
    def get(self, request):
        books = Book.objects.order_by('-views')[:5]
        serializer = BookSerializer(books, many=True)
        
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ShelfBookList(APIView):
    def get(self, request):
        books = Book.objects.order_by('publication_date')[:5]
        serializer = BookSerializer(books, many=True)
        
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ExtractBookDetail(APIView):
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
        

    

        


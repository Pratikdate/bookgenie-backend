import traceback
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
import json
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import requests
from chatapp.utils import HandleBindingItemSummary
from app.serializers import BindingItemSerializer, BindingSerializer
from app.models import Binding, BindingItem, ExtractedBook, VisitedActivity
from dotenv import load_dotenv
from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
#for summary


# from pdfminer.high_level import extract_text as extract_pdf_text
# from pytesseract import image_to_string  # For image OCR
from googleapiclient.discovery import build  # For YouTube video transcripts
# from docx import Document  # For Word document extraction
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter




# Ensure environment variables are loaded
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")




class BindingSummaryAPIView(APIView):

    def get(self, request, pk):
        try:
            # Retrieve the binding item by primary key
            binding = get_object_or_404(Binding, pk=pk)
            serializer = BindingSerializer(binding)

            # Get content type and content path
            content = serializer.data.get('items')  # Assuming resource_type field exists

            summarise_data=[]

            for binding_item in content:
                content_type = binding_item['resource_type']
                content_path = binding_item['resource_link']  # Adjust the field name as necessary

                # Initialize the summary handler
                summary_handler = HandleBindingItemSummary()

                # Summarization logic based on content type
                summary = summary_handler.summarize_content(content_type, content_path)
                summarise_data.append(summary)



            return Response({
                    'binding_item': serializer.data,
                    'summary': summarise_data,
                }, status=status.HTTP_200_OK)

        except BindingItem.DoesNotExist:
                return Response({'error': 'Binding item not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




class BindingSummaryAPIView(APIView):

    def get(self, request, pk):
        try:
            # Retrieve the binding item by primary key (pk)
            binding = get_object_or_404(Binding, pk=pk)
            
            # Serialize the binding to access its data
            serializer = BindingSerializer(binding)
            
            # Get the binding items (assuming 'items' is a list of binding resources)
            content = serializer.data.get('items', [])  # 'items' refers to the list of resources for the binding
            
            summarised_data = []

            # Initialize the summary handler
            summary_handler = HandleBindingItemSummary()

            # Loop through each binding item and summarize it based on its type
            for binding_item in content:
                content_type = binding_item['resource_type']
                content_path = binding_item['resource_link']  # Adjust field names as necessary
                
                if not content_type or not content_path:
                    continue  # Skip if any required data is missing
                
                
                # Use the summary handler to summarize content based on the type
                summary = summary_handler.summarize_content(content_type, content_path)
                
                # Add the summarized content to the list
                summarised_data.append({
                    'resource_type': content_type,
                    'resource_link': content_path,
                    'summary': summary
                })

            # Return a successful response with the serialized data and summaries
            return Response({
                'binding_item': serializer.data,
                'summaries': summarised_data,
            }, status=status.HTTP_200_OK)

        except BindingItem.DoesNotExist:
            return Response({'error': 'Binding item not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': e}, status=status.HTTP_400_BAD_REQUEST)





# View for handling chat with PDF
class ChatPDFView(APIView):
    def get(self, request, pk):
        try:
            handelChat = HandelChat(user_name=request.user.username)
            extractedBook = ExtractedBook.objects.get(pk=pk)

            # Read the PDF file from the media directory
            pdf_path = f"media/{extractedBook.book_file}"
            raw_text = handelChat.get_pdf_text(pdf_path)

            # Process the text and create the vector store
            text_chunks = handelChat.get_text_chunks(raw_text)
            handelChat.get_vector_store(text_chunks)

            return Response({"success": True, "message": "Vector store created for this book"}, status=status.HTTP_200_OK)

        except ExtractedBook.DoesNotExist:
            return Response({"success": False, "message": f"Book with id {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "message": "Error creating vector store", 'detail': e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, pk):
        try:
            handelChat = HandelChat()
            user_question = request.data.get('content')

            if not user_question:
                return Response({"success": False, "message": "No question provided"}, status=status.HTTP_400_BAD_REQUEST)

            response = handelChat.user_input(user_question)

            if response:
                return Response({"success": True, "content": response}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "No response generated"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Sample Home View
class Home(APIView):
    def get(self, request):
        return HttpResponse("Hello world")

# class HandelChat:
#     def __init__(self, user_name=None):
#         self.user_name = user_name or "User"  # Personalize with user's name if available

#     def get_pdf_text(self, path):
#         text = ""
#         try:
#             with open(path, "rb") as file:
#                 pdf_reader = PdfReader(file)
#                 for page in pdf_reader.pages:
#                     text += page.extract_text()
#             # Normalize and clean the text
#             text = text.replace("\n", " ").strip()
#         except Exception as e:
#             print(f"An error occurred: {e}")
#         return text

#     def get_text_chunks(self, text):
#         splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
#         chunks = splitter.split_text(text)
#         return chunks

#     def get_vector_store(self, chunks):
#         embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
#         vector_store = FAISS.from_texts(chunks, embedding=embeddings)
#         vector_store.save_local("faiss_index")

#     def get_conversational_chain(self):
#         # Prompt template with placeholders for book metadata
#         prompt_template = """
#         You are an Mr.Chat an AI assistant specializing in books. Always prioritize answering based on the given book details. 

#         Book Details:
#         - Title: {book_title}
#         - Author: {book_author}
#         - Description: {book_description}
#         - Published At: {book_publish_at}
#         - Genre: {book_genre}

#         Context (Relevant Documents):
#         {context}

#         Question: {question}

#         Answer accurately based on the book "{book_title}". If the provided context contains relevant information, use it to enhance your response. Do not provide generic or unrelated information. If the answer is not available in the book or context, state that clearly.

#         """
        
#         # model = ChatGoogleGenerativeAI(
#         #     model="gemini-pro", 
#         #     client=genai,  
#         #     temperature=0.7,
#         # )
#         model=Ollama(model="qwen:0.5b")
#         prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question", 
#                                                                            "book_title", "book_author", 
#                                                                            "book_description", "book_publish_at", 
#                                                                            "book_genre"])
#         chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
#         return chain


#     def handle_greetings(self, user_question):
#         greetings = {
#             "hii": f"Hello, {self.user_name}! How can I assist you today?",
#             "hello": f"Hi there, {self.user_name}! What can I do for you?",
#             "good morning": f"Good morning, {self.user_name}! How can I help you today?",
#             "good evening": f"Good evening, {self.user_name}! What would you like to ask?",
#             "what is your name": "I am BookBot, here to help you with your questions."
#         }
#         return greetings.get(user_question.lower(), None)

#     def handle_unknown_answer(self):
#         return (
#             f"Sorry, {self.user_name}, I couldn't find the answer to your question. "
#             "You might want to try rephrasing or asking about a specific topic in the book."
#         )

#     def user_input(self, user_question):
#         print(f"User Question: {user_question}")

#         # Handle personalized greetings
#         greeting_response = self.handle_greetings(user_question)
#         if greeting_response:
#             return greeting_response

#         # Load FAISS index and perform similarity search
#         embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
#         new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
#         docs = new_db.similarity_search(user_question, k=8)

#         # Check if relevant documents were retrieved
#         if not docs:
#             print("No relevant documents found.")
#             return self.handle_unknown_answer()

#         # Retrieve latest book metadata
#         latest_book = VisitedActivity.objects.order_by('-visited_at').first()
#         if latest_book:
#             book_title = latest_book.book.title
#             book_author = latest_book.book.author
#             book_description = latest_book.book.description
#             book_publish_at = latest_book.book.publication_date
#             book_genre = latest_book.book.genre
#             print(f"Latest Book: {book_title} by {book_author}")
#         else:
#             book_title = "Unknown Title"
#             book_author = "Unknown Author"
#             book_description = "No description available."
#             book_publish_at = "Unknown"
#             book_genre = "Unknown"
#             print("No recent book found in the database.")

#         # Generate a response using the conversational chain
#         try:
#             chain = self.get_conversational_chain()
#             response = chain({
#                 "input_documents": docs,
#                 "question": user_question,
#                 "book_title": book_title,
#                 "book_author": book_author,
#                 "book_description": book_description,
#                 "book_publish_at": book_publish_at,
#                 "book_genre": book_genre
#             }, return_only_outputs=True)
#             return response.get("output_text", self.handle_unknown_answer())
#         except Exception as e:
#             print(f"Error generating response: {e}")
#             return self.handle_unknown_answer()





class HandelChat:
    def __init__(self, user_name=None):
        self.user_name = user_name or "User"
        print(f"[INIT] HandelChat initialized with user_name: {self.user_name}")

    def get_pdf_text(self, path):
        """Extracts text from a given PDF file."""
        print(f"[INFO] Extracting text from PDF: {path}")
        text = ""
        try:
            with open(path, "rb") as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            cleaned_text = text.replace("\n", " ").strip()
            print(f"[SUCCESS] Extracted {len(cleaned_text)} characters from PDF.")
            return cleaned_text
        except Exception as e:
            print(f"[ERROR] Failed to read PDF: {e}")
            traceback.print_exc()
            return ""

    def get_text_chunks(self, text):
        """Splits large text into manageable chunks."""
        print(f"[INFO] Splitting text into chunks (Size: {len(text)} characters)")
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
            chunks = splitter.split_text(text)
            print(f"[SUCCESS] Split text into {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            print(f"[ERROR] Failed to split text: {e}")
            traceback.print_exc()
            return []

    def get_vector_store(self, chunks):
        """Generates embeddings and stores them in a FAISS vector store."""
        print(f"[INFO] Creating FAISS vector store with {len(chunks)} chunks.")
        try:
            embeddings = OllamaEmbeddings(model="qwen:0.5b")
            vector_store = FAISS.from_texts(chunks, embedding=embeddings)
            vector_store.save_local("faiss_index")
            print("[SUCCESS] FAISS vector store created and saved locally.")
        except Exception as e:
            print(f"[ERROR] Failed to create FAISS vector store: {e}")
            traceback.print_exc()

    def get_conversational_chain(self):
        """Creates a conversational chain using the DeepSeek model in Ollama."""
        print("[INFO] Setting up conversational chain using DeepSeek model.")
        try:
            prompt_template = """
            Context:
            - Book Title: {book_title}
            - Author: {book_author}
            - Description: {book_description}
            - Published At: {book_publish_at}
            - Genre: {book_genre}

            Relevant Documents:
            {context}

            Question: {question}

            Provide a concise and accurate response based on the context. If no relevant answer is found, state that clearly.
            """

            model = Ollama(model="deepseek")
            prompt = PromptTemplate(template=prompt_template, input_variables=[
                "context", "question", "book_title", "book_author",
                "book_description", "book_publish_at", "book_genre"
            ])
            print("[SUCCESS] Conversational chain initialized.")
            return load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
        except Exception as e:
            print(f"[ERROR] Failed to create conversational chain: {e}")
            traceback.print_exc()
            return None

    def handle_greetings(self, user_question):
        """Handles common greetings."""
        print(f"[INFO] Checking if '{user_question}' is a greeting.")
        greetings = {
            "hii": f"Hello, {self.user_name}! How can I assist you today?",
            "hello": f"Hi there, {self.user_name}! What can I do for you?",
            "good morning": f"Good morning, {self.user_name}! How can I help you today?",
            "good evening": f"Good evening, {self.user_name}! What would you like to ask?",
            "what is your name": "I am BookBot, here to help you with your questions."
        }
        response = greetings.get(user_question.lower(), None)
        if response:
            print(f"[SUCCESS] Greeting detected: {response}")
        return response

    def handle_unknown_answer(self):
        """Returns a default message when no relevant answer is found."""
        print("[INFO] No relevant answer found, returning default response.")
        return f"Sorry, {self.user_name}, I couldn't find an answer. Try rephrasing or asking about a specific book topic."

    def user_input(self, user_question):
        """Processes user input, retrieves relevant documents, and generates a response."""
        print(f"\n[USER INPUT] Received question: {user_question}")

        # Handle greetings first
        greeting_response = self.handle_greetings(user_question)
        if greeting_response:
            return greeting_response

        # Load FAISS vector store and retrieve relevant documents
        print("[INFO] Loading FAISS vector store for document retrieval.")
        try:
            embeddings = OllamaEmbeddings(model="qwen:0.5b")
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            docs = new_db.similarity_search(user_question, k=8)
            print(f"[SUCCESS] Retrieved {len(docs)} relevant documents.")
        except Exception as e:
            print(f"[ERROR] Failed to load FAISS index: {e}")
            traceback.print_exc()
            return self.handle_unknown_answer()

        if not docs:
            return self.handle_unknown_answer()

        # Retrieve latest book metadata from the database
        print("[INFO] Fetching latest book metadata from database.")
        try:
            latest_book = VisitedActivity.objects.order_by('-visited_at').first()
            book_info = {
                "book_title": latest_book.book.title if latest_book else "Unknown Title",
                "book_author": latest_book.book.author if latest_book else "Unknown Author",
                "book_description": latest_book.book.description if latest_book else "No description available.",
                "book_publish_at": latest_book.book.publication_date if latest_book else "Unknown",
                "book_genre": latest_book.book.genre if latest_book else "Unknown"
            }
            print(f"[SUCCESS] Book info retrieved: {book_info}")
        except Exception as e:
            print(f"[ERROR] Failed to fetch book metadata: {e}")
            traceback.print_exc()
            return self.handle_unknown_answer()

        # Generate a response using the conversational chain
        print("[INFO] Generating response using conversational chain.")
        try:
            chain = self.get_conversational_chain()
            if not chain:
                return self.handle_unknown_answer()

            response = chain({
                "input_documents": docs,
                "question": user_question,
                **book_info
            }, return_only_outputs=True)

            print("[SUCCESS] Generated response.")
            return response.get("output_text", self.handle_unknown_answer())
        except Exception as e:
            print(f"[ERROR] Failed to generate response: {e}")
            traceback.print_exc()
            return self.handle_unknown_answer()
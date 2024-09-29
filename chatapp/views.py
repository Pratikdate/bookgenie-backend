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
from app.models import Binding, BindingItem, ExtractedBook
from dotenv import load_dotenv
from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


#for summary


from pdfminer.high_level import extract_text as extract_pdf_text
from pytesseract import image_to_string  # For image OCR
from googleapiclient.discovery import build  # For YouTube video transcripts
from docx import Document  # For Word document extraction
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
            handelChat = HandelChat()
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

class HandelChat:
    def __init__(self, user_name=None):
        self.user_name = user_name or "User"  # Personalize with user's name if available

    def get_pdf_text(self, path):
        text = ""
        try:
            with open(path, "rb") as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"An error occurred: {e}")
        return text

    def get_text_chunks(self, text):
        splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        chunks = splitter.split_text(text)
        return chunks

    def get_vector_store(self, chunks):
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")

    def get_conversational_chain(self):
        prompt_template = """
        Context: {context}  
        Question: {question}
        
        Answer:
        """
        model = ChatGoogleGenerativeAI(
            model="gemini-pro", 
            client=genai,  
            temperature=0.8,
        )
        prompt = PromptTemplate(template=prompt_template, input_variables=['context', "question"])
        chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
        return chain

    # New method to handle greetings
    def handle_greetings(self, user_question):
        greetings = {
            "hi": f"Hello, {self.user_name}! How can I assist you today?",
            "hello": f"Hi there, {self.user_name}! What can I do for you?",
            "good morning": f"Good morning, {self.user_name}! How can I help you today?",
            "good evening": f"Good evening, {self.user_name}! What would you like to ask?",
            "what is your name": "I am BookBot, here to help you with your questions."
        }
        return greetings.get(user_question.lower(), None)

    # New method to handle unknown answers
    def handle_unknown_answer(self):
        return (
            f"Sorry, {self.user_name}, I couldn't find the answer to your question. "
            "You might want to try rephrasing or asking about a specific topic in the book."
        )

    def user_input(self, user_question):
        print(user_question)

        # Handle personalized greetings
        greeting_response = self.handle_greetings(user_question)
        if greeting_response:
            return greeting_response

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question, k=6)

        if not docs:
            # No relevant documents, return fallback response
            return self.handle_unknown_answer()

        # Otherwise, generate a response using the conversational chain
        chain = self.get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

        return response.get("output_text", self.handle_unknown_answer())  # Fallback if no answer is generated

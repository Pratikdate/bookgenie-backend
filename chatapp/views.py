from django.http import HttpResponse
from django.shortcuts import render
# chat_app/views.py
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
from app.models import ExtractedBook
from dotenv import load_dotenv # type: ignore
from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# Create your views here.




# Ensure environment variables are loaded
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class ChatPDFView(APIView):
    # permission_classes = [IsAuthenticated]
    # parser_classes = (MultiPartParser, FormParser)

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
            
            return Response({"success": True, "message": "Vector store is created for this book"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"success": False, "message": "Vector store is not created for this book", 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, pk, *args, **kwargs):
        try:
            handelChat = HandelChat()
            user_question = request.data.get('content')
            response = handelChat.user_input(user_question)
            
            if response:
                return Response({"success": True, "content": response}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "content": "No response generated"}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class Home(APIView):
    def get(self, request):
        return HttpResponse("hello world")
    


class HandelChat:
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
        You are a knowledgeable assistant trained to answer questions based on the provided context. 
        Answer the question as thoroughly as possible using the context provided. 
        If the question is not covered by the context, provide a helpful and related response based on general knowledge or reasoning.

        If the question is about your identity, respond with "My name is Mr. Chat.", 


        
        Context:{context} 
        Question:{question}

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

    def user_input(self, user_question):
        print(user_question)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question,k=6)
        
        chain = self.get_conversational_chain()
        response = chain({"input_documents":docs, "question": user_question}, return_only_outputs=True)
        
        return response.get("output_text", "No response generated")
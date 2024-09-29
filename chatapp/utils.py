import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
from pytesseract import image_to_string  # For OCR image text extraction
from PIL import Image  # To open image files for OCR processing
from googleapiclient.discovery import build  # To interact with YouTube API
from PyPDF2 import PdfFileReader  # To read PDFs
from docx import Document  # To read Word documents
from langchain.prompts import PromptTemplate  # For prompt templates
from langchain.chains.summarize import load_summarize_chain  # For summarize chain
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For splitting large texts
from langchain.vectorstores.faiss import FAISS  

from langchain.chains.question_answering import load_qa_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")





class HandleBindingItemSummary:
    def __init__(self, user_name=None):
        self.user_name = user_name or "User"  # Personalize with user's name if available
        self.youtube_api_key = YOUTUBE_API_KEY  # For extracting YouTube transcripts

    def fetch_text_from_url(self, url):
        """Fetch the content from a web page URL using web scraping."""
        try:
            # Make a GET request to fetch the raw HTML content
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad responses (4xx and 5xx)

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the main text from the webpage
            # You can refine the selection by choosing specific tags and class names
            paragraphs = soup.find_all('p')  # You can change 'p' to any other tag
            text = "\n".join([para.get_text() for para in paragraphs])

            return text if text else "No text found on this page."
        except requests.RequestException as e:
            print(f"Failed to fetch content from URL: {e}")
            return None

    def fetch_text_from_image(self, image_path):
        """Extract text from an image using OCR."""
        try:
            pass
         # pytesseract.image_to_string(Image.open(image_path))  # Extract text from the image
        except Exception as e:
            print(f"Failed to process image: {e}")
            return None

    def fetch_text_from_youtube(self, video_url):
        """Extract transcript from a YouTube video."""
        try:
            youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            video_id = self.extract_youtube_video_id(video_url)
            captions = youtube.captions().list(part="snippet", videoId=video_id).execute()
            transcript = self.fetch_youtube_transcript(video_id)
            return transcript if transcript else "No transcript available."
        except Exception as e:
            print(f"Failed to fetch YouTube transcript: {e}")
            return None

    def extract_youtube_video_id(self, url):
        """Extract video ID from YouTube URL."""
        from urllib.parse import urlparse, parse_qs
        query = urlparse(url).query
        return parse_qs(query).get('v', [None])[0]

    def fetch_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PdfFileReader(pdf_file)
                text = ""
                for page in range(pdf_reader.getNumPages()):
                    text += pdf_reader.getPage(page).extract_text()
            return text
        except Exception as e:
            print(f"Failed to extract text from PDF: {e}")
            return None

    def fetch_text_from_word(self, word_path):
        """Extract text from a Word document."""
        try:
            doc = Document(word_path)
            full_text = []
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"Failed to extract text from Word: {e}")
            return None

    def get_text_chunks(self, text):
        """Split the fetched text into smaller chunks for processing."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        chunks = splitter.split_text(text)
        return chunks

    def get_vector_store(self, chunks):
        """Embed the text chunks into a vector store for semantic search."""
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
        vector_store.save_local("faiss_binding_item_index")

    def get_summary_chain(self):
        """Prepare the conversational chain for generating a summary."""
        prompt_template = """
        You are given a set of documents. Summarize them concisely in plain language.
        Context: {context}
        
        Summary:
        """
        model = ChatGoogleGenerativeAI(
            model="gemini-pro", 
            client=genai,  
            temperature=0.8,
        )
        prompt = PromptTemplate(template=prompt_template, input_variables=['context', "question"])
        chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
        return chain

    def handle_unknown_summary(self):
        """Handle cases when no summary can be generated."""
        return f"Sorry, {self.user_name}, I couldn't generate a summary for this binding item."

    def summarize_content(self, content_type, path):
        """Summarize content based on the type (URL, Image, YouTube, PDF, Word, etc.)."""
        if content_type == "web":
            text = self.fetch_text_from_url(path)
        elif content_type == "image":
            text = self.fetch_text_from_image(path)
        elif content_type == "youtubevideo":
            text = self.fetch_text_from_youtube(path)
        elif content_type == "pdf":
            text = self.fetch_text_from_pdf(path)
        elif content_type == "word":
            text = self.fetch_text_from_word(path)
        else:
            return self.handle_unknown_summary()

        if not text:
            return self.handle_unknown_summary()

        print(text)
        # Split the text into chunks and build a vector store
        chunks = self.get_text_chunks(text)
        self.get_vector_store(chunks)

        # Use the summary chain to generate a concise summary of the content
        chain = self.get_summary_chain()
        response = chain({"input_documents": chunks}, return_only_outputs=True)

        return response.get("output_text", self.handle_unknown_summary())

import google.generativeai as genai
from django.core.files.storage import default_storage
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

from rest_framework import viewsets, permissions
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

import requests

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Document

class DocumentQAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        question = request.data.get("question")
        if not question:
            return Response({"error": "Question is required"}, status=400)

        file_path = document.file.path
        text = self.extract_text(file_path)
        if not text:
            return Response({"error": "Unable to extract text from document"}, status=500)

        prompt = f"Answer the question based on the following document:\n\n{text}\n\nQuestion: {question}"

        # Gemini API setup
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return Response({"error": response.json()}, status=response.status_code)

            answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return Response({"answer": answer})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def extract_text(self, file_path):
        if file_path.endswith(".pdf"):
            return self._extract_pdf(file_path)
        elif file_path.endswith(".docx"):
            return self._extract_docx(file_path)
        return None

    def _extract_pdf(self, path):
        import fitz  # PyMuPDF
        try:
            doc = fitz.open(path)
            return "\n".join([page.get_text() for page in doc])
        except:
            return None

    def _extract_docx(self, path):
        import docx
        try:
            doc = docx.Document(path)
            return "\n".join([para.text for para in doc.paragraphs])
        except:
            return None
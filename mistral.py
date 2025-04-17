import fitz # PyMuPDF
import os
import requests
import re
from pathlib import Path
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY") 
if not api_key:
    raise ValueError("API ключ не найден. Убедитесь, что он установлен в .env файле.")

API_URL = "https://api.mistral.ai/v1/chat/completions"

model = "mistral-large-latest"

client = Mistral(api_key=api_key)

def analyze_pdf(pdf_path): 
    doc = fitz.open(pdf_path) 
    page_info = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()  # Извлечение текста
        images = page.get_images(full=True)  # Извлечение изображений
    

        if text.strip():  # Если текст не пустой
           
            page_info.append({
                "page_number": page_num + 1,
                "type": "text",
                "content": text,
            })

        elif images:  # Если есть изображения, но текста нет
                output_dir="my_custom_folder"
                os.makedirs(output_dir, exist_ok=True)
            
                output_path = os.path.join(output_dir, f"page_{page_num + 1}.pdf")
        
                # Создаем новый PDF документ
                new_doc = fitz.open()
                
                # Копируем нужную страницу в новый документ
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Сохраняем новый документ
                new_doc.save(output_path)
                new_doc.close()
            

                # Обработка изображения с помощью OCR  
                try:
                    content = process_pdf(output_path)
                    page_info.append({
                        "page_number": page_num + 1,
                        "type": "image",
                        "content": content
                    })
                    
    
                except Exception as e:
                    page_info.append({
                        "page_number": page_num + 1,
                        "type": "image",
                        "content": f"Ошибка загрузки изображения: {str(e)}",
                    })


        else:  # Если нет ни текста, ни изображений
            page_info.append({
                "page_number": page_num + 1,
                "type": "empty",
                "content": "This page is empty."
            })

    return page_info

uploaded_pdf = client.files.upload(
    file={
        "file_name": "Example.pdf",
        "content": open("Example.pdf", "rb"),
    },
    purpose="ocr"
)  

signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)


def extract_certificates(pdf_path):
    # Открываем PDF-файл
    messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"содержит ли документ {pdf_path} сертификаты качества и если да, то сохрани в ответ номер страницы документа и название продукции, на которую выдан сертификат"
            },
            {
                "type": "document_url",
                "document_url": signed_url.url
            }
        ]
    }
]

    # Get the chat response
    chat_response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages
    )

    response = chat_response.choices[0].message.content
    return response
    

def process_pdf(file_path):
    
    # Убедитесь, что вы используете правильный метод для чтения содержимого файла
    uploaded_pdf = client.files.upload(
        file={
            "file_name": file_path,
            "content": open(file_path, "rb"),
        },
        purpose="ocr"
    )
    

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        }
    )

    
    return ocr_response    


pdf_path = "Example.pdf" 
page_analysis = analyze_pdf(pdf_path)

for page in page_analysis: 
    print(f"Page {page['page_number']}: {page['type']}") 
    print(f"Content: {page['content']}\n")

print(extract_certificates(pdf_path))

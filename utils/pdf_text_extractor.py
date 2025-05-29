import io
import asyncio
from typing import Optional
import fitz  # PyMuPDF

def extract_text_from_pdf_sync_fitz(pdf_bytes: bytes) -> Optional[str]:
    """
    Синхронная функция для извлечения текста из PDF, переданного как байты,
    используя PyMuPDF (fitz).
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        
        if not doc.page_count:
            print("DEBUG (pdf_text_extractor/fitz): PDF-файл не содержит страниц или поврежден.")
            return "PDF-файл не содержит страниц или поврежден."

        print(f"DEBUG (pdf_text_extractor/fitz): Всего страниц в PDF: {doc.page_count}")

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            print(f"DEBUG (pdf_text_extractor/fitz): Обработка страницы {page_num + 1}")
            
            extracted_page_text = page.get_text("text") 
            
            if extracted_page_text and extracted_page_text.strip():
                print(f"DEBUG (pdf_text_extractor/fitz): Текст со страницы {page_num + 1} (первые 100 симв.): {extracted_page_text.strip()[:100]}")
                text_parts.append(extracted_page_text.strip())
            else:
                print(f"DEBUG (pdf_text_extractor/fitz): На странице {page_num + 1} текст не извлечен или пуст.")
        
        doc.close()

        if text_parts:
            full_extracted_text = "\n\n--- Page Break ---\n\n".join(text_parts).strip()
            print(f"DEBUG (pdf_text_extractor/fitz): Общая длина извлеченного текста: {len(full_extracted_text)}")
            return full_extracted_text
        else:
            print("DEBUG (pdf_text_extractor/fitz): Не удалось извлечь текст из PDF (возможно, скан без текстового слоя).")
            return "Не удалось извлечь текст из PDF (возможно, это PDF-изображение без текстового слоя или файл пуст)."
    
    except fitz.fitz. PasswortError: # Более точный тип исключения для PyMuPDF
        print("Ошибка PyMuPDF: PDF-файл защищен паролем.")
        return "Ошибка: PDF-файл защищен паролем и не может быть обработан."
    except Exception as e:
        print(f"Ошибка при извлечении текста из PDF (байты, fitz): {e}")
        return f"Ошибка при обработке PDF-файла (fitz). Убедитесь, что это корректный PDF."

async def extract_text_from_pdf_bytes_async(pdf_bytes: bytes) -> Optional[str]:
    """
    Асинхронная обертка для извлечения текста из PDF, используя PyMuPDF (fitz).
    """
    return await asyncio.to_thread(extract_text_from_pdf_sync_fitz, pdf_bytes)
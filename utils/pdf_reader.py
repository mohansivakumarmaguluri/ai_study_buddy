import pypdf

def extract_text_from_pdf(file_obj) -> str:
    """
    Extracts text content from a PDF file stream uploaded via Streamlit's file_uploader.
    
    Args:
        file_obj: The file-like object from st.file_uploader.
        
    Returns:
        str: Extracted text from the PDF.
    """
    try:
        reader = pypdf.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Error parsing PDF file: {str(e)}")

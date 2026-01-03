#pdf_reader.py
import PyPDF2
import pdfplumber

class PDFReader:
    def read_pdf(self, file_path):
        """Read and extract text from PDF"""
        try:
            text = ""
            
            # Try pdfplumber first (better for complex PDFs)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n\n"
            
            if not text.strip():
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n\n"
            
            return True, text.strip()
            
        except Exception as e:
            return False, f"Failed to read PDF: {str(e)}"
    
    def read_pdf_summary(self, file_path, max_chars=1000):
        """Read PDF and return summary"""
        success, content = self.read_pdf(file_path)
        if success:
            summary = content[:max_chars]
            if len(content) > max_chars:
                summary += "..."
            return True, summary
        return success, content
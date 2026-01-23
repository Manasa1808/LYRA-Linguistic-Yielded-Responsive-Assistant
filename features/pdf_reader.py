# pdf_reader.py - Windows Compatible with Error Handling
import os
import platform

class PDFReader:
    def __init__(self):
        self.platform = platform.system()
        self.pdfplumber_available = False
        self.pypdf2_available = False
        
        # Check available libraries
        try:
            import pdfplumber
            self.pdfplumber_available = True
            print("✅ pdfplumber available")
        except ImportError:
            print("⚠️ pdfplumber not installed. Install with: pip install pdfplumber")
        
        try:
            import PyPDF2
            self.pypdf2_available = True
            print("✅ PyPDF2 available")
        except ImportError:
            print("⚠️ PyPDF2 not installed. Install with: pip install PyPDF2")
    
    def read_pdf(self, file_path, language='en'):
        """Read and extract text from PDF - Windows compatible"""
        
        print(f"\n{'='*60}")
        print(f"📄 READING PDF")
        print(f"{'='*60}")
        print(f"📁 File: {file_path}")
        print(f"🌐 Language: {language}")
        print(f"{'='*60}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_messages = {
                'en': f"PDF file not found: {file_path}",
                'hi': f"पीडीएफ फाइल नहीं मिली: {file_path}",
                'kn': f"ಪಿಡಿಎಫ್ ಫೈಲ್ ಸಿಗಲಿಲ್ಲ: {file_path}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
        
        # Check file extension
        if not file_path.lower().endswith('.pdf'):
            error_messages = {
                'en': f"Not a PDF file: {file_path}",
                'hi': f"यह पीडीएफ फाइल नहीं है: {file_path}",
                'kn': f"ಇದು ಪಿಡಿಎಫ್ ಫೈಲ್ ಅಲ್ಲ: {file_path}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
        
        if not self.pdfplumber_available and not self.pypdf2_available:
            error_messages = {
                'en': "No PDF library available. Install: pip install pdfplumber PyPDF2",
                'hi': "पीडीएफ लाइब्रेरी उपलब्ध नहीं है। इंस्टॉल करें: pip install pdfplumber PyPDF2",
                'kn': "ಪಿಡಿಎಫ್ ಲೈಬ್ರರಿ ಲಭ್ಯವಿಲ್ಲ. ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ: pip install pdfplumber PyPDF2"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
        
        try:
            text = ""
            page_count = 0
            
            # Method 1: Try pdfplumber first (better for complex PDFs)
            if self.pdfplumber_available:
                try:
                    import pdfplumber
                    print("📖 Using pdfplumber to extract text...")
                    
                    with pdfplumber.open(file_path) as pdf:
                        page_count = len(pdf.pages)
                        print(f"📄 Total pages: {page_count}")
                        
                        for i, page in enumerate(pdf.pages, 1):
                            print(f"   Reading page {i}/{page_count}...")
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n\n"
                    
                    if text.strip():
                        print(f"✅ Successfully extracted {len(text)} characters using pdfplumber")
                        print(f"{'='*60}\n")
                        return True, text.strip()
                except Exception as e:
                    print(f"⚠️ pdfplumber failed: {e}")
            
            # Method 2: Fallback to PyPDF2
            if self.pypdf2_available and not text.strip():
                try:
                    import PyPDF2
                    print("📖 Using PyPDF2 to extract text...")
                    
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_count = len(pdf_reader.pages)
                        print(f"📄 Total pages: {page_count}")
                        
                        for i, page in enumerate(pdf_reader.pages, 1):
                            print(f"   Reading page {i}/{page_count}...")
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n\n"
                    
                    if text.strip():
                        print(f"✅ Successfully extracted {len(text)} characters using PyPDF2")
                        print(f"{'='*60}\n")
                        return True, text.strip()
                except Exception as e:
                    print(f"⚠️ PyPDF2 failed: {e}")
            
            # If we got here, extraction failed
            if not text.strip():
                error_messages = {
                    'en': "Could not extract text from PDF. The PDF might be scanned/image-based.",
                    'hi': "पीडीएफ से टेक्स्ट निकाला नहीं जा सका। यह स्कैन की गई फाइल हो सकती है।",
                    'kn': "ಪಿಡಿಎಫ್‌ನಿಂದ ಪಠ್ಯವನ್ನು ಹೊರತೆಗೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಇದು ಸ್ಕ್ಯಾನ್ ಮಾಡಿದ ಫೈಲ್ ಆಗಿರಬಹುದು."
                }
                error_msg = error_messages.get(language, error_messages['en'])
                print(f"❌ {error_msg}")
                print(f"{'='*60}\n")
                return False, error_msg
            
        except FileNotFoundError:
            error_messages = {
                'en': f"File not found: {file_path}",
                'hi': f"फाइल नहीं मिली: {file_path}",
                'kn': f"ಫೈಲ್ ಸಿಗಲಿಲ್ಲ: {file_path}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
        except PermissionError:
            error_messages = {
                'en': f"Permission denied to access: {file_path}",
                'hi': f"फाइल खोलने की अनुमति नहीं है: {file_path}",
                'kn': f"ಫೈಲ್ ತೆರೆಯಲು ಅನುಮತಿ ಇಲ್ಲ: {file_path}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
        except Exception as e:
            error_messages = {
                'en': f"Failed to read PDF: {str(e)}",
                'hi': f"पीडीएफ पढ़ने में विफल: {str(e)}",
                'kn': f"ಪಿಡಿಎಫ್ ಓದಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
    
    def read_pdf_summary(self, file_path, max_chars=1000, language='en'):
        """Read PDF and return summary"""
        print(f"📄 Reading PDF summary (max {max_chars} chars)...")
        
        success, content = self.read_pdf(file_path, language)
        if success:
            summary = content[:max_chars]
            if len(content) > max_chars:
                summary += "..."
                
                summary_messages = {
                    'en': f"PDF summary (first {max_chars} characters):\n\n{summary}",
                    'hi': f"पीडीएफ सारांश (पहले {max_chars} अक्षर):\n\n{summary}",
                    'kn': f"ಪಿಡಿಎಫ್ ಸಾರಾಂಶ (ಮೊದಲ {max_chars} ಅಕ್ಷರಗಳು):\n\n{summary}"
                }
                return True, summary_messages.get(language, summary_messages['en'])
            
            return True, summary
        return success, content
    
    def get_pdf_info(self, file_path, language='en'):
        """Get PDF metadata information"""
        if not os.path.exists(file_path):
            error_messages = {
                'en': "PDF file not found",
                'hi': "पीडीएफ फाइल नहीं मिली",
                'kn': "ಪಿಡಿಎಫ್ ಫೈಲ್ ಸಿಗಲಿಲ್ಲ"
            }
            return False, error_messages.get(language, error_messages['en'])
        
        try:
            if self.pypdf2_available:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    info = {
                        'pages': len(pdf_reader.pages),
                        'title': pdf_reader.metadata.title if pdf_reader.metadata else 'Unknown',
                        'author': pdf_reader.metadata.author if pdf_reader.metadata else 'Unknown'
                    }
                    
                    info_messages = {
                        'en': f"PDF Info: {info['pages']} pages, Title: {info['title']}, Author: {info['author']}",
                        'hi': f"पीडीएफ जानकारी: {info['pages']} पृष्ठ, शीर्षक: {info['title']}, लेखक: {info['author']}",
                        'kn': f"ಪಿಡಿಎಫ್ ಮಾಹಿತಿ: {info['pages']} ಪುಟಗಳು, ಶೀರ್ಷಿಕೆ: {info['title']}, ಲೇಖಕ: {info['author']}"
                    }
                    return True, info_messages.get(language, info_messages['en'])
            else:
                error_messages = {
                    'en': "PyPDF2 not available for metadata extraction",
                    'hi': "मेटाडेटा निकालने के लिए PyPDF2 उपलब्ध नहीं है",
                    'kn': "ಮೆಟಾಡೇಟಾ ಹೊರತೆಗೆಯಲು PyPDF2 ಲಭ್ಯವಿಲ್ಲ"
                }
                return False, error_messages.get(language, error_messages['en'])
        except Exception as e:
            return False, f"Error: {str(e)}"
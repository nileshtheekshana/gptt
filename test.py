import os
import fitz  
import PyPDF2
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "xxxghpxxx_xxxIUYIHs1MlKD3mBfqA5xxxrboeGKTxBygZ3BBT12xxx")
ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4.1-mini"

def read_pdf_content(pdf_path):
    """Extract text content from PDF file"""
    print(f"Reading PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    
    try:
        # Try with PyMuPDF first (better text extraction)
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        
        if text.strip():
            print(f"PDF text extracted successfully: {len(text)} characters")
            return text.strip()
        
    except Exception as e:
        print(f"PyMuPDF failed: {e}, trying PyPDF2")
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                
                if text.strip():
                    print(f"PDF text extracted with PyPDF2: {len(text)} characters")
                    return text.strip()
                
        except Exception as e2:
            print(f"PyPDF2 also failed: {e2}")
    
    return None

def ask_gpt(question):
    """Send question to GPT and get response"""
    print("Sending to AI...")
    
    # Initialize Azure client
    try:
        client = ChatCompletionsClient(
            endpoint=ENDPOINT,
            credential=AzureKeyCredential(GITHUB_TOKEN),
        )
    except Exception as e:
        print(f"Failed to initialize Azure client: {e}")
        return None
    
    try:
        response = client.complete(
            messages=[
                SystemMessage("You are a helpful assistant. Analyze the provided content and give a comprehensive response."),
                UserMessage(question)
            ],
            temperature=0.7,
            top_p=1,
            model=MODEL
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            return content.strip() if content else "Empty response"
        else:
            return "No response received"
            
    except Exception as e:
        print(f"API request failed: {str(e)}")
        return None

def save_response_to_file(content, filename):
    """Save AI response to text file"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Response saved to: {filename}")
        return True
    except Exception as e:
        print(f"Failed to save file {filename}: {e}")
        return False

def read_text_file(file_path):
    """Read content from text file"""
    print(f"Reading text file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if content.strip():
            print(f"Text file read successfully: {len(content)} characters")
            return content.strip()
        else:
            print("Text file is empty")
            return None
            
    except Exception as e:
        print(f"Failed to read text file: {e}")
        return None

def main():
    """Main function"""
    input_files = ["in.pdf", "in.txt"]
    output_file = "out.java"
    
    print("File to AI Response Processor")
    print("=" * 30)
    
    # Check which input file exists
    input_file = None
    for file in input_files:
        if os.path.exists(file):
            input_file = file
            print(f"Found input file: {input_file}")
            break
    
    if not input_file:
        print(f"Error: No input file found. Looking for: {', '.join(input_files)}")
        return
    
    # Read file content based on type
    if input_file.endswith('.pdf'):
        content = read_pdf_content(input_file)
        if not content:
            print("Error: Could not extract text from PDF")
            return
    elif input_file.endswith('.txt'):
        content = read_text_file(input_file)
        if not content:
            print("Error: Could not read text file")
            return
    else:
        print("Error: Unsupported file type")
        return
    
    # Create prompt for AI
    prompt = f"Please analyze this document and provide a comprehensive response:\n\n{content}"
    
    # Truncate if too long
    if len(prompt) > 8000:
        prompt = prompt[:8000] + "\n\n[Content truncated due to length]"
        print("Warning: Content truncated due to length")
    
    # Get AI response
    answer = ask_gpt(prompt)
    if not answer:
        print("Error: Failed to get AI response")
        return
    
    # Save response
    if save_response_to_file(answer, output_file):
        print(f"Success! Check {output_file} for the AI response")
    else:
        print("Error: Failed to save response")

if __name__ == "__main__":
    main()
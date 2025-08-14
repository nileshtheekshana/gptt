import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "xxxghp_xxxRofjqjY17QOxxx1laOXy8G6cUjlt8truD3GWTvpxxx")
ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4.1-mini"

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

def ask_gpt(question):
    """Send question to GPT and get response"""
    print("Sending to AI...")
    
    try:
        client = ChatCompletionsClient(
            endpoint=ENDPOINT,
            credential=AzureKeyCredential(GITHUB_TOKEN),
        )
        
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

def main():
    """Main function"""
    input_file = "in.txt"
    output_file = "out.java"
    
    print("Text to AI Response Processor")
    print("=" * 30)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return
    
    # Read text file content
    content = read_text_file(input_file)
    if not content:
        print("Error: Could not read text file or file is empty")
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
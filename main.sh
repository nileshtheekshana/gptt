#!/bin/bash

# Configuration
GITHUB_TOKEN="${GITHUB_TOKEN:-xxxghpxxx_xxxUUvhITIYaHzHqOC4ujYZgHMxxxOcIWFRo1ECpdjxxx}"
ENDPOINT="https://models.github.ai/inference"
MODEL="openai/gpt-4.1-mini"

# Function to escape JSON string (basic version using only built-in tools)
escape_json() {
    local input="$1"
    # Basic escaping - replace problematic characters
    input="${input//\\/\\\\}"      # Replace \ with \\
    input="${input//\"/\\\"}"      # Replace " with \"
    input="${input//$'\n'/\\n}"    # Replace newlines with \n
    input="${input//$'\r'/\\r}"    # Replace carriage returns with \r
    input="${input//$'\t'/\\t}"    # Replace tabs with \t
    echo "$input"
}

# Function to read text file
read_text_file() {
    local file_path="$1"
    echo "Reading text file: $file_path" >&2
    
    if [[ ! -f "$file_path" ]]; then
        echo "Error: Text file not found: $file_path" >&2
        return 1
    fi
    
    local content
    content=$(cat "$file_path" 2>/dev/null)
    
    if [[ -n "$content" ]]; then
        echo "Text file read successfully: ${#content} characters" >&2
        echo "$content"
        return 0
    else
        echo "Text file is empty" >&2
        return 1
    fi
}

# Function to extract basic text from PDF (very limited, only works with simple PDFs)
read_pdf_basic() {
    local pdf_path="$1"
    echo "Attempting basic PDF text extraction: $pdf_path" >&2
    
    if [[ ! -f "$pdf_path" ]]; then
        echo "Error: PDF file not found: $pdf_path" >&2
        return 1
    fi
    
    # Try to extract readable text using strings command (very basic)
    local text_content
    text_content=$(strings "$pdf_path" 2>/dev/null | grep -v "^%" | grep -E "[a-zA-Z]{3,}" | head -100)
    
    if [[ -n "$text_content" ]]; then
        echo "Basic PDF text extraction completed (limited): ${#text_content} characters" >&2
        echo "$text_content"
        return 0
    else
        echo "Error: Could not extract readable text from PDF" >&2
        echo "Note: PDF text extraction is very limited without additional tools" >&2
        return 1
    fi
}

# Function to send question to AI (using wget)
ask_gpt() {
    local question="$1"
    echo "Sending to AI..." >&2
    
    if [[ "$GITHUB_TOKEN" == "xxx" ]]; then
        echo "Error: GITHUB_TOKEN environment variable not set" >&2
        echo "Please set it with: export GITHUB_TOKEN=\"your_token_here\"" >&2
        return 1
    fi
    
    # Escape content for JSON
    local escaped_question
    escaped_question=$(escape_json "$question")
    
    # Create JSON payload
    local json_payload
    json_payload=$(cat <<EOF
{
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant. Analyze the provided content and give a comprehensive response."
        },
        {
            "role": "user", 
            "content": "$escaped_question"
        }
    ],
    "model": "$MODEL",
    "temperature": 0.7,
    "top_p": 1
}
EOF
)
    
    # Make API request using wget
    local response
    response=$(wget --quiet --method=POST "$ENDPOINT/chat/completions" \
        --header="Content-Type: application/json" \
        --header="Authorization: Bearer $GITHUB_TOKEN" \
        --body-data="$json_payload" -O - 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        echo "Error: API request failed" >&2
        return 1
    fi
    
    # Extract content from response using basic text processing
    # Look for "content":"..." pattern and extract the content
    local content
    content=$(echo "$response" | sed -n 's/.*"content":"\([^"]*\)".*/\1/p' | head -1)
    
    if [[ -z "$content" ]]; then
        echo "Error: No response received or could not parse response" >&2
        echo "Raw response: $response" >&2
        return 1
    fi
    
    # Unescape basic JSON escapes
    content="${content//\\\"/\"}"
    content="${content//\\n/$'\n'}"
    content="${content//\\t/$'\t'}"
    content="${content//\\\\/\\}"
    
    echo "$content"
    return 0
}

# Function to save response to file
save_response_to_file() {
    local content="$1"
    local filename="$2"
    
    if echo "$content" > "$filename" 2>/dev/null; then
        echo "Response saved to: $filename" >&2
        return 0
    else
        echo "Failed to save file $filename" >&2
        return 1
    fi
}

# Main function
main() {
    local input_files=("in.txt" "in.pdf")  # Prefer .txt since PDF extraction is limited
    local output_file="out.txt"
    
    echo "File to AI Response Processor"
    echo "=============================="
    echo "Note: This version uses wget instead of curl"
    echo "PDF support is very limited - text files recommended"
    echo ""
    
    # Check basic dependencies (should be available on most systems)
    if ! command -v wget >/dev/null 2>&1; then
        echo "Error: wget is required but not found." >&2
        echo "wget is usually pre-installed on most systems." >&2
        exit 1
    fi
    
    if ! command -v strings >/dev/null 2>&1; then
        echo "Warning: 'strings' command not found - PDF processing will not work" >&2
    fi
    
    # Check which input file exists
    local input_file=""
    for file in "${input_files[@]}"; do
        if [[ -f "$file" ]]; then
            input_file="$file"
            echo "Found input file: $input_file"
            break
        fi
    done
    
    if [[ -z "$input_file" ]]; then
        echo "Error: No input file found. Looking for: ${input_files[*]}" >&2
        echo "Please create either 'in.txt' or 'in.pdf' in the current directory" >&2
        exit 1
    fi
    
    # Read file content based on type
    local content
    if [[ "$input_file" == *.txt ]]; then
        content=$(read_text_file "$input_file")
        if [[ $? -ne 0 || -z "$content" ]]; then
            echo "Error: Could not read text file" >&2
            exit 1
        fi
    elif [[ "$input_file" == *.pdf ]]; then
        echo "Warning: PDF text extraction is very basic and may not work properly" >&2
        echo "For better results, convert your PDF to a text file first" >&2
        content=$(read_pdf_basic "$input_file")
        if [[ $? -ne 0 || -z "$content" ]]; then
            echo "Error: Could not extract text from PDF" >&2
            echo "Try converting the PDF to a text file (.txt) instead" >&2
            exit 1
        fi
    else
        echo "Error: Unsupported file type" >&2
        exit 1
    fi
    
    # Create prompt for AI
    local prompt="Please analyze this document and provide a comprehensive response:

$content"
    
    # Truncate if too long (8000 characters)
    if [[ ${#prompt} -gt 8000 ]]; then
        prompt="${prompt:0:8000}

[Content truncated due to length]"
        echo "Warning: Content truncated due to length" >&2
    fi
    
    # Get AI response
    local answer
    answer=$(ask_gpt "$prompt")
    if [[ $? -ne 0 || -z "$answer" ]]; then
        echo "Error: Failed to get AI response" >&2
        exit 1
    fi
    
    # Save response
    if save_response_to_file "$answer" "$output_file"; then
        echo ""
        echo "Success! Check $output_file for the AI response"
    else
        echo "Error: Failed to save response" >&2
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi


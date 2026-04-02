import re
import json
import easyocr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def get_text_from_image(file_path: str) -> str:
    """Extracts raw text from an image file."""
    reader = easyocr.Reader(['en'])
    result = reader.readtext(file_path, detail=0, paragraph=True)
    return "".join(result)

def extract_structured_data(text: str) -> dict:
    """Uses an LLM to extract structured data from raw text."""
    llm = ChatOpenAI(
        base_url="http://127.0.0.1:1234/v1",
        api_key="lm-studio",
        model="qwen3.5-9b-claude-4.6-opus-uncensored-distilled",
        temperature=0.0,
        timeout=180.0
    )

    prompt = PromptTemplate.from_template(
        """You are a data extraction specialist. From the raw OCR text provided below, extract the merchant name, total amount, transaction date, and a suitable category.

        RULES:
        - Return ONLY a single, valid JSON object.
        - The JSON object must have these exact keys: "merchant", "amount", "date", "category".
        - **Amount**: Must be a float, with no currency symbols.
        - **Date**: Must be in YYYY-MM-DD format. If the year is missing, assume the current year.
        - **Category**: Choose the best fit from: "Meals & Entertainment", "Transport", "Accommodation", "Office Supplies", "Other".
        - If a value cannot be determined, set it to `null`.

        RAW OCR TEXT:
        {ocr_text}

        JSON OUTPUT:
        """
    )

    formatted_prompt = prompt.format(ocr_text=text)
    ai_response = llm.invoke(formatted_prompt)
    
    # Clean the response to get only the JSON part
    json_match = re.search(r'\{.*\}', ai_response.content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
            
    # Fallback if regex or parsing fails
    return {
        "merchant": "Unknown",
        "amount": 0.0,
        "date": "1970-01-01",
        "category": "Other"
    }

import os
import json
from google import genai
from google.genai import types
from app.ai.prompts import get_system_prompt
from app.ai.schemas import build_error_response

def process_ai_request(user_message: str) -> dict:
    """Calls the modern Google GenAI SDK to classify intent."""
    system_prompt = get_system_prompt()
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
         return build_error_response("LLM API key is missing from environment variables.")
         
    try:
        client = genai.Client(api_key=api_key)
                # Change the model string to the one requested by the API
        response = client.models.generate_content(
            model='gemini-3.6-flash',  # <--- Update this to 3.6-flash!
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )

        
        if not response or not response.text:
            return build_error_response("Model returned an empty response or content was blocked by safety filters.")
            
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
        
    except Exception as e:
        return build_error_response(f"AI processing failed: {str(e)}")

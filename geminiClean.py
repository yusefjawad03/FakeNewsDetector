import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key = os.getenv("GEMINI_API_KEY"))
generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 65536,
  "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-thinking-exp-01-21",
  generation_config=generation_config,
)
chat_session = model.start_chat(
  history=[
  ]
)
def clean_text(text):
    prompt = f"You will receive text from a an information source. You will remove any information that would not be useful in examining this informations credibility. This includes advertisements, footers, headers, other links on the page. Items that should be kept include, title, source/author, date published, and bodies of text. Your goal is to extract the info that could be used and return only a json file that has one field called clean_text. The value of this field should be the cleaned text. Do not return any other information. The text is: {text}"
    try:
        response = chat_session.send_message(prompt)
        cleaned_text = response.text.strip()
        return cleaned_text
    except Exception as e:
        print(f"Error cleaning text: {e}")
        return "Unable to clean text at this time."

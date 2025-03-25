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
#response = chat_session.send_message("Hey! How are you?")
#print(response.text)

def generate_reasoning(score, article_text, category):
    # Validate inputs
    if not (1 <= score <= 10):
        raise ValueError("Score must be between 1 and 10.")
    
    if category.lower() not in ['style', 'reputation', 'fact']:
        raise ValueError("Category must be one of 'style', 'reputation', or 'fact'.")

    # Define category-specific prompts
    prompts = {
        'style': (
            f"The article has received a Style Score of {score} out of 10. "
            "Based on this score and the following text, provide a 3-4 sentence explanation "
            "detailing the style strengths or weaknesses observed. Reference specific parts of the text."
            "Be confident in your response, you are providing only additional context. You agree with the score."

        ),
        'reputation': (
            f"The article has received a Reputation Score of {score} out of 10. "
            "Based on this score and the following text, provide a 3-4 sentence explanation "
            "detailing the reputation aspects assessed. Reference specific parts of the text."
            "Be confident in your response, you are providing only additional context. You agree with the score."
        ),
        'fact': (
            f"The article has received a Fact Score of {score} out of 10. "
            "Based on this score and the following text, provide a 3-4 sentence explanation "
            "detailing the factual accuracy or inaccuracies observed. Reference specific parts of the text."
            "Be confident in your response, you are providing only additional context. You agree with the score."
        ),
    }

    prompt = prompts[category.lower()] + f"\n\nArticle Text:\n{article_text}\n\nExplanation:"

    try:
        response = chat_session.send_message(prompt)
        reasoning = response.text.strip()
        return reasoning
    except Exception as e:
        print(f"Error generating reasoning for {category}: {e}")
        return "Unable to generate reasoning at this time."

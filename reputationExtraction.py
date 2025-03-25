# reputationExtraction.py

import os
from openai import OpenAI, ChatCompletion
import json

# Initialize OpenAI client with the API key from environment variable or other secure storage
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "[openai-key-will-go-here-temp]")  # Replace with secure method
client = OpenAI(api_key="sk") 

def extract_reputation_data(text):
    """
    Extracts website_url, linkedin_username, and scholar_name from the provided text using OpenAI.

    Args:
        text (str): The article text to analyze.

    Returns:
        dict: A dictionary containing 'website_url', 'linkedin_username', and 'scholar_name'.
    """
    prompt = (
        "Extract the following information from the given text:\n"
        "- website_url\n"
        "- linkedin_username\n"
        "- scholar_name\n\n"
        "If any information is not found, use the default values:\n"
        "website_url: 'http://www.johndoe.com'\n"
        "linkedin_username: 'johndoe'\n"
        "scholar_name: 'John Doe'\n\n"
        "Provide the output in JSON format like this:\n"
        "{\n"
        '  "website_url": "http://example.com",\n'
        '  "linkedin_username": "exampleuser",\n'
        '  "scholar_name": "Example Scholar"\n'
        "}\n\n"
        "Here is the text:\n"
        f'"{text}"'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.3,
        )

        response_content = response.choices[0].message.content.strip()
        # Attempt to parse JSON from the response
        data = json.loads(response_content)
        
        # Validate and set default values if necessary
        website_url = data.get("website_url", "http://www.johndoe.com")
        linkedin_username = data.get("linkedin_username", "johndoe")
        scholar_name = data.get("scholar_name", "John Doe")

        return {
            "website_url": website_url if website_url else "http://www.johndoe.com",
            "linkedin_username": linkedin_username if linkedin_username else "johndoe",
            "scholar_name": scholar_name if scholar_name else "John Doe"
        }

    except Exception as e:
        # In case of any error, return default values
        print(f"Error during reputation data extraction: {e}")
        return {
            "website_url": "http://www.johndoe.com",
            "linkedin_username": "johndoe",
            "scholar_name": "John Doe"
        }

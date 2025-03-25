import os
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from urllib.parse import urlparse
load_dotenv()
import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from progressHold import add_progress

# Configure generative model (if you need it later in your app)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 65536,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21", generation_config=generation_config
)
chat_session = model.start_chat(history=[])

def virus_check(article_url):
    # Submit the URL for scanning
    vt_url = "https://www.virustotal.com/api/v3/urls"
    payload = {"url": article_url}
    headers = {
        "accept": "application/json",
        "x-apikey": os.getenv("VIRUSTOTAL_API_KEY"),
        "content-type": "application/x-www-form-urlencoded"
    }
    add_progress()
    post_response = requests.post(vt_url, data=payload, headers=headers)
    
    try:
        post_json = post_response.json()
        analysis_id = post_json["data"]["id"]
    except Exception as e:
        print("Error parsing VirusTotal submission response:", e)
        return None
        
    # Build URL for analysis results endpoint using the analysis_id
    analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
    add_progress()
    # Poll the analysis endpoint until the status is "completed" or until timeout
    timeout = 600           # Maximum wait time in seconds
    interval = 5           # Polling interval in seconds
    elapsed = 0
    analysis_json = None
    add_progress()
    while elapsed < timeout:
        analysis_response = requests.get(analysis_url, headers={
            "accept": "application/json",
            "x-apikey": os.getenv("VIRUSTOTAL_API_KEY")
        })
        try:
            analysis_json = analysis_response.json()
            status = analysis_json["data"]["attributes"].get("status", "").lower()
            if status == "completed":
                break
            else:
                print(f"Analysis status is '{status}'. Waiting {interval} seconds...")
        except Exception as e:
            print("Error parsing analysis response:", e)

        time.sleep(interval)
        elapsed += interval
    else:
        print("Timed out waiting for analysis to complete.")
        return None

    try:
        stats = analysis_json["data"]["attributes"]["stats"]
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
    except Exception as e:
        print("Error parsing stats from analysis:", e)
        return None
    add_progress()
    # Calculate a reputation score from 1 to 10
    # Deduct 2 points for each malicious detection and 1 point for each suspicious detection,
    # ensuring score is bounded between 1 and 10.
    score = 10 - (malicious * 2) - (suspicious)
    score = max(1, min(10, score))
    add_progress()
    print("VirusTotal Submission Response:")
    print(post_json)
    print("\nFinal Analysis Response:")
    print(analysis_json)
    print("\nCalculated Reputation Score:", score)
    add_progress()
    return score, analysis_json
#virus_check("https://br-icloud.com.br")


chat_session = model.start_chat(history=[])

def extract_author(article_text):
    # Create a prompt that asks Gemini to extract only the author's name.
    prompt = (
        "Read the following article text and extract ONLY the author's name. "
        "If the article does not contain an author, simply reply with 'N/A'.\n\n"
        "Article Text:\n" + article_text + "\n\nAuthor:"
    )

    try:
        response = chat_session.send_message(prompt)
        # Strip any leading/trailing whitespace
        author = response.text.strip()
        #print("Extracted Author:", author)
        return author
    except Exception as e:
        print(f"Error extracting author: {e}")
        return "N/A"


chat_session = model.start_chat(history=[])
def generate_author_trustworthiness(author,url):
    # Create a prompt that asks Gemini to evaluate the trustworthiness of the author.
    trimmed_url = urlparse(url).netloc.lstrip("www.")
    prompt = (
        "Evaluate the trustworthiness of the following author on a scale of 1 to 10, "
        "where 1 is not trustworthy and 10 is highly trustworthy. "
        "Provide a number between 1 and 10, with no additional text.\n\n"
        f"Author: {author}\n\nURL: {trimmed_url}"
    )

    try:
        response = chat_session.send_message(prompt)
        # Strip any leading/trailing whitespace
        score = response.text.strip()
        #print("Author Trustworthiness Score:", score)
        return score
    except Exception as e:
        print(f"Error generating author trustworthiness score: {e}")
        return 1
    
def get_reputation_score(article_text, article_url):
    # Extract the author from the article text
    author = extract_author(article_text)
    # Evaluate the trustworthiness of the author
    author_score = generate_author_trustworthiness(author, article_url)
    # Check the reputation of the article URL
    reputation_score, reputation_analysis = virus_check(article_url)
    final_score = (int(author_score) + int(reputation_score)) / 2
    prompt = (
        f"You have given the article an overall Reputation Score of {final_score:.2f} out of 10, based equally off of the domain's safety and the author's public persona/reputation. "
        "Based on this score and the returned Virustotal text given below, provide a 3-4 sentence explanation "
        "detailing the reputation aspects assessed. Reference specific parts of the text."
        "Be confident in your response, you are providing only additional context. You agree with the score. Virustotal's report: {reputation_analysis}. Full article text: {article_text}. URL: {article_url} Be professional in your response."
        "You are not justifying the score, but providing additional context. Do not use words like likely or possibly."
    )
    try:
        response = chat_session.send_message(prompt)
        reasoning = response.text.strip()
        print(reasoning)
        return final_score, reasoning
    except Exception as e:
        print(f"Error generating reputation reasoning: {e}")
        return 1, "Error retrieving explanation"
#get_reputation_score("This article was written by Annie Karni.", "https://www.nytimes.com/2025/03/05/us/politics/democrats-trump-al-green-protests-congress.html")
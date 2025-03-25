import yaml
import requests
import factExtraction
from openai import OpenAI
import json
from bs4 import BeautifulSoup
import numpy as np

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)


openai_client = OpenAI(api_key=config["OPENAI_API_KEY"])

#utility Functions for politifact

def cosineSimilarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def getEmbedding(text):
    """Fetch OpenAI embedding for a given text."""
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

#genre Classification

def classifyGenre(article_text):
    """Classify article into 'science', 'health', 'politics', or 'other'."""
    print("-------------Determining Genre-------------")

    prompt = f"""
    Categorize the following news article into one of the following genres:
    - science
    - health
    - politics
    - other

    Respond ONLY with a single word from the list above. Do NOT include any explanation.

    News Article:
    {article_text}
    """

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        genre = completion.choices[0].message.content.strip().lower()
        valid_genres = {"science", "health", "politics", "other"}
        if genre not in valid_genres:
            raise ValueError(f"Unexpected genre received: {genre}")

        print(f"-------------Genre classification complete: {genre} -------------")
        return genre

    except Exception as e:
        print(f"Error classifying genre: {e}")
        return "other"

#Fact-Checking/evidence gathering Functions

#Check scientific claim using PubMed API.
def checkScienceFact(claim):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": claim,
        "retmode": "json",
        "api_key": config["NCBI_API_KEY"]
    }

    response = requests.get(base_url, params=params)
    
    try:
        data = response.json()
        search_results = data.get("esearchresult", {})
        article_count = int(search_results.get("count", 0))
        article_ids = search_results.get("idlist", [])

        return {
            "source": "PubMed",
            "factuality": "Relevant studies found" if article_count > 0 else "No matching studies found",
            "details": f"Found {article_count} related articles. IDs: {article_ids}" if article_count > 0 else "No direct scientific articles were found related to this claim."
        }

    except json.JSONDecodeError:
        return {
            "source": "PubMed",
            "factuality": "Error",
            "details": "Failed to parse JSON response from API."
        }

#Check political claim using PolitiFact and OpenAI embeddings (webscraping)
def checkPoliticalFact(claim):
    url = 'https://www.politifact.com/factchecks/'
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "Failed to retrieve data from PolitiFact"}

    soup = BeautifulSoup(response.content, 'html.parser')
    fact_checks = soup.find_all('li', class_='o-listicle__item')

    claim_embedding = getEmbedding(claim)
    best_match = None
    best_similarity = -1

    for fact in fact_checks:
        statement = fact.find('div', class_='m-statement__quote').get_text(strip=True)
        rating_img = fact.find('div', class_='m-statement__meter').find('img')
        rating = rating_img['alt'] if rating_img else 'No Rating'
        source = fact.find('div', class_='m-statement__meta').get_text(strip=True)

        statement_embedding = getEmbedding(statement)
        similarity = cosineSimilarity(claim_embedding, statement_embedding)

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = {
                "statement": statement,
                "rating": rating,
                "source": source,
                "similarity": round(similarity, 3)
            }

    if best_match and best_similarity > 0.7:
        return best_match
    elif best_match:
        best_match["warning"] = "Low similarity - verify manually."
        return best_match
    else:
        return {"error": "No close match found on PolitiFact."}

#use webscrapping to find cdc articles that can support or refute claim

#needed to brew install chromeDriver and pip install webdriver-manager, check with brendan to make sure the server has these!!!

#selenium imports cause javascript rendering dont come up
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def checkHealthFact(claim):
    # Configure Selenium options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Auto-manage ChromeDriver using webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Construct search URL
    search_url = f"https://search.cdc.gov/search/?audience=General%20public&query={claim}"

    # Open the page
    driver.get(search_url)
    time.sleep(3)  # Allow JavaScript to load the content

    # Parse the loaded page
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Close Selenium driver
    driver.quit()

    # Find search result items
    results = soup.find_all('div', class_='result', limit=5)

    if not results:
        return {
            "claim": claim,
            "results": [],
            "message": "No results found."
        }

    # Extract titles and links
    extracted_results = []
    for result in results:
        title_tag = result.find('div', class_='result-title').find('a')
        if title_tag and title_tag.get('href'):
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href')

            extracted_results.append({
                "title": title,
                "link": link
            })

    return {
        "claim": claim,
        "results": extracted_results
    }

#display Function

def displayResult(claim, result):
    """Display the result of the fact-check."""
    print(f"\nClaim: {claim}")

    if "error" in result:
        print(f" - Error: {result['error']}")
    elif "statement" in result:  # Political fact-check
        print(f" - Matched Statement: {result['statement']}")
        print(f" - Rating: {result['rating']}")
        print(f" - Source: {result['source']}")
        print(f" - Similarity: {result.get('similarity', 'N/A')}")
        if "warning" in result:
            print(f" - Warning: {result['warning']}")
    elif "results" in result:  # Health fact-check from CDC search
        if not result["results"]:
            print(" - No relevant CDC articles found.")
        else:
            print(" - Top CDC Search Results:")
            for idx, res in enumerate(result["results"], 1):
                print(f"   {idx}. {res['title']}")
                print(f"      Link: {res['link']}")
    else:  # Science or Health fact-check
        print(f" - Source: {result.get('source', 'Unknown')}")
        print(f" - Verdict: {result.get('factuality', 'Unknown')}")
        print(f" - Details: {result.get('details', 'No additional information')}")

#test usage

def main():
    with open("scienceArticle.txt", 'r') as file:
        article_content = file.read()

    claims = factExtraction.extract_facts_gpt(article_content)
    parsed_facts = json.loads(claims)

    genre = classifyGenre(article_content)

    for fact in parsed_facts:
        claim = fact["claim"]

        if genre == "science":
            print(f"\nChecking scientific fact: {claim}")
            result = checkScienceFact(claim)
        elif genre == "politics":
            print(f"\nChecking political fact: {claim}")
            result = checkPoliticalFact(claim)
        elif genre == "health":
            print(f"\nChecking health fact: {claim}")
            result = checkHealthFact(claim)
        else:
            result = {"error": "Unsupported genre"}

        displayResult(claim, result)

if __name__ == "__main__":
    main()

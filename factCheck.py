import requests
# from transformers import pipeline
import factExtraction
from openai import OpenAI
import json

# functions to check facts for specific genres like science, health, politics, etc.
    

# Classifies the claim into categories like 'science', 'politics', or 'health'
def classifyGenre(article_text):
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

    client = OpenAI(api_key=config["OPENAI_API_KEY"])

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        # Extract the response text
        genre = completion.choices[0].message.content.strip().lower()

        # Validate the response
        valid_genres = {"science", "health", "politics", "other"}
        if genre not in valid_genres:
            raise ValueError(f"Unexpected genre received: {genre}")

        print(f"-------------Genre classification complete: {genre} -------------")
        return genre

    except Exception as e:
        print(f"Error classifying genre: {e}")
        return "other"

    
#pubmed/ncbi for scientific verifications
def check_science_fact(claim):
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
        
        # Extract relevant data
        search_results = data.get("esearchresult", {})
        article_count = int(search_results.get("count", 0))
        article_ids = search_results.get("idlist", [])

        if article_count > 0:
            return {
                "source": "PubMed",
                "factuality": "Relevant studies found",
                "details": f"Found {article_count} related articles. IDs: {article_ids}"
            }
        else:
            return {
                "source": "PubMed",
                "factuality": "No matching studies found",
                "details": "No direct scientific articles were found related to this claim."
            }

    except json.JSONDecodeError:
        return {
            "source": "PubMed",
            "factuality": "Error",
            "details": "Failed to parse JSON response from API."
        }



# Uses Politifact API to verify political claims.
def check_political_fact(claim):
    base_url = "https://politifact.com/api/v1/claims/"
    response = requests.get(base_url, params={"query": claim})
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}


#Uses CDC API to verify health-related claims.
def check_health_fact(claim):
    base_url = "https://data.cdc.gov/resource/"
    response = requests.get(base_url, params={"query": claim})
    return response.json()


# Combines results from APIs and formats the output.
def aggregate_results(claim, results):
    aggregated = {
        "claim": claim,
        "results": results
    }
    return aggregated


def display_results(aggregated_results):
    for result in aggregated_results:
        print(f"Claim: {result['claim']}")

        if isinstance(result["results"], dict):
            print(f" - Source: {result['results'].get('source', 'Unknown')}")
            print(f" - Verdict: {result['results'].get('factuality', 'Unknown')}")
            print(f" - Details: {result['results'].get('details', 'No additional information')}\n")
        else:
            print(" - Unexpected response format. Check API output.\n")


with open("scienceArticle.txt", 'r') as file:
    article_content = file.read()
    
claims = factExtraction.extract_facts_gpt(article_content)
parsed_facts = json.loads(claims)
# print(claims)
aggregated_results = []
genre = classifyGenre(article_content)
for fact in parsed_facts:
    claim = fact["claim"]
    if genre == "science":
        print(f"in science check for: {claim}")
        result = check_science_fact(claim)
    elif genre == "politics":
        result = check_political_fact(claim)
    elif genre == "health":
        result = check_health_fact(claim)
    else:
        result = {"error": "Unsupported genre"}
    aggregated_results.append(aggregate_results(claim, result))
display_results(aggregated_results)
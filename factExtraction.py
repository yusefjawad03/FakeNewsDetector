import openai
import os
import json
import requests
from openai import OpenAI
import yaml
import time
from contextlib import redirect_stderr, redirect_stdout
from OpenFactVerification.factcheck import FactCheck
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# use pytests to setup test cases in seperate file

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Function to extract facts from an article using OpenAI
def extractFacts(article_text):
    
    print("-------------Extracting facts, claims, and statistics from article-------------")
    
    prompt = f"""
    Extract all key facts, statistics, and claims from the following news article. 
    Add context to the extracted facts, statistics, and claims ONLY from the article_text. 
    The context should added so when the fact, statistic, or claim is fact checked, it's checked with the context so we get the most reliable fact checking output.
    Provide the results in the following JSON format:
    [
      {{"claim": "Claim 1", "entities": ["Entity 1", "Entity 2"], "type": "Fact/Statistic/Claim"}},
      {{"claim": "Claim 2", "entities": ["Entity 3"], "type": "Fact"}}
    ]

    News Article:
    {article_text}
    """

    client = OpenAI(api_key=config["OPENAI_API_KEY"])

    completion = client.chat.completions.create( #
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    # Extract the JSON string from the response
    extracted_facts = completion.choices[0].message.content
    cleaned_content = extracted_facts.strip("```json").strip("```").strip()
    
    print("-------------Facts, claims, and statistics extracted-------------")

    return cleaned_content


# Function to call the Google Fact Check API
def googleFactCheck(claim):
    print(f"\n--------------------in google check for claim: {claim}--------------------\n")
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": claim,
        "key": config["GOOGLE_FACT_API_KEY"]
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        result = response.json()
        print(f"\n--------------------End Google check for claim: {claim}--------------------\n")
        return result.get("claims", [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        print(f"\n--------------------End Google check for claim: {claim}--------------------\n")
        return None


# librAI call (no longer being used, switch to an async func)
def call_librAI_fact_check_api(claim):
    
    print(f"\n--------------------in LibrAi check for claim: {claim}--------------------\n")
    
    factcheck_instance = FactCheck(api_config=config)

    # results = factcheck_instance.check_text(claim)
    # time.sleep(7)
    # return results if results else {}

    try:
        # Suppress both stdout and stderr
       with open(os.devnull, 'w') as fnull, redirect_stdout(fnull), redirect_stderr(fnull):#silence print statments from call
            results = factcheck_instance.check_text(claim)
            time.sleep(7)
            print(f"\n--------------------End LibrAi check for claim: {claim}--------------------\n")
            return results if results else {}
    except Exception as e:
        print(f"Error during LibrAI fact-checking: {e}")
        print(f"\n--------------------End LibrAI check for claim: {claim}--------------------\n")
        return {}


# Function to combine Google and LibrAI fact-checking results
def combineResults(google_results, librAI_results):
    combined_results = []

    # Process Google API results
    for result in google_results:
        combined_results.append({
            "source": "Google Fact Checker",
            "claim": result.get("text", "Unknown Claim"),
            "factuality": result.get("claimReview", [{}])[0].get("textualRating", "Unknown"),
            "publisher": result.get("claimReview", [{}])[0].get("publisher", {}).get("name", "Unknown"),
            "url": result.get("claimReview", [{}])[0].get("url", "No URL provided")
        })

    # Process LibrAI API results
    # print(f"Type of librAI_results: {type(librAI_results)}")
    # print(f"Content of librAI_results: {librAI_results}")
    if "claim_detail" in librAI_results:
        for claim_data in librAI_results["claim_detail"]:
            combined_results.append({
                "source": "LibrAI",
                "claim": claim_data.get("claim", "Unknown Claim"),
                "factuality": claim_data.get("factuality", "N/A"),
                "evidences": claim_data.get("evidences", [])
            })

    return combined_results

# Display combined fact-checking results
def displayCombinedResults(combined_results):
    with open("results.txt", "w") as file:
        file.write("\n=== Combined Fact-Checking Results ===\n")
        for result in combined_results:
            file.write(f"Source: {result['source']}\n")
            file.write(f"Claim: {result['claim']}\n")
            file.write(f"Factuality: {result['factuality']}\n")
            if result['source'] == "Google Fact Check API":
                file.write(f"Publisher: {result['publisher']}\n")
                file.write(f"URL: {result['url']}\n")
            elif result['source'] == "LibrAI" and result.get('evidences'):
                file.write("Evidences:\n")
                for evidence in result['evidences']:
                    file.write(f"  - Relationship: {evidence.get('relationship', 'Unknown')}\n")
                    file.write(f"    Reasoning: {evidence.get('reasoning', 'No reasoning provided')}\n")
                    file.write(f"    URL: {evidence.get('url', 'No URL provided')}\n")
            file.write("\n==================================================\n")




# Asynchronous function to call LibrAI Fact Checking API
async def asyncLibrAI(claim, factcheck_instance):
    try:
        # Run synchronous function in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, factcheck_instance.check_text, claim)
        return result if result else {}
    except Exception as e:
        print(f"LibrAI API error: {e}")
        return {}

# asynchronous fact-checking function for both google and librai (only LibrAI is async)
async def asyncFactCheck(parsed_facts, config, factcheck_instance):
    tasks = []
    combined_results = []

    for fact in parsed_facts:
        claim = fact["claim"]

        # google API call
        google_results = googleFactCheck(claim)

        # Asynchronous LibrAI API call
        librAICheck = asyncLibrAI(claim, factcheck_instance)
        tasks.append(asyncio.create_task(librAICheck))

        # Combine Google results immediately
        combined_results.extend(combineResults(google_results, {}))

    # Wait for all LibrAI async tasks to complete
    librAI_results_list = await asyncio.gather(*tasks)

    # Combine LibrAI results
    for librAI_results in librAI_results_list:
        combined_results.extend(combineResults([], librAI_results))

    return combined_results

#main func to call
def fullFactCheckTest(file_path, config=config, factcheck_instance = FactCheck(api_config=config)):
    with open(file_path, 'r') as file:
        article_content = file.read()

    # Extract facts from the article
    facts = extractFacts(article_content)

    if facts:
        try:
            parsed_facts = json.loads(facts)

            #asynchronous fact-checking
            combined_results = asyncio.run(asyncFactCheck(parsed_facts, config, factcheck_instance))

            # Display combined results
            displayCombinedResults(combined_results)

            # Scoring logic
            google_score = 0
            google_numTrue = 0
            google_results = [result for result in combined_results if result.get("source") == "Google Fact Checker"]

            for result in google_results:
                if result.get("factuality") == "True":
                    google_numTrue += 1
                elif result.get("factuality") == "Mostly True":
                    google_numTrue += 0.7

            google_score = google_numTrue / len(parsed_facts) if parsed_facts else 0

            # Calculate score for LibrAI fact checker
            librai_score = 0
            librai_Total = 0
            librai_results = [result for result in combined_results if result.get("source") == "LibrAI"]

            for result in librai_results:
                factuality = result.get("factuality", 0)
                if factuality not in ["No evidence found.", "Nothing to check."]:
                    librai_Total += float(factuality)

            librai_score = librai_Total / len(librai_results) if librai_results else 0

            # Normalize scores to 0-1 range
            google_score = google_score if google_score <= 1 else google_score / 100
            librai_score = librai_score if librai_score <= 1 else librai_score / 100

            # Calculate overall score
            if google_score == 0.0:
                overall_score = librai_score
            else:
                overall_score = (google_score * 0.1) + (librai_score * 0.9)

            # Convert to percentage and round
            overall_score = round(overall_score * 100, 2)

            print(f"Google fact check score: {google_score * 100:.2f}%")
            print(f"LibrAI fact check score: {librai_score * 100:.2f}%")
            print(f"Overall fact check score: {overall_score}%")

            return overall_score

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
    else:
        print("Failed to extract facts.")
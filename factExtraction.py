import openai
import os
import json
import requests
from openai import OpenAI
from factcheck import FactCheck
import time
from contextlib import redirect_stderr, redirect_stdout

# use pytests to setup test cases in seperate file


# Function to extract facts from an article using OpenAI
def extract_facts_gpt(article_text):
    
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
def check_fact_with_google(claim):
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

# librAI call
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
def combine_fact_check_results(google_results, librAI_results):
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
    
# Display fact-checking results
def display_fact_check_results(factcheck_results):
    claims = factcheck_results.get('claim_detail', [])
    overall_factuality = factcheck_results.get('summary', {}).get('factuality', 'N/A')

    print("\n=== Fact-Checking Results ===")
    if isinstance(overall_factuality, float):
        print(f"Overall Factuality Score: {overall_factuality * 100:.2f}%\n")
    else:
        print(f"Overall Factuality Score: {overall_factuality}\n")

    for claim_data in claims:
        claim = claim_data.get('claim', 'Unknown Claim')
        factuality = claim_data.get('factuality', 'N/A')
        evidences = claim_data.get('evidences', [])

        print(f"Claim: {claim}")
        if isinstance(factuality, float):
            print(f"Factuality Score: {factuality * 100:.2f}%")
        else:
            print(f"Factuality Score: {factuality}")

        if evidences:
            print("Sources/Proof:")
            for evidence in evidences:
                relationship = evidence.get('relationship', 'Unknown')
                reasoning = evidence.get('reasoning', 'No reasoning provided')
                url = evidence.get('url', 'No URL provided')

                print(f"  - Relationship: {relationship}")
                print(f"    Reasoning: {reasoning}")
                print(f"    URL: {url}")
        else:
            print("No evidence found for this claim.")

        print("\n" + "="*50 + "\n")


# Display combined fact-checking results
def display_combined_results(combined_results):
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


def fullFactCheckTest(file_path):
    # file_path = input("\nPlease enter file path of article: ")
    
    # if file_path == "":
    #     file_path = 'someTrueSomeFaketest.txt'
        
    with open(file_path, 'r') as file:
        article_content = file.read()

    # Extract facts from the article
    facts = extract_facts_gpt(article_content)

    # print(f"facts after extraction: {facts}")
    # print(type(facts))

    if facts:
        try:
            parsed_facts = json.loads(facts)
            combined_results = []

            for fact in parsed_facts:
                claim = fact["claim"]
                # print(f"Checking claim: {claim}")

                # Call Google Fact Check API
                google_results = check_fact_with_google(claim)
                # print(f"Google Results for '{claim}': {google_results}")

                # Call LibrAI Fact Checking API
                librAI_results = call_librAI_fact_check_api(claim)
                # print(f"LibrAI Results for '{claim}': {librAI_results}")

                # Combine the results
                combined_results.extend(combine_fact_check_results(google_results, librAI_results))

            # Display combined results
            display_combined_results(combined_results)
            
            # calculate score for google fact checker
            # print(".....................")
            # print(combined_results)
            
            google_score = 0
            google_numTrue = 0
            google_results = [result for result in combined_results if result.get("source") == "Google Fact Checker"]

            for result in google_results:
                # print("google true")
                # print(result.get("claim"))
                # print(result.get("factuality"))
                if result.get("factuality") == "True":
                    google_numTrue+=1
                if result.get("factuality") == "Mostly True":
                    google_numTrue+=.7
                    
            google_score = google_numTrue/len(parsed_facts)
            
            # calculate score for Librai fact checker
            librai_score = 0
            librai_Total = 0
            librai_results = [result for result in combined_results if result.get("source") == "LibrAI"]
            
            for result in librai_results:
                if result.get("factuality") == "No evidence found." or result.get("factuality") == "Nothing to check.":
                    continue
                librai_Total += result.get("factuality")
                    
            librai_score = librai_Total/len(librai_results)
            
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
        
# linkedin.py
import requests
from datetime import datetime


#API: https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api/playground/apiendpoint_1d2ead16-5039-4883-ac25-390fa57edf94
def calculate_experience_score(positions):
    """Calculate score based on work experience"""
    if not positions:
        return 0, 0, 0
    
    total_years = 0
    leadership_roles = 0
    total_positions = len(positions) if positions else 0
    current_year = datetime.now().year
    
    try:
        for position in positions:
            # Calculate duration
            start_year = position.get('start', {}).get('year', 0)
            end_year = position.get('end', {}).get('year')
            
            # Handle ongoing positions (end_year = 0)
            if end_year == 0:
                end_year = current_year
            
            if start_year > 0 and end_year >= start_year:
                duration = end_year - start_year
                total_years += duration
                
                # Check for leadership positions
                title = position.get('title', '').lower()
                if any(role in title for role in ['ceo', 'chief', 'president', 'director', 'vp', 'head', 'leader', 'founder']):
                    leadership_roles += 1
    except (TypeError, AttributeError):
        return 0, 0, 0
    
    # Calculate scores with reasonable caps
    experience_score = min(40, total_years * 2)  # Cap at 40 points
    leadership_score = min(20, leadership_roles * 4)  # Cap at 20 points, 5 points per leadership role
    
    total_score = min(60, experience_score + leadership_score)  # Ensure total doesn't exceed 60
    
    return total_score, total_positions, leadership_roles

def get_google_scholar_data(name, api_key):
    """Fetch Google Scholar profile data using SerpApi, https://serpapi.com/google-scholar-api"""
    try:
        url = f"https://serpapi.com/search.json"
        params = {
            "engine": "google_scholar_profiles",
            "mauthors": name,
            "hl": "en",  # Specify language,
            "api_key": api_key
        }
        response = requests.get(url, params=params)
        # print("Response Status Code:", response.status_code)
        # print("Response Content:", response.text)
        response.raise_for_status()  # Raise an exception for bad HTTP responses
        
        data = response.json()

        # print("Full API Response:", json.dumps(data, indent=2))

        # More robust data extraction
        if "profiles" in data and data["profiles"]:
            # Take the first profile
            author = data["profiles"][0]
            # print("Google Scholar Data:", author)  

            # h_index = author.get('h_index', 0) if isinstance(author.get('h_index'), int) else 0
            citation_count = author.get('cited_by', 0) if isinstance(author.get('cited_by'), int) else 0
            # publication_count = author.get('publications_count', 0) if isinstance(author.get('publications_count'), int) else 0
                        
            # return h_index, citation_count, publication_count
            return citation_count

        print("No scholar profiles found.")
        return 0, 0, 0
    
    except requests.RequestException as e:
        print(f"Request error fetching Google Scholar data: {e}")
        return 0, 0, 0
    
# Google Safe Browsing API Integration
def check_url_safety(api_key, url):
    """Check URL safety using Google Safe Browsing API"""
    try:
        safe_browsing_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        payload = {
            "client": {
                "clientId": "your-client-id",
                "clientVersion": "1.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}
        
        response = requests.post(safe_browsing_url, json=payload, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # If the response contains a threat match, URL is unsafe
        if data.get("matches"):
            return False  # Unsafe
        return True  # Safe
    except Exception as e:
        print(f"Error checking URL safety: {str(e)}")
        return None  # Unknown safety status

# Integration into the main credibility score
def calculate_url_score(api_key, url):
    """Calculate a score based on URL safety"""
    try:
        is_safe = check_url_safety(api_key, url)
        if is_safe is None:
            return 0  # Neutral score if API fails
        return 10 if is_safe else -10  # Reward 10 points for safe URLs, penalize 10 for unsafe
    except Exception as e:
        print(f"Error calculating URL score: {str(e)}")
        return 0


def calculate_scholar_score(citation_count):
    """Calculate score based on scholarly data"""
    try:
        # Scale scores with caps
        # h_index_score = min(10, h_index / 5)  # Cap at 10 points
        citation_score = min(10, citation_count / 1000)  # Cap at 10 points
        # publication_score = min(10, publication_count / 50)  # Cap at 10 points
        
        # Total scholarly score (max 30)
        total_scholar_score = citation_score
        return total_scholar_score
    except Exception as e:
        print(f"Error calculating scholar score: {str(e)}")
        return 0


def calculate_education_score(educations):
    """Calculate score based on education"""
    if not educations:
        return 0, 0
    
    try:
        score = 0
        edu_count = len(educations) if educations else 0
        
        for education in educations:
            # school = education.get('schoolName', '').lower()
            degree = education.get('degree', '').lower()
            
            # Points for degree level
            if any(d in degree for d in ['phd', 'doctorate']):
                score += 15
            elif any(d in degree for d in ['mba', 'master']):
                score += 10
            elif any(d in degree for d in ['bachelor', 'bs', 'ba', 'b.s', 'b.a', 'ab']):
                score += 8
                
        return min(20, score), edu_count
    except (TypeError, AttributeError):
        return 0, 0

def calculate_skill_score(skills):
    """Calculate score based on skills and endorsements listed on linkedin"""
    if not skills:
        return 0, 0, 0
    
    try:
        total_endorsements = sum(skill.get('endorsementsCount', 0) for skill in skills)
        skill_count = len(skills) if skills else 0
        
        endorsement_score = min(10, total_endorsements / 20)  # Cap at 10 points
        skill_variety_score = min(10, skill_count / 2)  # Cap at 10 points
        
        return endorsement_score + skill_variety_score, skill_count, total_endorsements
    except (TypeError, AttributeError):
        return 0, 0, 0

def get_linkedin_profile(name, headers):
    """Get LinkedIn profile data"""
    try:
        url = "https://linkedin-data-api.p.rapidapi.com/"
        querystring = {"username": name}
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            # print("LinkedIn Profile Data:", data)  
            # Check if the response contains actual profile data
            if not data or data.get('error') or data.get('status') == 'error':
                return None
            return data
        return None
    except Exception as e:
        print(f"Error fetching profile: {str(e)}")
        return None

def get_domain_trust_score(domain, api_key):
    """
    Fetch domain trust score from ScamPredictor API
    
    Args:
        domain (str): The domain to check
        api_key (str): RapidAPI key
    
    """
    try:
        url = f"https://scampredictor.p.rapidapi.com/domain/{domain}"
        
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "scampredictor.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            class_score = data.get('domain_class', 5)
            
            trust_score = class_score
            
            # Validate trust score is between 1-5
            if 1 <= trust_score <= 5:
                return trust_score
            else:
                print(f"Invalid class score received: {class_score}")
                return 0
        else:
            print(f"Failed to fetch domain trust score. Status code: {response.status_code}")
            return 0
    
    except requests.RequestException as e:
        print(f"Error fetching domain trust score: {e}")
        return 0

def get_empty_score_breakdown():
    """Return an empty score for no authors"""
    return {
        'total_score': 0,
        'experience_score': 0,
        'education_score': 0,
        'skill_score': 0,
        'scholar_score': 0,
        'url_score': 0,
        'domain_score': 0,
        'scoring_factors': {
            'years_of_experience': 0,
            'leadership_positions': 0,
            'education_count': 0,
            'skill_count': 0,
            'total_endorsements': 0,
            # 'h_index': 0,
            'citation_count': 0,
            # 'publication_count': 0,
            'url': 'N/A',
            'domain': 'N/A',
            'domain_trust_score': 0,
            'url_safe': 'Unknown'
        }
    }

def calculate_credibility_score(profile_data, scholar_data, url, safe_browsing_api_key, domain_api_key):
    """Calculate overall credibility score"""
    if not profile_data and not scholar_data:
        return 0, get_empty_score_breakdown()
    
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        # print("domain", domain)
        # Calculate individual component scores
        positions = profile_data.get('position', []) or profile_data.get('fullPositions', []) or []
        educations = profile_data.get('educations', []) or []
        skills = profile_data.get('skills', []) or []
        
        experience_score, position_count, leadership_count = calculate_experience_score(positions)
        education_score, edu_count = calculate_education_score(educations)
        skill_score, skill_count, endorsement_count = calculate_skill_score(skills)
        
        # Scholar data
        citation_count= scholar_data
        scholar_score = calculate_scholar_score(citation_count)
        
        # URL safety score
        url_score = calculate_url_score(safe_browsing_api_key, url)

        domain_trust_score = get_domain_trust_score(domain, domain_api_key)
        domain_score = domain_trust_score * 2  # Convert 1-5 scale to 2-10 points
        
        # Weight factors for final score
        WEIGHTS = {
            'experience': 15, 
            'education': 10,   
            'skills': 5,      
            'scholar': 5,     
            'url_safety': 30,  
            'domain_trust': 35 
        }
        MAX_SCORES = {
            'experience': 60,
            'education': 20,
            'skills': 20,
            'scholar': 10,
            'url_safety': 10,
            'domain_trust': 10
        }

        # Normalize and weight scores
        total_weight = sum(WEIGHTS.values())
        normalized_score = (
            (experience_score / MAX_SCORES['experience']) * WEIGHTS['experience'] +
            (education_score / MAX_SCORES['education']) * WEIGHTS['education'] +
            (skill_score / MAX_SCORES['skills']) * WEIGHTS['skills'] +
            (scholar_score / MAX_SCORES['scholar']) * WEIGHTS['scholar'] +
            (url_score / MAX_SCORES['url_safety']) * WEIGHTS['url_safety'] +
            (domain_score / MAX_SCORES['domain_trust']) * WEIGHTS['domain_trust']
        )

        # Scale to percentage
        total_percentage_score = (normalized_score / total_weight) * 100
        # Prepare detailed breakdown
        score_breakdown = {
            'total_score': total_percentage_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'skill_score': skill_score,
            'scholar_score': scholar_score,
            'url_score': url_score,
            'domain_score': domain_score,
            'scoring_factors': {
                'years_of_experience': position_count,
                'leadership_positions': leadership_count,
                'education_count': edu_count,
                'skill_count': skill_count,
                'total_endorsements': endorsement_count,
                # 'h_index': h_index,
                'citation_count': citation_count,
                # 'publication_count': publication_count,
                'url': url,
                'domain': domain,
                'domain_trust_score': domain_trust_score,
                'url_safe': "Safe" if url_score > 0 else "Unsafe" if url_score < 0 else "Unknown"
            }
        }
        
        return total_percentage_score, score_breakdown
    except Exception as e:
        print(f"Error calculating credibility score: {str(e)}")
        return 0, get_empty_score_breakdown()


def main():
    headers = {
        "X-RapidAPI-Key": "7c963ab537msh1c91075acd364b3p1ff392jsnf523b930f1dd",
        "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
    }
    scholar_api_key = "0b336f30e9feb2ef6991a61edda58e813bbf368bd6e8a9c92f2f0c0a8bff8482"
    safe_browsing_api_key = "AIzaSyCAPWZUkjobj7T-mX2p0kI5A3PeGSrn5as"
    
    domain_api_key = "7c963ab537msh1c91075acd364b3p1ff392jsnf523b930f1dd"

    try:
        username = input("Enter the LinkedIn username: ")
        scholar_name = input("Enter the scholar name for Google Scholar lookup: ")
        website_url = input("Enter the URL to evaluate: ")
        
        profile_data = get_linkedin_profile(username, headers)
        scholar_data = get_google_scholar_data(scholar_name, scholar_api_key)
        
        if profile_data or scholar_data:
            score, breakdown = calculate_credibility_score(profile_data, scholar_data, website_url, safe_browsing_api_key, domain_api_key)
        else:
            print("\nProfile not found or invalid username.")
            score, breakdown = 0, get_empty_score_breakdown()
        
        print("\nCredibility Score Analysis")
        print("=" * 50)
        percentage_score = score
        print(f"Overall Credibility Score: {score:.1f}/100 ({percentage_score:.1f}%)")
        print("\nScore Breakdown:")
        print(f"- Experience & Leadership: {breakdown['experience_score']:.1f}/60")
        print(f"- Education: {breakdown['education_score']:.1f}/20")
        print(f"- Skills & Endorsements: {breakdown['skill_score']:.1f}/20")
        print(f"- Scholarly Impact: {breakdown['scholar_score']:.1f}/30")
        print(f"- URL Safety: {breakdown['url_score']:.1f}/10")
        print(f"- Domain Trust: {breakdown['domain_score']:.1f}/10")
        
        print("\nKey Factors:")
        factors = breakdown['scoring_factors']
        print(f"- Years of Experience: {factors['years_of_experience']}")
        print(f"- Leadership Positions: {factors['leadership_positions']}")
        print(f"- Educational Qualifications: {factors['education_count']}")
        print(f"- Professional Skills: {factors['skill_count']}")
        print(f"- Total Skill Endorsements: {factors['total_endorsements']}")
        # print(f"- H-Index: {factors['h_index']}")
        print(f"- Citation Count: {factors['citation_count']}")
        # print(f"- Publication Count: {factors['publication_count']}")
        print(f"- URL Safety: {factors['url_safe']}")
        print(f"- Domain: {factors['domain']}")
        print(f"- Domain Trust Score: {factors['domain_trust_score']}/5")

            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please try again.")


if __name__ == "__main__":
    main()

# from flask import Flask, request, jsonify
# from linkedin import calculate_credibility_score, get_linkedin_profile, get_google_scholar_data

# app = Flask(__name__)

# @app.route('/calculate', methods=['POST'])
# def calculate():
#     try:
#         data = request.json
#         scholar_name = data['scholarName']
#         linkedin_username = data['linkedinUsername']
#         website_url = data['websiteUrl']

#         # Dummy headers and keys (replace with real ones)
#         headers = {"X-RapidAPI-Key": "7c963ab537msh1c91075acd364b3p1ff392jsnf523b930f1dd", "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"}
#         scholar_api_key = "0b336f30e9feb2ef6991a61edda58e813bbf368bd6e8a9c92f2f0c0a8bff8482"
#         safe_browsing_api_key = "AIzaSyCAPWZUkjobj7T-mX2p0kI5A3PeGSrn5as"
#         domain_api_key = "7c963ab537msh1c91075acd364b3p1ff392jsnf523b930f1dd"

#         profile_data = get_linkedin_profile(linkedin_username, headers)
#         scholar_data = get_google_scholar_data(scholar_name, scholar_api_key)

#         if profile_data or scholar_data:
#             score, _ = calculate_credibility_score(profile_data, scholar_data, website_url, safe_browsing_api_key, domain_api_key)
#             # percentage_score = score * 100
#             return jsonify({"score": score})
#         else:
#             return jsonify({"error": "Unable to fetch profile or scholar data"}), 400
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(port=5000)

from flask import Flask, request, jsonify
from ollama_hwpcs import get_trustworthiness_score
from reputation import calculate_credibility_score, get_linkedin_profile, get_google_scholar_data
import csv
import os

app = Flask(__name__)

def log_to_csv(data, filename='post_data_log.csv'):
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['text', 'scholarName', 'linkedinUsername', 'websiteUrl']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  #Write headers if the file does not exist
        writer.writerow(data)


@app.route('/style-check', methods=['POST'])
def evaluate_style():
    try:
        content = request.json
        article_text = content.get('text')
        if not article_text:
            return jsonify({'error': 'No text provided'}), 400
        style_score = analyze_text(article_text)
        return jsonify({'style_score': style_score})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fact-check', methods=['POST'])
def evaluate_fact():
    try:
        content = request.json
        article_text = content.get('text')
        if not article_text:
            return jsonify({'error': 'No text provided'}), 400
        fact_score = analyze_text(article_text)
        return jsonify({'fact_score': fact_score})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reputation-check', methods=['POST'])
def evaluate_reputation():
    try:
        content = request.json
        article_text = content.get('text')
        if not article_text:
            return jsonify({'error': 'No text provided'}), 400
        reputation_score = analyze_text(article_text)
        return jsonify({'reputation_score': reputation_score})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


def analyze_text(text):
    score = get_trustworthiness_score(text)
    return score


@app.route('/evaluate-text', methods=['POST'])
def evaluate_everything():
    try:
        content = request.json
        article_text = content.get('text')
        
        if not article_text:
            return jsonify({'error': 'No text provided'}), 400
        log_to_csv({'text': article_text})
        style_score = analyze_text(article_text)
        reputation_score = 7.31414
        fact_score = 3.92343124
        return jsonify({
            'style_score': style_score,
            'reputation_score': reputation_score,
            'fact_score': fact_score
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
@app.route('/evaluate-text-test', methods=['POST'])
def evaluate_everything_test():
    try:
        content = request.json
        article_text = content.get('text')
        
        if not article_text:
            return jsonify({'error': 'No text provided'}), 400
        log_to_csv({'text': article_text})
        style_score = analyze_text(article_text)
        reputation_score = 7.31414
        fact_score = 3.92343124
        return jsonify({
            'style_score': style_score,
            'reputation_score': reputation_score,
            'fact_score': fact_score
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        scholar_name = data['scholarName']
        linkedin_username = data['linkedinUsername']
        website_url = data['websiteUrl']
        headers = {"X-RapidAPI-Key": "7c963ab537msh1c91075acd364b3p1ff392jsnf523b930f1dd", "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"}
        scholar_api_key = "0b336f30e9feb2ef6991a61edda58e813bbf368bd6e8a9c92f2f0c0a8bff8482"
        safe_browsing_api_key = "AIzaSyCAPWZUkjobj7T-mX2p0kI5A3PeGSrn5as"
        domain_api_key = "7c963ab537msh1c91075acd364b3p1ff392jsnf523b930f1dd"
        profile_data = get_linkedin_profile(linkedin_username, headers)
        scholar_data = get_google_scholar_data(scholar_name, scholar_api_key)
        if profile_data or scholar_data:
            score, _ = calculate_credibility_score(profile_data, scholar_data, website_url, safe_browsing_api_key, domain_api_key)
            return jsonify({"score": score})
        else:
            return jsonify({"error": "Unable to fetch profile or scholar data"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug =True,host='0.0.0.0', port=80)
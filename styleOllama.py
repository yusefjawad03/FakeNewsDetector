from ollama import Client
import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from progressHold import add_progress

def get_trustworthiness_score(text):
    print("Input text:", text)
    add_progress()
    client = Client(
        host='http://localhost:11434',
        headers={'x-some-header': 'some-value'}
    )
    
    try:
        # Get the trustworthiness score
        score_response = client.chat(model='llama3:latest', messages=[
            {
                'role': 'user',
                'content': f"Determine the trustworthiness of the following text on a scale of 1 to 10, ONLY RETURN A NUMBER BETWEEN 1 AND 10, WITH NO TEXT: '{text}'",
            },
        ])
    except Exception as e:
        print("Error while getting score:", e)
        return 1, "Error retrieving score"
    
    print("Full score response:", score_response)
    score_content = getattr(score_response, 'message', {}).get('content', '').strip()
    print("Extracted score:", score_content)
    add_progress()
    # Convert the score to an integer
    try:
        score = int(score_content)
        print("Converted score to int:", score)
    except ValueError:
        print("Invalid score format, defaulting to 1")
        score = 1
    add_progress()
    # Ensure the score is within the 1-10 range
    final_score = min(max(score, 1), 10)
    print("Final bounded score:", final_score)
    add_progress()
    try:
        # Get the explanation for the score
        explanation_response = client.chat(model='llama3:latest', messages=[
            {
                'role': 'user',
                'content': f"Why did the text get a trustworthiness score of {final_score} to the following text? Respond in less than 20 words and from a third-person perspective: '{text}'",
            },
        ])
    except Exception as e:
        print("Error while getting explanation:", e)
        explanation = "Error retrieving explanation"
    else:
        explanation = getattr(explanation_response, 'message', {}).get('content', '').strip()
        print("Explanation:", explanation)
    add_progress()
    add_progress()
    return final_score, explanation
from ollama import Client

def get_trustworthiness_score(text):
    print("Input text:", text)

    client = Client(
        host='http://localhost:11434',
        headers={'x-some-header': 'some-value'}
    )
    try:
        response = client.chat(model='llama3:latest', messages=[
            {
                'role': 'user',
                'content': f"Determine the trustworthiness of the following text on a scale of 1 to 10, ONLY RETURN A NUMBER BETWEEN 1 AND 10, WITH NO TEXT: '{text}'",
            },
        ])
    except Exception as e:
        print("Error:", e)
        return 1

    print("full response was:", response)
    score_content = getattr(response, 'message', {}).get('content', '').strip()
    print("finalized score:", score_content) 

    #converter
    try:
        score = int(score_content)
        print("converted int:", score)  #debug
    except ValueError:
        print("Didn't work, reset to 1")
        score = 0

    final_score = min(max(score, 1), 10)
    print("Final score (bounded):", final_score)  #debug

    return final_score
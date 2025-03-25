# evaluator.py
from combinedServer.ollama_hwpcs import get_trustworthiness_score
import csv
import random

def evaluate_file(filename, true_label):
    """Evaluate 10 articles from lines 2 to 250 in the given file. true_label is True if articles are true, else False"""
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = list(csv.reader(csvfile))
        headers = reader.pop(0) 
        subset_rows = reader[1:250]
        selected_rows = random.sample(subset_rows, min(10, len(subset_rows)))
    
    total = 0
    correct = 0
    for row in selected_rows:
        title = row[0]
        text = row[1]

        score = get_trustworthiness_score(text)
        predicted_label = score >= 5  #true if score >=5
        if predicted_label == true_label:
            correct +=1
        total +=1
    percent_correct = (correct / total) * 100 if total > 0 else 0
    return percent_correct

def main():
    true_accuracy = evaluate_file('True.csv', true_label=True)
    fake_accuracy = evaluate_file('Fake.csv', true_label=False)
    print(f"True articles accuracy: {true_accuracy:.2f}%")
    print(f"Fake articles accuracy: {fake_accuracy:.2f}%")

if __name__ == '__main__':
    main()

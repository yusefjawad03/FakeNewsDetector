# evaluate.py
from sklearn.metrics import accuracy_score, classification_report
from model import load_model, load_data
import torch

# Load model and data
train_dataset, test_dataset = load_data()  # This now uses both train.csv and test.csv
model = load_model()

# Evaluation
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
model.to(device)

def evaluate_model(model, dataloader):
    model.eval()
    predictions = []
    with torch.no_grad():
        for batch in dataloader:
            batch = {key: val.to(device) for key, val in batch.items()}
            outputs = model(**batch)
            logits = outputs.logits
            predictions.extend(torch.argmax(logits, axis=1).cpu().numpy())
    return predictions

test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=16)
predictions = evaluate_model(model, test_loader)

# Since test.csv doesn't have labels, we can't use classification_report or accuracy_score.
# Instead, we just output the predictions for each test instance:
print(predictions)

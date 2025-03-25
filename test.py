import torch
import pandas as pd
from transformers import BertTokenizer
from model import load_model, NewsDataset

# Load the trained model
model_path = "bert_fake_news_detector.pth"
model = load_model()
model.load_state_dict(torch.load(model_path))
model.eval()  # Set model to evaluation mode

# Set device (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Load test data
test_df = pd.read_csv("test.csv")

# Fill missing values
test_df["text"] = test_df["text"].fillna("")

# Tokenizer (same as used in training)
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Function to make predictions
def predict(text):
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    inputs = {key: val.to(device) for key, val in inputs.items()}  # Move to GPU if available
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        prediction = torch.argmax(logits, dim=1).item()
    
    return prediction  # 0 (real) or 1 (fake)

# Run predictions on test data
test_df["predicted_label"] = test_df["text"].apply(predict)

# Save results
test_df.to_csv("test_predictions.csv", index=False)
print("Predictions saved to 'test_predictions.csv'.")

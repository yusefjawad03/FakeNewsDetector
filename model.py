# model.py
import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# Define the NewsDataset class outside of the load_data function
class NewsDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels=None):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels) if self.labels is not None else len(self.encodings)

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        if self.labels is not None:
            item['labels'] = torch.tensor(self.labels.iloc[idx])
        return item

# Load and preprocess data
def load_data(train_file='train.csv', test_file='test.csv'):
    # Load train dataset
    df_train = pd.read_csv(train_file)
    
    # Handle missing values in the 'text' column by filling them with an empty string or placeholder
    df_train['text'] = df_train['text'].fillna('')

    X_train = df_train['text']
    y_train = df_train['label']
    
    # Load test dataset
    df_test = pd.read_csv(test_file)
    df_test['text'] = df_test['text'].fillna('')
    X_test = df_test['text']
    
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    def tokenize_data(texts, labels=None, max_length=512):
        # Ensure texts is a list of strings
        if isinstance(texts, pd.Series):
            texts = texts.tolist()
        return tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors='pt',
            add_special_tokens=True
        ), labels

    train_encodings, train_labels = tokenize_data(X_train, y_train)
    test_encodings, _ = tokenize_data(X_test)  # No labels for test set

    train_dataset = NewsDataset(train_encodings, train_labels)
    test_dataset = NewsDataset(test_encodings)  # No labels for test set

    return train_dataset, test_dataset

# Load the BERT model
def load_model():
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
    return model

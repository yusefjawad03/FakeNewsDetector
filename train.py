import torch
from torch.utils.data import DataLoader
from transformers import AdamW
from model import load_model, load_data

# Load data and model
train_dataset, test_dataset = load_data()
model = load_model()

# Set device (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# DataLoader (for batching)
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)

# Define optimizer and loss function
optimizer = AdamW(model.parameters(), lr=5e-5)
loss_fn = torch.nn.CrossEntropyLoss()

# Training loop
epochs = 1  # You can adjust this
for epoch in range(epochs):
    model.train()
    total_loss = 0
    
    for batch in train_loader:
        optimizer.zero_grad()
        
        # Move batch to device
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        # Forward pass
        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        total_loss += loss.item()

        # Backward pass and optimization
        loss.backward()
        optimizer.step()

    avg_loss = total_loss / len(train_loader)
    print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

# Save the trained model
torch.save(model.state_dict(), "bert_fake_news_detector.pth")
print("Training complete. Model saved as 'bert_fake_news_detector.pth'.")

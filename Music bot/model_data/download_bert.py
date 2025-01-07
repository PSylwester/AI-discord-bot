from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Ścieżka lokalna, gdzie zostanie zapisany model
model_path = "./models/bert"

# Pobierz model i tokenizer
model_name = "bert-base-uncased"  # Możesz użyć innego pretrenowanego modelu
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Zapisz model lokalnie
tokenizer.save_pretrained(model_path)
model.save_pretrained(model_path)

print(f"Model BERT został pobrany i zapisany w: {model_path}")

from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Ścieżka do oryginalnego modelu
model_path = "./models/bert_custom"

# Wczytaj model i tokenizer
model = AutoModelForSequenceClassification.from_pretrained(model_path, ignore_mismatched_sizes=True)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Przypisz etykiety dla 4 klas
model.config.id2label = {0: "rpg", 1: "shooter", 2: "strategy", 3: "horror"}
model.config.label2id = {v: k for k, v in model.config.id2label.items()}

# Zapisz naprawiony model
model.save_pretrained(model_path)
tokenizer.save_pretrained(model_path)
print("Model naprawiony i zapisany ponownie.")

from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import Dataset
import random

# Przygotowanie zbalansowanych danych
data = [
    {"text": "The Witcher 3 is an immersive RPG game.", "expected_label": "rpg"},
    {"text": "Call of Duty is a first-person shooter with action combat.", "expected_label": "shooter"},
    {"text": "Age of Empires is a real-time strategy game.", "expected_label": "strategy"},
    {"text": "Resident Evil is a survival horror game.", "expected_label": "horror"},
    {"text": "Tetris is a relaxing puzzle game for everyone.", "expected_label": "general"},
]
random.shuffle(data)

# Mapowanie etykiet
label_mapping = {"rpg": 0, "shooter": 1, "strategy": 2, "horror": 3, "general": 4}

# Konwersja do formatu Dataset
dataset = Dataset.from_list(data).train_test_split(test_size=0.2)

# Tokenizacja
model_path = "./models/bert_custom"  # Ścieżka do istniejącego modelu
tokenizer = AutoTokenizer.from_pretrained(model_path)

def preprocess(examples):
    tokenized = tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)
    tokenized["labels"] = [label_mapping[label] for label in examples["expected_label"]]
    return tokenized

tokenized_data = dataset.map(preprocess, batched=True)

# Załaduj istniejący model
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Parametry treningowe dla fine-tuningu
training_args = TrainingArguments(
    output_dir="./results_finetune",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=2,  # Krótszy trening
    load_best_model_at_end=True,
)

# Fine-tuning modelu
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_data["train"],
    eval_dataset=tokenized_data["test"],
    tokenizer=tokenizer,
)

trainer.train()

# Zapisanie dostosowanego modelu
model.save_pretrained("./models/bert_custom_finetuned")
tokenizer.save_pretrained("./models/bert_custom_finetuned")

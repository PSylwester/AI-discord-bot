import importlib
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import Dataset
from evaluate import load

# Funkcja wczytująca dane z plików Python
def load_data_from_files(file_names):
    data = []
    for file_name in file_names:
        module = importlib.import_module(file_name)
        data.extend(module.data)
    return data

# Lista plików z danymi
files = ["shooter_data.py", "strategy_data.py", "rpg_data.py", "horror.py", "general"]

# Wczytanie danych z plików
data = load_data_from_files(files)

# Przygotowanie zestawu danych
dataset = Dataset.from_list(data).train_test_split(test_size=0.2)

label_mapping = {
    "shooter": 0,
    "strategy": 1,
    "rpg": 2,
    "horror": 3,
    "general": 4,
}

# Wczytaj model i tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=5)

# Tokenizacja danych
def preprocess(examples):
    tokenized = tokenizer(examples["text"], truncation=True, padding=True)
    tokenized["labels"] = [label_mapping[label] for label in examples["expected_label"]]
    return tokenized

tokenized_data = dataset.map(preprocess, batched=True)

# Dodanie metryki
metric = load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = logits.argmax(axis=-1)
    return metric.compute(predictions=predictions, references=labels)

# Ustawienia trenowania
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="steps",
    save_steps=10,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=10,
    report_to="none",
    use_cpu=True
)

# Trening
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_data["train"],
    eval_dataset=tokenized_data["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)
trainer.train()

# Zapisz wytrenowany model
model.save_pretrained("./models/bert_custom")
tokenizer.save_pretrained("./models/bert_custom")

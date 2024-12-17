import importlib
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import Dataset
from evaluate import load

# Wczytanie danych z plików
from rpg_data import rpg_data
from shooter_data import shooter_data
from strategy_data import strategy_data
from horror_data import horror_data

data = rpg_data + shooter_data + strategy_data + horror_data

# Przygotowanie zestawu danych
dataset = Dataset.from_list(data).train_test_split(test_size=0.2)

# Mapowanie etykiet
label_mapping = {
    "rpg": 0,
    "shooter": 1,
    "strategy": 2,
    "horror": 3,
}

# Wczytaj model i tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=len(label_mapping))

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
    evaluation_strategy="steps",
    save_steps=100,
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

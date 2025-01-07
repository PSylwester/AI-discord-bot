import random
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from sklearn.model_selection import StratifiedKFold
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from transformers import EarlyStoppingCallback
import json

# 1. Load Data
from rpg_data import rpg_data
from shooter_data import shooter_data
from strategy_data import strategy_data
from general_data import general_data

data = rpg_data + shooter_data + strategy_data + general_data
random.shuffle(data)

texts = [item['text'] for item in data]
labels = [item['expected_label'] for item in data]

label_mapping = {"rpg": 0, "shooter": 1, "strategy": 2, "general": 3}
labels = [label_mapping[label] for label in labels]

# 2. Tokenization
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)

data_dict = {
    "input_ids": encodings["input_ids"],
    "attention_mask": encodings["attention_mask"],
    "labels": labels
}

dataset = Dataset.from_dict(data_dict)

# 3. Cross-Validation Setup
skf = StratifiedKFold(n_splits=5)
all_metrics = []

for fold, (train_index, val_index) in enumerate(skf.split(encodings["input_ids"], labels)):
    print(f"Starting Fold {fold + 1}")

    train_dataset = Dataset.from_dict({
        "input_ids": [encodings["input_ids"][i] for i in train_index],
        "attention_mask": [encodings["attention_mask"][i] for i in train_index],
        "labels": [labels[i] for i in train_index]
    })

    val_dataset = Dataset.from_dict({
        "input_ids": [encodings["input_ids"][i] for i in val_index],
        "attention_mask": [encodings["attention_mask"][i] for i in val_index],
        "labels": [labels[i] for i in val_index]
    })

    # 4. Model Definition
    model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=4)

    # 5. Training Arguments
    training_args = TrainingArguments(
        output_dir=f"./results_fold_{fold}",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-5,
        per_device_train_batch_size=16,
        num_train_epochs=5,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir=f"./logs_fold_{fold}",
        logging_steps=10,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy"
    )

    # 6. Metrics
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
        accuracy = accuracy_score(labels, predictions)
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    # 7. Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )

    # 8. Train the Model
    trainer.train()

    # 9. Evaluate and Save Metrics
    eval_results = trainer.evaluate()
    all_metrics.append(eval_results)
    print(f"Metrics for Fold {fold + 1}:", eval_results)

# 10. Average Metrics
average_metrics = {
    "accuracy": np.mean([m["eval_accuracy"] for m in all_metrics]),
    "precision": np.mean([m["eval_precision"] for m in all_metrics]),
    "recall": np.mean([m["eval_recall"] for m in all_metrics]),
    "f1": np.mean([m["eval_f1"] for m in all_metrics])
}
print("Average Metrics Across Folds:", average_metrics)

# Save Final Metrics
with open("./results/average_metrics.json", "w") as f:
    json.dump(average_metrics, f, indent=4)

# Final Training on All Data
print("Training final model on all data...")
final_train_dataset = Dataset.from_dict({
    "input_ids": encodings["input_ids"],
    "attention_mask": encodings["attention_mask"],
    "labels": labels
})

final_model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=4)

final_training_args = TrainingArguments(
    output_dir="./final_model",
    evaluation_strategy="no",
    learning_rate=3e-5,
    per_device_train_batch_size=16,
    num_train_epochs=5,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir="./logs_final",
    save_total_limit=1
)

final_trainer = Trainer(
    model=final_model,
    args=final_training_args,
    train_dataset=final_train_dataset
)

final_trainer.train()

# Save Final Model
final_model.save_pretrained("./models/bert_custom_final")
tokenizer.save_pretrained("./models/bert_custom_final")
print("Final model saved in ./models/bert_custom_final")

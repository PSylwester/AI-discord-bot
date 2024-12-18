import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Załaduj model i tokenizer
model_path = "./models/bert_custom_final"
model = AutoModelForSequenceClassification.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 2. Przykładowe dane testowe
test_texts = [
    "Lead your troops to victory in this strategy game.",  # strategy
    "Explore dungeons and fight dragons in this epic RPG.",  # rpg
    "Shoot your enemies in fast-paced multiplayer matches.",  # shooter
    "Relax and enjoy this simple puzzle-solving experience.",  # general
    "Embark on a grand adventure to save the kingdom.",  # rpg
    "Battle royale games are all about survival.",  # shooter
    "Plan your moves carefully to outsmart your opponent.",  # strategy
    "Solve word puzzles and relax after a busy day."  # general
]
test_labels = [2, 0, 1, 3, 0, 1, 2, 3]  # Odpowiadające etykiety klas

# 3. Mapowanie etykiet
label_mapping = {0: "rpg", 1: "shooter", 2: "strategy", 3: "general"}

# 4. Predykcja i zapisywanie wyników
predictions = []
for text in test_texts:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    outputs = model(**inputs)
    predicted_class = outputs.logits.argmax(axis=-1).item()
    predictions.append(predicted_class)

# 5. Raport wyników
print("\nClassification Report:")
print(classification_report(test_labels, predictions, target_names=label_mapping.values()))

# 6. Wizualizacja: Macierz pomyłek
conf_matrix = confusion_matrix(test_labels, predictions)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=label_mapping.values(), yticklabels=label_mapping.values())
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix")
plt.show()

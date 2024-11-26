from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# Wczytaj model i tokenizer
model_path = "./models/bert_custom"
model = AutoModelForSequenceClassification.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)

# Dane testowe
test_data = [
    {"input": "I will play Witcher 3 or Skyrim tonight", "expected": "rpg"},
    {"input": "Let's go with Age of Empires or maybe Civilization VI", "expected": "strategy"},
    {"input": "Call of Duty and Counter Strike are my favorite games", "expected": "shooter"},
    {"input": "Something spooky like Resident Evil or Dead by Daylight", "expected": "horror"},
    {"input": "I just want to relax and play Tetris", "expected": "general"}
]

candidate_labels = ["shooter", "strategy", "rpg", "horror", "general"]

# Testowanie
correct = 0
for test in test_data:
    result = classifier(test["input"], candidate_labels)
    predicted = result["labels"][0]
    print(f"Input: {test['input']}")
    print(f"Expected: {test['expected']}, Predicted: {predicted}")
    if predicted == test["expected"]:
        correct += 1

accuracy = correct / len(test_data)
print(f"Accuracy: {accuracy * 100:.2f}%")

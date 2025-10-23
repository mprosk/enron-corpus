import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Sample data - you'll need a larger and more diverse dataset for a real-world scenario
emails = [
    ("news", "Latest updates on technology advancements."),
    ("spam", "Congratulations! You've won a million dollars."),
    ("personal", "Hi friend, how have you been?"),
    ("business", "Invoice for services rendered."),
    # Add more examples with different categories
]

# Split data into features (X) and labels (y)
labels, messages = zip(*emails)


# Preprocess text data
def preprocess_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r"\W", " ", text)  # Remove non-alphanumeric characters
    return text


messages = [preprocess_text(message) for message in messages]

# Convert text data into numerical features using Bag of Words (BoW) representation
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(messages)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42
)

# Train the Naive Bayes classifier
classifier = MultinomialNB()
classifier.fit(X_train, y_train)

# Make predictions on the test set
predictions = classifier.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, predictions)
print(f"Accuracy: {accuracy:.2f}")

# Print classification report for detailed performance metrics
print("Classification Report:\n", classification_report(y_test, predictions))

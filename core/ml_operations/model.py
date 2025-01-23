from core.utils.code_preprocessing import *
import torch


class Model:
    def __init__(self, vectorizer, selector, model, name, filetype):
        self.vectorizer = vectorizer
        self.selector = selector
        self.model = model
        self.name = name
        self.filetype = filetype

    def __str__(self):
        return self.name

    def predict(self, code):
        prediction = None

        code = "\n".join(code)
        code = remove_blank_lines(code)
        code = replace_strings_and_chars(code)
        code = replace_numbers(code)
        code = replace_booleans(code)
        code_tokens_list = tokenize_code(code)

        code_vec = self.__ngram_vectorize_text(
            texts=[word_list_to_string(code_tokens_list)],
        )

        # Use the trained model to make a prediction on the preprocessed text
        if self.filetype == "pkl":
            prediction = self.model.predict(code_vec)
            prediction = prediction[0]
        elif self.filetype == "h5":
            code_vec = code_vec.toarray()
            prediction = self.model(code_vec)
            prediction = prediction[0][0]
            if prediction > 0.5:
                prediction = 1
            else:
                prediction = 0

        return prediction

    def __ngram_vectorize_text(self, texts):
        # Vectorize new texts using the same vectorizer that was used during training.
        x = self.vectorizer.transform(texts)

        # Select top 'k' features using the same selector that was used during training.
        x = self.selector.transform(x).astype("float32")

        return x


class CodeBERTModel:
    def __init__(self, tokenizer, model, name, number_of_kus):
        self.tokenizer = tokenizer
        self.model = model
        self.name = name
        self.number_of_kus = number_of_kus

    def __str__(self):
        return self.name

    def number_of_kus(self):
        return self.number_of_kus

    def predict(self, code):
        code = "\n".join(code)
        code = remove_blank_lines(code)
        code = replace_strings_and_chars(code)
        code = replace_numbers(code)
        code = replace_booleans(code)

        # Tokenize the input code snippet
        inputs = self.tokenizer([code], padding=True, truncation=True, return_tensors='pt')

        # Make predictions
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Convert logits to probabilities
        predictions = torch.sigmoid(outputs.logits)

        # Apply a threshold to get binary predictions
        threshold = 0.5
        binary_predictions = (predictions > threshold).int()

        return binary_predictions[0]

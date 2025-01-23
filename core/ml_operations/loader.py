import os
from joblib import load
import tensorflow as tf
from .model import *
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Suppress TensorFlow warnings about CPU instructions
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def load_models_from_directory(directory, models_to_load=None):
    models = []

    # Iterate over all subdirectories
    for subdir in os.listdir(directory):
        if not os.path.isdir(os.path.join(directory, subdir)):
            continue

        # Confirm it matches the "K#" pattern
        if models_to_load is not None and subdir not in models_to_load:
            continue

        vectorizer = None
        selector = None
        model = None
        filetype = None

        # Find and load the vectorizer
        vectorizer_path = None
        for file in os.listdir(os.path.join(directory, subdir)):
            if file.startswith(f"{subdir}_vectorizer") and file.endswith(".pkl"):
                vectorizer_path = os.path.join(directory, subdir, file)
                vectorizer = load(vectorizer_path)
                break
        if not vectorizer_path:
            print(f"Vectorizer not found for {subdir}. Skipping...")
            continue

        # Find and load the selector
        selector_path = None
        for file in os.listdir(os.path.join(directory, subdir)):
            if file.startswith(f"{subdir}_selector") and file.endswith(".pkl"):
                selector_path = os.path.join(directory, subdir, file)
                selector = load(selector_path)
                break
        if not selector_path:
            print(f"Selector not found for {subdir}. Skipping...")
            continue

        # Load the model, either .pkl or .h5
        model_path = None
        for file in os.listdir(os.path.join(directory, subdir)):
            if file.endswith("model.pkl"):
                model_path = os.path.join(directory, subdir, file)
                model = load(model_path)
                filetype = "pkl"
                break
            elif file.endswith("model.h5"):
                model_path = os.path.join(directory, subdir, file)
                model = tf.keras.models.load_model(model_path)
                filetype = "h5"
                break

        if not model_path:
            print(f"No suitable model found for {subdir}. Skipping...")
            continue

        if vectorizer and selector and model:
            print(f"Loaded {subdir} model")
            # append the loaded Model instance to the models list
            models.append(Model(vectorizer, selector, model, subdir, filetype))

    return models


def load_codebert_model(directory, number_of_kus=27):
    tokenizer = AutoTokenizer.from_pretrained(directory)
    model = AutoModelForSequenceClassification.from_pretrained(directory)
    return CodeBERTModel(tokenizer, model, "CodeBERT", number_of_kus)

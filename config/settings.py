import os

ROOT_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
TEMP_FILES_BASE_PATH = os.path.normpath(os.path.join(ROOT_DIR, "temp"))
OUTPUT_FILES_BASE_PATH = os.path.normpath(os.path.join(ROOT_DIR, "output"))
CLONED_REPO_BASE_PATH = os.path.normpath(os.path.join(ROOT_DIR, "cloned_repos"))
MODELS_BASE_PATH = os.path.normpath(os.path.join(ROOT_DIR, "models", "binary_classifiers"))
CODEBERT_BASE_PATH = os.path.normpath(os.path.join(ROOT_DIR, "models", "codebert"))
FILE_TYPE = "java"
MODELS_TO_LOAD = [
    "K2",
    "K3",
    "K4",
    "K6",
    "K7",
    "K8",
    "K9",
    "K10",
    "K11",
    "K12",
    "K13",
    "K14",
    "K15",
    "K16",
    "K17",
    "K18",
    "K19",
    "K20",
    "K21",
    "K22",
    "K23",
    "K24",
    "K25",
    "K27",
    "K28",
]

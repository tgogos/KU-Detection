import os

from api.data_db import get_analysis_withsha_db
from .code_file import CodeFile


def read_files_from_directory(directory: str):
    """
    Read the contents of all .java files in the specified directory. The author and timestamp fields are left empty.

    Parameters:
        directory (str): The directory containing the .java files.

    Returns:
        dict: A dictionary with filenames as keys and their CodeFile objects as values.
    """
    files = [f for f in os.listdir(directory) if f.endswith(".java")]
    contents = {}

    for filename in files:
        file_path = os.path.join(directory, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            contents[filename] = CodeFile(filename, f.read())

    return contents


import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def read_files_from_dict_list(dict_list: list):
    """
    Read the contents of all .java files in the directories found inside the git contribution dictionaries.

    Parameters:
        dict_list (list): A list of git contribution dictionaries.

    Returns:
        dict: A dictionary with filenames as keys and their CodeFile objects as values.
    """
    contents = {}
    logging.info("Starting to process the dictionary list for file contributions.")

    for contribution in dict_list:
        try:
            sha = contribution["sha"]
            temp_filepath = contribution["temp_filepath"]
            logging.debug(f"Processing contribution with SHA: {sha} and temp filepath: {temp_filepath}")

            # Check if the analysis already exists in the database
            existing_analysis = get_analysis_withsha_db(sha)
            if len(existing_analysis) != 0:
                logging.info(f"Skipping contribution with SHA: {sha}, analysis already exists.")
                continue

            filename = os.path.basename(temp_filepath).split(".")[0]
            contents[filename] = CodeFile(
                filename,
                contribution["file_content"],
                author=contribution["author"],
                timestamp=contribution["timestamp"],
                sha=sha,
            )
            logging.debug(f"Successfully processed file: {filename}")

        except KeyError as e:
            logging.error(f"KeyError: Missing key {e} in contribution: {contribution}")
        except Exception as e:
            logging.exception(f"An unexpected error occurred while processing contribution: {contribution}")

    logging.info("Finished processing all contributions.")
    return contents


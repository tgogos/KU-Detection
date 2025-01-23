import csv
from config.settings import MODELS_TO_LOAD


def export_to_csv(files, csv_filename):
    kus = MODELS_TO_LOAD

    headers = ['filename', 'author', 'timestamp', 'sha'] + kus

    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for code_file in files.values():
            row = [
                      code_file.filename,
                      code_file.author,
                      code_file.timestamp,
                      code_file.sha
                  ] + [1 if code_file.ku_results[ku] else 0 for ku in kus]
            writer.writerow(row)

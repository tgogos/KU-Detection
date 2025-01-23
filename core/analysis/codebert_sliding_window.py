from core.utils.code_file import CodeFile
from core.ml_operations.model import CodeBERTModel
from typing import List


def codebert_sliding_window(
        files: List[CodeFile],
        min_win_size: int,
        max_win_size: int,
        win_increase_step: int,
        move_step: int,
        model: CodeBERTModel,
):
    file_results = {}

    for f in files:
        detected_kus = [0] * model.number_of_kus
        min_win_size = min(min_win_size, f.total_lines)
        max_win_size = min(max_win_size, f.total_lines)

        for win_size in range(min_win_size, max_win_size + 1, win_increase_step):
            for start_idx in range(0, f.total_lines - win_size + 1, move_step):
                end_idx = start_idx + win_size
                window_lines = f.lines[start_idx:end_idx]

                results = model.predict(window_lines)

                # If a KU is detected in the window, it counts as being detected in the file
                for i, result in enumerate(results):
                    if detected_kus[i] == 0 and result:
                        detected_kus[i] = 1

        file_results[f.filename] = detected_kus

        for i, result in enumerate(detected_kus):
            f.add_ku_result(f"K{i + 1}", result)
    return file_results

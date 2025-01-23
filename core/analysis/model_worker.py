def model_worker(
        model,
        files,
        min_win_size,
        max_win_size,
        win_increase_step,
        move_step,
):
    file_results = {}

    for filename, f in files.items():
        min_win_size = min(min_win_size, f.total_lines)
        max_win_size = min(max_win_size, f.total_lines)

        for win_size in range(min_win_size, max_win_size + 1, win_increase_step):
            for start_idx in range(0, f.total_lines - win_size + 1, move_step):
                end_idx = start_idx + win_size
                window_lines = f.lines[start_idx:end_idx]

                result = model.predict(window_lines)
                if result is None:
                    continue
                # If a result is true, mark KU as detected and move on to the next file
                if int(result) == 1:
                    file_results[filename] = True
                    break
            else:
                continue
            break
        else:
            file_results[filename] = False

    return file_results

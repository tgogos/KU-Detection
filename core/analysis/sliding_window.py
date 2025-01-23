import concurrent.futures
from .model_worker import model_worker


def sliding_window(
        files,
        min_win_size,
        max_win_size,
        win_increase_step,
        move_step,
        models,
):
    # Initialize the data structure for results
    model_results = {}

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                model_worker,
                model,
                files,
                min_win_size,
                max_win_size,
                win_increase_step,
                move_step,
            ): model
            for model in models
        }

        for future in concurrent.futures.as_completed(futures):
            model = futures[future]
            file_results = future.result()
            model_results[str(model)] = file_results

            for code_file in files.values():
                code_file.add_ku_result(str(model), file_results[code_file.filename])

    return model_results

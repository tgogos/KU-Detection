import os
import logging
import json
import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
import time

from api.data_db import save_commits_to_db, get_commits_from_db, save_analysis_to_db, save_repo_to_db, \
    get_all_repos_from_db, get_analysis_from_db, delete_repo_from_db, getdetected_kus, get_commits_timestamps_from_db
from core.git_operations import clone_repo, repo_exists, extract_contributions
from core.git_operations.repo import pull_repo, get_history_repo
from core.utils.code_files_loader import read_files_from_dict_list
from core.ml_operations.loader import load_codebert_model
from core.analysis.codebert_sliding_window import codebert_sliding_window
from config.settings import CLONED_REPO_BASE_PATH, CODEBERT_BASE_PATH

app = Flask(__name__)

# Load model
model = load_codebert_model(CODEBERT_BASE_PATH, 27)

def init_routes(app):
    @app.route('/commits', methods=['POST'])
    def list_commits():
        data = request.get_json()
        repo_url = data.get('repo_url')
        commit_limit = data.get('limit', 50)

        if not repo_url:
            return jsonify({"error": "Repository URL is required"}), 400

        repo_name = repo_url.split('/')[-1].replace('.git', '')

        if not repo_exists(repo_name):
            clone_repo(repo_url, os.path.join(CLONED_REPO_BASE_PATH, "fake_session_id", str(repo_name)))
        else:
            # Pull the latest changes if the repository already exists
            pull_repo(os.path.join(CLONED_REPO_BASE_PATH, "fake_session_id", str(repo_name)))

        commits = extract_contributions(os.path.join(CLONED_REPO_BASE_PATH, "fake_session_id", repo_name),
                                        commit_limit=commit_limit)

        #print(commits)
        save_commits_to_db(repo_name, commits)

        return jsonify(commits)

    @app.route('/repos', methods=['POST'])
    def create_repo():
        data = request.json
        repo_name = data.get('repo_name')
        url = data.get('url', '')
        description = data.get('description', '')
        comments = data.get('comments', '')

        try:
            save_repo_to_db(repo_name, url, description, comments)
            return jsonify({"message": "Repository created successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/detected_kus', methods=['GET'])
    def get_detected_kus():
        try:
            kus_list = getdetected_kus()
            if kus_list is not None:
                #print(kus_list)
                #print("____")
                #print(jsonify(kus_list))
                return kus_list, 200
            else:
                return jsonify({"error": "Failed to retrieve detected KUs"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/repos/<string:repo_name>', methods=['PUT'])
    def edit_repo(repo_name):
        data = request.json
        url = data.get('url', '')
        description = data.get('description', '')
        comments = data.get('comments', '')

        try:
            save_repo_to_db(repo_name, url, description, comments)
            return jsonify({"message": "Repository updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/timestamps', methods=['GET'])
    def get_timestamps():
        try:
            repo_name = request.args.get('repo_name')

            if not repo_name:
                return jsonify({"error": "Repository name is required"}), 400

            # Καλούμε την συνάρτηση για να ανακτήσουμε τα timestamps των commits από τη βάση δεδομένων
            timestamps = get_commits_timestamps_from_db(repo_name)

            if timestamps is None:
                return jsonify({"error": "Failed to retrieve timestamps"}), 500

            #print(timestamps)
            return jsonify(timestamps), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/historytime', methods=['GET'])
    def historytime():
        try:
            # Λήψη του repo_url από τα query parameters
            repo_url = request.args.get('repo_url')
            if not repo_url:
                return jsonify({"error": "Missing 'repo_url' parameter"}), 400

            repo_name = repo_url.split('/')[-1].replace('.git', '')

            # Κλήση της μεθόδου get_history_repo με το URL του repository
            commit_history = get_history_repo(repo_url, repo_name, CLONED_REPO_BASE_PATH)

            # Μετατροπή των timestamps σε string για να επιστραφούν στο JSON response
            commit_dates = [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in commit_history]

            return jsonify({"repo_name": repo_name, "commit_dates": commit_dates}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/delete_repo/<string:repo_name>', methods=['DELETE'])
    def delete_repo(repo_name):
        try:
            # Κλήση στη συνάρτηση που διαγράφει τα δεδομένα από τη βάση
            delete_repo_from_db(repo_name)
            return jsonify({"message": f"Repository '{repo_name}' and related data deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/repos', methods=['GET'])
    def list_repos():
        try:
            repos = get_all_repos_from_db()
            return jsonify(repos), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    @app.route('/analyze', methods=['GET'])
    def analyze():
        repo_url = request.args.get('repo_url')

        if not repo_url:
            logging.error("No repository URL provided.")
            return jsonify({"error": "Repository URL is required"}), 400

        repo_name = repo_url.split('/')[-1].replace('.git', '')
        logging.info(f"Starting analysis for repository: {repo_name}")

        # Get commits from the database
        commits = get_commits_from_db(repo_name)

        if not commits:
            logging.error(f"No commits found for repository: {repo_name}")
            return jsonify({"error": "No commits found for the repository"}), 400

        try:
            # Read files from the commits
            files = read_files_from_dict_list(commits)
            logging.info(f"Retrieved {len(files)} files for analysis.")

            analysis_results = []

            @stream_with_context
            def generate():
                analyzed_files_count = 0

                for file in files.values():
                    try:
                        logging.debug(f"Analyzing file: {file.filename}")
                        start_time = time.time()
                        results = codebert_sliding_window([file], 35, 35, 1, 25, model)
                        end_time = time.time()
                        elapsed_time = end_time - start_time

                        if isinstance(file.timestamp, datetime.datetime):
                            timestmp = file.timestamp.isoformat()
                        else:
                            timestmp = file.timestamp

                        file_data = {
                            "filename": file.filename,
                            "author": file.author,
                            "timestamp": timestmp,
                            "sha": file.sha,
                            "detected_kus": file.ku_results,
                            "elapsed_time": elapsed_time
                        }
                        analysis_results.append(file_data)
                        yield f"data: {json.dumps(file_data)}\n\n"
                        analyzed_files_count += 1
                        logging.info(f"Successfully analyzed file {analyzed_files_count}/{len(files)}: {file.filename}")

                    except Exception as e:
                        logging.exception(
                            f"Error analyzing file: {file.filename}. Total analyzed before error: {analyzed_files_count}.")
                        raise

                # Save results to the database
                save_analysis_to_db(repo_name, analysis_results)
                logging.info(
                    f"Analysis completed for repository: {repo_name}. Total files analyzed: {len(analysis_results)}")
                yield "data: end\n\n"

            return Response(generate(), mimetype='text/event-stream')

        except Exception as e:
            logging.exception(f"Unexpected error during analysis for repository: {repo_name}")
            return jsonify({"error": "An error occurred during analysis"}), 500

    @app.route('/analyzedb', methods=['GET'])
    def analyzedb():
        try:
            # Παίρνουμε το repo_name από τα query parameters (π.χ., /analyzedb?repo_name=my_repo)
            repo_name = request.args.get('repo_name')

            if not repo_name:
                return jsonify({"error": "repo_name parameter is required"}), 400

            # Καλούμε τη συνάρτηση για να ανακτήσουμε τα δεδομένα από τη βάση
            analysis_data = get_analysis_from_db(repo_name)

            #print(analysis_data)

            if analysis_data is None:
                return jsonify({"error": "Failed to retrieve analysis data"}), 500

            # Επιστρέφουμε τα δεδομένα σε μορφή JSON
            return analysis_data, 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    from flask import Flask, jsonify, request

    app = Flask(__name__)


if __name__ == '__main__':
    app.run(debug=True)

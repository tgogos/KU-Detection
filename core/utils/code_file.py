from .code_preprocessing import (remove_comments, remove_imports, remove_packages)


class CodeFile:
    def __init__(self, filename, content, author=None, timestamp=None, sha=None):
        self.filename = filename
        self.content = content
        self.content = self.__clean_file()
        self.lines = self.__split_in_lines()
        self.total_lines = len(self.lines)

        self.author = author
        self.timestamp = timestamp
        self.sha = sha
        self.ku_results = {}

    def __str__(self):
        return self.filename

    def __clean_file(self):
        content = remove_comments(self.content)
        content = remove_imports(content)
        content = remove_packages(content)
        return content

    def __split_in_lines(self):
        lines = self.content.split("\n")
        # Ignore lines that are empty or only contain "{" or "}"
        lines = [line for line in lines if (line.strip() not in ["", "{", "}"])]
        return lines

    def add_ku_result(self, ku_name, result):
        self.ku_results[ku_name] = result

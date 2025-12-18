from abc import ABC, abstractmethod


class FilenameSanitizer(ABC):
    @abstractmethod
    def sanitize(self, filename: str) -> str:
        pass


class SecurityFilenameSanitizer(FilenameSanitizer):
    def __init__(self, max_length: int = 255):
        self.max_length = max_length
        self.dangerous_chars = [
            ";",  # Command separator in shell
            "|",  # Pipe in shell
            "&",  # Background command in shell
            "$",  # Variable in shell
            "`",  # Command substitution in shell
            "<",  # Input redirection in shell
            ">",  # Output redirection in shell
            "\0",  # Null byte
        ]

    def sanitize(self, filename: str) -> str:
        filename = filename.replace("..", "")
        filename = filename.replace("/", "_").replace("\\", "_")

        for char in self.dangerous_chars:
            filename = filename.replace(char, "")

        filename = "".join(c for c in filename if c.isprintable())

        if len(filename) > self.max_length:
            if "." in filename:
                name, ext = filename.rsplit(".", 1)
                available = self.max_length - len(ext) - 1
                filename = name[:available] + "." + ext
            else:
                filename = filename[: self.max_length]

        return filename

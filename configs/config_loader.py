import yaml


class ConfigLoaderException(Exception):
    """Base exception for ConfigLoader."""


class ConfigFileNotFoundError(ConfigLoaderException):
    """Raised when the configuration file is not found."""

    def __init__(self, file_path: str):
        super().__init__(f"Configuration file not found: {file_path}")
        self.file_path = file_path


class ConfigFileFormatError(ConfigLoaderException):
    """Raised when the configuration file has invalid YAML format."""

    def __init__(self, file_path: str, error: Exception):
        super().__init__(f"Invalid YAML format in file {file_path}: {error}")
        self.file_path = file_path
        self.error = error


class ConfigLoader:
    """
    A utility class to load and parse YAML configuration files.

    This class provides a static method to load YAML files and ensures
    proper error handling for missing files and invalid formats.
    """

    @staticmethod
    def load_config(file_path: str) -> dict:
        """
        Loads a YAML configuration file.

        :param file_path: Path to the YAML file.
        :return: Configuration as a dictionary.
        :raises ConfigFileNotFoundError: If the file does not exist.
        :raises ConfigFileFormatError: If the YAML format is invalid.
        """
        try:
            with open(file_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise ConfigFileNotFoundError(file_path)
        except yaml.YAMLError as e:
            raise ConfigFileFormatError(file_path, e)
        except Exception as e:
            raise ConfigLoaderException(
                f"Unexpected error loading configuration file {file_path}: {e}"
            )

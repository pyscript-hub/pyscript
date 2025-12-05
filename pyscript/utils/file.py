import json
from pathlib import Path


def get_text(path: Path) -> str:
    """
    Return the content of a file given a path.

    Arguments:
        path: Path to the file.

    Returns:
        str: Content of the file.
    """

    return Path(path).read_text()


def get_json(path: Path) -> dict:
    """
    Return a dictionary of the content of a json file.

    Arguments:
        path: Path to the json file

    Returns:
        dict: Content of the json file

    Raises:
        JSONDecodeError: If the content is malformed.
    """

    return json.loads(get_text(path))


def copy(source_path: Path, destination_path: Path) -> None:
    """
    Copy a file from source_path to destination_path.

    Arguments:
        source_path: Path to the source file
        destination_path: Path to the destination file
    """

    destination_path.write_text(get_text(source_path))
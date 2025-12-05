import json

import requests


# pyscript-hub repository base url
REPO_BASE_URL = "https://raw.githubusercontent.com/pyscript-hub/pyscript-hub/main"


def load_script_metadata(script_name: str) -> dict:
    """
    Load a script metadata from the official repository.

    Arguments:
        script_name: the name of the script to load metadata from

    Returns:
        a dictionary of the script metadata

    Raises:
        FileNotFoundError: if the file on the repository was not found
    """

    metadata_path = f"metadata/{script_name}.json"
    content = _fetch_from_repo(metadata_path)
    return json.loads(content)


def load_script_file(script_name: str) -> str:
    """
    Load a script file from the official repository.

    Arguments:
        script_name: the name of the script to load

    Returns:
        the content of the script file

    Raises:
        FileNotFoundError: if the file on the repository was not found
    """

    script_path = f"scripts/{script_name}.py"
    content = _fetch_from_repo(script_path)
    return content


def load_categories() -> dict:
    """
    Load categories from the official repository.

    Returns:
        A dictionary of the categories with a list of the relative scripts.

    Raises:
        FileNotFoundError: if the file on the repository was not found.
    """

    categories_path = "categories.json"
    content = _fetch_from_repo(categories_path)
    return json.loads(content)


# Helpers

def _fetch_from_repo(path: str) -> str:
    """
    Download a file from the official repository on GitHub.

    Arguments:
        path: the path of the file to download

    Returns:
        The content of the file

    Raises:
        FileNotFoundError: if the file on the repository was not found
    """

    url = f"{REPO_BASE_URL}/{path}"
    response = requests.get(url)
    if response.status_code != 200:
        raise FileNotFoundError(f"File on GitHub not found: {url}")
    return response.text
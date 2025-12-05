import json
from pathlib import Path
from typing import Any, Optional

from pyscript.core.manager import METADATA_DIR
from pyscript.core.script_manager import extract_description, extract_dependencies
from pyscript.utils import file

REQUIRED_FIELDS = [
    ("dependencies", []),
    ("type", "custom")
]


def generate(script_name: str,
             description: str,
             dependencies: list[tuple[str, str]]
             ) -> dict:
    """
    Generate the metadata dictionary of a script from value passed.

    Arguments:
        script_name: name of the script
        description: description of the script
        dependencies: list of tuples of module name and module description

    Returns:
        metadata: a dictionary of the metadata

    Raises:
        ValueError: if the dependencies has a wrong format
    """

    if not _has_dependencies_structure(dependencies):
        raise ValueError("invalid dependencies format. "
                         "Please check they are a list of tuples of module name and module version.")

    metadata: dict = {
        "name": script_name,
        "description": description,
        "dependencies": dependencies
    }

    return metadata


def extract(script_path: Path) -> dict:
    """
    Extract the metadata from a script.
    Features:
    - name
    - external dependencies (only top-level, without standard modules)

    Arguments:
        script_path: path to the script

    Returns:
        a dictionary of the metadata
    """

    script_name = script_path.stem
    description = extract_description(script_path)
    dependencies = extract_dependencies(script_path)

    metadata = {
        "name": script_name,
        "description": description,
        "dependencies": dependencies,
    }

    return metadata


def save(script_name: str, metadata: dict, overwrite: bool = False) -> None:
    """
    Save the metadata of a script.

    Arguments:
        script_name: name of the script
        metadata: metadata to save
        overwrite: whether to overwrite existing metadata (default: False)

    Raises:
        FileExistsError: if the metadata file for the given name already exists
    """

    METADATA_DIR.mkdir(exist_ok=True)
    metadata_file = _get_path(script_name)

    if metadata_file.exists() and not overwrite:
        raise FileExistsError(script_name)

    metadata_file.touch()
    metadata_file.write_text(json.dumps(metadata, indent=4))


def delete(script_name: str) -> None:
    """
    Remove the metadata of a script.

    Arguments:
        script_name: name of the script

    Raises:
        FileNotFoundError: if the metadata file for the given name doesn't exist
    """

    metadata_file = _get_path(script_name)
    if metadata_file.exists():
        metadata_file.unlink()
    else:
        raise FileNotFoundError(f"Metadata file for {script_name} doesn't exist.")


def update(script_name: str, new_values: dict[str, Any]) -> None:
    """
    Update the metadata of a script giving new values.

    Arguments:
        script_name: name of the script.
        new_values: dictionary of new values to update.

    Raises:
        FileExistsError: if the metadata file for the given name doesn't exist.
    """

    old_metadata = get(script_name)

    for key, value in new_values.items():
        old_metadata[key] = value

    save(script_name, old_metadata, overwrite=True)


def get(script_name: str) -> dict:
    """
    Get the metadata dictionary from a metadata file.

    Arguments:
        script_name: name of the script for which get the metadata

    Returns:
        a dictionary of the metadata

    Raises:
        FileNotFoundError: if the metadata file for the given name doesn't exist
    """

    metadata_file = _get_path(script_name)

    if not metadata_file.exists():
        raise FileNotFoundError(f"metadata file for {script_name} doesn't exist.")

    return file.get_json(metadata_file)


def get_from_path(path: Path) -> dict:
    """
    Get the metadata dictionary from a metadata file.

    Arguments:
        path: path of the metadata file

    Returns:
        a dictionary of the metadata
    """

    if not path.exists():
        raise FileNotFoundError(f"metadata file {path} doesn't exist.")

    return file.get_json(path)


def complete(metadata: dict[str, Any], required_fields: Optional[list[tuple[str, Any]]]=None) -> None:
    """
    Complete the metadata of a script with required fields.

    Arguments:
        metadata: a dictionary of the current metadata
        required_fields: a list of required fields in the form (name, default_value). Leave None to use the default list.

    Returns:
        The metadata completed with the missing fields
    """

    if required_fields is None:
        required_fields = REQUIRED_FIELDS

    for field, value in required_fields:
        if metadata.get(field, None) is None:
            metadata[field] = value


# Helpers

def _get_path(script_name: str) -> Path:
    """
    Get the metadata file path of a script from its name.

    Arguments:
        script_name: name of the script

    Returns:
        The Path to the metadata file
    """

    path = METADATA_DIR / f"{script_name}.json"
    return path


def _has_dependencies_structure(dependencies: list[tuple[str, str]]) -> bool:
    """
    Check if the dependencies has a wrong format. They must be a list of tuples of module name and module version (both strings).

    Arguments:
        dependencies: list of tuples of module name and module version

    Returns:
        A boolean indicating if the dependencies has a correct format or not
    """

    if not isinstance(dependencies, list):
        return False
    for module in dependencies:
        if not isinstance(module, tuple):
            return False
        if len(module) != 2:
            return False
        if not (isinstance(module[0], str) and isinstance(module[1], str)):
            return False
    return True

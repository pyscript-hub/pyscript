from pathlib import Path
from typing import Optional, Any

import pyscript.core.metadata_manager as metadata_manager
from pyscript.core import script_manager
from pyscript.utils import file
from pyscript.utils.console import Console
from pyscript.utils.parser import parse_script_name


def add_script(
    script_path: Path,
    metadata_path: Optional[Path] = None,
    description: Optional[str] = None,
    dependencies: Optional[str] = None,
) -> None:
    """
    Add a new script.

    Arguments:
        script_path: path to the script
        metadata_path: path to the metadata
        description: description of the script
        dependencies: list of dependencies of the script, as tuples of values (name, version)
    """

    # Check the script file exists
    if not script_path.exists():
        Console.print_error(f"'{script_path}' does not exist", "Please provide a valid script path.")
        return

    # Check the script is a Python file
    if not script_path.suffix == '.py':
        Console.print_error(f"'{script_path}' is not a Python file",
                            "Be sure the path provided is of a Python file.")
        return

    # Parse dependencies
    parsed_deps = []
    if dependencies:
        dependencies = dependencies.split()
        for dep in dependencies:
            if "=" in dep:
                pkg, ver = dep.split("=", 1)
            else:
                pkg, ver = dep, ""
            parsed_deps.append((pkg, ver))

    script_name = parse_script_name(script_path.stem)

    # Check if the script already exists
    if script_manager.exists(script_name):
        Console.print_error(f"script '{script_name}' already exists",
                            f"It was already added or it has the same name of a script already present.")
        return

    # Generate metadata from arguments or script docs
    try:
        metadata = _get_metadata_from_args(script_path, metadata_path, description, parsed_deps)
    except FileNotFoundError:
        Console.print_error("metadata file not found", "Be sure to provide a valid file path.")
        return
    except ValueError:
        Console.print_error("invalid dependencies format", "Be sure to provide a file with a valid JSON format.")
        return

    # Save metadata
    try:
        metadata_manager.save(script_name, metadata)
    except FileExistsError:
        Console.print_error(f"metadata file for {script_name} already exists",
                            "If it should not exists, use the [bold green]clean[/bold green] command and try again.")
        return

    # Save script
    script = file.get_text(script_path)
    script_manager.save(script_name, script)
    Console.print_success(f"Script [bold]{script_path.name}[/] added successfully.")


def _get_metadata_from_args(
        script_path: Path,
        metadata_path: Optional[Path] = None,
        description: Optional[str] = None,
        dependencies: Optional[list[tuple[str, str]]] = None
    ) -> dict[str, Any]:
    """
    Return the metadata handling command inputs or retrieving them from the script.

    Arguments:
        script_path: path to the script
        metadata_path: path to the metadata
        description: description of the script
        dependencies: list of dependencies

    Returns:
        A dictionary of the metadata

    Raises:
        FileNotFoundError: if the metadata file does not exist
        ValueError: if the dependencies have a wrong format
    """

    script_name = parse_script_name(script_path.stem)

    # If the metadata file is provided and exists return its content
    if metadata_path:
        try:
            return metadata_manager.get_from_path(metadata_path)
        except FileNotFoundError as e:
            raise e

    # Try to extract the description from the main method docs if not provided
    if not description:
        description = script_manager.extract_description(script_path)
        if not description:
            Console.print_warning("no description passed and found in the script",
                          "Provide it as a docstring for the main method of the script or with the option "
                          "[bold cyan]--description[/bold cyan] to show it in the [bold green]list[/bold green] command.")

    # Extract dependencies if not provided
    if dependencies is None:
        dependencies = metadata_manager.extract_dependencies(script_path)
    return metadata_manager.generate(script_name, description, dependencies)
from typing import Optional

from pyscript.core import script_manager, metadata_manager
from pyscript.core.venv_manager import delete, delete_dependencies
from pyscript.utils.console import Console


def remove_script(script_name: str, metadata: bool = False, venv: bool = False, deps_to_remove: Optional[str] = None):
    """
    Remove:
    - a script with the metadata file and the virtual environment
    - the metadata file
    - the virtual environment
    - specific dependencies

    Arguments:
        script_name: name of the script to remove.
        metadata: if the metadata file should be removed or not.
        venv: if the virtual environment should be removed or not.
        deps_to_remove: a list of dependencies to remove.
    """

    if venv and deps_to_remove:
        Console.print_error("invalid arguments. [bold cyan]--dependencies[/] is redundant with [bold cyan]--venv[/]")
        return

    if not script_manager.exists(script_name):
        Console.print_error(f"script '{script_name}' not found")
        return

    to_do: dict[str, bool] = _handle_args(metadata, venv, deps_to_remove)

    if not _user_confirm(script_name, to_do["metadata"], to_do["script"]):
        Console.print("Operation cancelled.")
        return

    if to_do["metadata"]:
        Console.print(f"🔧 Deleting metadata file for [bold]{script_name}[/bold]...")
        try:
            metadata_manager.delete(script_name)
            Console.print_success(f"Metadata for {script_name} deleted.")
        except FileNotFoundError:
            Console.print_warning(f"no metadata file for [bold]{script_name}[/bold] found")

    if to_do["venv"]:
        try:
            delete(script_name)
            Console.print_success(f"Virtual environment for {script_name} deleted.")
        except FileNotFoundError:
            Console.print_warning(f"no virtual environment for [bold]{script_name}[/bold] found")

    if to_do["dependencies"]:
        deps = _parse_deps(deps_to_remove)
        Console.print(f"🔧 Uninstalling dependencies {', '.join([f'[bold]{d}[/]' for d in deps])} "
                      f"for [bold]{script_name}[/bold]...")
        delete_dependencies(script_name, deps)
        Console.print_success(f"Dependencies for [bold]{script_name}[/bold] uninstalled.")

    if to_do["script"]:
        Console.print(f"🔧 Deleting script file [bold]{script_name}[/bold]...")
        script_manager.delete(script_name)
        Console.print_success(f"Script '{script_name}' deleted.")


def _handle_args(metadata: bool = False, venv: bool = False, deps_to_remove: Optional[list[str]] = None) -> dict[str, bool]:
    """
    Handle command arguments, deciding what action will be taken.

    Arguments:
        metadata: `metadata` argument.
        venv: `venv` argument.
        deps_to_remove: `deps_to_remove` argument.

    Returns:
        A dictionary of actions to be performed or not.
    """

    to_do: dict[str, bool] = {
        "script": False,
        "metadata": False,
        "venv": False,
        "dependencies": False,
    }
    if metadata:
        to_do["metadata"] = True
    if venv:
        to_do["venv"] = True
    if deps_to_remove:
        to_do["dependencies"] = True
    if not metadata and not venv and not deps_to_remove:
        to_do["script"] = True
        to_do["metadata"] = True
        to_do["venv"] = True
    return to_do


def _parse_deps(deps_string: str) -> list[str]:
    return deps_string.split(" ")


def _user_confirm(script_name: str, metadata: bool = False, script: bool = False) -> bool:
    """
    Helper function for user confirmation (for script deletion or metadata deletion).

    Arguments:
        script_name: name of the script to remove.
        metadata: if the metadata file needs to be removed.
        script: if the script should be removed.

    Returns:
        A boolean indicating whether user confirmation or not.
    """

    if metadata and not script:
        return Console.confirm_action(f"Do you want to remove the metadata for the script [bold]{script_name}[/]?")
    if script:
        return Console.confirm_action(f"Do you want to remove the script [bold]{script_name}[/]?")
    return True

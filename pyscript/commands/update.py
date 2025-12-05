from pathlib import Path
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

import pyscript.core.metadata_manager as metadata_manager
from pyscript.core import script_manager
from pyscript.core.script_manager import get_available_scripts
from pyscript.utils import file
from pyscript.utils.console import Console, console

import pyscript.utils.github as github


def update_script(
        script_name: Optional[str],
        script_path: Optional[str],
        metadata_path: Optional[str],
        update_all: bool,
):
    """
    This function handle the update of a script.
    Cases:
    - replace the script with a new one giving the path
    - replace the script metadata with a new one giving the path
    - replacing the script and its metadata giving both paths
    - download the latest version of a standard script
    - download the latest version of all standard scripts

    Arguments:
        script_name: The name of the script to be updated.
        script_path: The path of the script to be updated.
        metadata_path: The path of the metadata to be updated.
        update_all: If True, update all scripts.
    """

    # Check arguments validity
    if not (script_name or script_path or metadata_path or update_all):
        Console.print_error("empty command", "A script name or the [cyan]--all[/] option is required.")
        return

    if update_all and (script_name or script_path or metadata_path):
        Console.print_error("invalid arguments. [cyan]--all[/cyan] must be used alone (e.g. [bold green]pyscript[/] [bold cyan]--all[/])")
        return

    to_do: dict[str, bool] = _handle_args(script_name, script_path, metadata_path, update_all)

    # Perform actions
    if to_do["all"]:
        update_all_scripts()
        return

    if not script_manager.exists(script_name):
        Console.print_error(f"script '{script_name}' not found")
        return

    if to_do["standard"]:
        update_standard(script_name)
        return

    if to_do["metadata"]:
        update_metadata(script_name, metadata_path)

    if to_do["script"]:
        update_single(script_name, script_path, not to_do["metadata"])


def _handle_args(
        script_name: Optional[str],
        script_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
        update_all: bool = False) -> dict[str, bool]:
    """
    Handle command arguments, deciding what action will be taken.

    Arguments:
        script_name: `script_name` argument.
        script_path: `script_path` argument.
        metadata_path: `metadata_path` argument.
        update_all: `update_all` argument.

    Returns:
        A dictionary of actions to be performed or not.
    """

    to_do: dict[str, bool] = {
        "standard": False,
        "script": False,
        "metadata": False,
        "all": False,
    }

    if update_all:
        to_do["all"] = True
        return to_do
    if script_path:
        to_do["script"] = True
    if metadata_path:
        to_do["metadata"] = True
    if script_name and (not script_path and not metadata_path):
        to_do["standard"] = True
    return to_do


def update_all_scripts() -> None:
    """
    Update all standard scripts, checking which ones are obsolete
    and updating them to the last version available on the official repository.
    """

    Console.print("🔧 Upgrading all scripts...")
    standard = _get_default_scripts()

    # Create a progress view for an optimal visualization of the processo for the user
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
            transient=True
    ) as progress:

        task_id = progress.add_task("Updating...", total=len(standard))

        # Iterate for each standard script
        for script, version in standard.items():
            progress.update(task_id, description=f"Checking [bold]{script}[/] version...")

            # Load metadata from the official repository (handling missing metadata)
            try:
                repo_metadata = github.load_script_metadata(script)
            except FileNotFoundError:
                Console.print(f"   [bold yellow]⚠[/] Failed to load metadata for script '{script}'. "
                              f"Metadata not present on the official repository (skipped).")
                progress.advance(task_id)
                continue

            # Get repo script version (handling invalid metadata)
            try:
                repo_version = float(repo_metadata["version"])
            except ValueError:
                Console.print_error(f"   [bold yellow]⚠[/] Invalid metadata on the repository for [bold]{script}[/] (skipped).")
                progress.advance(task_id)
                continue

            # Check if the script is up-to-date
            if repo_version == float(version):
                Console.print_success(f"[bold]{script}[/] is up-to-date.")
                progress.advance(task_id)
                continue

            progress.update(task_id, description=f"Updating [bold]{script}[/]...")

            # Download the script file from the official repository
            try:
                content = github.load_script_file(script)
            except FileNotFoundError:
                Console.print(f"   [bold yellow]⚠[/] Script '{script}' not found on the official repository (skipped).")
                progress.advance(task_id)
                continue

            # Save the new script and its metadata
            script_manager.save(script, content)
            metadata_manager.save(script, repo_metadata, True)
            Console.print(f"   [green]✔[/] [bold]{script}[/] is now up-to-date.")

            progress.advance(task_id)

    Console.print_success("All scripts are up-to-date.")


def update_standard(script: str) -> None:
    """
    Update a specific standard script to the latest version available on the official repository.

    Arguments:
        script: name of the script to be updated.
    """

    Console.print(f"🔧 Updating [bold]{script}[/]...")

    # Load script metadata from the repository
    try:
        repo_metadata = github.load_script_metadata(script)
    except FileNotFoundError:
        Console.print_error(f"script '{script}' not found on the official repository.")
        return

    # Check if the script passed is standard
    is_standard = True
    metadata = metadata_manager.get(script)
    if "type" not in metadata.keys() or metadata["type"] != "standard":
        Console.print_warning(f"local [bold]{script}[/] is not a standard script")
        if not Console.confirm_action("Do you want to replace it with the latest version from the official repository?"):
            Console.print("Operation cancelled.")
            return
        is_standard = False

    if is_standard:
        # Get local script version
        try:
            version = float(metadata["version"])
        except KeyError:
            Console.print_warning(f"no version specified for [bold]{script}[/] in the metadata.", "Downloading the latest version...")
            version = 0
        except ValueError:
            Console.print_warning("version specified in the is invalid.")
            return

        # Get repo script version (handling invalid metadata)
        try:
            repo_version = float(repo_metadata["version"])
        except ValueError:
            Console.print_error(f"invalid metadata on the repository for [bold]{script}[/].")
            return

        # Check if the script is up-to-date
        if repo_version == version:
            Console.print_success(f"[bold]{script}[/] is up-to-date.")
            return

    # Download the script file from the official repository
    try:
        content = github.load_script_file(script)
    except FileNotFoundError:
        Console.print_error(f"script '{script}' not found on the official repository.")
        return

    # Save the new script and its metadata
    script_manager.save(script, content)
    metadata_manager.save(script, repo_metadata, True)
    Console.print_success(f"[bold]{script}[/] is now up-to-date.")


def update_metadata(script: str, metadata_path: str) -> None:
    """
    Update the metadata file of a custom script giving the new one.

    Arguments:
        script: name of the script whose metadata file needs to be updated.
        metadata_path: path to the metadata file which will replace the old metadata.
    """

    Console.print(f"🔧 Updating [bold]{script}[/] metadata...")

    try:
        metadata_manager.get(script)
    except FileNotFoundError:
        Console.print_warning(f"no old metadata present for '{script}'")

    # Extracting and saving metadata
    metadata = file.get_json(Path(metadata_path))
    metadata_manager.save(script, metadata, True)

    Console.print_success(f"[bold]{script}[/] metadata updated.")


def update_single(script: str, script_path: str, update_metadata: bool = False) -> None:
    """
    Update a custom user script, giving the new one.

    Arguments:
        script: name of the script to update.
        script_path: path to the script file which will replace the old one.
    """

    Console.print(f"🔧 Updating [bold]{script}[/]...")

    # Extracting and saving script
    content = file.get_text(Path(script_path))
    script_manager.save(script, content)

    # Updating the metadata
    if update_metadata:
        _update_single_metadata(script, script_path)
    
    Console.print_success(f"[bold]{script}[/] updated.")


def _update_single_metadata(script: str, script_path: str) -> None:
    """
    Update the metadata file of a custom script to match the latest version.

    Arguments:
        script: name of the script to update.
    """

    Console.print(f"🔧 Updating metadata for [bold]{script}[/] to match the latest version...")
    dependencies = script_manager.extract_dependencies(Path(script_path))
    new_values = {"dependencies": dependencies}
    metadata_manager.update(script, new_values)


def _get_default_scripts() -> dict[str, float]:
    """
    Return the default scripts and their current versions.
    """

    scripts = get_available_scripts()
    standard = {}

    for script in scripts:
        metadata = metadata_manager.get(script)
        if "type" not in metadata.keys():
            continue
        if metadata["type"] == "standard":
            try:
                version = float(metadata["version"])
            except KeyError:
                Console.print_warning(f"standard script [bold]{script}[/] has no version saved in the metadata",
                                      "The latest available on the official repository will be downloaded.")
                version = 0.0
            except ValueError:
                Console.print_warning(f"invalid version saved in the metadata for [bold]{script}[/]",
                                      "The latest available on the official repository will be downloaded.")
                version = 0.0
            standard[script] = version

    return standard
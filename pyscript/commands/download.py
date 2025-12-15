from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

import pyscript.core.metadata_manager as metadata_manager
import pyscript.utils.github as github
from pyscript.core import script_manager
from pyscript.utils.console import Console, console


def download_scripts(scripts: Optional[list[str]], category: Optional[str] = None) -> None:
    """
    Download one or more scripts or all scripts from a category from the official repository on GitHub.

    Arguments:
        scripts: List of scripts to download.
        category: Category to download scripts from.
    """

    if not scripts and not category:
        Console.print_error("no argument provided", "Specify at least a script or a category.")
        return

    if scripts and category:
        Console.print_error("invalid arguments", "To specify a category use the [bold cyan]--category[/] option only.")
        return

    if category:
        download_category(category)
        return

    download_multiple_scripts(scripts)


def download_category(category: str) -> None:
    """
    Download all scripts available on a category.

    Arguments:
        category: Category to download scripts from.
    """

    Console.print("🔧 Checking category from the repository...")

    # Loading categories json file from the repository
    try:
        categories = github.load_categories()
    except FileNotFoundError:
        Console.print_error("unable to load categories from the official repository",
                            "This is due to an error in the official repository. Please try again. "
                            "If the error persist open an issue on GitHub.")
        return

    if category not in categories:
        Console.print_error(f"category [bold]{category}[/] not found", "Please specify a valid category.")
        return

    # Extract the scripts name belonging to the required category
    scripts = categories[category]

    # Show scripts available and ask user confirmation
    Console.print(f"The following scripts were found in [bold]{category}[/]:\n - [bold magenta]" + "[/]\n - [bold magenta]".join(
        scripts) + "[/]")
    if not Console.confirm_action("Do you want to download them?"):
        Console.print("Operation cancelled.")
        return

    download_multiple_scripts(scripts)


def download_multiple_scripts(scripts: list[str]) -> None:
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
            transient=True
    ) as progress:
        task_id = progress.add_task(f"Starting...", total=len(scripts))

        for script_name in scripts:
            progress.update(task_id, description=f"[cyan]Downloading[/] [bold]{script_name}[/][cyan]...[/]")

            # Check if the script is already downloaded
            if script_manager.exists(script_name):

                # If the existing script is a custom script, ask the user to overwrite
                if not _is_custom_with_standard_name(script_name):
                    Console.print_warning(f"[bold]{script_name}[/bold] already installed")
                    progress.advance(task_id)
                    continue

                Console.print_warning(f"[bold]{script_name}[/] already exists as a custom script", "Delete it if you want to download the standard one.")
                continue

            # Download the metadata
            try:
                metadata = github.load_script_metadata(script_name)
                metadata_manager.save(script_name, metadata)

            except FileExistsError:
                Console.print_warning(f"metadata for [bold]{script_name}[/bold] already exists")
                Console.print(f"️🔧 Removing old metadata file...")

                metadata_manager.delete(script_name)
                metadata_manager.save(script_name, metadata)
                pass
            except FileNotFoundError:
                Console.print_error(f"[bold]{script_name}[/bold] not found on the official repository",
                                    "Use the option [bold cyan]--list[/] to list all available scripts.")
                progress.advance(task_id)
                continue

            # Download the script
            try:
                script_code = github.load_script_file(script_name)
                script_manager.save(script_name, script_code)
                Console.print_success(f"{script_name} installed successfully.")
            except FileNotFoundError as e:
                Console.print_error(f"unable to download [bold]{script_name}[/bold]", str(e))

                # Rollback metadata
                try:
                    metadata_manager.delete(script_name)
                except FileNotFoundError:
                    Console.print_error(f"failed to remove metadata for [bold]{script_name}[/bold] during rollback")
                    return
            finally:
                progress.advance(task_id)


def _is_custom_with_standard_name(script_name: str) -> bool:
    """
    Check if a script is defined as custom (supposed it exists and should be a standard script).
    If no type is present, it's supposed to be a custom script.

    Arguments:
        script_name: Name of the script.

    Returns:
        A boolean indicating if the script is defined "custom".
    """

    metadata = metadata_manager.get(script_name)
    try:
        return metadata["type"] == "custom"
    except KeyError:
        return True
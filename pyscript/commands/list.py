from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from pyscript.core.manager import SCRIPTS_DIR
from pyscript.core.script_manager import extract_description
from pyscript.utils.console import Console

import pyscript.core.metadata_manager as metadata_mng


def list_scripts():
    """
    Print a table of all available scripts.
    """

    scripts = get_available_scripts()

    if not scripts:
        Console.print_warning("no script available", "Add a new script or download one from [magenta]GitHub[/magenta].")
        return

    table = get_category_table(scripts)
    Console.print(table)


def get_table(scripts: list[dict[str, str]]) -> Panel:
    """
    Returns the table of available scripts.

    Arguments:
        scripts: a list of dictionaries describing the scripts.

    Returns:
        A Panel containing the table of available scripts.
    """

    table = Table(show_header=False, box=None)
    for script in sorted(scripts, key=lambda item: item["name"]):
        name, desc = script["name"], script["description"]
        table.add_row(f"[cyan]{name}[/cyan]", f"{desc}")
    panel = Panel(
        table,
        title="Scripts",
        title_align="left",
        border_style="dim",
        padding=(0, 0),
    )
    return panel


def get_category_table(scripts: list[dict[str, str]]) -> Panel | Group:
    """
    Returns the table of available scripts, divided by category.

    Arguments:
        scripts: a list of dictionaries describing the scripts. Each script
                 must include: "name", "description", and "category".

    Returns:
        A Panel containing sub-panels, one for each category.
    """

    # Global order for category and name
    scripts_sorted = sorted(scripts, key=lambda s: (s["category"], s["name"]))

    # Category order: custom first, then alphabetical
    categories = sorted({s["category"] for s in scripts_sorted if s["category"] != "custom"})

    # If there is no standard script, treat custom scripts as only scripts
    if not categories:
        return get_table(scripts)

    # Add custom category if there are custom scripts
    if any(s["category"] == "custom" for s in scripts_sorted):
        categories = ["custom"] + categories

    category_panels = []
    max_name_length = max(len(s["name"]) for s in scripts_sorted)

    # Create a panel for each category
    for category in categories:
        group = [s for s in scripts_sorted if s["category"] == category]
        if not group:
            continue

        # Category scripts table
        table = Table(show_header=False, box=None, expand=True)

        table.add_column(
            "",  # prima colonna: nome script
            width=max_name_length + 4,  # padding extra per non stare strettissimo
            no_wrap=True
        )

        table.add_column(
            "",  # seconda colonna: descrizione
            overflow="fold",
            ratio=1
        )

        for script in group:
            table.add_row(
                f"[cyan]{script['name']}[/cyan]",
                script["description"]
            )

        # Custom style for custom
        if category == "custom":
            title = "[bold magenta]User Scripts[/bold magenta]"
            border = "magenta"
        else:
            title = f"[bold yellow]{category.title()}[/bold yellow]"
            border = "bold bright_black"

        # Panel for each category
        panel = Panel(
            table,
            title=title,
            title_align="left",
            border_style=border,
            padding=(0, 1),
        )

        category_panels.append(panel)

    return Group(*category_panels)


def get_available_scripts() -> list[dict[str, str]]:
    """
    Returns a list of all scripts available.

    Returns:
        A list of dictionaries containing the script name and its description (if one can be retrieved)
    """

    return [
        {
            "name": f.stem, #.replace("-", " "),
            "description": get_description(f),
            "category": get_category(f),
        }
        for f in SCRIPTS_DIR.glob("*.py") if f.name != "__init__.py"
    ]


def get_description(script_path: Path) -> str:
    """
    Get the script description. It is retrieved from the metadata file if exists, otherwise from the main method docstring.

    Arguments:
        script_path: path to the script

    Returns:
        The script description if found, blank otherwise
    """

    try:
        metadata = metadata_mng.get(script_path.stem)
        return metadata["description"]
    except FileNotFoundError:
        pass
    except KeyError:
        pass

    # If the metadata file was not found or the description was not found in the metadata file,
    # it will be retrieved from the script main method docstring
    desc = extract_description(script_path)
    return desc if desc else ""


def get_category(script_path: Path) -> str:
    """
    Get the script category. It is retrieved from the metadata file if exists, otherwise it is assumed custom.

    Arguments:
        script_path: path to the script

    Returns:
        The script category if found, "custom" otherwise
    """

    try:
        metadata = metadata_mng.get(script_path.stem)
        return metadata["category"]
    except FileNotFoundError:
        pass
    except KeyError:
        pass

    return "custom"
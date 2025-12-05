import importlib
from pathlib import Path
from typing import Optional, List, Annotated

import typer

from pyscript.commands.add import add_script
from pyscript.commands.clean import clean_environment
from pyscript.commands.download import download_scripts
from pyscript.commands.list import list_scripts
from pyscript.commands.remove import remove_script
from pyscript.commands.run import run_script
from pyscript.commands.update import update_script
from pyscript.core.manager import init
from pyscript.utils.console import Console


app = typer.Typer(
    help="🐍 pyscript — Simple modular Python script runner",
    callback=init
)


def version_callback(value: bool):
    if value:
        v = importlib.metadata.version("pyscript")
        print(f"pyscript {v}")
        raise typer.Exit()


@app.callback()
def main(
        version: Annotated[
            Optional[bool],
            typer.Option(
                "--version", "-V",
                help="Show the Pyscript version and exit.",
                callback=version_callback
            )
        ] = None
):
    pass


@app.command("list")
def list_commands():
    """
    List all available commands.
    """

    list_scripts()
    Console.print()


@app.command()
def run(
        script_name: str = typer.Argument(..., help="Script name"),
        args: str = typer.Argument(None, help="Optional argument for the script")
):
    """
    Execute a script.
    """

    run_script(script_name, extra_args=args)
    Console.print()


@app.command()
def add(
        script_path: Path = typer.Argument(..., help="Path to the Python script to add"),
        metadata_file: Optional[Path] = typer.Option(
            None,
            "--metadata", "-m",
            help="Metadata file JSON of the script"),
        description: Optional[str] = typer.Option(
            None,
            "--description", "-d",
            help="Script description"),
        dependencies: Optional[str] = typer.Option(
            None,
            "--dependencies", "-p",
            help="Dependencies in format pkg=version or pkg (delimit them with double quotes, e.g. \"matplotlib=1.0.0 rich\")"
        ),
):
    """
    Add a new script.
    """

    add_script(
        script_path=script_path,
        metadata_path=metadata_file,
        description=description,
        dependencies=dependencies,
    )
    Console.print()


@app.command()
def download(
        scripts: List[str] = typer.Argument(None, help="One or more script to download."),
        category: str = typer.Option(None, "--category", "-c",
                                     help="Download all script belonging to a certain category."),
):
    """
    Download scripts from the official repository.
    """

    download_scripts(scripts, category)
    Console.print()


@app.command()
def remove(
        script_name: str = typer.Argument(..., help="Script name"),
        metadata: bool = typer.Option(False, "--metadata", "-m", help="Delete the metadata file of the script."),
        venv: bool = typer.Option(False, "--venv", "-v", help="Delete the virtual environment of the script."),
        dependencies: str = typer.Option(None, "--dependencies", "-p",
                                         help="list of dependencies to remove from the venv (delimit them with double quotes)."),
):
    """
    Remove a script or a related component.
    """

    remove_script(
        script_name=script_name,
        metadata=metadata,
        venv=venv,
        deps_to_remove=dependencies if dependencies else None
    )
    Console.print()


@app.command()
def update(
        script_name: Optional[str] = typer.Argument(None, help="Script name"),
        new_script: Optional[str] = typer.Option(None, "--path", "-p", help="Path to the new script."),
        metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="Metadata file JSON of the script."),
        update_all: bool = typer.Option(False, "--all", "-a",
                                        help="Update all the default scripts to the latest version."),
):
    """
    Update a script and/or its metadata.
    """

    update_script(script_name, new_script, metadata, update_all)
    Console.print()


@app.command()
def clean():
    """
    Clean up temporary files and unused resources.
    """

    clean_environment()
    Console.print()


if __name__ == "__main__":
    init()
    app()

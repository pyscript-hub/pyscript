import shutil
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from pyscript.core.manager import BASE_DIR, SCRIPTS_DIR, METADATA_DIR, VENVS_DIR
from pyscript.utils.console import Console, console


def clean_environment():
    """
    Remove orphaned metadata, orphaned venvs, and __pycache__ directories.
    """

    removed_metadata = 0
    removed_venvs = 0
    removed_pycache = 0

    Console.print("🧹 Cleaning environment...")

    # Retrieving existing scripts
    existing_scripts = {p.stem for p in SCRIPTS_DIR.glob("*.py")}

    with _get_new_progress() as progress:
        task_id = progress.add_task("Cleaning...", total=None)

        # Checking for orphan metadata files
        for meta in METADATA_DIR.glob("*.json"):
            script_name = meta.stem
            if script_name not in existing_scripts:
                progress.update(task_id, description=f"[dim]Deleting[/] [bold]{script_name}[/] metadata...")
                meta.unlink()
                removed_metadata += 1
                Console.print(f"   [bold green]✔[/] Removed [bold]{script_name}[/] metadata.")
                progress.advance(task_id)

        # Checking for orphan venv directories
        if VENVS_DIR.exists():
            for venv in VENVS_DIR.iterdir():
                if venv.is_dir():
                    script_name = venv.name
                    if script_name not in existing_scripts:
                        progress.update(task_id, description=f"[dim]Deleting[/] [bold]{script_name}[/] virtual environment...")
                        shutil.rmtree(venv)
                        removed_venvs += 1
                        Console.print(f"   [bold green]✔[/] Removed [bold]{script_name}[/] virtual environment.")
                        progress.advance(task_id)

        # Cleaning pycache
        for pycache in BASE_DIR.rglob("__pycache__"):
            progress.update(task_id, description=f"[dim]Deleting[/] [bold]{Path(*list(pycache.parts)[-3:])}[/]")
            shutil.rmtree(pycache)
            removed_pycache += 1
            progress.advance(task_id)

    # Render results
    if removed_metadata == removed_venvs == removed_pycache == 0:
        Console.print("[bold green]✔[/] Environment already cleaned!")
        return

    Console.print("\n[bold green]✔[/] Environment cleaned!")

    if removed_metadata:
        Console.print(f"  - Removed {removed_metadata} orphans metadata")

    if removed_venvs:
        Console.print(f"  - Removed {removed_venvs} orphans virtual environments")

    if removed_pycache:
        Console.print(f"  - Removed {removed_pycache} __pycache__ directories")


def _get_new_progress() -> Progress:
    """
    Returns:
        A new progress object.
    """

    return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
    )
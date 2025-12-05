import importlib
import shlex
import sys
from pathlib import Path
from typing import Optional, Any

import pyscript.core.metadata_manager as metadata_manager
from pyscript.core import script_manager
from pyscript.core.script_manager import get_available_scripts
from pyscript.core.venv_manager import prepare, recreate
from pyscript.utils.console import Console
from pyscript.utils.error import VenvError


def run_script(script_name: str, extra_args: Optional[Any] = None):
    """
    Execute the specified script with the optional arguments. If needed, it creates the virtual environment installing eventual dependencies.

    Arguments:
        script_name: the name of the script to execute
        extra_args: a list of extra arguments to pass to the script
    """

    available = get_available_scripts()

    # Check script name passed exists
    if script_name not in available:
        Console.print_error(f"script [bold]{script_name}[/bold] not found",
                            "Use [bold green]list[/bold green] to see all available scripts.")
        return

    # Retrieve script metadata if exists, create them otherwise
    try:
        metadata = metadata_manager.get(script_name)
        metadata_manager.complete(metadata)
    except FileNotFoundError:
        script_path = script_manager.get_path(script_name)
        metadata = metadata_manager.extract(script_path)
        metadata_manager.save(script_name, metadata)

    # Prepare virtual environment if necessary
    try:
        env_path = prepare(script_name, metadata["dependencies"])
    except VenvError:
        Console.print_error(f"Unable to prepare the virtual environment for [bold]{script_name}[/]")
        return

    # Choose to execute the script into the virtual env or directly
    if env_path is None:
        python_exec = Path(sys.executable)

        if not python_exec.exists():
            Console.print_error(f"unable to find the system executable")
            return
    else:
        max_try = 2
        # Try for `max_try` times to recreate the virtual env in case the executable was not found
        for attempt in range(max_try):
            python_exec = env_path / ("Scripts" if sys.platform == "win32" else "bin") / "python"

            # Recreate the virtual environment in case the python executable was not found
            if python_exec.exists():
                break

            # At the last attempt return an error
            if attempt == max_try-1:
                Console.print_error(f"unable to find the executable in the virtual environment")
                return

            Console.print_warning(f"Python executable not found in the virtual environment for [bold]{script_name}[/bold]")
            env_path = recreate(script_name, metadata["dependencies"])

    if not script_manager.exists(script_name):
        Console.print_error(f"Script not found: [bold]{script_name}[/bold]")
        return

    script_path = script_manager.get_path(script_name)

    # Load the module dynamically
    try:
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        Console.print_error(f"Unable to load script [bold]{script_name}[/bold]", str(e))
        return

    # Check main() exists
    if not hasattr(module, "main"):
        Console.print_error(
            f"[bold]{script_name}[/bold] has no [i]main()[/i] function.",
            "Provide a main() entry point inside the script."
        )
        return

    # Execute main() with arguments
    try:
        args = shlex.split(extra_args) if extra_args else []

        # Make rich consider this as the start point for the error traceback print
        _rich_traceback_guard = True

        module.main(*args)
    except Exception as e:
        raise e
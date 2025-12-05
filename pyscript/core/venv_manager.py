import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

from pyscript.core.manager import VENVS_DIR
from pyscript.utils.console import Console, console
from pyscript.utils.error import VenvError, DependenceInstallationError


def prepare(script_name: str, dependencies: list[tuple[str, str]]) -> Optional[Path]:
    """
    Create a virtual environment for the script, if it not exists, and install the dependencies, if not installed or with an older version.
    In case no third party dependencies are needed, no virtual environment will be created.

    Arguments:
        script_name: name of the script for which the virtual environment should be created
        dependencies: list of (package, version) tuples representing the dependencies of the script

    Returns:
        The Path to the created virtual environment if needed, None otherwise.

    Raises:
        VenvError: If the virtual environment cannot be created properly.
    """

    # If no third party dependencies are needed no virtual environment is created
    if not dependencies:
        return None

    env_path = _ensure_env_exists(script_name)

    max_try = 1
    for attempt in range(max_try):
        try:
            _check_and_install_deps(script_name, dependencies, env_path)
            break
        except DependenceInstallationError:
            raise VenvError()
        except FileNotFoundError:
            Console.print_error("virtual environment damaged")
            if attempt == max_try:
                raise VenvError()
            recreate(script_name, dependencies)
    return env_path


def recreate(script_name: str, dependencies: list[tuple[str, str]]) -> Optional[Path]:
    """
    Recreate a virtual environment. Remove the ild virtual environment and create a new one.

    Arguments:
        script_name: script name
        dependencies: Python script dependencies
    """

    Console.print(f"🔧 Removing virtual environment for [bold]{script_name}[/bold]...")
    env_path = _get_env_path(script_name)
    _remove_venv(env_path)
    return prepare(script_name, dependencies)


def delete(script_name: str) -> None:
    """
    Remove a virtual environment.

    Arguments:
        script_name: name of the script whose virtual environment needs to be removed.

    Raises:
        FileNotFoundError: If the virtual environment does not exist.
    """

    path = _get_env_path(script_name)
    if not path.exists():
        raise FileNotFoundError()

    Console.print(f"🔧 Removing virtual environment for [bold]{script_name}[/bold]...")
    _remove_venv(path)


def delete_dependencies(script_name: str, dependencies: list[str]) -> bool:
    """
    Uninstall specific dependencies in a dedicated virtual environment.

    Arguments:
        script_name: The name of the script for which dependencies should be uninstalled.
        dependencies: The list of dependencies to uninstall.

    Returns:
        A boolean indicating if the dependencies were uninstalled.
    """

    env_path = _get_env_path(script_name)
    pip_path = _ensure_pip(env_path)

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
            transient=True
    ) as progress:

        task_id = progress.add_task("Starting...", total=len(dependencies))

        for dep in dependencies:
            progress.update(task_id, description=f"[dim]Uninstalling[/] [bold cyan]{dep}[/]...")

            # Check if the dependency is installed
            if not _check_installed_dependence_version(env_path, dep):
                Console.print(f"   [bold yellow]⚠[/] Dependency [bold]{dep}[/] not installed (skipped).")
                continue

            # Uninstall the dependency
            try:
                subprocess.run(
                    [str(pip_path), "uninstall", "-y", dep],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                Console.print(f"   [green]✔[/] Uninstalled [bold]{dep}[/]")
            except subprocess.CalledProcessError as e:
                Console.print(Panel(
                    f"Error uninstalling {dep}:\n{e.stderr.strip()}",
                    title="[red]Uninstallation Failed[/]",
                    border_style="red"
                ))
                raise DependenceInstallationError()

            progress.advance(task_id)
    return True


# Helpers

def _get_env_path(script_name: str) -> Path:
    """
    Returns the script's virtual environment.
    """

    return VENVS_DIR / script_name


def _ensure_env_exists(script_name: str) -> Path:
    """
    Creates a virtual environment for the script, if it not exists.
    """

    env_path = _get_env_path(script_name)
    if not env_path.exists():
        Console.print(f"🔧 Creating virtual environment for [bold]{script_name}[/bold]...")
        subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True)
    return env_path


def _install_dependencies(pip_path: Path, dependencies: list[tuple[str, str]]):
    """
    Install dependencies in a dedicated virtual environment.

    Arguments:
        pip_path: Path to the pip executable.
        dependencies: The dependencies to install.

    Raises:
        InstallationError: If a dependency cannot be installed.
    """

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
            transient=True
    ) as progress:

        task_id = progress.add_task("Starting...", total=len(dependencies))

        for pkg, ver in dependencies:
            package = f"{pkg}=={ver}" if ver else pkg
            progress.update(task_id, description=f"[dim]Installing[/] [bold cyan]{pkg}[/]...")
            try:
                subprocess.run(
                    [str(pip_path), "install", package],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                Console.print(f"   [green]✔[/] Installed [bold]{package}[/]")
            except subprocess.CalledProcessError as e:
                Console.print(Panel(
                    f"Error installing {package}:\n{e.stderr.strip()}",
                    title="[red]Installation Failed[/]",
                    border_style="red"
                ))
                raise DependenceInstallationError()
            progress.advance(task_id)
    return True


def _ensure_pip(env_path: Path) -> Optional[Path]:
    """
    Returns the pip executable if it exists.

    Arguments:
        env_path: Path to the virtual environment.

    Returns:
        The pip executable path or None.
    """

    pip_path = env_path / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    return pip_path if pip_path.exists() else None


def _check_and_install_deps(script_name: str, dependencies: list[tuple[str, str]], env_path: Path):
    """
    Checks if the dependencies are already installed and if not installs them.

    Arguments:
        script_name: Name of the script.
        dependencies: The dependencies to install.
        env_path: Path to the virtual environment.

    Raises:
        FileNotFoundError: If the pip executable was not found.
        DependenceInstallationError: If a dependency cannot be installed.
    """

    pkg_to_ins = []
    pkg_to_upd = []

    for pkg, ver in dependencies:
        installed_version = _check_installed_dependence_version(env_path, pkg)

        if not installed_version:
            package_spec = (pkg, ver) if ver else (pkg, "")
            pkg_to_ins.append(package_spec)
            continue

        if installed_version != ver and ver:
            package_spec = (pkg, ver) if ver else (pkg, "")
            pkg_to_upd.append(package_spec)

    # Ensure pip executable exists
    pip_path = _ensure_pip(env_path)
    if not pip_path:
        raise FileNotFoundError()

    # Install missing dependencies
    if pkg_to_ins:
        count = len(pkg_to_ins)
        label = "dependency" if count == 1 else "dependencies"
        Console.print(f"🔧 Installing {count} missing {label} for [bold]{script_name}[/]:")
        try:
            _install_dependencies(pip_path, pkg_to_ins)
        except DependenceInstallationError as e:
            raise e

    # Updating old dependencies
    if pkg_to_upd:
        count = len(pkg_to_upd)
        label = "dependency" if count == 1 else "dependencies"
        Console.print(f"🔧 Updating {count} {label} for [bold]{script_name}[/]:")
        try:
            _install_dependencies(pip_path, pkg_to_upd)
        except DependenceInstallationError as e:
            raise e


def _check_installed_dependence_version(env_path, pkg) -> Optional[str]:
    """
    Checks the dependency version installed, if there is one.

    Arguments:
        env_path: Path to the virtual environment.
        pkg: The package to check.

    Returns:
        The version installed or None.
    """

    try:
        python_exec = env_path / ("Scripts" if sys.platform == "win32" else "bin") / "python"
        installed_version = subprocess.run(
            [str(python_exec), "-c", f"import importlib.metadata; print(importlib.metadata.version('{pkg}'))"],
            capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        installed_version = None
    return installed_version


def _remove_venv(env_path: Path):
    """
    Remove a virtual environment.

    Arguments:
        env_path: Path to the virtual environment.
    """

    shutil.rmtree(env_path)
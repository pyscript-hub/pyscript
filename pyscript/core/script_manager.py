import ast
import importlib
import inspect
import sys
from pathlib import Path

from pyscript.core.manager import SCRIPTS_DIR


# Set of standard moduls to ignore
STANDARD_MODULES = set(sys.builtin_module_names).union(set(sys.stdlib_module_names))


def get_available_scripts() -> list[str]:
    """
    Returns a list of all scripts available.

    Returns:
        A list of all scripts name available.
    """

    return [f.stem for f in SCRIPTS_DIR.glob("*.py") if f.name != "__init__.py"]


def get_path(name: str) -> Path:
    """
    Get the path of a script giving its name.

    Arguments:
        name: the name of the script.

    Returns:
        The path to the script.
    """

    return SCRIPTS_DIR / f"{name}.py"


def exists(name: str) -> bool:
    """
    Returns whether a script exists.

    Arguments:
        name: The name of the script.

    Returns:
        A boolean indicating whether a script exists.
    """

    return (SCRIPTS_DIR / f"{name}.py").exists()


def delete(name: str) -> None:
    """
    Deletes a script file.

    Arguments:
        name: The name of the script.
    """

    path = SCRIPTS_DIR / f"{name}.py"
    if path.exists():
        path.unlink()


def save(name: str, content: str) -> None:
    """
    Saves a script file.

    Arguments:
        name: The name of the script.
        content: The content to be saved.
    """

    path = SCRIPTS_DIR / f"{name}.py"
    path.write_text(content)


def extract_description(script_path: Path) -> str:
    """
    Returns the script main method docstring from a generic python file, if available.

    Arguments:
        script_path: path to the script

    Returns:
        the script main method docs if available, blank otherwise
    """

    try:
        # Load dynamically the module from the Python file
        module_name = script_path.stem
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Check the main method exists and get the docstring
        if hasattr(module, 'main'):
            return inspect.getdoc(module.main)
        else:
            return ""

    except Exception:
        return ""  # Return blank in case of error


def extract_dependencies(script_path: Path) -> list[tuple[str, str]]:
    """
    Analyze the script to retrive third party dependencies.

    Arguments:
        script_path: path of the script

    Returns:
        a list of tuples containing the third party dependencies as (name, version)
    """

    deps = set()  # use a set to avoid duplicates

    with open(script_path, "r") as f:
        tree = ast.parse(f.read(), filename=str(script_path))

        for node in ast.walk(tree):
            # Caso: import X, import X.y, import X.y.z
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = _normalize_module_name(alias.name)
                    if not _is_standard_module(top):
                        deps.add(top)

            # Caso: from X import Y
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = _normalize_module_name(node.module)
                    if not _is_standard_module(top):
                        deps.add(top)

    dependencies = [(dep, "") for dep in sorted(list(deps))]
    return dependencies


# Helpers

def _is_standard_module(module_name: str) -> bool:
    """
    Returns:
        True if the module is standard module (part of sys.builtin_module_names or sys.stdlib_module_names).
    """

    # Check if is built-in
    if module_name in STANDARD_MODULES:
        return True

    # 2. Proviamo a trovare lo spec: se non ha "origin" o è "built-in" / "stdlib"
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        if spec.origin is None:
            return True
        if "python" in spec.origin and "site-packages" not in spec.origin:
            return True
    except Exception:
        pass

    return False


def _normalize_module_name(module: str) -> str:
    """
    Normalizza un import restituendo SOLO il pacchetto top-level.

    Esempi:
    - "rich.console" → "rich"
    - "rich.table" → "rich"
    - "psutil" → "psutil"
    """
    return module.split(".")[0]

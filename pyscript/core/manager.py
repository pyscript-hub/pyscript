import shutil
from pathlib import Path


BASE_DIR = Path.home() / ".pyscript"
SCRIPTS_DIR = BASE_DIR / "scripts"
METADATA_DIR = BASE_DIR / "metadata"
VENVS_DIR = BASE_DIR / "venvs"

INITIALIZED_FILE = BASE_DIR / ".initialized"


def init():
    """
    Initialize the environment.
    """

    # Create environment's directories
    for d in [BASE_DIR, SCRIPTS_DIR, METADATA_DIR, VENVS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Perform initialization action needed only at the first run of the command
    if not INITIALIZED_FILE.exists():
        _install_default_scripts()
        INITIALIZED_FILE.touch()  # Create the flag


def _install_default_scripts():
    """
    Copy default scripts on first run (if missing).
    """

    default_dir = Path(__file__).parent.parent / "default_scripts"

    for py_file in default_dir.glob("*.py"):
        script_name = py_file.stem
        target = SCRIPTS_DIR / py_file.name

        if not target.exists():
            shutil.copy(py_file, target)

        # copy metadata JSON if exists
        meta_src = default_dir / f"{script_name}.json"
        meta_dst = METADATA_DIR / f"{script_name}.json"
        if meta_src.exists() and not meta_dst.exists():
            shutil.copy(meta_src, meta_dst)
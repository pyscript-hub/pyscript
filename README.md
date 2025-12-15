# 🐍 pyscript

**Simple modular Python script runner**

> **Note:**
> This is version **0.1.2 – Beta release**.
> It represents the first public version of the project and may contain bugs or incomplete features.
> Use it for testing, exploration, and feedback purposes.

`pyscript` is a modular CLI (Command Line Interface) designed to centralize, manage, and execute Python scripts. Forget about navigating through endless folders and manually activating virtual environments: `pyscript` handles everything for you, allowing you to launch your favorite tools from anywhere in your terminal.

## ✨ Key Features

  * **Centralized Execution:** Run your scripts from any directory simply by using their name.
  * **Automatic Venv Management:** Automatically creates, manages, and activates virtual environments for each script. If dependencies change, the environment adapts automatically.
  * **Smart Metadata:** Don't want to write JSON files? `pyscript` automatically generates metadata by extracting descriptions from docstrings and dependencies by parsing script imports.
  * **Pyscript Hub:** Download "standard" ready-to-use scripts from an official centralized repository.
  * **Complete Management:** Intuitive commands to add, remove, update, and clean up scripts and temporary files.

## 🛠 Installation

### Prerequisites

  * Python **3.9** or higher.
  * Git.

### Setup

1.  Clone the repository:

    ```bash
    git clone https://github.com/pyscript-hub/pyscript.git
    cd pyscript
    ```

2.  Install the package locally (using a global virtual environment or user-level installation is recommended):

    ```bash
    pip install .
    ```

    *Or for development:*

    ```bash
    pip install -e .
    ```

Once installed, the `pyscript` command will be available in your terminal.

## 🚀 Usage

The basic syntax is:

```bash
pyscript <command> [arguments]
```

### 1\. Execute a script (`run`)

This is the core of the tool. It executes a script while handling the virtual environment automatically.

```bash
pyscript run <script_name> [args]
```

  * **Note:** The script must contain a `main()` function acting as the entry point.

### 2\. Script Management

#### Add a script (`add`)

Import a local script into `pyscript`.

```bash
pyscript add path/to/myscript.py
```

  * **Options:**
      * `--description "..."`: Add a manual description (otherwise read from the docstring).
      * `--dependencies "pandas requests"`: Specify dependencies manually.

#### List scripts (`list`)

Displays a table with all available scripts, categorized into "User Scripts" (custom) and standard scripts.

```bash
pyscript list
```

#### Remove a script (`remove`)

Delete a script, its metadata, or its virtual environment.

```bash
pyscript remove <script_name>
```

  * **Options:**
      * No options: Removes the script, metadata, and venv (asks for confirmation).
      * `--venv`: Removes only the virtual environment.
      * `--metadata`: Removes only the metadata file.
      * `--dependencies "lib1 lib2"`: Uninstalls specific dependencies from the virtual environment.

#### Update a script (`update`)

Update the code or metadata of a script.

```bash
pyscript update <script_name> --path path/to/new_version.py
```

  * **Options:**
      * `--all`: Updates all downloaded standard scripts to the latest version available on the official repository.

### 3\. Pyscript Hub (`download`)

Download useful scripts from the official repository.

```bash
# Download specific scripts
pyscript download script_name1 script_name2

# Download an entire category (e.g., utility, math, etc.)
pyscript download --category utility
```

### 4\. Maintenance (`clean`)

Cleans up orphan files (metadata without scripts, unused venvs) and cache.

```bash
pyscript clean
```

## ⚙️ Under the Hood

All data is saved in your home directory within `.pyscript`:

  * `~/.pyscript/scripts/`: Contains the `.py` files.
  * `~/.pyscript/metadata/`: Contains `.json` files with info (version, dependencies, description).
  * `~/.pyscript/venvs/`: Contains isolated virtual environments for each script.

### Compatible Script Example

To add a script to `pyscript`, ensure it follows this structure:

```python
# myscript.py
import requests

def main():
    """
    This is an example description that pyscript will read automatically.
    """
    print("Hello from pyscript!")

if __name__ == "__main__":
    main()
```

When you run `pyscript add myscript.py`, the tool will detect `requests` as a dependency and install it in the dedicated venv.

## 📂 Project Structure

```text
./
├── pyproject.toml       # Package configuration and dependencies
├── pyscript
│   ├── __init__.py
│   ├── __main__.py      # Entry point (Typer app)
│   ├── commands         # Logic for individual commands (add, run, list...)
│   ├── core             # Core logic (venv, metadata, and script management)
│   ├── default_scripts  # Base scripts installed on first run
│   └── utils            # Utilities for console, file system, and GitHub
└── requirements.txt
```

## 📦 Dependencies

The project is built on modern and robust libraries:

  * **Typer:** For CLI creation.
  * **Rich:** For colorful output, tables, and progress bars.
  * **Psutil:** For process management.
  * **Requests:** To interact with the online Hub.

## 📝 Project Status

Currently in **Beta (0.1.2)**.
It represents the first public version of the project and may contain bugs or incomplete features.
Use it for testing, exploration, and feedback purposes.

## 👤 Author

**Lorenzo Zorri**

  * Email: lorenzo.zorri.developer@gmail.com

## 📄 License

This project is distributed under the **MIT** license.

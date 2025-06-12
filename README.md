# Codebase Dumper

A straightforward VS Code extension that grabs all the relevant source code in your project and dumps it into a single, clean text file.

It's designed to make it easy to copy-paste your entire codebase into an AI prompt for review, analysis, or anything else you can think of.

## Features

* **One Command:** Dumps your entire relevant codebase with a single command from the Command Palette.
* **Git-Aware:** Uses your `git` history as the source of truth, so you only get files that are actually part of your project.
* **Smart Filtering:** Automatically ignores junk directories like `node_modules`, `.venv`, `.git`, `dist`, `build`, and `__pycache__`.
* **Binary-Free:** Skips binary files like images, fonts, and executables to keep the output clean.
* **Safe:** Never overwrites an existing file. If `MyProject.txt` exists, it will create `MyProject (1).txt` automatically.
* **Includes File Tree:** Starts the dump file with a clean, text-based tree of your file structure for easy context.

## How to Use

1.  Open your project folder in VS Code.
2.  Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux, `Cmd+Shift+P` on Mac).
3.  Start typing and select **`Dump Codebase to Text File`**.

That's it. A new file named `[Your-Project-Name].txt` will appear in your project's root directory.

## Configuration

All configuration is done directly inside the Python script. If you need to change what gets included or excluded, you'll have to edit the script packaged with the extension.

**Script Location:** `[Your-Extension-Folder]/scripts/dump_codebase.py`

You can modify these Python sets at the top of the file:

#### Whitelisted File Types
```python
# ✅ Whitelisted file types
include_patterns: Set[str] = {
    "*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.rs",
    "*.html", "*.css", "*.json", "*.toml", "*.yml", "*.yaml",
    "*.md", "*.txt", "*.sh", "*.env.example", "*.env.*"
}

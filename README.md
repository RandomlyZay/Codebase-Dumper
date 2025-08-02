# Codebase Dumper

A powerful VS Code extension that grabs your entire project's source code and packages it into a single text file, perfectly formatted for use with large language models (LLMs).

It's designed to make it easy to copy-paste your entire codebase into an AI prompt for comprehensive reviews, architectural audits, feature brainstorming, and more.

## Features

* **Multiple AI Personas:** Comes with pre-built prompts for various tasks:
  * **Generate RooReview:** Get a detailed, actionable code review.
  * **RooReview Auditor:** A second-opinion AI to validate the initial review and catch hallucinations.
  * **Codebase Auditor:** A high-level architectural and structural analysis of your project.
  * **Feature Architect:** A collaborative partner for brainstorming and implementing new features.
  * **Dump Codebase:** A neutral dump of your code for general-purpose queries.
  * **Dump Git Diffs:** Dumps only the uncommitted changes in your repository.
* **Git-Aware:** Uses your `git` history as the source of truth, so you only get files that are actually part of your project.
* **Smart Filtering:** Automatically ignores junk directories like `node_modules`, `.venv`, `.git`, `dist`, `build`, and `__pycache__`.
* **Binary-Free:** Skips binary files like images, fonts, and executables to keep the output clean.
* **Safe:** Never overwrites an existing file. If `MyProject.txt` exists, it will create `MyProject (1).txt` automatically.
* **Includes File Tree:** Starts the dump file with a clean, text-based tree of your file structure for easy context.

## How to Use (Command Palette)

1.  Open your project folder in VS Code.
2.  Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux, `Cmd+Shift+P` on Mac).
3.  Start typing and select one of the Codebase Dumper commands, like **`Generate RooReview`**.

That's it. A new file named `[Your-Project-Name].txt` (or similar) will appear in your project's root directory, ready to be used with an AI.

## How to Use (Context Menu)

1.  Right-click on a folder in the VS Code Explorer.
2.  Select **`Generate RooReview`** or **`Dump Diffs`** from the context menu.

## Customization

You can customize the included file types or excluded directories by editing the Python script directly.

**Script Location:** `[Your-Extension-Folder]/scripts/dump_codebase.py`

Modify the `include_patterns` set at the top of the file to add or remove file types.
```python
include_patterns: set[str] = { ... }
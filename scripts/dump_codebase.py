from __future__ import annotations
import subprocess
from pathlib import Path
import fnmatch
import sys

# --- CONFIGURATION ---

project_root = Path.cwd()
project_name = project_root.name

# Whitelisted file types
include_patterns: set[str] = {
    "*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.rs",
    "*.html", "*.css", "*.json", "*.toml", "*.yml", "*.yaml",
    "*.md", "*.txt", "*.sh", "*.env.example"
}

# Pre-compiled tuple for faster extension checking
include_extensions = tuple(p[1:] for p in include_patterns if p.startswith("*."))


# Explicitly excluded filenames
excluded_names: set[str] = {".env", "secrets.json"}

# Explicitly excluded directory names
excluded_dirs: set[str] = {
    ".git", ".idea", ".vscode", "node_modules",
    ".venv", "venv", "dist", "build", "__pycache__"
}

# Prompt header
prompt_header = """# 🧠 You are *RooReview*, an elite AI code reviewer.
Your mission is to analyze a full codebase and produce a **RooReview** report.
This report will be a prioritized list of issues and suggestions aimed at improving code quality, structure, and maintainability.

## Your Job: Code-Centric Improvements Only

Your output should *only* consist of suggested code changes and related architectural or logical improvements.
Absolutely no external tool recommendations (like Git, CI/CD, etc.) or non-code-specific advice.
Focus strictly on what can be modified within the code itself.
Here's what to look for:

* **Critical bugs, logical flaws, or unhandled edge cases.**
* **High-risk or unscalable architectural patterns/decisions.**
* Cleaner, more idiomatic patterns.
* Opportunities for modularization, abstraction, or reuse.
* Performance bottlenecks or wasteful logic.
* Ambiguous naming conventions, redundant code, or missing type annotations/definitions.
* Security risks (e.g., unvalidated input, unsafe access).

## RooReview Output Format:

* Label each issue with a severity: `❌ Critical`, `⚠️ Moderate`, `💡 Minor`
* Sort issues from most severe to least.
* For each issue you identify, place a checkbox `[ ]` directly next to it.
* Provide a brief, technical rationale for each suggestion, explaining *why* it's an improvement.
* Provide direct, production-ready improved code examples when necessary – no hand-holding, just the solution.
* Be concise, blunt, and technical in your feedback.

---

## ✅ When to Say Nothing

If the codebase appears clean, efficient, and well-structured—*do not* fabricate suggestions just to appear useful.
Only flag issues that are **objectively suboptimal**, **potentially harmful**, or **measurably improvable**.
It is acceptable to say: “No issues found in this file/module.”
## 🪶 Minor Issue Scrutiny

Do *not* overload the review with `💡 Minor` nitpicks unless they offer a **clear, practical benefit** to clarity, maintainability, or scalability.
Avoid suggesting purely subjective style preferences unless they directly support code health.
## 🧱 Project Phase Awareness

Assume this code is actively being developed.
Prioritize improvements that enhance reliability, maintainability, or performance *within scope*.
Avoid suggesting massive architectural refactors unless the current design is provably fragile or limiting.
If something is “fine for now,” treat it as such unless it poses future risk.
---
"""

# --- TYPE DEFINITIONS ---
Tree = dict[str, "Tree" | None]

# --- HELPER FUNCTIONS ---

def get_unique_filename(base_name: str) -> Path:
    """Generates a unique filename like 'name.txt', 'name (1).txt', etc."""
    output_path = project_root / f"{base_name}.txt"
    counter = 1
    while output_path.exists():
        output_path = project_root / f"{base_name} ({counter}).txt"
        counter += 1
    return output_path

def is_binary(path: Path) -> bool:
    """A simple heuristic to check if a file is binary by checking for null bytes."""
    try:
        with open(path, "rb") as f:
            return b'\0' in f.read(2048)
    except IOError:
        return True

def is_valid_file(path: Path) -> bool:
    """Checks if a file should be included in the output based on config."""
    # A more direct check for common extensions, fallback for complex patterns
    if not (
        path.name.endswith(include_extensions) or
        any(fnmatch.fnmatch(path.name, pat) for pat in include_patterns)
    ):
        return False

    if is_binary(path):
        return False
    return True

def build_tree(paths: list[Path]) -> Tree:
    """Builds a nested dictionary representing the file structure."""
    tree: Tree = {}
    for path in paths:
        d = tree
        # Use path.parts to build the nested structure
        for part in path.parts[:-1]:
            d = d.setdefault(part, {})
        d[path.parts[-1]] = None
    return tree

def render_tree(tree: Tree, prefix: str = "") -> list[str]:
    """Renders a directory tree, sorting files before directories at each level."""
    lines: list[str] = []
    # Use an inline lambda for sorting instead of a separate helper function
    items = sorted(
        tree.items(),
        key=lambda item: (isinstance(item[1], dict), item[0])
    )

    for i, (name, subtree) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{name}")

        if isinstance(subtree, dict):
            extension = "    " if is_last else "│   "
            lines.extend(render_tree(subtree, prefix + extension))

    return lines

# --- MAIN LOGIC ---

def get_project_files() -> list[Path]:
    """Gets and filters all relevant project files using Git."""
    try:
        # Build exclusion pathspecs for Git to handle filtering efficiently
        git_exclusions = [f":(exclude){d}" for d in excluded_dirs]
        git_exclusions.extend([f":(exclude){n}" for n in excluded_names])

        cmd = ["git", "ls-files", "-c", "-o", "--exclude-standard"] + git_exclusions
        git_files_output = subprocess.check_output(cmd).decode().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Not a Git repository or 'git' command not found. Make sure you are in a git-initialized directory.")
        sys.exit(1)

    all_paths = (Path(p_str) for p_str in git_files_output)
    valid_paths = [p for p in all_paths if is_valid_file(p)]

    # Sort files: root files first, then by full path string.
    return sorted(valid_paths, key=lambda p: (len(p.parts) > 1, str(p)))

def write_codebase_to_file(files: list[Path], output_path: Path):
    """Writes the codebase tree and contents to the specified output file."""
    tree = build_tree(files)
    tree_str = "\n".join(render_tree(tree))

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        if "--no-prompt" not in sys.argv:
            f.write(prompt_header)

        f.write("\n## 📁 File Structure\n\n")
        f.write(tree_str + "\n\n")
        f.write("## 📄 File Contents\n\n")
        for path in files:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                f.write(f"### {path.as_posix()}\n")
                f.write("```\n")
                f.write(content.rstrip() + "\n")
                f.write("```\n\n")
            except (IOError, UnicodeDecodeError) as e:
                f.write(f"<Could not read file {path.as_posix()}: {e}>\n\n")

def main():
    """Coordinates getting files and writing the output."""
    included_files = get_project_files()
    if not included_files:
        print("No files to dump after filtering.")
        return

    output_file_path = get_unique_filename(project_name)
    write_codebase_to_file(included_files, output_file_path)
    print(f"✅ Codebase dumped to: {output_file_path.name}")


if __name__ == "__main__":
    main()
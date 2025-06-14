import subprocess
from pathlib import Path
import fnmatch
from typing import List, Dict, Optional, Set

# --- CONFIGURATION ---

project_root = Path.cwd()
project_name = project_root.name

# ✅ Whitelisted file types
include_patterns: Set[str] = {
    "*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.rs",
    "*.html", "*.css", "*.json", "*.toml", "*.yml", "*.yaml",
    "*.md", "*.txt", "*.sh", "*.env.example"
}

# ❌ Explicitly excluded filenames
excluded_names: Set[str] = {".env", "secrets.json"}

# 📂 Explicitly excluded directory names
excluded_dirs: Set[str] = {
    ".git", ".idea", ".vscode", "node_modules",
    ".venv", "venv", "dist", "build", "__pycache__"
}

# 💬 Prompt header
prompt_header = """# 🧠 You are *RooReview*, an elite AI code reviewer.

Your mission is to analyze a full codebase and produce a **RooReview** report. This report will be a prioritized list of issues and suggestions aimed at improving code quality, structure, and maintainability.

## Your Job: Code-Centric Improvements Only
Your output should *only* consist of suggested code changes and related architectural or logical improvements. Absolutely no external tool recommendations (like Git, CI/CD, etc.) or non-code-specific advice. Focus strictly on what can be modified within the code itself.

Here's what to look for:

- **Critical bugs, logical flaws, or unhandled edge cases.**
- **High-risk or unscalable architectural patterns/decisions.**
- Cleaner, more idiomatic patterns.
- Opportunities for modularization, abstraction, or reuse.
- Performance bottlenecks or wasteful logic.
- Ambiguous naming conventions, redundant code, or missing type annotations/definitions.
- Security risks (e.g., unvalidated input, unsafe access).

## RooReview Output Format:
- Label each issue with a severity: `❌ Critical`, `⚠️ Moderate`, `💡 Minor`
- Sort issues from most severe to least.
- For each issue you identify, place a checkbox `[ ]` directly next to it.
- Provide direct, production-ready improved code examples when necessary – no hand-holding, just the solution.
- Be concise, blunt, and technical in your feedback.

You will be provided with the file tree and the full contents of all relevant source files. Ignore non-code files unless they inherently contain logic (e.g., JSON schemas with validation logic, configuration files with programmatic impact).
---
"""

# --- TYPE DEFINITIONS ---
Tree = Dict[str, Optional['Tree']]

# --- HELPER FUNCTIONS ---

def get_unique_filename() -> Path:
    """
    Checks if a file exists and finds a unique name by appending a number.
    Returns a Path object for the unique filename.
    """
    output_path = project_root / f"{project_name}.txt"
    counter = 1
    # Keep trying new names until we find one that doesn't exist
    while output_path.exists():
        output_path = project_root / f"{project_name} ({counter}).txt"
        counter += 1
    return output_path

def is_binary(path: Path) -> bool:
    """Heuristically checks if a file is binary."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
            if not chunk: return False
            nontext = sum(1 for b in chunk if b < 9 or (b > 13 and b < 32) or b > 126)
            return nontext / len(chunk) > 0.3
    except Exception:
        return True

def is_included_file(path: Path) -> bool:
    """Checks if a file should be included in the dump based on all exclusion and inclusion criteria."""
    if any(part in excluded_dirs for part in path.parts) or path.name in excluded_names:
        return False
    if not any(fnmatch.fnmatch(path.name, pat) for pat in include_patterns):
        return False
    if is_binary(path):
        return False
    return True

def build_tree(paths: List[Path]) -> Tree:
    """Builds a nested dictionary representing the file tree."""
    tree: Tree = {}
    for path in paths:
        parts = path.parts
        d = tree
        for part in parts[:-1]:
            next_d = d.get(part)
            if not isinstance(next_d, dict):
                next_d = {}
                d[part] = next_d
            d = next_d
        d[parts[-1]] = None
    return tree

def render_tree(tree: Tree, prefix: str = "") -> List[str]:
    """Renders the file tree dictionary into a string representation."""
    lines: List[str] = []
    items = sorted(tree.items())
    for i, (name, subtree) in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        lines.append(f"{prefix}{connector}{name}")
        if isinstance(subtree, dict):
            extension = "    " if i == len(items) - 1 else "│   "
            lines.extend(render_tree(subtree, prefix + extension))
    return lines

# --- MAIN EXECUTION ---

def main():
    # Step 1: Get all Git-tracked files
    try:
        git_ls_files_output = subprocess.check_output(["git", "ls-files"]).decode().splitlines()
        all_tracked_files = [Path(p) for p in git_ls_files_output]
    except subprocess.CalledProcessError:
        print("❌ Not a Git repository or 'git ls-files' command failed.")
        return

    # Step 2: Filter for files to include in the dump
    included_files = sorted([path for path in all_tracked_files if is_included_file(path)])
    
    if not included_files:
        print("No files to dump after filtering.")
        return

    # Step 3: Build and render the file tree
    tree = build_tree(included_files)
    tree_str = "\n".join(render_tree(tree))

    # Step 4: Get a unique filename to avoid overwriting existing files
    output_file_path = get_unique_filename()

    # Step 5: Write the codebase dump to the unique output file
    with open(output_file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(prompt_header)
        f.write("\n## 📁 File Structure\n\n")
        f.write(tree_str + "\n\n")
        f.write("## 📄 File Contents\n\n")
        for path in included_files:
            f.write(f"### {path.as_posix()}\n")
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                f.write("```\n")
                f.write(content.strip() + "\n")
                f.write("```\n\n")
            except Exception as e:
                f.write(f"<Could not read file: {e}>\n\n")

    print(f"✅ Codebase dumped to: {output_file_path.name}")

if __name__ == "__main__":
    main()
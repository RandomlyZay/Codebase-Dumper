import subprocess
from pathlib import Path
import sys

# --- CONFIGURATION ---

prompt_header = """Here are the changes implemented based on your last review. Please analyze this diff and let me know if the suggestions were correctly implemented or if any new issues were introduced. """

# --- HELPER FUNCTIONS ---
def get_unique_filename(base_path: Path, base_name: str) -> Path:
    """Generates a unique filename in the given base path."""
    output_path = base_path / f"{base_name}.txt"
    counter = 1
    while output_path.exists():
        output_path = base_path / f"{base_name} ({counter}).txt"
        counter += 1
    return output_path

def get_full_diff() -> tuple[str, Path | None]:
    """
    Gets the uncommitted diff for all changes in the repo.
    Returns a tuple of (diff_string, repo_root_path).
    Returns ("", None) on error.
    """
    try:
        # 1. Find the repo root.
        repo_root_cmd = ["git", "rev-parse", "--show-toplevel"]
        # ✅ Specify UTF-8 encoding
        repo_root_str = subprocess.check_output(
            repo_root_cmd, text=True, encoding="utf-8", stderr=subprocess.PIPE
        ).strip()
        repo_root = Path(repo_root_str)

        # 2. Check for initial commit.
        subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            check=True,
            capture_output=True,
            text=True, # ✅ Process stderr as text
            encoding="utf-8", # ✅ Use UTF-8 for error messages
            cwd=repo_root
        )
    except FileNotFoundError:
        print("❌ Git not found. Make sure it's installed and in your PATH.")
        return "", None
    except subprocess.CalledProcessError as e:
        if "unknown revision" in e.stderr:
            print("🤔 No commits found. Cannot create a diff against HEAD.")
            print("   Please make an initial commit first.")
        else:
            print(f"❌ Error finding git repo root: {e.stderr.strip()}")
        return "", None

    # 1. Determine the output filename BEFORE listing untracked files.
    output_file = get_unique_filename(repo_root, "diff_dump")

    # 2. Get all untracked files.
    cmd_untracked = ["git", "ls-files", "--others", "--exclude-standard"]
    # ✅ Specify UTF-8 encoding
    untracked_output = subprocess.check_output(
        cmd_untracked, text=True, encoding="utf-8", cwd=repo_root
    )

    # 3. Filter out the determined output filename from the list.
    untracked_files_to_add = [
        f for f in untracked_output.splitlines()
        if repo_root / f != output_file
    ]

    try:
        # 4. Use "intent-to-add" on the FILTERED list.
        if untracked_files_to_add:
            subprocess.run(["git", "add", "-N"] + untracked_files_to_add, check=True, cwd=repo_root)

        # 5. Get the diff, excluding the output file via pathspec.
        pathspec = f":(exclude){output_file.relative_to(repo_root)}"
        # ✅ Specify UTF-8 encoding (This was the line that crashed)
        full_diff = subprocess.check_output(
            ["git", "diff", "HEAD", "--", ".", pathspec],
            text=True,
            encoding="utf-8",
            cwd=repo_root
        ).strip()

        return full_diff, output_file

    except subprocess.CalledProcessError as e:
        print("❌ Error running a git command.")
        error_message = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else str(e)
        print(f"   Git error: {error_message}")
        return "", None
    finally:
        # 6. VERY IMPORTANT: Clean up by resetting only the files we added.
        if untracked_files_to_add:
            subprocess.run(["git", "reset", "--"] + untracked_files_to_add, check=True, cwd=repo_root)

# --- MAIN EXECUTION ---
def main():
    """Main function to generate and save the diff."""
    diff_output, output_file_path = get_full_diff()

    if not diff_output:
        print("No uncommitted changes detected or an error occurred. Nothing to dump.")
        return

    # Now we write the content to the file path we determined earlier.
    with open(output_file_path, "w", encoding="utf-8", newline="\n") as f:
        # Conditionally write the prompt header
        if "--no-prompt" not in sys.argv:
            f.write(prompt_header)
            f.write("\n---\n\n")

        f.write("```diff\n")
        f.write(diff_output + "\n")
        f.write("```")

    print(f"✅ Full diff dumped to: {output_file_path.name}")

if __name__ == "__main__":
    main()
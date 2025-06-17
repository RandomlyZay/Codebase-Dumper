import subprocess
from pathlib import Path
import sys

# --- CONFIGURATION ---

prompt_header = """Here are the changes I've made based on your last review.

Please analyze this diff and let me know if I've correctly implemented the suggestions or introduced any new issues.
"""

# --- HELPER FUNCTIONS ---
def get_unique_filename(base_name: str) -> Path:
    output_path = Path.cwd() / f"{base_name}.txt"
    counter = 1
    while output_path.exists():
        output_path = Path.cwd() / f"{base_name} ({counter}).txt"
        counter += 1
    return output_path

def get_diff_excluding_file(exclude_filename: str) -> str:
    """
    Gets the uncommitted diff and excludes any hunk that involves the given filename.
    """
    try:
        cmd = ["git", "diff"]
        raw_diff = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode()

        filtered_lines = []
        skip_file = False
        for line in raw_diff.splitlines():
            if line.startswith("diff --git"):
                skip_file = exclude_filename in line
            if not skip_file:
                filtered_lines.append(line)

        return "\n".join(filtered_lines)
    except subprocess.CalledProcessError as e:
        print("❌ Error running 'git diff'.")
        print(f"   Git error: {e.stderr.decode().strip()}")
        return ""
    except FileNotFoundError:
        print("❌ Git not found or not a repository.")
        return ""

# --- MAIN EXECUTION ---
def main():
    output_file_path = get_unique_filename("diff_dump")
    diff_output = get_diff_excluding_file(output_file_path.name)

    if not diff_output.strip():
        print("No uncommitted changes detected. Nothing to dump.")
        return

    with open(output_file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(prompt_header)
        f.write("\n---\n\n")
        f.write("```diff\n")
        f.write(diff_output.strip() + "\n")
        f.write("```")

    print(f"✅ Diff dumped to: {output_file_path.name}")

if __name__ == "__main__":
    main()
import subprocess
import sys
from pathlib import Path


def has_changes(file_path: str) -> bool:
    base_path = Path(__file__).parent
    full_path = base_path / file_path
    
    if not full_path.exists():
        return False
    
    result = subprocess.run(
        ['git', 'diff', '--quiet', 'HEAD', str(full_path)],
        cwd=base_path.parent,
        capture_output=True
    )
    
    return result.returncode != 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_changes.py <file1> [file2] ...", file=sys.stderr)
        sys.exit(2)
    
    files_to_check = sys.argv[1:]
    
    any_changes = any(has_changes(file) for file in files_to_check)
    
    if any_changes:
        print(f"Changes detected in: {', '.join(files_to_check)}")
        sys.exit(0)
    else:
        print(f"No changes in: {', '.join(files_to_check)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

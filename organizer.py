import logging
import os
import shutil
import sys
from pathlib import Path


EXTENSION_MAP = {
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".txt": "Documents", ".xlsx": "Documents", ".pptx": "Documents",
    ".csv": "Documents",
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".bmp": "Images", ".svg": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos", ".mov": "Videos",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code",
    ".java": "Code", ".cpp": "Code", ".json": "Code",
}

CATEGORY_FOLDERS = set(EXTENSION_MAP.values()) | {"Others"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("organizer.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def unique_destination(dest: Path) -> Path:
    """If dest exists, return 'name (1).ext', 'name (2).ext', ... instead."""
    if not dest.exists():
        return dest
    counter = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({counter}){dest.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def organize(target: Path) -> dict:
    summary = {}  # category -> number of files moved
    errors = 0

    # Step 3: os.scandir() to inspect every entry in the folder
    with os.scandir(target) as entries:
        files = [Path(e.path) for e in entries if e.is_file()]

    for file in files:
        if file.name == Path(__file__).name or file.suffix == ".log":
            continue  # don't move the script itself or its log

        category = EXTENSION_MAP.get(file.suffix.lower(), "Others")
        category_dir = target / category
        category_dir.mkdir(exist_ok=True)  # create subfolder dynamically

        destination = unique_destination(category_dir / file.name)

        # Step 4: try-except around the move
        try:
            shutil.move(str(file), str(destination))  # shutil.move() relocates
            summary[category] = summary.get(category, 0) + 1
            logging.info("Moved %s -> %s", file.name, destination.relative_to(target))
        except FileExistsError:
            logging.warning("Skipped %s: destination already exists", file.name)
            errors += 1
        except PermissionError:
            logging.error("Skipped %s: permission denied (file in use?)", file.name)
            errors += 1
        except OSError as exc:
            logging.error("Skipped %s: %s", file.name, exc)
            errors += 1

    return {"summary": summary, "errors": errors}


def print_summary(result: dict) -> None:
    # Step 5: formatted execution summary
    summary, errors = result["summary"], result["errors"]
    total = sum(summary.values())
    print("\n" + "=" * 40)
    print(" ORGANIZER SUMMARY")
    print("=" * 40)
    for category, count in sorted(summary.items()):
        print(f" {category:<12} {count:>4} file(s)")
    print("-" * 40)
    print(f" Total relocated: {total}")
    print(f" Skipped (errors): {errors}")
    print("=" * 40)


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads"
    if not target.is_dir():
        logging.error("Folder not found: %s", target)
        sys.exit(1)

    logging.info("Organizing: %s", target)
    print_summary(organize(target))


if __name__ == "__main__":
    main()
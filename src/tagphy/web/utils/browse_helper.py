import os
from pathlib import Path

from tagphy import app_root
from tagphy.tools.pipeline import DEFAULT_OUTPUT_DIR_NAME, IMAGE_EXTENSIONS


class BrowseHelper:
    """List dirs and image files under the app root for the Scan folder picker."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root).resolve() if root else app_root()

    def list_directory(self, path: str = "") -> dict:
        current = self._resolve_under_root(path)
        if not current.is_dir():
            raise ValueError("Path is not a directory")
        if self._is_output_dir(current):
            raise ValueError("Cannot browse the output directory")

        entries: list[dict] = []
        try:
            names = sorted(os.listdir(current), key=str.lower)
        except OSError as e:
            raise ValueError(f"Cannot read directory: {e}") from e

        for name in names:
            if name == DEFAULT_OUTPUT_DIR_NAME:
                continue
            child = current / name
            try:
                if child.is_dir():
                    entries.append(
                        {
                            "name": name,
                            "type": "dir",
                            "path": child.as_posix(),
                        }
                    )
                elif child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
                    entries.append(
                        {
                            "name": name,
                            "type": "file",
                            "path": child.as_posix(),
                        }
                    )
            except OSError:
                continue

        parent = None
        if current != self.root:
            parent = current.parent.as_posix()

        return {
            "current": current.as_posix(),
            "parent": parent,
            "entries": entries,
        }

    def _resolve_under_root(self, path: str) -> Path:
        if not path:
            return self.root
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as e:
            raise ValueError("Path is outside the app root") from e
        if not candidate.exists():
            raise ValueError("Path does not exist")
        return candidate

    def _is_output_dir(self, current: Path) -> bool:
        output = (self.root / DEFAULT_OUTPUT_DIR_NAME).resolve()
        try:
            current.relative_to(output)
            return True
        except ValueError:
            return False

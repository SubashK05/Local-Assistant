
from pathlib import Path
import shutil


# Project root: directory containing manage.py
BASE_DIR = Path(__file__).resolve().parents[3]

WORKSPACE = (BASE_DIR / "workspace").resolve()


def resolve_workspace_path(path="."):
    """
    Resolve a relative path safely inside workspace.
    """

    target = (WORKSPACE / path).resolve()

    if not target.is_relative_to(WORKSPACE):
        raise ValueError("Access outside workspace is not allowed.")

    return target


def list_files(path="."):
    """
    List files and directories inside workspace.
    """

    try:
        target = resolve_workspace_path(path)

        if not target.exists():
            return {
                "success": False,
                "error": "Path does not exist."
            }

        if not target.is_dir():
            return {
                "success": False,
                "error": "Path is not a directory."
            }

        items = []

        for item in sorted(target.iterdir()):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file"
            })

        return {
            "success": True,
            "path": str(target.relative_to(WORKSPACE)),
            "items": items
        }

    except (ValueError, OSError) as error:
        return {
            "success": False,
            "error": str(error)
        }


def read_file(path):
    """
    Read a text file inside workspace.
    """

    try:
        target = resolve_workspace_path(path)

        if not target.exists():
            return {
                "success": False,
                "error": "File does not exist."
            }

        if not target.is_file():
            return {
                "success": False,
                "error": "Path is not a file."
            }

        # Avoid loading very large files into memory
        max_size = 100_000

        if target.stat().st_size > max_size:
            return {
                "success": False,
                "error": "File is too large to read (maximum 100 KB)."
            }

        content = target.read_text(encoding="utf-8")

        return {
            "success": True,
            "path": str(target.relative_to(WORKSPACE)),
            "content": content
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "File is not a supported UTF-8 text file."
        }

    except (ValueError, OSError) as error:
        return {
            "success": False,
            "error": str(error)
        }


def create_file(path, content):
    try:
        target = resolve_workspace_path(path)

        if target.exists():
            return {
                "success": False,
                "error": "File already exists. Cannot overwrite."
            }

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": str(target.relative_to(WORKSPACE)),
            "message": "File created successfully."
        }

    except (ValueError, OSError) as error:
        return {
            "success": False,
            "error": str(error)
        }



def create_folder(path):
    try:
        target = resolve_workspace_path(path)

        if target.exists():
            return {
                "success": False,
                "error": "File or folder already exists."
            }

        target.mkdir(parents=True)

        return {
            "success": True,
            "path": str(target.relative_to(WORKSPACE)),
            "message": "Folder created successfully."
        }

    except (ValueError, OSError) as error:
        return {"success": False, "error": str(error)}


def edit_file(path, content):
    try:
        target = resolve_workspace_path(path)

        if not target.exists():
            return {"success": False, "error": "File does not exist."}

        if not target.is_file():
            return {"success": False, "error": "Path is not a file."}

        target.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": str(target.relative_to(WORKSPACE)),
            "message": "File updated successfully."
        }

    except (ValueError, OSError) as error:
        return {"success": False, "error": str(error)}


def move_item(source, destination):
    try:
        src = resolve_workspace_path(source)
        dst = resolve_workspace_path(destination)

        if not src.exists():
            return {"success": False, "error": "Source does not exist."}

        if dst.exists():
            return {
                "success": False,
                "error": "Destination already exists."
            }

        if src.is_dir() and dst.is_relative_to(src):
            return {
                "success": False,
                "error": "Cannot move a folder into itself."
            }

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        return {
            "success": True,
            "source": source,
            "destination": destination,
            "message": "Item moved successfully."
        }

    except (ValueError, OSError) as error:
        return {"success": False, "error": str(error)}


def copy_item(source, destination):
    try:
        src = resolve_workspace_path(source)
        dst = resolve_workspace_path(destination)

        if not src.exists():
            return {"success": False, "error": "Source does not exist."}

        if dst.exists():
            return {
                "success": False,
                "error": "Destination already exists."
            }

        if src.is_dir() and dst.is_relative_to(src):
            return {
                "success": False,
                "error": "Cannot copy a folder into itself."
            }

        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

        return {
            "success": True,
            "source": source,
            "destination": destination,
            "message": "Item copied successfully."
        }

    except (ValueError, OSError) as error:
        return {"success": False, "error": str(error)}


def delete_item(path):
    try:
        target = resolve_workspace_path(path)

        if not target.exists():
            return {"success": False, "error": "Item does not exist."}

        # Never allow deleting the workspace root itself.
        if target == WORKSPACE:
            return {
                "success": False,
                "error": "Cannot delete the workspace root."
            }

        # Move deleted items into a workspace trash folder.
        trash = resolve_workspace_path(".trash")
        trash.mkdir(exist_ok=True)

        destination = trash / target.name

        if destination.exists():
            return {
                "success": False,
                "error": "An item with this name already exists in trash."
            }

        shutil.move(str(target), str(destination))

        return {
            "success": True,
            "path": path,
            "message": "Item moved to workspace trash."
        }

    except (ValueError, OSError) as error:
        return {"success": False, "error": str(error)}

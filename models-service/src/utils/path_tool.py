from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def make_absolute(path: Path) -> Path:
    if not path.is_absolute():
        return get_project_root() / path
    return path


def get_abs_path(relative_path: str) -> Path:
    return get_project_root() / relative_path

if __name__ == '__main__':
    pass
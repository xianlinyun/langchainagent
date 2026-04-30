from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent
def get_abs_path(relative_path: str) -> Path:
    return get_project_root() / relative_path

if __name__ == '__main__':
    pass
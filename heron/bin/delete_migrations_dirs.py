import shutil
from pathlib import Path

from heron import settings

if __name__ == "__main__":
    path_dirs = settings.BASE_DIR

    list_migrations_dirs = [
        rep for rep in path_dirs.glob("**/**") if rep.is_dir() and rep.name.endswith("migrations")
    ]

    for rep in list_migrations_dirs:
        print(rep)
        shutil.rmtree(Path(rep))

import shutil
from pathlib import Path

if __name__ == '__main__':
    path_dirs = Path("D:\SitesWeb\heron")

    list_migrations_dirs = [rep for rep in path_dirs.glob("**/**") if rep.is_dir() and rep.name.endswith("migrations")]

    for rep in list_migrations_dirs:
        print(rep)
        shutil.rmtree(Path(rep))

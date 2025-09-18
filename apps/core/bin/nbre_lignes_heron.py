from pathlib import Path


def main():
    files_path = Path(r"/Users/paulo/SitesWeb/heron/apps")
    nbre_lines = 0
    for file in files_path.rglob("*.*"):
        if file.is_file() and str(file.name)[-3:] != "pyc" and str(file.name)[:2] != "00":
            print(file.name)
            with file.open("rb") as fil:
                for _ in fil:
                    nbre_lines += 1

    files_path = Path(r"/Users/paulo/SitesWeb/heron/heron")
    for file in files_path.rglob("*.*"):
        if file.is_file() and str(file.name)[-3:] != "pyc" and str(file.name)[:2] != "00":
            print(file.name)
            with file.open("rb") as fil:
                for _ in fil:
                    nbre_lines += 1

    print(nbre_lines)


if __name__ == "__main__":
    main()

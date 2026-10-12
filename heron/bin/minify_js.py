from pathlib import Path

import requests

from heron import settings

url = "https://javascript-minifier.com/raw"


def minify(file, file_minify):
    """Appel d'une api rest pour minifier un fichier js
        :param file: fichier à minifier
        :param file_minify: nom du fichier minifier
        :return: text js minifié
    """
    data = {"input": open(file, "rb").read()}
    response = requests.post(url, data=data)
    with open(file_minify, "w") as file_to_write:
        file_to_write.write(response.text)


if __name__ == "__main__":
    path = (Path(settings.BASE_DIR) / "files/static/js").resolve()

    files_list = [

    ]

    for file_name in files_list:
        fichier = path / f"{file_name}.js"
        fichier_minify = path / f"{file_name}.min.js"
        minify(fichier, fichier_minify)

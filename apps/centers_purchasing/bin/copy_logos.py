# pylint: disable=E0401
"""
Module de copy des logos vers le répertoire static
"""
from heron.settings import MEDIA_DIR, STATIC_DIR


def copy_static(logos_set: set) -> None:
    """
    Cpoie des logos dans le répsrtoire static, static/img et static/images
    :param logos_set: set des logos
    :return:
    """
    media_path = MEDIA_DIR / "logos"
    static_path = STATIC_DIR
    static_images = STATIC_DIR / "images"
    static_img = STATIC_DIR / "img"

    for logo in logos_set:
        logo_name = logo.replace("logos/", "")
        logo_path = media_path / logo_name
        logo_static = static_path / logo_name
        logo_images = static_images / logo_name
        logo_img = static_img / logo_name

        if logo_path.is_file():
            logo_static.write_bytes(logo_path.read_bytes())
            logo_images.write_bytes(logo_path.read_bytes())
            logo_img.write_bytes(logo_path.read_bytes())


if __name__ == "__main__":
    copy_static(
        {
            "logos/logo-maison-acuitis-horizontal-01.png",
            "logos/logo-maison-acuitis-horizontal-01_FI7Cyx4.png",
            "logos/logo_grandaudition.png",
            "logos/logodo.png",
            "logos/logomaa.png",
            "logos/logounisson.png",
        }
    )

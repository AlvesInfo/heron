# pylint: disable=E0401,C0413
"""
FR : Utilitaires de génération PDF avec Playwright
EN : PDF generation utilities with Playwright

Commentaire:
    Fonction générique html_to_pdf qui remplace le pattern WeasyPrint :
        HTML(string=content).write_pdf(pdf_path, font_config=font_config)

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
from pathlib import Path
from typing import AnyStr, Union

from apps.invoices.bin.playwright.browser_manager import get_browser_manager


def html_to_pdf(html_content: str, pdf_path: Union[Path, AnyStr], **kwargs) -> None:
    """
    Génère un PDF à partir d'un contenu HTML via Playwright (Chromium).

    Remplacement direct de :
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)

    :param html_content: Contenu HTML complet
    :param pdf_path: Chemin de sortie du fichier PDF
    :param kwargs: Options supplémentaires pour page.pdf()
                   (format, margin, print_background, etc.)
    """
    manager = get_browser_manager()
    page = manager.new_page()

    try:
        # Correction du line-height : Chromium a un interlignage par defaut
        # plus grand que WeasyPrint. On aligne sur le rendu WeasyPrint (~1.2).
        css_fix = """<style>
            table, td, th, p, tr { line-height: 1 !important; }
        </style>"""
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", f"<head>{css_fix}", 1)
        elif "<style>" in html_content:
            html_content = html_content.replace("<style>", f"{css_fix}<style>", 1)
        else:
            html_content = css_fix + html_content

        page.set_content(html_content, wait_until="networkidle")

        pdf_options = {
            "path": str(pdf_path),
            "format": "A4",
            "print_background": True,
            "margin": {
                "top": "10mm",
                "bottom": "10mm",
                "left": "10mm",
                "right": "10mm",
            },
        }
        pdf_options.update(kwargs)
        page.pdf(**pdf_options)
    finally:
        page.close()
# pylint: disable=E0401,C0413
"""
FR : Script de benchmark WeasyPrint vs Playwright pour la génération de PDF
EN : Benchmark script WeasyPrint vs Playwright for PDF generation

Commentaire:
    Lance la génération d'un même PDF avec les deux moteurs et compare les temps.

    Usage :
        python apps/invoices/bin/playwright/benchmark.py

    Il faut modifier l'UUID ci-dessous avec un uuid_identification valide
    de votre base de données.

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
import os
import sys
import time
from pathlib import Path

import django

# Playwright sync API utilise un event loop async en interne,
# Django bloque les appels ORM dans ce contexte sans cette variable.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent.parent.parent)

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from uuid import UUID

from django.conf import settings

# =====================================================================
# CONFIGURATION : Modifier l'UUID avec une facture existante
# =====================================================================
UUID_INVOICE = UUID("ba9b221a-f465-4ddf-949a-dfbb0d8c5f0b")
# =====================================================================

OUTPUT_DIR = Path(settings.SALES_INVOICES_FILES_DIR)


def benchmark_weasyprint():
    """Benchmark avec WeasyPrint (version originale)"""
    from apps.invoices.bin.pdf_marchandises import invoice_marchandise_pdf

    pdf_path = OUTPUT_DIR / "benchmark_weasyprint_playwright.pdf"

    # Warm-up (premier appel souvent plus lent)
    invoice_marchandise_pdf(UUID_INVOICE, pdf_path)
    if pdf_path.is_file():
        pdf_path.unlink()

    # Benchmark
    times = []
    size_wp = 0
    for i in range(3):
        start = time.perf_counter()
        invoice_marchandise_pdf(UUID_INVOICE, pdf_path)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  WeasyPrint  - run {i + 1}: {elapsed:.3f}s")
        if pdf_path.is_file():
            size_wp = pdf_path.stat().st_size
            # On supprime sauf le dernier run (conservé pour vérification)
            if i < 2:
                pdf_path.unlink()

    print(f"  -> PDF conservé : {pdf_path}")
    return times, size_wp


def benchmark_playwright():
    """Benchmark avec Playwright"""
    from apps.invoices.bin.playwright.pdf_marchandises import invoice_marchandise_pdf

    pdf_path = OUTPUT_DIR / "benchmark_playwright.pdf"

    # Warm-up (lance le browser Chromium)
    invoice_marchandise_pdf(UUID_INVOICE, pdf_path)
    if pdf_path.is_file():
        pdf_path.unlink()

    # Benchmark
    times = []
    size_pw = 0
    for i in range(3):
        start = time.perf_counter()
        invoice_marchandise_pdf(UUID_INVOICE, pdf_path)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Playwright  - run {i + 1}: {elapsed:.3f}s")
        if pdf_path.is_file():
            size_pw = pdf_path.stat().st_size
            if i < 2:
                pdf_path.unlink()

    print(f"  -> PDF conservé : {pdf_path}")
    return times, size_pw


def main():
    print("=" * 60)
    print("BENCHMARK : WeasyPrint vs Playwright")
    print(f"UUID facture : {UUID_INVOICE}")
    print("=" * 60)

    print("\n--- WeasyPrint ---")
    wp_times, wp_size = benchmark_weasyprint()

    print("\n--- Playwright ---")
    pw_times, pw_size = benchmark_playwright()

    # Fermeture propre du browser
    from apps.invoices.bin.playwright.browser_manager import get_browser_manager
    get_browser_manager().close()

    # Résultats
    wp_avg = sum(wp_times) / len(wp_times)
    pw_avg = sum(pw_times) / len(pw_times)
    speedup = wp_avg / pw_avg if pw_avg > 0 else 0

    print("\n" + "=" * 60)
    print("RESULTATS (moyenne sur 3 runs, hors warm-up)")
    print("=" * 60)
    print(f"  WeasyPrint : {wp_avg:.3f}s  (taille: {wp_size:,} octets)")
    print(f"  Playwright : {pw_avg:.3f}s  (taille: {pw_size:,} octets)")
    print(f"  Ratio      : x{speedup:.1f}")
    print("=" * 60)
    print("\nFICHIERS PDF CONSERVES (dernier run) :")
    print(f"  WeasyPrint : {OUTPUT_DIR / 'benchmark_weasyprint_playwright.pdf'}")
    print(f"  Playwright : {OUTPUT_DIR / 'benchmark_playwright.pdf'}")


if __name__ == "__main__":
    main()
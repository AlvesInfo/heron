# pylint: disable=E0401,C0413
"""
FR : Script de benchmark WeasyPrint vs fpdf2 pour la génération de PDF
EN : Benchmark script WeasyPrint vs fpdf2 for PDF generation

Usage:
    python apps/invoices/bin/fpdf2/benchmark.py

    Modifier l'UUID ci-dessous avec un uuid_identification valide.

created at: 2024-02-10
created by: Paulo ALVES
"""
import os
import sys
import time
from pathlib import Path

import django

# Détection automatique du BASE_DIR à partir de l'emplacement du script
# benchmark.py est dans apps/invoices/bin/fpdf2/ → 4 niveaux au-dessus = racine du projet
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

    pdf_path = OUTPUT_DIR / "benchmark_weasyprint_fpdf2.pdf"

    # Warm-up
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
        print(f"  WeasyPrint - run {i + 1}: {elapsed:.3f}s")
        if pdf_path.is_file():
            size_wp = pdf_path.stat().st_size
            # On supprime sauf le dernier run (conservé pour vérification)
            if i < 2:
                pdf_path.unlink()

    print(f"  -> PDF conservé : {pdf_path}")
    return times, size_wp


def benchmark_fpdf2():
    """Benchmark avec fpdf2"""
    from apps.invoices.bin.fpdf2.pdf_marchandises import invoice_marchandise_pdf

    pdf_path = OUTPUT_DIR / "benchmark_fpdf2.pdf"

    # Warm-up
    invoice_marchandise_pdf(UUID_INVOICE, pdf_path)
    if pdf_path.is_file():
        pdf_path.unlink()

    # Benchmark
    times = []
    size_fp = 0
    for i in range(3):
        start = time.perf_counter()
        invoice_marchandise_pdf(UUID_INVOICE, pdf_path)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  fpdf2     - run {i + 1}: {elapsed:.3f}s")
        if pdf_path.is_file():
            size_fp = pdf_path.stat().st_size
            if i < 2:
                pdf_path.unlink()

    print(f"  -> PDF conservé : {pdf_path}")
    return times, size_fp


def main():
    print("=" * 60)
    print("BENCHMARK : WeasyPrint vs fpdf2")
    print(f"UUID facture : {UUID_INVOICE}")
    print("=" * 60)

    print("\n--- WeasyPrint ---")
    wp_times, wp_size = benchmark_weasyprint()

    print("\n--- fpdf2 ---")
    fp_times, fp_size = benchmark_fpdf2()

    # Résultats
    wp_avg = sum(wp_times) / len(wp_times)
    fp_avg = sum(fp_times) / len(fp_times)
    speedup = wp_avg / fp_avg if fp_avg > 0 else 0

    print("\n" + "=" * 60)
    print("RESULTATS (moyenne sur 3 runs, hors warm-up)")
    print("=" * 60)
    print(f"  WeasyPrint : {wp_avg:.3f}s  (taille: {wp_size:,} octets)")
    print(f"  fpdf2      : {fp_avg:.3f}s  (taille: {fp_size:,} octets)")
    print(f"  Ratio      : x{speedup:.1f}")
    print("=" * 60)
    print("\nFICHIERS PDF CONSERVES (dernier run) :")
    print(f"  WeasyPrint : {OUTPUT_DIR / 'benchmark_weasyprint_fpdf2.pdf'}")
    print(f"  fpdf2      : {OUTPUT_DIR / 'benchmark_fpdf2.pdf'}")


if __name__ == "__main__":
    main()
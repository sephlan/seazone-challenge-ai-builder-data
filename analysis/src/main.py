"""
Análise de Investimento Short-Stay — Itapema, SC
Desafio Seazone AI Builder · Parte 1

Execução: uv run python -m src.main
"""

import time
from pathlib import Path

from src.ingest import load_all_datasets, data_quality_report
from src.features import build_listings_enriched, build_listings_revenue
from src.analysis import (
    analyze_best_profile,
    analyze_best_location,
    analyze_revenue_drivers,
    analyze_building_roi,
)


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    timings = {}

    # --- Fase 1: Ingestão e qualidade ---
    t0 = time.perf_counter()
    datasets = load_all_datasets(DATA_DIR)
    data_quality_report(datasets, OUTPUT_DIR)
    timings["fase1_ingestao"] = time.perf_counter() - t0
    print(f"✓ Fase 1 concluída em {timings['fase1_ingestao']:.2f}s")

    # --- Fase 2: Feature engineering ---
    t0 = time.perf_counter()
    listings = build_listings_enriched(datasets)
    revenue = build_listings_revenue(datasets, listings)
    timings["fase2_features"] = time.perf_counter() - t0
    print(f"✓ Fase 2 concluída em {timings['fase2_features']:.2f}s")

    # --- Fase 3: Análises ---
    t0 = time.perf_counter()

    print("\n--- P1: Melhor perfil de imóvel ---")
    analyze_best_profile(revenue, datasets, OUTPUT_DIR)

    print("\n--- P2: Melhor localização ---")
    analyze_best_location(revenue, OUTPUT_DIR)

    print("\n--- P3: Características das melhores receitas ---")
    analyze_revenue_drivers(revenue, OUTPUT_DIR)

    print("\n--- P4/P5: Prédio 50 aptos + ROI ---")
    analyze_building_roi(revenue, datasets, OUTPUT_DIR)

    timings["fase3_analises"] = time.perf_counter() - t0
    print(f"\n✓ Fase 3 concluída em {timings['fase3_analises']:.2f}s")

    # --- Resumo de tempos ---
    total = sum(timings.values())
    print(f"\n{'='*50}")
    print("Tempos de execução:")
    for fase, t in timings.items():
        print(f"  {fase}: {t:.2f}s")
    print(f"  TOTAL: {total:.2f}s")


if __name__ == "__main__":
    main()

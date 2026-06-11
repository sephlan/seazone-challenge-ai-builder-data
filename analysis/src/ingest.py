"""Fase 1 — Ingestão e auditoria de qualidade dos dados."""

import polars as pl
from pathlib import Path


def load_all_datasets(data_dir: Path) -> dict[str, pl.DataFrame]:
    """Carrega os 5 CSVs com tipagem adequada."""

    details = pl.read_csv(
        data_dir / "Details_Itapema.csv",
        infer_schema_length=5000,
        null_values=["<NA>", ""],
    )

    hosts = pl.read_csv(
        data_dir / "Hosts_ids_Itapema.csv",
        infer_schema_length=5000,
        null_values=["<NA>", ""],
    )

    mesh = pl.read_csv(
        data_dir / "Mesh_Ids_Data_Itapema.csv",
        infer_schema_length=5000,
        null_values=["<NA>", ""],
    )

    price = pl.read_csv(
        data_dir / "Price_AV_Itapema.csv",
        infer_schema_length=5000,
        null_values=["<NA>", ""],
    )

    vivareal = pl.read_csv(
        data_dir / "VivaReal_Itapema.csv",
        infer_schema_length=5000,
        null_values=["<NA>", ""],
    )

    return {
        "details": details,
        "hosts": hosts,
        "mesh": mesh,
        "price": price,
        "vivareal": vivareal,
    }


def data_quality_report(datasets: dict[str, pl.DataFrame], output_dir: Path) -> None:
    """Gera relatório de qualidade: shape, nulos, duplicatas, tipos."""

    lines = ["# Relatório de Qualidade dos Dados\n"]

    for name, df in datasets.items():
        lines.append(f"## {name}")
        lines.append(f"- **Shape:** {df.shape[0]} linhas × {df.shape[1]} colunas")

        # Nulos por coluna (top 10)
        null_counts = {
            col: df[col].null_count()
            for col in df.columns
            if df[col].null_count() > 0
        }
        if null_counts:
            sorted_nulls = sorted(null_counts.items(), key=lambda x: -x[1])[:10]
            lines.append("- **Nulos (top 10):**")
            for col, count in sorted_nulls:
                pct = count / df.shape[0] * 100
                lines.append(f"  - `{col}`: {count} ({pct:.1f}%)")
        else:
            lines.append("- **Nulos:** nenhum")

        # Duplicatas na chave primária provável
        if name == "details":
            pk = "airbnb_listing_id"
        elif name == "hosts":
            pk = "owner_id"
        elif name == "mesh":
            pk = "airbnb_listing_id"
        elif name == "price":
            pk = None  # composta
        elif name == "vivareal":
            pk = "listing_id"
        else:
            pk = None

        if pk:
            n_unique = df[pk].n_unique()
            n_total = df.shape[0]
            if n_unique < n_total:
                lines.append(
                    f"- **Duplicatas em `{pk}`:** {n_total - n_unique} "
                    f"({n_total} total, {n_unique} únicos)"
                )
            else:
                lines.append(f"- **Chave `{pk}`:** sem duplicatas")

        if name == "price":
            acq_dates = df["aquisition_date"].cast(pl.Utf8).str.slice(0, 10).unique().sort()
            lines.append(f"- **Datas de aquisição:** {acq_dates.to_list()}")
            stay_min = df["date"].min()
            stay_max = df["date"].max()
            lines.append(f"- **Range de estadia:** {stay_min} a {stay_max}")
            n_listings = df["airbnb_listing_id"].n_unique()
            lines.append(f"- **Listings únicos com preço:** {n_listings}")

        lines.append("")

    report_path = output_dir / "data_quality.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Relatório salvo em {report_path}")

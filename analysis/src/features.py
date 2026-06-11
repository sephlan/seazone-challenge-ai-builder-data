"""Fase 2 — Feature engineering: joins, receita estimada, ocupação."""

import polars as pl
from pathlib import Path


def build_listings_enriched(datasets: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """
    Join Details + Hosts + Mesh (snapshot mais recente por listing).
    Retorna tabela master com perfil completo de cada listing.
    """
    details = datasets["details"]
    hosts = datasets["hosts"]
    mesh = datasets["mesh"]

    # Mesh: manter apenas o snapshot mais recente por listing
    mesh_latest = (
        mesh
        .sort("aquisition_date", descending=True)
        .group_by("airbnb_listing_id")
        .first()
        .select(["airbnb_listing_id", "latitude", "longitude", "suburb"])
    )

    # Hosts: deduplicar por owner_id (manter o com mais reviews)
    hosts = (
        hosts
        .sort("number_of_reviews_host", descending=True, nulls_last=True)
        .group_by("owner_id")
        .first()
    )

    # Cast owner_id para mesmo tipo em ambos
    details_cast = details.with_columns(
        pl.col("owner_id").cast(pl.Utf8).alias("owner_id")
    )
    hosts_cast = hosts.with_columns(
        pl.col("owner_id").cast(pl.Utf8).alias("owner_id")
    )

    # Cast listing_id para mesmo tipo
    details_cast = details_cast.with_columns(
        pl.col("airbnb_listing_id").cast(pl.Utf8).alias("airbnb_listing_id")
    )
    mesh_latest = mesh_latest.with_columns(
        pl.col("airbnb_listing_id").cast(pl.Utf8).alias("airbnb_listing_id")
    )

    # Joins
    enriched = (
        details_cast
        .join(hosts_cast, on="owner_id", how="left", suffix="_host")
        .join(mesh_latest, on="airbnb_listing_id", how="left")
    )

    print(f"  Listings enriquecidos: {enriched.shape[0]} linhas")
    print(f"  Com geolocalização: {enriched.filter(pl.col('suburb').is_not_null()).shape[0]}")
    print(f"  Com dados de host: {enriched.filter(pl.col('is_superhost').is_not_null()).shape[0]}")

    return enriched


def build_listings_revenue(
    datasets: dict[str, pl.DataFrame],
    listings: pl.DataFrame,
) -> pl.DataFrame:
    """
    Calcula receita estimada por listing usando Price_AV.
    
    Estratégia (conforme spec):
    - Usa snapshot mais recente (2025-01-20) como preço resolvido
    - Calcula delta entre snapshots como sinal de yield management
    - Estima ocupação: noites sem registro = ocupadas/bloqueadas
    """
    price = datasets["price"]

    # Cast listing_id
    price = price.with_columns(
        pl.col("airbnb_listing_id").cast(pl.Utf8).alias("airbnb_listing_id")
    )

    # Extrair data de aquisição (só a parte da data)
    price = price.with_columns(
        pl.col("aquisition_date").cast(pl.Utf8).str.slice(0, 10).alias("acq_date")
    )

    # --- Snapshot mais recente (2025-01-20) para receita ---
    latest_snapshot = price.filter(pl.col("acq_date") == "2025-01-20")

    # Se listing não tem dados no snapshot 20, fallback para 07, depois 06
    all_listings_price = price.select("airbnb_listing_id").unique()
    listings_in_20 = latest_snapshot.select("airbnb_listing_id").unique()

    # Para simplificar, usar o snapshot mais recente disponível por listing×date
    price_resolved = (
        price
        .sort("acq_date", descending=True)
        .group_by(["airbnb_listing_id", "date"])
        .first()
    )

    # --- Receita bruta por listing (soma de preços no período) ---
    revenue_per_listing = (
        price_resolved
        .group_by("airbnb_listing_id")
        .agg([
            pl.col("price").sum().alias("receita_bruta_periodo"),
            pl.col("price").median().alias("preco_mediano_noite"),
            pl.col("price").mean().alias("preco_medio_noite"),
            pl.col("price").count().alias("noites_com_preco"),
            pl.col("price").min().alias("preco_min"),
            pl.col("price").max().alias("preco_max"),
        ])
    )

    # --- Período total de estadia: 2025-01-06 a 2025-04-20 = 104 noites ---
    total_noites = 104

    revenue_per_listing = revenue_per_listing.with_columns([
        # Ocupação estimada: noites SEM preço / total = proxy de reservadas
        ((total_noites - pl.col("noites_com_preco")) / total_noites)
            .clip(0, 1)
            .alias("ocupacao_estimada"),
        # Noites disponíveis
        pl.col("noites_com_preco").alias("noites_disponiveis"),
    ])

    # --- Delta entre snapshots (yield management) ---
    # Comparar preço do mesmo listing×date entre aquisição 06 e 20
    snap_06 = price.filter(pl.col("acq_date") == "2025-01-06").select([
        "airbnb_listing_id", "date",
        pl.col("price").alias("price_06"),
    ])
    snap_20 = price.filter(pl.col("acq_date") == "2025-01-20").select([
        "airbnb_listing_id", "date",
        pl.col("price").alias("price_20"),
    ])

    yield_delta = (
        snap_06
        .join(snap_20, on=["airbnb_listing_id", "date"], how="inner")
        .with_columns(
            ((pl.col("price_20") - pl.col("price_06")) / pl.col("price_06") * 100)
            .alias("delta_pct")
        )
        .group_by("airbnb_listing_id")
        .agg([
            pl.col("delta_pct").median().alias("yield_delta_mediano_pct"),
            pl.col("delta_pct").mean().alias("yield_delta_medio_pct"),
        ])
    )

    # --- Join tudo com listings enriquecidos ---
    result = (
        listings
        .join(revenue_per_listing, on="airbnb_listing_id", how="left")
        .join(yield_delta, on="airbnb_listing_id", how="left")
    )

    # Filtrar apenas listings com dados de preço
    with_revenue = result.filter(pl.col("receita_bruta_periodo").is_not_null())
    print(f"  Listings com receita calculada: {with_revenue.shape[0]} / {result.shape[0]}")

    return result

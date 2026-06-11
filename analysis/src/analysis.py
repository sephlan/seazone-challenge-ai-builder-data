"""Fase 3 — Análises: perfil, localização, drivers de receita, ROI."""

import polars as pl
from pathlib import Path


def analyze_best_profile(
    revenue: pl.DataFrame,
    datasets: dict[str, pl.DataFrame],
    output_dir: Path,
) -> None:
    """P1: Melhor perfil de imóvel (bedrooms × listing_type × receita/m²)."""

    df = revenue.filter(pl.col("receita_bruta_periodo").is_not_null())

    # Receita por bedrooms × listing_type
    profile = (
        df
        .group_by(["number_of_bedrooms", "listing_type"])
        .agg([
            pl.col("receita_bruta_periodo").median().alias("receita_mediana"),
            pl.col("receita_bruta_periodo").mean().alias("receita_media"),
            pl.col("preco_mediano_noite").median().alias("diaria_mediana"),
            pl.col("ocupacao_estimada").median().alias("ocupacao_mediana"),
            pl.len().alias("n_listings"),
        ])
        .filter(pl.col("n_listings") >= 10)  # volume mínimo
        .sort("receita_mediana", descending=True)
    )

    print(profile.head(15))

    # Estimativa de m² via VivaReal por bedrooms
    vr = datasets["vivareal"]
    m2_por_bedroom = (
        vr
        .filter(
            pl.col("usable_area").is_not_null()
            & (pl.col("usable_area").cast(pl.Float64) > 20)
            & (pl.col("usable_area").cast(pl.Float64) < 500)
        )
        .with_columns(pl.col("usable_area").cast(pl.Float64).alias("area"))
        .group_by("bedrooms")
        .agg(pl.col("area").median().alias("m2_mediano"))
        .sort("bedrooms")
    )

    print("\nÁrea mediana por bedrooms (VivaReal):")
    print(m2_por_bedroom)

    # Salvar
    profile.write_csv(output_dir / "p1_perfil_imovel.csv")


def analyze_best_location(revenue: pl.DataFrame, output_dir: Path) -> None:
    """P2: Melhor localização por receita mediana (filtro ≥20 listings)."""

    df = revenue.filter(
        pl.col("receita_bruta_periodo").is_not_null()
        & pl.col("suburb").is_not_null()
    )

    location = (
        df
        .group_by("suburb")
        .agg([
            pl.col("receita_bruta_periodo").median().alias("receita_mediana"),
            pl.col("receita_bruta_periodo").mean().alias("receita_media"),
            pl.col("preco_mediano_noite").median().alias("diaria_mediana"),
            pl.col("ocupacao_estimada").median().alias("ocupacao_mediana"),
            pl.col("latitude").median().alias("lat"),
            pl.col("longitude").median().alias("lng"),
            pl.len().alias("n_listings"),
        ])
        .filter(pl.col("n_listings") >= 20)
        .sort("receita_mediana", descending=True)
    )

    print(location)

    location.write_csv(output_dir / "p2_localizacao.csv")


def analyze_revenue_drivers(revenue: pl.DataFrame, output_dir: Path) -> None:
    """P3: O que diferencia os listings de alta receita."""

    df = revenue.filter(pl.col("receita_bruta_periodo").is_not_null())

    # Definir top 20% vs. restante
    p80 = df["receita_bruta_periodo"].quantile(0.80)

    df = df.with_columns(
        pl.when(pl.col("receita_bruta_periodo") >= p80)
        .then(pl.lit("top_20"))
        .otherwise(pl.lit("restante"))
        .alias("segmento")
    )

    # Comparar métricas entre segmentos
    comparison_cols = [
        "star_rating", "number_of_reviews", "number_of_bedrooms",
        "number_of_guests", "number_of_bathrooms", "picture_count",
        "preco_mediano_noite", "ocupacao_estimada",
    ]

    comparison = (
        df
        .group_by("segmento")
        .agg([
            pl.col(c).median().alias(f"{c}_mediana")
            for c in comparison_cols
            if c in df.columns
        ] + [pl.len().alias("n")])
    )

    print(comparison)

    # Superhost vs. não
    if "is_superhost" in df.columns:
        superhost_rev = (
            df
            .group_by("is_superhost")
            .agg([
                pl.col("receita_bruta_periodo").median().alias("receita_mediana"),
                pl.len().alias("n"),
            ])
        )
        print("\nReceita por superhost status:")
        print(superhost_rev)

    # Guest favorite
    if "is_guest_favorite" in df.columns:
        fav_rev = (
            df
            .group_by("is_guest_favorite")
            .agg([
                pl.col("receita_bruta_periodo").median().alias("receita_mediana"),
                pl.len().alias("n"),
            ])
        )
        print("\nReceita por guest_favorite:")
        print(fav_rev)

    # Yield management (delta preço entre snapshots)
    if "yield_delta_mediano_pct" in df.columns:
        yield_comp = (
            df
            .group_by("segmento")
            .agg(
                pl.col("yield_delta_mediano_pct").median().alias("yield_delta_med")
            )
        )
        print("\nYield management por segmento:")
        print(yield_comp)

    comparison.write_csv(output_dir / "p3_drivers_receita.csv")


def analyze_building_roi(
    revenue: pl.DataFrame,
    datasets: dict[str, pl.DataFrame],
    output_dir: Path,
) -> None:
    """P4/P5: Onde construir, como projetar, ROI 2025-2027."""

    df = revenue.filter(
        pl.col("receita_bruta_periodo").is_not_null()
        & pl.col("suburb").is_not_null()
    )
    vr = datasets["vivareal"]

    # --- Decisão: suburb e tipologia (baseada em P1 + P2) ---
    # Selecionar top suburb por receita mediana com volume
    top_suburb = (
        df.group_by("suburb")
        .agg([
            pl.col("receita_bruta_periodo").median().alias("rec_med"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 20)
        .sort("rec_med", descending=True)
        .head(1)["suburb"][0]
    )

    # Selecionar top bedrooms no suburb escolhido
    suburb_data = df.filter(pl.col("suburb") == top_suburb)
    top_beds = (
        suburb_data.group_by("number_of_bedrooms")
        .agg([
            pl.col("receita_bruta_periodo").median().alias("rec_med"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 5)
        .sort("rec_med", descending=True)
        .head(1)["number_of_bedrooms"][0]
    )

    print(f"  Suburb escolhido: {top_suburb}")
    print(f"  Tipologia escolhida: {top_beds} quartos")

    # --- Métricas do segmento escolhido ---
    segmento = suburb_data.filter(pl.col("number_of_bedrooms") == top_beds)
    diaria_mediana = segmento["preco_mediano_noite"].median()
    ocupacao_alta = segmento["ocupacao_estimada"].median()

    print(f"  Diária mediana: R$ {diaria_mediana:.0f}")
    print(f"  Ocupação estimada (alta temporada): {ocupacao_alta:.1%}")

    # --- Custo de aquisição via VivaReal ---
    vr_suburb = vr.filter(
        (pl.col("suburb") == top_suburb)
        & pl.col("sale_price").is_not_null()
        & pl.col("usable_area").is_not_null()
    ).with_columns([
        pl.col("sale_price").cast(pl.Float64).alias("price"),
        pl.col("usable_area").cast(pl.Float64).alias("area"),
    ]).filter(
        (pl.col("area") > 20) & (pl.col("area") < 500) & (pl.col("price") > 100000)
    )

    preco_m2 = (vr_suburb["price"] / vr_suburb["area"]).median()
    m2_mediano = vr_suburb.filter(
        pl.col("bedrooms") == top_beds
    )["area"].median()

    if m2_mediano is None:
        m2_mediano = 80.0  # fallback conservador

    print(f"  Preço/m² VivaReal ({top_suburb}): R$ {preco_m2:,.0f}")
    print(f"  m² mediano ({top_beds}q): {m2_mediano:.0f}")

    # --- Premissas ROI ---
    N_APTOS = 50
    CUSTO_CONSTRUCAO_M2 = 5500  # CUB-SC + margem (benchmark 2025)
    CUSTO_TERRENO_PCT = 0.20  # terreno = ~20% do custo total

    area_por_apto = m2_mediano
    custo_construcao_total = N_APTOS * area_por_apto * CUSTO_CONSTRUCAO_M2
    custo_terreno = custo_construcao_total * CUSTO_TERRENO_PCT
    investimento_total = custo_construcao_total + custo_terreno

    # Sazonalidade: dados cobrem alta (jan-abr)
    # Baixa temporada (mai-dez): ocupação estimada ~40% da alta, diária ~70% da alta
    FATOR_OCUPACAO_BAIXA = 0.40
    FATOR_DIARIA_BAIXA = 0.70
    MESES_ALTA = 4
    MESES_BAIXA = 8

    receita_alta_mensal = diaria_mediana * 30 * ocupacao_alta
    receita_baixa_mensal = diaria_mediana * FATOR_DIARIA_BAIXA * 30 * (ocupacao_alta * FATOR_OCUPACAO_BAIXA)

    receita_bruta_anual_unit = (receita_alta_mensal * MESES_ALTA) + (receita_baixa_mensal * MESES_BAIXA)
    receita_bruta_anual = receita_bruta_anual_unit * N_APTOS

    # Custos operacionais
    COMISSAO_PLATAFORMA = 0.15
    CUSTOS_GESTAO = 0.20  # gestão Seazone
    CONDOMINIO_MENSAL = 800  # estimativa
    IPTU_ANUAL = 2500  # estimativa

    custos_op_unit = (
        receita_bruta_anual_unit * (COMISSAO_PLATAFORMA + CUSTOS_GESTAO)
        + CONDOMINIO_MENSAL * 12
        + IPTU_ANUAL
    )
    custos_op_total = custos_op_unit * N_APTOS

    receita_liquida_anual = receita_bruta_anual - custos_op_total

    # --- ROI 2025, 2026, 2027 ---
    VALORIZACAO_ANUAL = 0.06  # FIPEZAP litoral SC
    INFLACAO = 0.045

    roi_results = []
    for year_offset, year in enumerate([2025, 2026, 2027]):
        fator_val = (1 + VALORIZACAO_ANUAL) ** year_offset
        fator_inf = (1 + INFLACAO) ** year_offset

        receita_liq = receita_liquida_anual * fator_inf
        valor_patrimonio = investimento_total * fator_val
        roi = receita_liq / investimento_total * 100

        roi_results.append({
            "ano": year,
            "receita_bruta_anual": receita_bruta_anual * fator_inf,
            "custos_operacionais": custos_op_total * fator_inf,
            "receita_liquida": receita_liq,
            "investimento_total": investimento_total,
            "valor_patrimonio": valor_patrimonio,
            "roi_pct": roi,
        })

        print(f"\n  {year}:")
        print(f"    Receita bruta: R$ {receita_bruta_anual * fator_inf:,.0f}")
        print(f"    Receita líquida: R$ {receita_liq:,.0f}")
        print(f"    ROI: {roi:.2f}%")

    # --- Resumo ---
    print(f"\n  === RESUMO DO INVESTIMENTO ===")
    print(f"  Local: {top_suburb}")
    print(f"  Tipologia: {top_beds} quartos, {area_por_apto:.0f}m²")
    print(f"  Investimento total (construção + terreno): R$ {investimento_total:,.0f}")
    print(f"  Diária mediana: R$ {diaria_mediana:,.0f}")
    print(f"  Ocupação alta temporada: {ocupacao_alta:.1%}")

    # Salvar
    roi_df = pl.DataFrame(roi_results)
    roi_df.write_csv(output_dir / "p4p5_roi_predio.csv")

    # Premissas em arquivo separado para transparência
    premissas = {
        "suburb": top_suburb,
        "bedrooms": str(top_beds),
        "m2_por_apto": str(area_por_apto),
        "n_aptos": str(N_APTOS),
        "custo_construcao_m2": str(CUSTO_CONSTRUCAO_M2),
        "custo_terreno_pct": str(CUSTO_TERRENO_PCT),
        "investimento_total": str(investimento_total),
        "diaria_mediana": str(diaria_mediana),
        "ocupacao_alta": str(ocupacao_alta),
        "fator_ocupacao_baixa": str(FATOR_OCUPACAO_BAIXA),
        "fator_diaria_baixa": str(FATOR_DIARIA_BAIXA),
        "comissao_plataforma": str(COMISSAO_PLATAFORMA),
        "custos_gestao": str(CUSTOS_GESTAO),
        "valorizacao_anual": str(VALORIZACAO_ANUAL),
        "inflacao": str(INFLACAO),
    }
    premissas_df = pl.DataFrame({"parametro": list(premissas.keys()), "valor": list(premissas.values())})
    premissas_df.write_csv(output_dir / "p4p5_premissas.csv")

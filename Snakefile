# Snakefile: the whole jerboa replication, in the order the results in results/ were produced.
#
#   pixi run snakemake --cores 1             # open data only: GBIF, iNaturalist, WorldClim + CMIP6
#   pixi run snakemake --cores 1 climatedt   # adds ERA5 + Climate DT (needs DestinE upgraded access)
#   pixi run snakemake --cores 1 era5land    # ERA5-Land cross-check (CDS account; the CDS queue is slow)
#   pixi run snakemake --cores 1 -n          # dry run
#
# Downloads go to work/ (not committed). Accounts are read from the usual files, never copied here:
# DestinE ~/.polytopeapirc (Climate DT), CDS ~/.cdsapirc (ERA5-Land). ERA5 comes from the anonymous Microsoft
# Planetary Computer copy; GBIF, iNaturalist, NCBI, OpenStreetMap Nominatim, Europe PMC and WorldClim are open.

W = "work"
DT_MODELS = ["IFS-FESOM", "IFS-NEMO"]
DT_YEARS = range(1991, 2041)
ERA5_YEARS = range(1991, 2021)
OCC = {"": "occurrences", "_occurrences_merged": "occurrences_merged", "_occurrences_genbank": "occurrences_genbank"}


rule all:
    input:
        expand("results/sdm_worldclim{tag}.json", tag=OCC),
        expand("results/null_control_worldclim{tag}.json", tag=OCC),
        "figures/helvaci2025_fig1A_digitised_overlay.png",


rule climatedt:
    input:
        rules.all.input,
        "results/sdm_era5_occurrences_merged.json",
        "results/null_control_era5_occurrences_merged.json",
        "results/resampler_comparison.json",
        "results/doc_figure_climatedt.json",


rule era5land:
    input: expand(f"{W}/era5l/{{year}}.npz", year=ERA5_YEARS)


# ---------- occurrences ----------
rule gbif:
    output: f"{W}/occ/occurrences.parquet", "results/occurrences_summary.json"
    shell: "python pipeline/00_occurrences.py {W}"

rule figure1a:                      # the authors' published map (Europe PMC, CC BY 4.0) and the overlay check
    input: "inputs/literature/helvaci2025_fig1A_digitised.csv"
    output: "figures/helvaci2025_fig1A_digitised_overlay.png"
    shell:
        "python pipeline/digitise/fetch_figure.py {W}/fig && "
        "python pipeline/digitise/fig1_points.py {W}/fig/biology-14-01184-g001.jpg "
        "{W}/fig/fig1A_check.csv {output} && cmp {W}/fig/fig1A_check.csv {input}"

rule genbank_localities:            # committed input; rerun only to check (Nominatim answers can change)
    output: f"{W}/occ/genbank_localities_check.csv"
    shell: "python pipeline/digitise/genbank_localities.py {output}"

rule occurrences_merged:            # GBIF + iNaturalist + the 53 localities digitised from Figure 1A
    input: f"{W}/occ/occurrences.parquet", "inputs/literature/helvaci2025_fig1A_digitised.csv"
    output: f"{W}/occ/occurrences_merged.parquet", "results/occurrences_merged_summary.json"
    shell: "python pipeline/00b_extra_occurrences.py {W}"

rule occurrences_genbank:           # GBIF + iNaturalist + the authors' GenBank localities instead of the map
    input: f"{W}/occ/occurrences.parquet", "inputs/literature_genbank/olgunkaracan2024_genbank_localities.csv"
    output: f"{W}/occ/occurrences_genbank.parquet", "results/occurrences_genbank_summary.json"
    shell: "python pipeline/00b_extra_occurrences.py {W} occurrences_genbank {input[1]}"


# ---------- WorldClim + CMIP6 ----------
rule worldclim:
    output: f"{W}/clim/cells.parquet", f"{W}/clim/worldclim_baseline_1970-2000.parquet"
    shell: "python pipeline/01_worldclim_healpix.py {W}"

rule sdm_worldclim:
    input: f"{W}/clim/worldclim_baseline_1970-2000.parquet", lambda w: f"{W}/occ/{OCC[w.tag]}.parquet"
    output: "results/sdm_worldclim{tag}.json", "results/loss_worldclim{tag}.csv"
    wildcard_constraints: tag="(_occurrences_merged|_occurrences_genbank)?"
    params: occ=lambda w: OCC[w.tag]
    shell: "python pipeline/02_sdm.py {W} worldclim {params.occ}"

rule null_worldclim:
    input: "results/sdm_worldclim{tag}.json"
    output: "results/null_control_worldclim{tag}.json"
    wildcard_constraints: tag="(_occurrences_merged|_occurrences_genbank)?"
    params: occ=lambda w: OCC[w.tag]
    shell: "python pipeline/06_null_control.py {W} worldclim {params.occ}"


# ---------- ERA5 + Climate Digital Twin ----------
rule climatedt_download:            # DestinE upgraded access; resumable, one file per year
    input: f"{W}/clim/cells.parquet"
    output: expand(f"{W}/dt/{{model}}/{{year}}.npz", model=DT_MODELS, year=DT_YEARS)
    shell: " && ".join(f"python pipeline/03_climatedt.py {W} {m}" for m in DT_MODELS)

rule era5_download:                 # Planetary Computer, anonymous; about 25 s a year
    input: f"{W}/clim/cells.parquet"
    output: expand(f"{W}/era5/{{year}}.npz", year=ERA5_YEARS)
    shell: "python pipeline/04b_era5.py {W}"

rule era5land_download:             # CDS; requests in parallel (04_era5land.py is the one-at-a-time version)
    input: f"{W}/clim/cells.parquet"
    output: expand(f"{W}/era5l/{{year}}.npz", year=ERA5_YEARS)
    shell: "python pipeline/04c_era5land_parallel.py {W} 10"

rule bioclim_era5:
    input: rules.era5_download.output, rules.climatedt_download.output
    output: f"{W}/clim/era5_baseline_1991-2020.parquet", "results/bioclim_checks_era5.json"
    shell: "python pipeline/05_bioclim.py {W} era5 " + " ".join(DT_MODELS)

rule sdm_era5:
    input: f"{W}/clim/era5_baseline_1991-2020.parquet", f"{W}/occ/occurrences_merged.parquet"
    output: "results/sdm_era5_occurrences_merged.json", "results/loss_era5_occurrences_merged.csv"
    shell: "python pipeline/02_sdm.py {W} era5 occurrences_merged"

rule null_era5:
    input: "results/sdm_era5_occurrences_merged.json"
    output: "results/null_control_era5_occurrences_merged.json"
    shell: "python pipeline/06_null_control.py {W} era5 occurrences_merged"

rule resamplers:                    # healpix-resample choices against an exact area overlap (needs Climate DT)
    input: f"{W}/clim/cells.parquet"
    output: "results/resampler_comparison.json"
    shell: "python pipeline/90_compare_resamplers.py {W}"


# ---------- figures of the country file (rows + PNGs; the chart code is in docs/country_file/) ----------
rule doc_figures:
    input:
        expand("results/loss_worldclim{tag}.csv", tag=["", "_occurrences_merged"]),
        expand("results/null_control_worldclim{tag}.json", tag=["", "_occurrences_merged"]),
        "results/loss_era5_occurrences_merged.csv", "results/null_control_era5_occurrences_merged.json",
    output:
        "results/doc_figure_loss_vs_null.json", "results/doc_figure_climatedt.json",
        "figures/doc_loss_vs_null.png", "figures/doc_worldclim_vs_climatedt.png",
    shell: "python pipeline/99_doc_figures.py"

# ltool

[![PyPI](https://img.shields.io/pypi/v/ltool.svg)](https://pypi.org/project/ltool/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ltool.svg)](https://pypi.org/project/ltool/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/ltool.svg)](https://pypi.org/project/ltool/)
[![License](https://img.shields.io/pypi/l/ltool.svg)](https://pypi.org/project/ltool/)
<!-- Optional (GitLab-specific). Replace placeholders, then uncomment:
[![pipeline status](https://gitlab.example.org/YOUR_NAMESPACE/YOUR_PROJECT/badges/main/pipeline.svg)](https://gitlab.example.org/YOUR_NAMESPACE/YOUR_PROJECT/-/pipelines)
[![coverage report](https://gitlab.example.org/YOUR_NAMESPACE/YOUR_PROJECT/badges/main/coverage.svg)](https://gitlab.example.org/YOUR_NAMESPACE/YOUR_PROJECT/-/graphs/main/charts)
-->

**ltool** is a layer detection tool based on the **Wavelet Covariance Transform (WCT)** for lidar profile analysis.

It provides:

- A **programmatic Python API** (`get_layers`)
- A **standalone CLI** (`ltool_standalone`) for local processing
- An **SCC/server CLI** (`ltool_scc`) for server-side processing using an `.ini` configuration
- Export of retrieved layers to NetCDF and generation of diagnostic plots

---

## Installation

From PyPI:

```bash
pip install ltool
```

For development:

```bash
pip install -e .
```

---

## Scientific note (WCT sign convention)

ltool uses a derivative-like WCT implementation with a **forward-difference** convention:

> **WCT sign convention:** computed as `final − initial`.  
> Compared to the alternative `initial − final` definition, this results in a **global sign reversal** of the WCT field.  
> All boundary detection logic in ltool is consistent with this convention.

---

## Quick start

### Python API

```python
from ltool.__ltool__ import get_layers

layer_obj = get_layers(
    height=height,
    sig=sig,
    sig_err=sig_err,
    method="optimized_prm",
)

print(layer_obj.layers)
```

Export and plots:

```python
layer_obj.export_to_netcdf(dir_out="/path/to/output", save_netcdf=True)
layer_obj.visualize(dir_out="/path/to/output", save_plots=True)
```

### Standalone CLI

Run on a directory of NetCDF files:

```bash
ltool_standalone \
  --input_path /absolute/path/to/data \
  --method optimized_prm \
  --save_plots \
  --save_netcdf
```

### SCC/server CLI

```bash
ltool_scc \
  --measurement_id 123456 \
  --config_file /absolute/path/to/ltool.ini
```

---

## Layer detection methods

The `--method` option controls how bases/tops are selected. Choices:

- `height_based`
- `wct_based`
- `snr_based`
- `prm_based`
- `optimized_wct`
- `optimized_snr`
- `optimized_prm` (**default**)

See `docs/methods.md` for the full explanation.

---

## Documentation (MkDocs)

Serve docs locally:

```bash
mkdocs serve
```

Build static site:

```bash
mkdocs build
```

### Publish docs on GitLab (GitLab Pages)

This repo includes a ready-to-use **GitLab Pages** pipeline in `.gitlab-ci.yml`.

After pushing to GitLab:
1. Ensure your default branch is `main` (or update the CI rule accordingly).
2. In GitLab, enable **Pages** if your instance requires it (Project → Settings → Pages).
3. The pipeline will build MkDocs and publish the site automatically.

---

## Project layout

Recommended structure:

```text
.
├── pyproject.toml
├── src/
│   └── ltool/
├── examples/
├── docs/
├── mkdocs.yml
└── .gitlab-ci.yml
```

---

## Release (PyPI)

Build:

```bash
rm -rf dist build *.egg-info
python -m build
```

Upload:

```bash
python -m twine upload dist/*
```

---

## License

Add your license information here (e.g., `LICENSE` file and short statement).

---

## Citation

If this project is used in academic work, please cite your related publication/software reference (add details here).

---

## Contact

Maintainer: Your Name  
Your Institute  
Email: your.email@institute.org

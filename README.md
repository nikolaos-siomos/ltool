# ltool

[![PyPI](https://img.shields.io/pypi/v/ltool.svg?cacheSeconds=300)](https://pypi.org/project/ltool/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ltool.svg?cacheSeconds=300)](https://pypi.org/project/ltool/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/ltool.svg?cacheSeconds=300)](https://pypi.org/project/ltool/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue?cacheSeconds=300)](https://nikolaos-siomos.github.io/ltool/)
[![License](https://img.shields.io/github/license/nikolaos-siomos/ltool.svg)](LICENSE)

**Documentation:** https://nikolaos-siomos.github.io/ltool/

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

See `docs/methods/pairing.md` for the full explanation.

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

This project is licensed under the terms of the [ GNU AFFERO GENERAL PUBLIC LICENSE](LICENSE).

---

## Contact

Maintainer: Nikolaos Siomos  
LMU  
Email: nikolaos.siomos@lmu.de

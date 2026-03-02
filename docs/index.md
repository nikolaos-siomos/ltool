# ltool

**ltool** is a layer detection tool based on the **Wavelet Covariance Transform (WCT)**.

This documentation covers:

- The **programmatic API** (`get_layers`)
- The **local CLI** (`ltool_standalone`)
- The **SCC/server CLI** (`ltool_scc`)
- A **Python example** that runs the CLI entry point (`run_ltool.py`)

## Installation

```bash
pip install ltool
```

## Quick start

### CLI

```bash
ltool_standalone --input_path /absolute/path/to/data --save_plots --save_netcdf
```

### Python API

```python
from ltool.__ltool__ import get_layers

layer_obj = get_layers(height=height, sig=sig, sig_err=sig_err)
print(layer_obj.layers)
```

## Where to go next

- **API → [get_layers](api/get_layers.md)**: Programmatic usage and exported outputs
- **CLI → [ltool_standalone](cli/standalone.md)**: local processing of a file or directory
- **CLI → [ltool_scc](cli/scc.md)**: server-mode processing using a configuration file
- **Examples → [Run from python](examples/run_ltool.md)**: call the CLI entry point from Python code

# `examples/run_ltool.py` — Running the standalone CLI from Python

## Overview

This example shows how to call the standalone CLI entry point (`ltool.__ltool_standalone__.main`) **from Python** by passing an `argv` list (the same arguments you’d pass on the command line).

This is useful if you want to:

- integrate ltool into a larger pipeline/script,
- run it programmatically while still using CLI parsing & file handling.

---

## Example

```python
from ltool.__ltool_standalone__ import main as ltool

argv = [
    "--input_path", "/absolute/path/to/SCC/",
    "--include-glob", "*_003_*_elda_*",
    "--method", "optimized_prm",
    "--save_plots",
    "--save_netcdf",
]

geom, obj = ltool(argv)
```

### Return values

- `geom`: geometrical output dataset(s) returned by `export_to_netcdf`  
  - a single element if exactly one file was processed
  - a list if multiple files were processed

- `obj`: the `get_layers` object(s) (same single vs list logic)

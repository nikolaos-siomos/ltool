# `ltool_standalone` — Local CLI tool (`ltool.__ltool_standalone__`)

## Overview

`ltool_standalone` is a command line interface for running ltool on:

- a **single NetCDF file**, or
- a **directory** containing NetCDF files (SCC DB or EARLINET DB format is supported)

This module:
1. Collects CLI settings (via `readers/parse_options.py`)
2. Finds input files (optional include/exclude filters)
3. Reads each profile
4. Runs `get_layers(...)`
5. Optionally saves:
   - plots (`--save_plots`)
   - NetCDF output (`--save_netcdf`)

Entry point (from your `pyproject.toml`):

- `ltool_standalone = "ltool.__ltool_standalone__:main"`

---

## Command line arguments

### Required

- `--input_path` *(absolute path, file or directory)*  
  Absolute path to an input directory or a single input file.

### Layering algorithm

- `--alpha` *(float, default `600.`)*  
  Dilation alpha value in meters.

- `--snr_factor` *(float, default `3.291`)*  
  Signal-to-noise ratio threshold.

- `--wct_peak_margin` *(float, default `0.7`)*  
  WCT peak margin.

- `--method` *(default `optimized_prm`)*  
  Choices (see also the [methods](../methods/pairing.md) section):
  - `height_based`
  - `wct_based`
  - `snr_based`
  - `prm_based`
  - `optimized_wct`
  - `optimized_snr`
  - `optimized_prm`

### Input filtering

If the folder contains multiple files, the can be filtered with the following options based on their filenames:

- `--wavelength` *(str, default `None`)*  
  Choices: `None`, `355`, `532`, `1064`  
  Internally formatted as zero-padded string (e.g. `"0532"`), or `None`.

- `--include-glob` *(repeatable)*  
  Filename glob patterns to include (matched on filename only).  
  Example: `--include-glob '*_elda_*'`

- `--exclude-glob` *(repeatable)*  
  Filename glob patterns to exclude.  
  Example: `--exclude-glob '*quicklook*'`

- `--name-regex` *(str)*  
  Optional regex on filename only.  
  Example: `--name-regex '.*_b(0355|0532).*'`

- `--netcdf-ext` *(repeatable, default `[".nc"]`)*  
  Allowed NetCDF extensions.  
  Example: `--netcdf-ext .nc --netcdf-ext .nc4`

### Output controls

- `--output_folder` *(optional)*  
  Output root folder resolution rules:
  - If omitted: defaults to `<base_dir>/../output_<timestamp>`
  - If relative: resolved relative to `<base_dir>/<output_folder>/output_<timestamp>`
  - If absolute: `<output_folder>/output_<timestamp>`

  Where `base_dir` is:
  - `input_path`, if `input_path` is a directory
  - parent directory of `input_path`, if `input_path` is a file

### Plotting

- `--plot_max_height` *(float, default `15.`)*  
  Max height for y-axis (units depend on `--plot_height_units`).

- `--plot_height_units` *(default `km_asl`)*  
  Choices: `km`, `km_asl`, `km_agl`, `m`, `m_asl`, `m_agl`

- `--plot_product_type` *(default `BSC`)*  
  Choices: `BSC`, `EXT`, `PLDR`, `SIG` (Currently only BSC has been tested)

- `--dpi` *(int, default `100`)*  
  Plot resolution.

### Flags

- `--debug`  
  Print processing stage messages.

- `--show_plots`  
  Show plots interactively.

- `--save_plots`  
  Save plots to disk.

- `--save_netcdf`  
  Save layer output NetCDF to disk.

---

## Minimal CLI example

Run ltool on all `.nc` files in a directory, save plots and netcdf:

```bash
ltool_standalone   --input_path /absolute/path/to/input_dir   --method optimized_prm   --save_plots   --save_netcdf
```

Example with filtering:

```bash
ltool_standalone   --input_path /absolute/path/to/input_dir   --include-glob '*_elda_*'   --exclude-glob '*quicklook*'   --wavelength 532   --method optimized_prm   --save_plots   --save_netcdf
```

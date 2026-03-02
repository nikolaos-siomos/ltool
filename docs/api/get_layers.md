# `ltool.__ltool__` — Programmatic API

## Overview

`ltool.__ltool__.get_layers` is the main programmatic interface of **ltool**.  
It runs the layer detection algorithm on a single lidar profile (product/signal) and computes layer boundaries and derived geometrical properties. The layering technique is based on a [reversed Haar Wavelet Covariance Transform](#wct-sign-convention) (**WCT**).

Typical use:

1. Create a `get_layers` object from `height`, `sig`, `sig_err`
2. Access results from attributes (`layers`, `layer_features`, etc.)
3. Optionally export results:
   - `export_to_netcdf(...)`
   - `visualize(...)`

---

## Class: `get_layers`

### Constructor

```python
from ltool.__ltool__ import get_layers

layer_obj = get_layers(
    height=height,          # 1D array (m_agl)
    sig=sig,                # 1D array
    sig_err=sig_err,        # 1D array
    alpha=600.0,            # default: 600.
    snr_factor=3.291,       # default: 3.291
    wct_peak_margin=0.7,    # default: 0.7
    debug=False,            # default: False
    method="optimized_prm", # default: "optimized_prm"
)
```

### Parameters

- **height** *(1D array-like)*  
  Height grid of the lidar profile (expected units: **m_agl**).

- **sig** *(1D array-like)*  
  Lidar profile values (product or signal).

- **sig_err** *(1D array-like)*  
  Uncertainty of the lidar profile values.

- **alpha** *(float, default `600.`)*  
  WCT dilation parameter **in meters**.

- **snr_factor** *(float, default `3.291`)*  
  Signal-to-noise ratio scaling factor used to validate boundary features.

- **wct_peak_margin** *(float, default `0.7`)*  
  Peak selection threshold used to reject weak adjacent WCT features and pick a single base/top.

- **method** *(str, default `"optimized_prm"`)*  
  Layer boundary selection method (see the available methods [here](../methods/pairing.md)).

- **debug** *(bool, default `False`)*  
  If `True`, prints processing stage messages.

> Note: If `height`, `sig`, `sig_err` are `xarray.DataArray`, they are converted to NumPy arrays internally.

---

## Stored results (object attributes)

Creating `get_layers(...)` computes WCT, candidate features, layer pairing, and derived layer properties. The following attributes are stored on the object.

### Metadata and timing

- **`version`** *(str)*  
  ltool version string.

- **`start_time`** *(datetime)*  
  Timestamp when processing started.

- **`stop_time`** *(datetime)*  
  Timestamp when processing finished.

- **`duration`** *(timedelta)*  
  Total processing time (`stop_time - start_time`).

### Input profile

- **`height`** *(1D array)*
- **`sig`** *(1D array)*
- **`sig_err`** *(1D array)*

### WCT outputs

- **`wct`** *(1D array)*  
  Wavelet covariance transform of the profile.

- **`wct_err`** *(1D array)*  
  WCT uncertainty estimate.

- **`wct_mc`** *(array-like)*  
  Additional WCT Monte Carlo output (as returned by `wct_calculation(...)`).

### Valid range and candidate boundaries

- **`first_valid_idx`** *(int)*  
  Index of first valid height bin.

- **`first_valid_height`** *(float)*  
  Height value at `first_valid_idx`.

- **`all_bases`** *(array-like)*  
  All candidate layer bases detected by the feature selection step.

- **`all_tops`** *(array-like)*  
  All candidate layer tops detected by the feature selection step.

- **`layer_features`** *(array-like)*  
  Final paired base/top features returned by `determine_layer_boundaries(...)`.

### Final layer properties

- **`layers`** *(2D array-like)*  
  Derived layer geometrical properties per layer, computed by
  `calculate_geometrical_properties(...)`.

> The exact content/column meaning of `layers` is determined by the implementation in `layering_functions/geometrical_calculations.py`.

### WCT sign convention
In this implementation we compute the Haar wavelet forward difference convention (final − initial). More specifically, we use the mother wavelet function ψ'(t) = - ψ(t), where ψ(t) is defined according to  https://en.wikipedia.org/wiki/Haar_wavelet  This results in a global sign reversal of the WCT field. Consequently, features that appear as positive peaks according to the standard Haar definition will appear as negative peaks here (and vice versa). Layer boundary detection in ltool is consistent with this convention.

---

## Export and visualization

### `export_to_netcdf(...)`

Exports retrieved layers and selected metadata to an SCC-style NetCDF file.

```python
geom_dataset, fname = layer_obj.export_to_netcdf(
    dir_out="/absolute/path/to/output",
    save_netcdf=True,
    debug=True,
    station_ID="MY_STATION",
    wavelength="532",
    start_time="2026-03-02T00:00:00",
    stop_time="2026-03-02T00:10:00",
    measurement_ID="123456",
    # plus any additional metadata as keyword args:
    operator="me",
    campaign="demo",
)
```

**Key parameters:**
- `dir_out`: output directory
- `save_netcdf`: if `False`, nothing is written (but the dataset may still be created/returned)
- `subfolder`: folder inside `dir_out` (default `"netcdf"`; pass `""` to write directly into `dir_out`)
- `station_ID`, `wavelength`, `start_time`, `stop_time`, `measurement_ID`: used in naming + metadata
- Extra keyword args are added to metadata.

**Returns:**
- `geom_dts`: dataset-like object returned by `export_nc(...)` (or `None` if no layers)
- `fname`: produced file name

---

### `visualize(...)`

Generates a PNG plot showing detected layers against the profile and WCT.

**Important note**
The ploting function has only be tested for backscatter products. The units are converted internally to according to the provided height_units for ploting. Meter units are expected when creating the class object.

```python
png_name = layer_obj.visualize(
    dir_out="/absolute/path/to/output",
    max_height=15.0,
    plot_product_type="BSC",
    show=False,
    save_plots=True,
    station_ID="MY_STATION",
    wavelength="532",
    start_time="2026-03-02T00:00:00",
    stop_time="2026-03-02T00:10:00",
    measurement_ID="123456",
)
```

**Key parameters:**
- `max_height`: y-axis limit
- `height_units`: label units (default `"km_asl"`)
- `dpi_val`: PNG DPI (default `100`)
- `show`: if `True`, displays interactively
- `save_plots`: if `False`, does not write image (but can still display if `show=True`)
- `subfolder`: folder inside `dir_out` (default `"plots"`; pass `""` for direct)

**Returns:**
- `fname`: produced image filename

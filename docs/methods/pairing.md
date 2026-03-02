# Layer Boundary Detection Methods

The `--method` option controls how layer boundaries (bases and tops) are
selected from the Wavelet Covariance Transform (WCT) features.

``` bash
--method optimized_prm
```

**Default:** `optimized_prm`



## Overview

The available methods are:
  - `height_based`
  - `wct_based`
  - `snr_based`
  - `prm_based`
  - `optimized_wct`
  - `optimized_snr`
  - `optimized_prm`

------------------------------------------------------------------------
<br>

**`height_based`:** Selects the lowermost base and the uppermost top as the layer boundaries.

**`wct_based`:** Selects the base and top with the maximum absolute WCT value as the layer boundaries.

**`snr_based`:** Selects the base and top with the maximum SNR value as the layer boundaries.

**`prm_based`:**\
Selects the base and top with the maximum "prominance" value as the layer boundaries. The prominance is define as the difference between the absolute WCT and its corresponding error. The error is calculated by multiplying the snr_factor (defaults to 3.291) with the absolute WCT value of the base/top.

**`optimized_wct`:** Selects the lowermost/uppermost base/top within a certain margin with respect to the corresponding maximum absolute WCT value as the layer boundaries. The margin is provided with the wct_peak_marging parameter (defaults to 70 %). 

**`optimized_snr`:** Selects the lowermost/uppermost base/top within a certain margin with respect to the corresponding maximum SNR value as the layer boundaries. The prominance is define as the difference between the absolute WCT and its corresponding error. The error is calculated by multiplying the snr_factor (defaults to 3.291) with the absolute WCT value of the base/top. The margin is provided with the wct_peak_marging parameter (defaults to 70 %). 

**`optimized_prm`:** Selects the lowermost/uppermost base/top within a certain margin with respect to the corresponding maximum prominance value as the layer boundaries. The prominance is define as the difference between the absolute WCT and its corresponding error. The error is calculated by multiplying the snr_factor (defaults to 3.291) with the absolute WCT value of the base/top. The margin is provided with the wct_peak_marging parameter (defaults to 70 %). 

------------------------------------------------------------------------

# -*- coding: utf-8 -*-
"""
Wavelet covariance transform with externally supplied product errors and
analytical uncertainty propagation.
"""
import numpy as np

def get_first_valid_height(height, sig):
    height = np.asarray(height, dtype=float)
    sig = np.asarray(sig, dtype=float)

    if height.ndim != 1 or sig.ndim != 1:
        raise ValueError("height and sig must be 1D")

    if height.size != sig.size:
        raise ValueError("height and sig must have the same length")

    valid_indices = np.where(np.isfinite(sig))[0]

    if valid_indices.size == 0:
        raise ValueError("signal contains no finite values")

    first_valid_idx = valid_indices[0]
    first_valid_height = height[first_valid_idx]

    return first_valid_idx, first_valid_height

def _integral_linear_weights(height, x0, x1, z_ext=None, ext_idx=None):
    """
    Return weights ``w`` such that ``integral y(z) dz == sum(w * y)`` for a
    piecewise-linear profile over [x0, x1].

    Below ``z_ext``, the value at ``ext_idx`` is extended as a constant.
    No support is provided above the profile top.
    """
    height = np.asarray(height, dtype=float)
    n = height.size
    weights = np.zeros(n, dtype=float)

    if not np.isfinite(x0) or not np.isfinite(x1) or x1 < x0:
        return None
    if x0 == x1:
        return weights
    if x1 > height[-1]:
        return None

    # Constant lower extension.
    if z_ext is not None and ext_idx is not None and x0 < z_ext:
        extension_end = min(x1, z_ext)
        if extension_end > x0:
            weights[ext_idx] += extension_end - x0
        x0 = max(x0, z_ext)

    if x0 >= x1:
        return weights

    if x0 < height[0]:
        x0 = height[0]
    if x0 >= x1:
        return weights

    # Add each overlapping piecewise-linear segment analytically.
    first_segment = max(np.searchsorted(height, x0, side="right") - 1, 0)
    last_segment = min(np.searchsorted(height, x1, side="left"), n - 1)

    for j in range(first_segment, last_segment):
        seg_left = height[j]
        seg_right = height[j + 1]
        a = max(x0, seg_left)
        b = min(x1, seg_right)
        if b <= a:
            continue

        dz = seg_right - seg_left
        ta = (a - seg_left) / dz
        tb = (b - seg_left) / dz
        width = b - a

        # Trapezoid of the linearly interpolated endpoint values.
        weights[j] += 0.5 * width * ((1.0 - ta) + (1.0 - tb))
        weights[j + 1] += 0.5 * width * (ta + tb)

    return weights


def _window_has_constant_step(height, x0, x1, atol=1e-2, rtol=0.0):
    dz = np.diff(height)
    n = len(height)

    if x1 > height[-1] or x1 <= x0:
        return False

    x0_eff = max(x0, height[0])
    if x0_eff >= x1:
        return True

    k0 = np.searchsorted(height, x0_eff, side="right") - 1
    k1 = np.searchsorted(height, x1, side="left") - 1
    k0 = min(max(k0, 0), n - 2)
    k1 = min(max(k1, 0), n - 2)

    local_steps = dz[k0:k1 + 1]
    if local_steps.size == 0:
        return True

    return np.allclose(local_steps, local_steps[0], atol=atol, rtol=rtol)


def wct_calculation(height, product, product_error, alpha,
                    debug=False, step_tol=1e-2):
    """
    Calculate WCT and propagate externally supplied independent errors.

    The WCT at each center is represented as a linear combination of profile
    bins. For independent bin errors ``sigma_j``, the propagated variance is

        Var(WCT) = sum_j (c_j * sigma_j)**2,

    where ``c_j`` is the WCT coefficient of bin ``j``.

    Parameters
    ----------
    height : array-like
        Strictly increasing height coordinate.
    product : array-like
        Product profile. Internal NaNs invalidate WCT windows that touch them.
    product_error : array-like
        Externally supplied one-sigma random error per product bin. Errors are
        assumed independent. A non-finite error invalidates only the propagated
        WCT error for windows that use that bin; the WCT value can remain valid.
    alpha : float
        Full WCT window width in the same units as ``height``.
    debug : bool, optional
        Print masking diagnostics.
    step_tol : float, optional
        Absolute tolerance for local grid-step consistency.

    Returns
    -------
    wct : ndarray
    wct_error : ndarray
    """
    height = np.asarray(height, dtype=float)
    product = np.asarray(product, dtype=float)
    product_error = np.asarray(product_error, dtype=float)

    if height.ndim != 1 or product.ndim != 1 or product_error.ndim != 1:
        raise ValueError("height, product, and product_error must be 1D")
    if not (len(height) == len(product) == len(product_error)):
        raise ValueError("height, product, and product_error must have the same length")
    if np.any(~np.isfinite(height)):
        raise ValueError("height contains non-finite values")
    if np.any(np.diff(height) <= 0):
        raise ValueError("height must be strictly increasing")
    if np.any(np.isfinite(product_error) & (product_error < 0)):
        raise ValueError("product_error contains negative finite values")
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be finite and positive")

    n = product.size
    valid_indices = np.where(np.isfinite(product))[0]
    if valid_indices.size == 0:
        dummy = np.full(n, np.nan)
        return dummy, dummy.copy()

    first_valid_idx = valid_indices[0]
    z_ext = height[first_valid_idx]
    half_alpha = alpha / 2.0

    wct = np.full(n, np.nan)
    wct_error = np.full(n, np.nan)

    below_first_bin_mask = np.zeros(n, dtype=bool)
    lower_ext_mask = np.zeros(n, dtype=bool)
    upper_edge_mask = np.zeros(n, dtype=bool)
    step_mask = np.zeros(n, dtype=bool)
    data_mask = np.zeros(n, dtype=bool)
    error_mask = np.zeros(n, dtype=bool)

    for i, center in enumerate(height):
        x0 = center - half_alpha
        x1 = center
        x2 = center + half_alpha

        if center < z_ext:
            below_first_bin_mask[i] = True
            continue
        if x2 > height[-1]:
            upper_edge_mask[i] = True
            continue
        if x0 < z_ext:
            lower_ext_mask[i] = True

        lower_weights = _integral_linear_weights(
            height, x0, x1, z_ext=z_ext, ext_idx=first_valid_idx
        )
        upper_weights = _integral_linear_weights(
            height, x1, x2, z_ext=z_ext, ext_idx=first_valid_idx
        )
        if lower_weights is None or upper_weights is None:
            data_mask[i] = True
            continue

        coefficients = (upper_weights - lower_weights) / alpha
        used = coefficients != 0.0

        if np.any(~np.isfinite(product[used])):
            data_mask[i] = True
            continue

        wct[i] = np.sum(coefficients[used] * product[used])

        if np.any(~np.isfinite(product_error[used])):
            error_mask[i] = True
        else:
            variance = np.sum((coefficients[used] * product_error[used]) ** 2)
            wct_error[i] = np.sqrt(variance)

        if not _window_has_constant_step(
            height, x0, x2, atol=step_tol, rtol=0.0
        ):
            step_mask[i] = True

    final_wct_mask = below_first_bin_mask | upper_edge_mask | step_mask | data_mask
    wct[final_wct_mask] = np.nan
    wct_error[final_wct_mask | error_mask] = np.nan

    if debug:
        print(f"-- Kept {np.sum(~final_wct_mask)} WCT bins")
        print(f"-- Valid propagated errors at {np.sum(np.isfinite(wct_error))} bins")
        print(f"-- Masked {np.sum(below_first_bin_mask)} bins below first valid height")
        print(f"-- Recovered {np.sum(lower_ext_mask & ~final_wct_mask)} lower-edge bins")
        print(f"-- Masked {np.sum(upper_edge_mask)} upper-edge bins")
        print(f"-- Masked {np.sum(step_mask)} bins due to local step changes")
        print(f"-- Masked {np.sum(data_mask)} bins due to product gaps")
        print(f"-- Error unavailable at {np.sum(error_mask & ~final_wct_mask)} otherwise-valid WCT bins")

    return wct, wct_error

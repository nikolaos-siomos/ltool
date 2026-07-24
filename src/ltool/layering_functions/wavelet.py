# -*- coding: utf-8 -*-
"""
Created on Thu May  5 15:19:16 2016

@author: nick
"""
import numpy as np

def get_first_valid_height(height, sig):
    
    finite_mask = np.isfinite(sig)
    first_valid_idx = np.where(finite_mask)[0][0]
    first_valid_height = height[first_valid_idx]
    
    return(first_valid_idx, first_valid_height)
        
# def wct_calculation(height, product, product_error, alpha, 
#                     n_profiles = 1000, seed = 0, debug = False):
    
#     np.random.seed(seed)
#     # np.testing.assert_almost_equal(height[1:] - height[:-1], height[1] - height[0],decimal=5, verbose = True, err_msg="--Error: The height scale of the provided lidar profile is irregular. Please use a height scale with a constant step")
    
#     if not np.allclose(height[1:] - height[:-1], height[1] - height[0], atol=1e-5):
#         if debug:
#             print("-- Skipping WCT: irregular height grid")
        
#         dummy = np.nan * np.zeros(100)
        
#         return dummy, dummy, dummy

#     step = height[1] - height[0]
    
#     ihalf = int(alpha / (2.* step))
        
#     wct = np.full(len(product), np.nan)
#     wct_err = np.full(len(product), np.nan)
    
#     # Monte Carlo error calculation
#     sig_sim = np.full((n_profiles, len(product)), np.nan)  # initialize with NaNs

#     # valid_mask = ~np.isnan(product) & ~np.isnan(product_error)

#     # # Fill only valid positions
#     # sig_sim[:, valid_mask] = np.random.normal(
#     #     loc=product[valid_mask],
#     #     scale=product_error[valid_mask],
#     #     size=(n_profiles, valid_mask.sum())
#     # )
    
#     first_valid_idx, _ = get_first_valid_height(height, product)

#     # Fill only valid positions
#     sig_sim = np.random.normal(
#         loc=product,
#         scale=product_error,
#         size=(n_profiles, product.size)
#     )
    
#     # Store the original product as the first scenario of Monte Carlo
#     sig_sim[0,:] = product

#     # --- Extrapolate cumtrapz below the first height using sig0 (per-profile) ---
#     sig0 = sig_sim.copy()[:, first_valid_idx]
#     left_prefix = np.nan * np.zeros((sig0.size, ihalf))
#     prefix_steps = np.arange(ihalf, 0, -1, dtype=float)      # ihalf ... 
#     for i in range(ihalf):
#         left_prefix[:,i] = (-prefix_steps[i] * step) * sig0     # (n_profiles, ihalf)
#     integrant = np.concatenate((left_prefix, sig_sim), axis = 1)
#     sig_sim_ = sig_sim.copy()[:,first_valid_idx:]
#     integrant = np.pad(sig_sim_, ((0,0),(ihalf,0)), mode = 'edge')
    
#     # Cumulative trapezoid sum along the product axis
#     trapz_base = np.pad(integrant, ((0,0),(0,1))) + np.pad(integrant, ((0,0),(1,0))) / 2.0
#     mask_nan = (trapz_base != trapz_base)
#     trapz_base[mask_nan] = 0.
#     cumtrapzsum = np.cumsum(trapz_base[:,:-1] * step, axis = 1)
#     cumtrapzsum[mask_nan[:,:-1]] = np.nan
    
#     shifted_up = np.pad(cumtrapzsum,((0,0),(ihalf,0)),constant_values = np.nan)[:,:-ihalf]
#     shifted_dn = np.pad(cumtrapzsum,((0,0),(0,ihalf)),constant_values = np.nan)[:,ihalf:]

#     int_up = shifted_dn - cumtrapzsum
#     int_dn = cumtrapzsum - shifted_up
    
#     wct_mc = (int_up - int_dn) / alpha 
#     wct = wct_mc[0,:]
#     wct_err = np.std(wct_mc[1:,:], axis = 0) 
    
#     wct_mc = np.pad(wct_mc[1:,ihalf:],((0,0),(first_valid_idx,0)),constant_values = np.nan) 
#     wct = np.pad(wct[ihalf:],(first_valid_idx,0),constant_values = np.nan) 
#     wct_err = np.pad(wct_err[ihalf:],(first_valid_idx,0),constant_values = np.nan) 
    
#     return(wct, wct_err, wct_mc)

def _interp_many(z, y2d, x, seg_idx):
    z0 = z[seg_idx]
    z1 = z[seg_idx + 1]

    if z1 == z0:
        return np.full(y2d.shape[0], np.nan)

    t = (x - z0) / (z1 - z0)
    return (1.0 - t) * y2d[:, seg_idx] + t * y2d[:, seg_idx + 1]


def _integral_linear_many(z, y2d, x0, x1, z_ext=None, y_ext=None):
    """
    Integrate many piecewise-linear profiles over [x0, x1].

    If z_ext and y_ext are provided, values below z_ext are extended
    as a constant y_ext for each profile.
    """
    m, n = y2d.shape
    out = np.full(m, np.nan)

    if not np.isfinite(x0) or not np.isfinite(x1) or x1 < x0:
        return out

    if x0 == x1:
        return np.zeros(m)

    # No support above profile top
    if x1 > z[-1]:
        return out

    total = np.zeros(m)

    # Optional constant extension below z_ext
    if z_ext is not None and y_ext is not None and x0 < z_ext:
        xlow = x0
        xhigh = min(x1, z_ext)
        if xhigh > xlow:
            total += y_ext * (xhigh - xlow)
        x0 = max(x0, z_ext)

    # Entire interval handled by lower extension
    if z_ext is not None and y_ext is not None and x1 <= z_ext:
        return total

    # If still below grid start, clamp
    if x0 < z[0]:
        x0 = z[0]

    if x0 >= x1:
        return total

    j0 = np.searchsorted(z, x0, side="right") - 1
    j1 = np.searchsorted(z, x1, side="right") - 1

    j0 = min(max(j0, 0), n - 2)
    j1 = min(max(j1, 0), n - 2)

    # Same segment
    if j0 == j1:
        y0 = _interp_many(z, y2d, x0, j0)
        y1 = _interp_many(z, y2d, x1, j1)
        bad = ~np.isfinite(y0) | ~np.isfinite(y1)
        val = 0.5 * (y0 + y1) * (x1 - x0)
        val[bad] = np.nan
        return total + val

    # First partial segment
    y_x0 = _interp_many(z, y2d, x0, j0)
    y_r0 = y2d[:, j0 + 1]
    first = 0.5 * (y_x0 + y_r0) * (z[j0 + 1] - x0)

    # Full segments
    full = np.zeros(m)
    if j1 > j0 + 1:
        dz = np.diff(z[j0 + 1:j1 + 1])
        y_left = y2d[:, j0 + 1:j1]
        y_right = y2d[:, j0 + 2:j1 + 1]
        full = np.sum(0.5 * (y_left + y_right) * dz[None, :], axis=1)

    # Last partial segment
    y_l1 = y2d[:, j1]
    y_x1 = _interp_many(z, y2d, x1, j1)
    last = 0.5 * (y_l1 + y_x1) * (x1 - z[j1])

    val = first + full + last

    touched_left = j0
    touched_right = j1 + 1
    bad = np.any(~np.isfinite(y2d[:, touched_left:touched_right + 1]), axis=1)
    val[bad] = np.nan

    return total + val


def _window_has_constant_step(height, x0, x1, atol=1e-2, rtol=0.0):
    dz = np.diff(height)
    n = len(height)

    if x1 > height[-1] or x1 <= x0:
        return False

    # below-bottom extrapolated region is ignored for step checking
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
                    n_profiles=1000, seed=0, debug=False,
                    step_tol=1e-2):

    rng = np.random.default_rng(seed)

    height = np.asarray(height, dtype=float)
    product = np.asarray(product, dtype=float)
    product_error = np.asarray(product_error, dtype=float)

    n = product.size

    if height.ndim != 1 or product.ndim != 1 or product_error.ndim != 1:
        raise ValueError("height, product, product_error must be 1D")

    if not (len(height) == len(product) == len(product_error)):
        raise ValueError("height, product, product_error must have same length")

    if np.any(~np.isfinite(height)):
        raise ValueError("height contains non-finite values")

    if np.any(np.diff(height) <= 0):
        raise ValueError("height must be strictly increasing")

    half_alpha = alpha / 2.0

    valid_indices = np.where(np.isfinite(product))[0]
    if valid_indices.size == 0:
        dummy = np.full(n, np.nan)
        return dummy, dummy, np.full((n_profiles - 1, n), np.nan)

    first_valid_idx = valid_indices[0]
    z_ext = height[first_valid_idx]

    sig_sim = rng.normal(
        loc=product,
        scale=product_error,
        size=(n_profiles, n)
    )
    sig_sim[0, :] = product

    # Constant extrapolated value below first valid bin for each MC profile
    y_ext = sig_sim[:, first_valid_idx]

    wct_all = np.full((n_profiles, n), np.nan)

    below_first_bin_mask = np.zeros(n, dtype=bool)
    lower_ext_mask = np.zeros(n, dtype=bool)
    upper_edge_mask = np.zeros(n, dtype=bool)
    step_mask = np.zeros(n, dtype=bool)

    for i, zc in enumerate(height):
        x0 = zc - half_alpha
        x1 = zc
        x2 = zc + half_alpha

        # Do not compute WCT for centers below the first valid bin
        if zc < z_ext:
            below_first_bin_mask[i] = True
            continue

        # Still mask bins whose upper half-window exceeds profile top
        if x2 > height[-1]:
            upper_edge_mask[i] = True
            continue

        # Lower extrapolation is allowed only for valid centers
        if x0 < z_ext:
            lower_ext_mask[i] = True

        int_dn = _integral_linear_many(
            height, sig_sim, x0, x1,
            z_ext=z_ext, y_ext=y_ext
        )
        int_up = _integral_linear_many(
            height, sig_sim, x1, x2,
            z_ext=z_ext, y_ext=y_ext
        )

        wct_all[:, i] = (int_up - int_dn) / alpha

        if not _window_has_constant_step(height, x0, x2, atol=step_tol, rtol=0.0):
            step_mask[i] = True

    final_mask = below_first_bin_mask | upper_edge_mask | step_mask
    wct_all[:, final_mask] = np.nan

    wct = wct_all[0, :]
    wct_err = np.nanstd(wct_all[1:, :], axis=0)
    wct_mc = wct_all[1:, :]

    if debug:
        n_kept = np.sum(~final_mask)
        n_below = np.sum(below_first_bin_mask)
        n_lower_ext = np.sum(lower_ext_mask & ~final_mask)
        n_upper = np.sum(upper_edge_mask)
        n_step = np.sum(step_mask)

        if n_step > 0:
            print("-- WCT computed on irregular grid")
        else:
            print("-- WCT computed on uniform grid")

        print(f"-- Kept {n_kept} bins")
        print(f"-- Masked {n_below} bins below the first valid height")
        print(f"-- Recovered {n_lower_ext} lower-edge bins by constant extrapolation")
        print(f"-- Masked {n_upper} upper-edge bins")
        if n_step > 0:
            print(f"-- Masked {n_step} bins due to local step changes")

    return wct, wct_err, wct_mc
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
        
def wct_calculation(height, product, product_error, alpha, 
                    n_profiles = 1000, seed = 0):
    
    np.random.seed(seed)
    np.testing.assert_almost_equal(height[1:] - height[:-1], height[1] - height[0],decimal=5, verbose = True, err_msg="--Error: The height scale of the provided lidar profile is irregular. Please use a height scale with a constant step")

    step = height[1] - height[0]
    
    ihalf = int(alpha / (2.* step))
        
    wct = np.full(len(product), np.nan)
    wct_err = np.full(len(product), np.nan)
    
    # Monte Carlo error calculation
    sig_sim = np.full((n_profiles, len(product)), np.nan)  # initialize with NaNs

    # valid_mask = ~np.isnan(product) & ~np.isnan(product_error)

    # # Fill only valid positions
    # sig_sim[:, valid_mask] = np.random.normal(
    #     loc=product[valid_mask],
    #     scale=product_error[valid_mask],
    #     size=(n_profiles, valid_mask.sum())
    # )
    
    first_valid_idx, _ = get_first_valid_height(height, product)

    # Fill only valid positions
    sig_sim = np.random.normal(
        loc=product,
        scale=product_error,
        size=(n_profiles, product.size)
    )
    
    # Store the original product as the first scenario of Monte Carlo
    sig_sim[0,:] = product

    # --- Extrapolate cumtrapz below the first height using sig0 (per-profile) ---
    sig0 = sig_sim.copy()[:, first_valid_idx]
    left_prefix = np.nan * np.zeros((sig0.size, ihalf))
    prefix_steps = np.arange(ihalf, 0, -1, dtype=float)      # ihalf ... 
    for i in range(ihalf):
        left_prefix[:,i] = (-prefix_steps[i] * step) * sig0     # (n_profiles, ihalf)
    integrant = np.concatenate((left_prefix, sig_sim), axis = 1)
    sig_sim_ = sig_sim.copy()[:,first_valid_idx:]
    integrant = np.pad(sig_sim_, ((0,0),(ihalf,0)), mode = 'edge')
    
    # Cumulative trapezoid sum along the product axis
    trapz_base = np.pad(integrant, ((0,0),(0,1))) + np.pad(integrant, ((0,0),(1,0))) / 2.0
    mask_nan = (trapz_base != trapz_base)
    trapz_base[mask_nan] = 0.
    cumtrapzsum = np.cumsum(trapz_base[:,:-1] * step, axis = 1)
    cumtrapzsum[mask_nan[:,:-1]] = np.nan
    
    shifted_up = np.pad(cumtrapzsum,((0,0),(ihalf,0)),constant_values = np.nan)[:,:-ihalf]
    shifted_dn = np.pad(cumtrapzsum,((0,0),(0,ihalf)),constant_values = np.nan)[:,ihalf:]

    int_up = shifted_dn - cumtrapzsum
    int_dn = cumtrapzsum - shifted_up
    
    wct_mc = (int_up - int_dn) / alpha 
    wct = wct_mc[0,:]
    wct_err = np.std(wct_mc[1:,:], axis = 0) 
    
    wct_mc = np.pad(wct_mc[1:,ihalf:],((0,0),(first_valid_idx,0)),constant_values = np.nan) 
    wct = np.pad(wct[ihalf:],(first_valid_idx,0),constant_values = np.nan) 
    wct_err = np.pad(wct_err[ihalf:],(first_valid_idx,0),constant_values = np.nan) 
    
    return(wct, wct_err, wct_mc)

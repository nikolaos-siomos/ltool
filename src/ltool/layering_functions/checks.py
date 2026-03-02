#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 16:53:06 2024

@author: nikos
"""

# def height_checks(height, height_units, ground_elevation, alpha):
    
    # valid_units = ['m_asl', 'm_agl', 'm_asl', 'km_asl']
    
    # if height_units not in valid_units:
    #     raise Exception(f"--Error: The provided height_units ({height_units}) are not valid. Please select one of: {valid_units}")
    
    # if ground_elevation is None:
    #     if height_units in ['m_asl', 'km_asl']:
    #         raise Exception("--Error: The ground_elevation must be provided if the height units are m_asl or km_asl. Please provide the ground_elevation argument ")
    #     else:
    #         ground_elevation = 0.
            
    # if height_units in ['m_asl', 'm_agl']:
    #     height = 1E-3 * height
    #     ground_elevation = 1E-3 * ground_elevation

def height_checks(height, height_units, ground_elevation, alpha):
    
    if alpha > 4000.:
        raise Exception(f"--Error: The provided alpha value is too large ({alpha}). Keep in mind that alpha is provided always in meters")

    if alpha < 30.:
        raise Exception(f"--Error: The provided alpha value is too small ({alpha}). Keep in mind that alpha is provided always in meters")
    
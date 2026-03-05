#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:45:16 2026

@author: nikos
"""

import numpy as np

# NumPy 2.x: prefer trapezoid; older NumPy: trapz exists
try:
    trapezoid = np.trapezoid
except AttributeError:
    trapezoid = np.trapz
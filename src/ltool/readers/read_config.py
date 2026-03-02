"""
@author: P. Paschou
"""
import configparser
import re, os
import numpy as np

class config():
    """
    Holds all the configurable variables
    
    Fields
    ===
        directories : Dict[str, str]
            Hold the paths of files
        
    """
    
    def __init__(self, path):
        """Reads the config file at the given path"""
        
        parser = configparser.ConfigParser()
        parser.read(path)
        if os.path.exists(path) == False:
            raise AssertionError(' The configuration file does not exist')

#Database   
        if parser.has_section('database'):
            self.dtb = parser._sections['database']
            for key in self.dtb.keys():
                self.dtb[key] = read_var(self.dtb[key], str)
            
        else:
            raise AssertionError(' The configuration file is missing a database section')

# SCC 
        
        if parser.has_section('scc'):
            self.scc = parser._sections['scc']
            for key in self.scc.keys():
                self.scc[key] = read_var(self.scc[key], str)
            
        else:
            raise AssertionError(' The configuration file is missing an scc section')
        

# -------- END OF CLASS

def read_dictionary_with_dtype(d, keys, func):
    return {
        key: func(value)
        for key, value in d.items()
        if key in keys
    }

def read_var(var, func):
    #converts the var in a certain type (int, float, etc) unless it is ''
    if var != '':
        var = func(var)
    return(var)

def comma_split(var, func):
    
    if var != '':
        var = re.split(',', var)
    
        var = np.array([item.strip() for item in var], 
                       dtype = func) #trimming the spaces
    else:
        var=[]
    return(var)

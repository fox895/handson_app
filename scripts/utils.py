"""
Small utility file to remove code not really part of the analysis.
Helper function
"""

import numpy as np

# Exchange rates
ex_rates = {'GBP': 1.22,
            'EUR': 1.10,
            'USD': 1.0,
            'AED': 0.27,
            'SAR': 0.27,
            'INR': 0.014,
            'DMK': 0.15, #  needs to be checked (assumed Danish Krone)
            'CHF': 1.02,
            'EGP': 0.061,
            'AUD': 0.68,
            'NZD': 0.64,
            'CAD': 0.76,
            'NOK': 0.11,
            'SEK': 0.10,
            'JPY': 0.0094,
            'THR': 1, # needs to be checked
            'RMB': 0.14,
            'ARP': 0.018,
            'CNY': 0.14,
            'SGD': 0.72,
            'ARS': 0.018,
            'ZZZ': 0,
            'MAD': 0.10} 

def to_usd(x):
    '''Converts to USD'''
    currency = x['CURRENCY']
    try:
        new = int(x['GOODS_VALUE'])*ex_rates[currency]
    except:
        new = 0
    return new

def get_pairs(df, A, B, prob_col, impact_col, targ):
    
    try:
        prob = len(df[A & (df[prob_col]==targ)])\
                   / len(df[A])
    except:
        prob = 0
    
    try:
        prob_c = len(df[B & (df[prob_col]==targ)])\
                 / len(df[B])
    except:
        prob_c = np.nan

    risk = prob * df[A & (df[prob_col]==targ)][impact_col].mean() # impact
    risk_c = prob_c * df[B & (df[prob_col]==targ)][impact_col].mean()

    if risk_c == 0:
        return np.nan
    else:
        return risk/risk_c
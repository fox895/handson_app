import pandas as pd
import numpy as np

# read the airports data
airports = pd.read_csv('../data/airports.dat.csv', header=None, index_col=0)

cols = ['NAME', 'CITY', 'AIRPORT_COUNTRY', 'IATA', 'ICAO', 'LATITUDE', 'LONGITUDE', 'ALTITUDE', 'TIMEZONE',
        'DST', 'TIMEZONE', 'TYPE', 'SOURCE']

airports.columns = cols

# read the claims data
df = pd.read_csv('../data/Sample_Cargo_Consignment_Data_CLAIMS.csv')
df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y')

# created origin destination pair columns
df['CONCAT'] = df['ORIGIN'].str.cat(df['DESTINATION'],sep="_")

def get_month(x):
    '''Function for extracting months'''
    return x['DATE'].month


def get_day(x):
    '''Function for extracting days of the week'''
    return x['DATE'].dayofweek



def is_week_day(x):
    ''' Function for finding a week day'''
    if x['DAY'] <= 4:
        return 1
    else:
        return 0

def get_quarter(x):
    '''Function for finding financial quarter'''
    if x['MONTH'] <= 3:
        return 1
    elif x['MONTH'] <= 6:
        return 2
    elif x['MONTH'] <= 9:
        return 3
    elif x['MONTH'] <= 12:
        return 4

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

df.loc[df['GOODS_VALUE']=='NZD', 'GOODS_VALUE'] = 0
df.loc[df['CLAIM']=='DELAYED','CLAIM'] = 'DELAY'

df.loc[:,'MONTH'] = df.apply(get_month, axis=1)
df.loc[:,'DAY'] = df.apply(get_day, axis=1)
df.loc[:,'WEEKDAY'] = df.apply(is_week_day, axis=1)
df.loc[:,'QUARTER'] = df.apply(get_quarter, axis=1)
df['GOODS_VALUE_IN_USD'] = df.apply(to_usd, axis=1)


# merge claims and airport databases
df['AIRLINE'] = df['AIRLINE_PREFIX'].astype(str).str.cat(df['AIRLINE_CODE'],sep="_")
df['GOODS_VALUE'] = df['GOODS_VALUE'].astype(int)
df = df.merge(airports[['IATA', 'AIRPORT_COUNTRY']], left_on='LOCATION', right_on='IATA', how='left')
df['AIRPORT_COUNTRY'] = df['AIRPORT_COUNTRY'].fillna('NO_INFO')

#-----------------------------------------------------------------------------------------
# Riskiness analysis
#-----------------------------------------------------------------------------------------

class Riskiness:
    def __init__(self,
                 col=None,
                 prob_col=None,
                 impact_col=None,
                 func='odds_ratio',
                 data_filter=[]):
        self.col = col
        self.prob_col = prob_col
        self.impact_col = impact_col
        self.func = func
        self.data_filter = data_filter
        
        
        
        
    def get_riskiness(self, df, probability=True):
        col = self.col
        prob_col = self.prob_col
        impact_col = self.impact_col
        func = self.func
        data_filter = self.data_filter

        df_dummy = df.copy()
        
        # feature = col
        # claim = prob_col
        
        # P(claim|feature)*I(claim|feature) / P(claim|~feature)*I(claim|~feature) 
        
        vals = df[col].unique()
        target = pd.get_dummies(df_dummy[prob_col])
        
        rr = pd.DataFrame()
        rr.index.name = col
        
        for val in vals:
            if (len(data_filter)==0) | (val in data_filter):
                
                if func == 'expected_riskiness':
                    rr.loc[val, func] = eval('self.'
                                          +func
                                          +'(df, col, prob_col, impact_col,'
                                          +'target, val)')
                    
                else:
                    for targ in target.columns:
                        result = eval('self.'
                                      +func
                                      +'(df, col, prob_col, impact_col,'
                                      +'targ, val, probability)')
                        if probability:
                            rr.loc[val, targ] = result[0]
                            rr.loc[val, targ+'_p'] = result[1]
                        else:
                            rr.loc[val, targ] = result
                            
        
        return rr
    
    def odds_ratio(self,
                   df,
                   col,
                   prob_col,
                   impact_col,
                   targ,
                   val,
                   probability):
        
        # feature = col
        # claim = prob_col
        
        # P(claim|feature)*I(claim|feature) / P(claim|~feature)*I(claim|~feature) 
        
        prob = len(df[(df[col]==val) & (df[prob_col]==targ)])\
               / len(df[df[col]==val])
               
        prob_c = len(df[(df[col]!=val) & (df[prob_col]==targ)])\
                 / len(df[df[col]!=val])
                 
        risk = prob * df[(df[col]==val) & (df[prob_col]==targ)][impact_col].mean() # impact
        risk_c = prob_c * df[(df[col]!=val) & (df[prob_col]==targ)][impact_col].mean() # impact
                 
        if probability:
            return risk / risk_c, prob/prob_c
        else:
            return risk / risk_c
    
    def relative_riskiness(self,
                           df,
                           col,
                           prob_col,
                           impact_col,
                           targ,
                           val,
                           probability):
        
        # P(claim|feature)*I(claim|feature) / P(claim)*I(claim)
        
        prob = len(df[(df[col]==val) & (df[prob_col]==targ)])\
               / len(df[df[col]==val])
        prob_c = len(df[df[prob_col]==targ])\
                 / len(df[prob_col])
                 
        risk = prob * df[(df[col]==val) & (df[prob_col]==targ)][impact_col].mean() # impact
        risk_c = prob_c * df[df[prob_col]==targ][impact_col].mean() # impact
        
        if probability:
            return risk / risk_c, prob/prob_c
        else:
            return risk / risk_c
        
    def expected_riskiness(self,
                           df,
                           col,
                           prob_col,
                           impact_col,
                           target,
                           val):
        risk = []
        for targ in target.columns:
            exp_risk = len(df[(df[col]==val) & (df[prob_col]==targ)])\
                       / len(df[df[col]==val])\
                       * df[(df[col]==val) & (df[prob_col]==targ)][impact_col].mean()
            if ~np.isnan(exp_risk):
                risk.append(exp_risk) # impact

        return np.sum(risk)

#--------------------------------------------------------------------------------
print(df.head())
columns = ['AIRLINE',
           'LOCATION',
           'AIRPORT_COUNTRY',
           'SHIPPER',
           'CURRENCY',
           'DAY',
           'MONTH',
           'WEEKDAY',
           'LOCATION',
           'ORIGIN',
           'DESTINATION',
           'CONCAT']

alpha = 2


risk_calc = Riskiness(impact_col='GOODS_VALUE_IN_USD', prob_col='CLAIM', func='relative_riskiness')

risky_cols = {}

for col in columns:
    # filter = df[col].value_counts()[df[col].value_counts() > 12].index
    risk_calc.col = col
    
    r = risk_calc.get_riskiness(df,  probability=False)
    
    risky_cols[col] = r[r['DAMAGED'].sort_values(ascending=False) > alpha]['DAMAGED'].index.tolist()

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
pairs = {}

columns = list(risky_cols.keys())

prob_col='CLAIM'
impact_col='GOODS_VALUE_IN_USD'
targ = 'DAMAGED'
alpha = 2

my_index = pd.MultiIndex(levels=[[],[]],
                         codes=[[],[]],
                         names=[u'factor i', u'factor j'])
my_columns = []
risk_pairs = pd.DataFrame(index=my_index, columns=my_columns)
risk_pairs_simple = pd.DataFrame(index=my_index, columns=[])

for targ in df['CLAIM'].unique():
    columns = list(risky_cols.keys())
    for col_i in risky_cols.keys():
        columns.remove(col_i)
        for val_i in risky_cols[col_i]:
            for col_j in columns:
                for val_j in risky_cols[col_j]:
                    A = df[col_i] == val_i
                    B = df[col_j] == val_j
                    C = df[prob_col] == df[prob_col]
                    risk_inc_i_j = (get_pairs(df, (A) & (B), (B), prob_col, impact_col, targ))
                    risk_inc_j_i = (get_pairs(df, (A) & (B), (A), prob_col, impact_col, targ))
                    
                    if (risk_inc_i_j > alpha) & (risk_inc_j_i > 1):
                        name = col_i+':'+str(val_i)+'__'+col_j+':'+str(val_j)
                        pairs[name] = risk_inc_i_j
                        
                        simple_risk = (get_pairs(df, (A) & (B), (C), prob_col, impact_col, targ))
                        
                        risk_pairs_simple.loc[(col_i+':'+str(val_i), col_j+':'+str(val_j)), targ] = simple_risk
                        
                        
risk_pairs_simple.to_csv('extremely_risky_pairs.csv')



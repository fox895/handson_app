"""
Matteo:
I rescructured part of the script to be more manageable. 
I choose to focus on the deployment part of the test.
Nevertheless I applied small modification to the code to suppress warnings and be more readable
(ie lines 74 and 80, creation of utils file)
"""
import os
import sys
import utils
import pandas as pd
import tabulate

from mathlabs import Riskiness

# Fn to be sure to have the right path
def path_fn(filename):
    datafolder = './data/'
    return os.path.join(datafolder, filename)

airport_cols = ['NAME', 'CITY', 'AIRPORT_COUNTRY', 
       'IATA', 'ICAO', 'LATITUDE', 
       'LONGITUDE', 'ALTITUDE', 'TIMEZONE',
       'DST', 'TIMEZONE', 'TYPE', 
       'SOURCE'
       ]

airports = pd.read_csv(
    path_fn('airports.dat.csv'),
    header=None,
    index_col=0,
    )
airports.columns = airport_cols

# Takes the name of the file from the cli call
filename = sys.argv[1]

df = pd.read_csv(path_fn(filename))

df['CONCAT'] = df['ORIGIN'].str.cat(df['DESTINATION'], sep="_")

# Used replace to fix NaN in GOODS_VALUE
df['GOODS_VALUE'] = df['GOODS_VALUE'].replace('NZD', '0').astype(int)
df['GOODS_VALUE_IN_USD'] = df.apply(utils.to_usd, axis=1)

# Ued pd.DatetimeIndex to create dates column more efficiently
df['MONTH'] = pd.DatetimeIndex(df['DATE'], dayfirst=True).month
df['DAY'] = pd.DatetimeIndex(df['DATE'], dayfirst=True).weekday
df['WEEKDAY'] = (df['DAY'] // 5 == 1).astype(int)
df['QUARTER'] = pd.DatetimeIndex(df['DATE'], dayfirst=True).quarter

# merge claims and airport databases
df['AIRLINE'] = df['AIRLINE_PREFIX'].astype(str).str.cat(df['AIRLINE_CODE'],sep="_")

df = df.merge(airports[['IATA', 'AIRPORT_COUNTRY']], left_on='LOCATION', right_on='IATA', how='left')
df['AIRPORT_COUNTRY'] = df['AIRPORT_COUNTRY'].fillna('NO_INFO')

#---------------------------------------------------------
columns = ['AIRLINE', 'LOCATION',
           'AIRPORT_COUNTRY', 'SHIPPER',
           'CURRENCY', 'DAY',
           'MONTH', 'WEEKDAY',
           'LOCATION', 'ORIGIN',
           'DESTINATION', 'CONCAT'
           ]

alpha = 2

#Moved Riskiness to its own file for better management
risk_calc = Riskiness(impact_col='GOODS_VALUE_IN_USD', prob_col='CLAIM', func='relative_riskiness')
risky_cols = {}


for col in columns:
    # Removed this filter as it is not really in use
    # filter = df[col].value_counts()[df[col].value_counts() > 12].index
    risk_calc.col = col
    
    r = risk_calc.get_riskiness(df,  probability=False)
    
    # Rewrote this line to suppress warning as pandas reindex the dataframe after it has been sorted
    # rendering the sorting in the mask not useful at this stage
    # risky_cols[col] = r[r['DAMAGED'].sort_values(ascending=False) > alpha]['DAMAGED'].index.tolist()
    risky_cols[col] = r[r['DAMAGED'] > alpha]['DAMAGED'].index.tolist()


pairs = {}

columns = list(risky_cols.keys())

prob_col='CLAIM'
impact_col='GOODS_VALUE_IN_USD'
targ = 'DAMAGED'


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
                    risk_inc_i_j = (utils.get_pairs(df, (A) & (B), (B), prob_col, impact_col, targ))
                    risk_inc_j_i = (utils.get_pairs(df, (A) & (B), (A), prob_col, impact_col, targ))
                    
                    if (risk_inc_i_j > alpha) & (risk_inc_j_i > 1):
                        name = col_i+':'+str(val_i)+'__'+col_j+':'+str(val_j)
                        pairs[name] = risk_inc_i_j
                        
                        simple_risk = (utils.get_pairs(df, (A) & (B), (C), prob_col, impact_col, targ))
                        
                        risk_pairs_simple.loc[(col_i+':'+str(val_i), col_j+':'+str(val_j)), targ] = simple_risk


# Obtain the current folder path
cwd = os.getcwd()               
# Print to file for download              
risk_pairs_simple.to_csv(os.path.join(cwd, 'data/risky_pairs.csv'))

#Print to STDOUT to be catched by the server
print(risk_pairs_simple.head().to_html(columns=['TOTAL LOSS', 'DAMAGED','DELAY']))


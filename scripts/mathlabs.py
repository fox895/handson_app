import pandas as pd

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
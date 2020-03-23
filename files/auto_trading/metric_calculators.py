# def win_ratio(df):
#     metric=sum(df['pnl_btc']<0)/df.shape[0]
#     return metric

def MDD_calculator(complete_series):
    mdd=0
    complete_series.reset_index(drop=True,inplace=True)
    for i,v in complete_series.iteritems():
        current=v
        future_series=complete_series[i+1::]
        for i,v in future_series.iteritems():
            mdd=max((current-v)/current,mdd)
    return(mdd)

# def growth_btc(df):
#     metric=df.iloc[-1]['capital_btc']
#     return metric

# def MDD_btc(df):
#     metric=MDD_calculator(df['capital_btc'])
#     return metric

def growth_usd(df):
    start=1000
    fin=df.iloc[-1]['capital_usd']
    metric=fin/start 
    return metric

def MDD_usd(df):
    metric=MDD_calculator(df['capital_usd'])
    return metric

# def growth_x_MDD_btc(df):
#     metric=(1-MDD_btc(df))*growth_btc(df)
#     return metric

# def growth_x_MDD_usd(df):
#     metric=(1-MDD_usd(df))*growth_usd(df)
#     return metric


# def growth_over_MDD(df):
#     metric=growth_usd(df)/MDD_usd(df)
#     return(metric)


def growth_by_MDD(df):
    metric=growth_usd(df)/MDD_usd(df)
    return(metric)


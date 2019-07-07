import pandas as pd

# system2 indicator generator
def sys2_indicator_generator(pvec,fast_period,slow_period):
    if slow_period<=fast_period: 
        print("ERROR")
        return
    pvec.rename("price",inplace=True)
    slow=pd.Series(pvec,name='slow').rolling(slow_period).mean()
    fast=pd.Series(pvec,name='fast').rolling(fast_period).mean()
    df=pd.concat([pvec,slow,fast],axis=1)
    return df

# system2 signal generator
def sys2_signal_generator(df):
    df["signal"]="none"
    df.loc[(df['fast']>df['slow']) & (df["price"] > df['slow']),"signal"]="long"
    df.loc[(df['fast']<df['slow']) & (df["price"] > df['slow']),"signal"]="p_long_sf_short"

    df.loc[(df['fast']<df['slow']) & (df["price"] < df['slow']),"signal"]="short"
    df.loc[(df['fast']>df['slow']) & (df["price"] < df['slow']),"signal"]="p_short_sf_long"
    return df

# system2 stoploss generator
def sys2_stoploss_generator(df):
    df['stoploss']=df['slow']
    return df

def sys2_init_detailed(pvec,fast_period,slow_period):
    df=sys2_indicator_generator(pvec,fast_period,slow_period)
    df=sys2_signal_generator(df)
    df=sys2_stoploss_generator(df)
    df=df[slow_period-1:]
    return df

def sys2_init(pvec,fast_period,slow_period):
    df=sys2_init_detailed(pvec,fast_period,slow_period)
    return df
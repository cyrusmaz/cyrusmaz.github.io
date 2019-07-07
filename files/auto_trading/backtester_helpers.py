import pandas as pd
def initialize_trades_dataframes():
    col_names_open =  ['entry_index', 'trade_type',
                       'contracts','margin',
                       'entry_price', 'stoploss',
                       'leverage','liq_price']

    col_names_historic =  ['entry_index','exit_index', 
                           'entry_price', 'exit_price',
                           'trade_type', 
                           'contracts','margin',
                           'stoploss','pnl_usd','pnl_btc',
                           'capital_usd','capital_btc', 'reason4close',
                           'leverage','liq_price']
    trades_open = pd.DataFrame(columns = col_names_open)
    trades_historic=pd.DataFrame(columns = col_names_historic)
    return [trades_open,trades_historic]


# profit/loss calculator 
def profit_calc_usd(amount,entry,exit,trade_type):
    delta=(exit-entry)/entry
    if trade_type=='long': 
        pnl=delta*amount
    elif trade_type=='short': 
        pnl=-delta*amount
#         pnl=0
    else: pnl='error'
    return pnl

def profit_calc_btc(amount,entry,exit,trade_type):
    return usd2btc(profit_calc_usd(amount,entry,exit,trade_type))

# alternative definition as https://www.bitmex.com/app/seriesGuide/XBT
# def profit_calc_btc(amount,entry,exit,trade_type):
#     return amount*(1/entry-1/exit)

#position size calculator
def position_size_calc(risk_tolerance,capital,entry,stoploss):
    WL=risk_tolerance*capital # Willing to Lose
    delta=(stoploss-entry)/entry # percentage change in price if stoploss is triggered
    position_size=abs(WL/delta)
    return (position_size)

def df_index_grab(df,col_name,value):
    return list(df[df[col_name]==value].index.values)

def contracts_leverage_liq_calc_core(trade_type,capital_btc,risk_per_trade,entry_price,stop_loss,max_leverage):
    
    capital_usd=btc2usd(capital_btc,entry_price)
    contracts=position_size_calc(risk_per_trade,capital_usd,entry_price,stop_loss)
    
    leverage=max(1,floor((contracts/capital_usd)*100)/100)
    
    if leverage>max_leverage:
        leverage=max_leverage
        contracts=capital_usd*(max_leverage-0.5) # minus 1 just to be safe (i.e. not put in too large an order)

    if trade_type=='short':
        liq_price=short_liq_calc(entry_price,leverage)
            
    if trade_type=='long':
        liq_price=long_liq_calc(entry_price,leverage)
    return contracts,leverage,liq_price

def contracts_leverage_liq_calc(trade_type,capital_btc,risk_per_trade,entry_price,stoploss,max_leverage):
    contracts,leverage,liq_price=contracts_leverage_liq_calc_core(trade_type,capital_btc,risk_per_trade,entry_price,stoploss,max_leverage)
    
    is_short=False
    if trade_type=='short':
        is_short=True

    # if abs(entry_price-stoploss)<=tau:
    #     # print("tau triggered")
    #     if is_short:
    #         stoploss=entry_price+tau+1
    #         contracts,leverage,liq_price,stoploss=contracts_leverage_liq_calc(trade_type,capital_btc,risk_per_trade,entry_price,stoploss,max_leverage,delta,tau)
    #     elif not is_short:
    #         stoploss=entry_price-tau-1
    #         contracts,leverage,liq_price,stoploss=contracts_leverage_liq_calc(trade_type,capital_btc,risk_per_trade,entry_price,stoploss,max_leverage,delta,tau)

    # if abs(liq_price-stoploss)<=delta:
    #     # print("delta triggered")
    #     max_leverage=max_leverage-1
    #     contracts,leverage,liq_price,stoploss=contracts_leverage_liq_calc(trade_type,capital_btc,risk_per_trade,entry_price,stoploss,max_leverage,delta,tau)


    return contracts,leverage,liq_price, stoploss

def usd2btc(capital_usd,btc_price):
    return (capital_usd/btc_price)

def btc2usd(capital_btc,btc_price):
    return (capital_btc*btc_price)


def margin_btc(position_size,entry_price,leverage):
    margin_btc = ((1/leverage) * position_size + 2 * taker_fee(position_size) )/ entry_price
    return (margin_btc)

def taker_fee(position_size):
    taker_fee= (0.075 / 100 * position_size) 
    return(taker_fee)

init_margin=0.01+2*0.00075
maint_margin=0.005+0.00075

# CHAD CORRECTION:
# Long liquidation price = Average Entry Price / (1 + IM - MM)
# Short liquidation price = Average Entry Price / (1 - (IM - MM))

def long_liq_calc_OLD_WRONG_CHAD(entry,leverage):
    liq=entry*(1-((1/leverage)-maint_margin))
    return liq

def long_liq_calc(entry,leverage):
    liq=entry/(1+((1/leverage)-maint_margin))
    return liq

def short_liq_calc(entry,leverage):
    liq=entry/(1-((1/leverage)-maint_margin))
    return liq


from math import floor
def aggregator(df, period,start=None):
    if period==1: return df
    if start is not None:
        df=df[df['date']>=start]
        df.reset_index(drop=True)
        
    num_rows=df.shape[0]
    num_rows=df.shape[0]
    x=range(0,floor(num_rows/period))
    i=[i*period for i in x]
    i=[j for j in i if j <= num_rows-period]
#     i=list(filter(lambda j: j<num_rows-period+1, i))
    df.iloc[i]['date']


    agg_df=pd.DataFrame(None, index=i, columns=['date','open','high','low','close'])
    agg_df['date']=df.iloc[i]['date']

    for j in i:
        open_=df.loc[j,'open']
        high=max(df.iloc[list(range(j,j+period-1))]['high'].values)
        low=min(df.iloc[list(range(j,j+period-1))]['low'].values)
        close=df.loc[j,'close']
        agg_df.loc[j,'open']=open_
        agg_df.loc[j,'high']=high
        agg_df.loc[j,'low']=low
        agg_df.loc[j,'close']=close
    
    return(agg_df)
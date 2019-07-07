
# coding: utf-8

# In[1]:


import pandas as pd
import random
import numpy as np
import collections
import functools
import uuid 
import time
import sys
import os

from backtester_helpers import *
from system2 import *
from metric_calculators import *

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


# In[2]:


def close_trade(uuid,current_row,reason):
    global trades_open
    global trades_historic
    global capital_usd
    global capital_btc

#     print(current_row)
    exit_index=current_row['index']+start_index+1
    
    if reason=='stoploss_triggered':
        exit_price=trades_open.loc[uuid]['stoploss']
    else:
        exit_price=current_row['price']

    entry_index=trades_open.loc[uuid]['entry_index']
    entry_price=trades_open.loc[uuid]['entry_price']
    stoploss=trades_open.loc[uuid]['stoploss']
    trade_type=trades_open.loc[uuid]['trade_type']
    contracts=trades_open.loc[uuid]['contracts']
    
    leverage=trades_open.loc[uuid]['leverage']
    liq_price=trades_open.loc[uuid]['liq_price']
    margin=trades_open.loc[uuid]['margin']
    
    pnl_usd=profit_calc_usd(contracts,entry_price,exit_price,trade_type)
    pnl_btc=usd2btc(pnl_usd,exit_price)
    
    capital_btc=capital_btc+pnl_btc+margin
    
    if capital_btc<=0:
        print("REKT!!!!!!")
        
    capital_usd=btc2usd(capital_btc,exit_price)


#     col_names_historic =  ['entry_index','exit_index', 
#                        'entry_price', 'exit_price',
#                        'trade_type', 
#                        'contracts','margin',
#                        'stoploss','pnl_usd','pnl_btc',
#                        'capital_usd','capital_btc', 'reason4close',
#                        'leverage','liq_price']

    closed_trade=pd.DataFrame([[entry_index,exit_index,
                                entry_price,exit_price,
                                trade_type,
                                contracts, margin,
                                stoploss,pnl_usd,pnl_btc,
                                capital_usd,capital_btc,reason,
                                leverage, liq_price
                               ]],columns=col_names_historic,index=[uuid])  
    
    trades_open.drop(uuid,inplace=True)
    trades_historic=trades_historic.append(closed_trade,ignore_index=False)

#     print("close {}. Reason: {}. Estimated pnl: {}"
#       .format(trade_type,reason,pnl_btc))

    
def open_trade(current_row):
    global trades_open
    global risk_per_trade
    global capital_usd
    global capital_btc

    entry_price=current_row['price']
    current_index=current_row['index']+start_index+1
    trade_type=current_row['signal']
    stoploss=current_row['stoploss']
    
    capital_usd=btc2usd(capital_btc,entry_price)
    
#   no leverage:  contracts=min(capital,position_size_calc(risk_per_trade,capital,entry_price,stoploss))

    contracts,leverage,liq_price,stoploss=contracts_leverage_liq_calc(trade_type,capital_btc,risk_per_trade,entry_price,stoploss,max_leverage) 

    if trade_type=='short' and liq_price<=stoploss and entry_price<=liq_price :
        print("PROBLEM HERE!!!!")
        print(trade_type)
        print(current_row)
        print("contracts=",contracts,"leverage=",leverage,"liq_price=", liq_price)
        print("t=",s,"k=",l)
        return

    if trade_type=='long'  and liq_price>=stoploss and entry_price>=liq_price :
        print("PROBLEM HERE!!!!")
        print (trade_type)
        print(current_row)
        print("contracts=",contracts,"leverage=",leverage,"liq_price=", liq_price)
        print("t=",s,"k=",l)
        return

    margin=margin_btc(contracts,entry_price,leverage)
    capital_btc=capital_btc-margin
    capital_usd=btc2usd(capital_btc,entry_price)

    new_trade=pd.DataFrame([[current_index,trade_type,contracts,margin,
                             entry_price,stoploss, leverage, liq_price
                            ]],columns=col_names_open,index=[str(uuid.uuid4())])
#     print(new_trade)
    trades_open=trades_open.append(new_trade,ignore_index=False)
    
#     print("open {} contracts {} at {} leverage. set stoploss at {}. liquidation price estimate: {}"
#           .format(contracts,trade_type,leverage,stoploss,liq_price))



def trade_manager(current_row,previous_signal):
    global trades_open
    global trades_historic

    
    current_signal=current_row['signal']
    current_close=current_row['price']
        
    # close trades based on stoplosses
    reason='stoploss_triggered'
    if trades_open.shape[0]!=0:
        long_index=df_index_grab(trades_open,'trade_type','long')
        for i in long_index:
            position=trades_open.loc[i]
            if current_close < position['stoploss']:
                close_trade(i,current_row,reason) 
                
        short_index=df_index_grab(trades_open,'trade_type','short')
        for i in short_index:
            position=trades_open.loc[i]
            if current_close > position['stoploss']:
                close_trade(i,current_row,reason) 
                
                
    long_index=df_index_grab(trades_open,'trade_type','long')
    short_index=df_index_grab(trades_open,'trade_type','short')    
    
    # open/close trades based on signal change
    reason='signal_change'
    if current_signal=='short' and len(short_index)==0: # close longs, open short
#         long_index=df_index_grab(trades_open,'trade_type','long')
        for i in long_index:
            close_trade(i,current_row,reason) 
        open_trade(current_row)
        
    elif current_signal=='long' and len(long_index)==0: # close shorts open long
#         short_index=df_index_grab(trades_open,'trade_type','short')
        for i in short_index:
            close_trade(i,current_row,reason) 
        open_trade(current_row) 
        
    # longs invalidated
    elif (current_signal=='p_long_sf_short' or current_signal=='p_short_sf_long') and previous_signal=='long':
#         long_index=df_index_grab(trades_open,'trade_type','long')
        reason='invalidated'
        for i in long_index:
            close_trade(i,current_row,reason) 
            
    # shorts invalidated
    elif (current_signal=='p_long_sf_short' or current_signal=='p_short_sf_long') and previous_signal=='short':
#         short_index=df_index_grab(trades_open,'trade_type','short')
        reason='invalidated'
        for i in short_index:
            close_trade(i,current_row,reason) 
    
    
def update_stoplosses(current_row):
    global trades_open
    
    current_slow=current_row['slow']

    current_price=current_row['price']
    
    short_index=df_index_grab(trades_open,'trade_type','short')
    for i in short_index:
        current_stoploss=trades_open.loc[i]['stoploss']
        if current_stoploss>current_slow and current_slow>current_price:
            trades_open.loc[i,'stoploss']=current_slow
        
    long_index=df_index_grab(trades_open,'trade_type','long')
    for i in long_index:
        current_stoploss=trades_open.loc[i]['stoploss']
        if current_stoploss<current_slow and current_slow<current_price:
            trades_open.loc[i,'stoploss']=current_slow

def close_all_trades():
    global trades_open
    open_trades_index=list(trades_open.index.values)
    reason='close_all_trades'
    for i in open_trades_index:
        close_trade(i,current_row,reason) 


# In[3]:


# set parameters
price_csv_directory="/home/zadegan/price/"
backtest_results_directory="/home/zadegan/backtest/"


fast_period=int(sys.argv[1])
slow_period=int(sys.argv[2])
risk_per_trade=float(sys.argv[3])
max_leverage=int(sys.argv[4])

start_index=int(sys.argv[5])
end_index=int(sys.argv[6])
price_file_name=sys.argv[7]

    

# In[4]:


# make file paths 
# price_file_name='pnew'
# price_file_name="rprice_1000"
price_csv_filename=price_file_name+".csv"

price_csv_filepath=os.path.join(price_csv_directory, price_csv_filename)

backtest_file_name="{}_fast{}_slow{}_risk{}_maxLev{}_start{}_end{}.csv".format(price_file_name,
                                                                               fast_period,
                                                                               slow_period,
                                                                               risk_per_trade,
                                                                               max_leverage,
                                                                               start_index,
                                                                               end_index)

backtest_file_path=os.path.join(backtest_results_directory, backtest_file_name)


# In[8]:


# load price data
if os.path.isfile(price_csv_filepath):
    pvec=pd.read_csv(price_csv_filepath,squeeze=True)
    print("backtesting {}".format(price_file_name))
else: 
    print("price path invalid")

# pvec
# pvec=pvec[list(range(max(0,start_index-slow_period-5),end_index+1))]


# In[6]:


# df=sys2_init(pvec,fast_period,slow_period)
# df=df.loc[list(range(start_index,end_index))]
# df.reset_index(drop=True,inplace=True)
# df['index']=pd.Series(df.index.values)
# df


# In[7]:


if not os.path.isfile(backtest_file_path):

    pvec=pvec[list(range(max(0,start_index-slow_period-5),end_index+1))]
    
    df=sys2_init(pvec,fast_period,slow_period)
    print(df.shape[0])
    df=df.loc[list(range(max(start_index-1,df.index.values[0]),end_index-1))]
    df.reset_index(drop=True,inplace=True)
    df['index']=pd.Series(df.index.values)
    
    trades_open,trades_historic=initialize_trades_dataframes()

#     capital_initial=1 # BTC value
#     btc_price_initial=df.loc[0]['price']
#     capital_btc=capital_initial
#     capital_usd=btc2usd(capital_btc,btc_price_initial)
    
    capital_initial=1000 # USD value
    btc_price_initial=df.loc[0]['price']
#     print("btc price:{}".format(btc_price_initial))
    capital_usd=capital_initial
#     print("capital USD:{}".format(capital_usd))
    capital_btc=usd2btc(capital_usd,btc_price_initial)
#     print("capital btc:{}".format(capital_btc))
    print(capital_btc)
    
    
    # simulate    
    for i, v in df.iterrows():
#         print(i)
        if i==0: 
            continue
        else:
            previous_signal=df.iloc[i-1]['signal']
            current_row=v 
#             print(v)
            trade_manager(current_row,previous_signal)
            update_stoplosses(current_row)

    close_all_trades()
    trades_historic.to_csv(backtest_file_path)

# elif os.path.isfile(backtest_file_path):
#     trades_historic=pd.read_csv(backtest_file_path,index_col=0)
    


# In[ ]:


# pvec=pvec[list(range(max(0,start_index-slow_period-5),end_index+1))]

# df=sys2_init(pvec,fast_period,slow_period)
# df=df.loc[list(range(max(start_index-1,df.index.values[0]),min(end_index-1,df.shape[0])))]
# df.reset_index(drop=True,inplace=True)
# df['index']=pd.Series(df.index.values)

# trades_open,trades_historic=initialize_trades_dataframes()

# #     capital_initial=1 # BTC value
# #     btc_price_initial=df.loc[0]['price']
# #     capital_btc=capital_initial
# #     capital_usd=btc2usd(capital_btc,btc_price_initial)

# capital_initial=1000 # USD value
# btc_price_initial=df.loc[0]['price']
# print("btc price:{}".format(btc_price_initial))
# capital_usd=capital_initial
# print("capital USD:{}".format(capital_usd))
# capital_btc=usd2btc(capital_usd,btc_price_initial)
# print("capital btc:{}".format(capital_btc))
# print(capital_btc)
# # sys2_init(pvec,fast_period,slow_period)

# # df=sys2_init(pvec,fast_period,slow_period)
# # df
# # # list(range(start_index-1,end_index-1))


# In[ ]:


# trades_historic


# In[ ]:



# s_t=pvec[list(range(0,1094))]
# s_t1=pvec[list(range(1,1095))]

# r=np.divide(s_t1,s_t)
# # 0.0037798533321100392
# np.log(np.divide(s_t1,s_t)).mean()
# # 0.003053919215378171
# np.std(r)
# r.mean()


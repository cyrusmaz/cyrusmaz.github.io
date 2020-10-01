
# coding: utf-8

# In[9]:


import numpy as np
from itertools import product
import math
import pandas as pd
import subprocess
import os
from metric_calculators import *
import sys

price_file_number = int(sys.argv[1])

# In[10]:


backtester_path="/home/maz/backtester_core.py"

backtest_results_directory="/home/maz/backtest/"
heatmap_df_directory = "/home/maz/heatmap"

heatmap_plot_directory_container = "/home/maz/heatmap_plot/"

price_csv_directory="/home/maz/price/"

sf_sequences_directory="/home/maz/sf_sequences_directory/"

growth_directory="/home/maz/growth/"


# In[11]:


# generate and write to disk backtest log for the grid of 'slow' and 'fast' parameter values
def backtest_generator(fast_start,fast_fin,slow_start,slow_fin,risk_per_trade,max_leverage,start_index,end_index,price_file_name):
    fast=list(range(fast_start,fast_fin+1))
    slow=list(range(slow_start,slow_fin+1))
    combos=list(product(fast, slow))
    # remove all combos that have fast>=slow
    filtered_combos = [combo for combo in combos if not combo[0]>=combo[1]]

    # empty dataframe
    # heat_df=pd.DataFrame(None, index=list(range(fast_start,fast_fin+1)), columns=list(range(slow_start,slow_fin+1)))

    for combo in filtered_combos:
        fast_period=combo[0]
        slow_period=combo[1]
        
        backtest_file_name="{}_fast{}_slow{}_risk{}_maxLev{}_start{}_end{}.csv".format(price_file_name,
                                                                                           fast_period,
                                                                                           slow_period,
                                                                                           risk_per_trade,
                                                                                           max_leverage,
                                                                                           start_index,
                                                                                           end_index)
        backtest_file_path=os.path.join(backtest_results_directory, backtest_file_name)

        if not os.path.isfile(backtest_file_path):
            # print("fast:{} slow:{} - BACKTESTING".format(fast_period,slow_period))
            terminal_command="/home/maz/backtest_env/bin/python3 "+ backtester_path + " {} {} {} {} {} {} {}".format(
                        fast_period,
                        slow_period,
                        risk_per_trade,
                        max_leverage,
                        start_index,
                        end_index,
                        price_file_name)
            
            os.system(terminal_command)
#             print(terminal_command)
        # elif os.path.isfile(backtest_file_path):
            # print("fast:{} slow:{} - EXISTS".format(fast_period,slow_period))
#             df=pd.read_csv(backtest_file_path)
    return 


# In[12]:


# generate and return a grid of performance measures for each value of 'slow' and 'fast'
def generalized_heat_df_generator(fast_start,fast_fin,slow_start,slow_fin,risk_per_trade,max_leverage,start_index,end_index,metric_calculator,price_file_name):
    fast=list(range(fast_start,fast_fin+1))
    slow=list(range(slow_start,slow_fin+1))
    combos=list(product(fast, slow))
    # remove all combos that have t>=k
    filtered_combos = [combo for combo in combos if not combo[0]>=combo[1]]
    # empty dataframe
    heat_df=pd.DataFrame(None, index=list(range(fast_start,fast_fin+1)), columns=list(range(slow_start,slow_fin+1)))

    for combo in filtered_combos:
        fast_period=combo[0]
        slow_period=combo[1]
        
        backtest_file_name="{}_fast{}_slow{}_risk{}_maxLev{}_start{}_end{}.csv".format(price_file_name,
                                                                                       fast_period,
                                                                                       slow_period,
                                                                                       risk_per_trade,
                                                                                       max_leverage,
                                                                                       start_index,
                                                                                       end_index)
    
        backtest_file_path=os.path.join(backtest_results_directory, backtest_file_name)
        
        if not os.path.isfile(backtest_file_path):
            heat=None
            print("fast:{} slow:{} - DOES NOT EXIST".format(fast_period,slow_period))
        else:
            df=pd.read_csv(backtest_file_path)
            heat=metric_calculator(df)
        heat_df.loc[fast_period,slow_period]=heat
        
    return heat_df


# In[13]:


# generate, write it to disk, and return heatmap
def heat_df_writer(fast_start,fast_fin,slow_start,slow_fin,risk_per_trade,
                   max_leverage, start_index,end_index,metric_calculator,
                   heatmap_df_directory,price_file_name):
    
    output_file_name = "{}_GROWTH_by_MDD_fast{}_{}_slow{}_{}_risk{}_maxLev{}_start{}_end{}.csv".format(
                                                            price_file_name,
                                                            fast_start,
                                                            fast_fin,
                                                            slow_start,
                                                            slow_fin,
                                                            risk_per_trade,
                                                            max_leverage,
                                                            start_index,
                                                            end_index)

    output_file_path = os.path.join(heatmap_df_directory, output_file_name)
    if not os.path.isfile(output_file_path):
#         print("{} - GENERATING".format(output_file_name))
        heat_df=generalized_heat_df_generator(fast_start,fast_fin,slow_start,slow_fin,risk_per_trade,max_leverage,start_index,end_index,metric_calculator,price_file_name)
        heat_df.to_csv(output_file_path,index=True)
    else:
#         print("{} - EXISTS".format(output_file_name))
        heat_df=pd.read_csv(output_file_path,index_col=0)
    return(heat_df)


# In[14]:


# given a start_index and end_index, do a gridsearch 
# to find and return the optimal 'slow' and 'fast' parameters 
def param_finder(start_index,end_index,price_file_name):
    backtest_generator(fast_start,fast_fin,slow_start,slow_fin,risk_per_trade,max_leverage,start_index,end_index,price_file_name)
    heat_df=heat_df_writer(fast_start,fast_fin,slow_start,slow_fin,risk_per_trade,
                   max_leverage, start_index,end_index,growth_usd,heatmap_df_directory,price_file_name)
    
    max_val=heat_df.max().max()

    max_row=heat_df.max(axis=1)
    max_col=heat_df.max(axis=0)

    best_slow=max_row.idxmax()
    best_fast=int(max_col.idxmax())
    output=[best_slow, best_fast]
    return(output)


# In[15]:


# backtest strategy from start_index to end_index using given slow/fast periods,
# then calculate performance metric of interest on backtest log, and return measure
def performance_calculator(fast_period,slow_period,start_index,end_index,metric_calculator,price_file_name):
    backtest_generator(fast_period,fast_period,
                       slow_period,slow_period,risk_per_trade,max_leverage,start_index,end_index,price_file_name)
    
    backtest_file_name="{}_fast{}_slow{}_risk{}_maxLev{}_start{}_end{}.csv".format(price_file_name,
                                                                                   fast_period,
                                                                                   slow_period,
                                                                                   risk_per_trade,
                                                                                   max_leverage,
                                                                                   start_index,
                                                                                   end_index)
    backtest_file_path=os.path.join(backtest_results_directory, backtest_file_name)
    
    df=pd.read_csv(backtest_file_path)
    measure=metric_calculator(df)
    return(measure)


# In[16]:


# price_csv_filename="pnew"+".csv"

# price_csv_filepath=os.path.join(price_csv_directory, price_csv_filename)
# s=pd.read_csv(price_csv_filepath,squeeze=True)


# In[17]:


fast_start=5
fast_fin=14
slow_start=20
slow_fin=30

risk_per_trade=0.08
max_leverage=30

# start_index=100
# end_index=202

# # param_finder(100,200)

# fast_period=20
# slow_period=40

 



def rolling_backtester(price_file_number):
    training_period=200
    testing_period=100
    
    price_file_name="rprice_"+str(price_file_number)
    
    
    price_csv_filename=price_file_name+".csv"
    price_csv_filepath=os.path.join(price_csv_directory, price_csv_filename)
    
    if os.path.isfile(price_csv_filepath):
        pvec=pd.read_csv(price_csv_filepath,squeeze=True)
    else: 
        print("price path invalid: {}".format(price_file_name))
        return
    length=len(pvec)
    
    growth_total=1
    
    slow_sequence=pd.Series()
    fast_sequence=pd.Series()
    
    train_end_current_index=training_period-1
    
    while train_end_current_index<length-1:
        train_start_index=max(0,train_end_current_index-training_period)
        train_end_index=train_end_current_index
        
        print("train_start: {} , train_end:{}".format(train_start_index,train_end_index))
        
        opt_params=param_finder(train_start_index,train_end_index,price_file_name)
        slow_period=opt_params[1]
        fast_period=opt_params[0]
        
        slow_sequence=pd.concat([slow_sequence,pd.Series(slow_period)])
        fast_sequence=pd.concat([fast_sequence,pd.Series(fast_period)])
        
        print("opt slow:{}, opt fast:{}".format(slow_period,fast_period))
        
        test_start_index=train_end_index
        test_end_index=min(length-1,test_start_index+testing_period)
        
        print("test_start: {} , test_end:{}".format(test_start_index,test_end_index))
        
        if test_end_index-test_start_index<=1: break;
        
        growth_test_set=performance_calculator(fast_period,slow_period,test_start_index,test_end_index,growth_usd,price_file_name)
        growth_total=growth_total*growth_test_set
        
        print("growth:{}".format(growth_total))
        
        train_end_current_index=min(test_end_index-1, length-1)
    
    sf_seq_df = pd.DataFrame({'slow': slow_sequence,
                              'fast': fast_sequence})
    sf_seq_df.reset_index(drop=True,inplace=True)
    
    sf_seq_df_file_name = "{}_train{}_test{}.csv".format(price_file_name,training_period,testing_period)
    sf_seq_df_file_path=os.path.join(sf_sequences_directory, sf_seq_df_file_name)
    
    
    sf_seq_df.to_csv(sf_seq_df_file_path)
    

    
    output=pd.DataFrame.from_dict({'growth': [growth_total],
                             'rprice': [price_file_number]})
    output_path=os.path.join(growth_directory,"rprice_"+str(price_file_number)+".csv")
        
    if not os.path.isfile(output_path):
        output.to_csv(output_path)
    if os.path.isfile(output_path):
        output_path=os.path.join(growth_directory,"rprice_"+str(price_file_number)+"_2.csv")
        output.to_csv(output_path)    
    return(growth_total)
    
    


# rolling_backtester(200,50,'pnew') # 24.576685781399227
# rolling_backtester(200,200,'pnew')


# In[18]:





# In[19]:


# price generation

# def price_simulations(M,T,seed):

# # M=1000

# #     T=1000
#     h=0.1
#     r=0.04
    
#     S0=1000
#     cutoff=10000

#     np.random.seed(500)
#     rejected=0
#     for j in range(0,M):

#         diff=0
#         while diff<cutoff:
#             S=pd.Series(data=0, index=range(0,T+1))
#             S[0]=S0
#             for i in range(0,T):
#                 S[i+1] = np.random.normal(loc=S[i] + r*S[i]*h, scale=0.2*S[i]*np.sqrt(h), size=None)
#             diff=(S.max()-S.min())
#             if (diff<cutoff):
#                 rejected+=1

#         # plt.plot(S)
#         rprice_file_name="rprice_"+str(j)
#         rprice_file_path=os.path.join(price_csv_directory, rprice_file_name+".csv")
#         S.to_csv(rprice_file_path,index=False)



rolling_backtester(price_file_number)

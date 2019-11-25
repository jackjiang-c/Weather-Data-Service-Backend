import pandas as pd
import numpy as np
from pandas import Series,DataFrame,merge
#read in:
df1=pd.read_csv("result_new.csv") 
df2=pd.read_csv("cold_eng.csv")
#temp, humidity change into int type:
df1['humidity_avg'] = df1['humidity_avg'] .astype(int)
df2['Humidity'] = df2['Humidity'] .astype(int)
df1['temp_avg'] = df1['temp_avg'] .astype(int)
df2['Average_temperature'] = df2['Average_temperature'] .astype(int)
#change df2 key name:
df2.rename(columns={'Humidity':'humidity_avg'}, inplace = True)
df2.rename(columns={'Average_temperature':'humidity_avg'}, inplace = True)
#drop duplicates
df1.drop_duplicates(subset='humidity_avg', inplace = True)
df2.drop_duplicates(subset='humidity_avg', inplace = True)
#merge df:
df = pd.merge(df1,df2,left_index=True,right_index=True,how='outer',on=['humidity_avg','temp_avg'])
#output:
df.to_csv('Result_cold.csv')

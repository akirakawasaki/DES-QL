import numpy as np
import pandas as pd

# load configuration
df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
#print(df_cfg[['item']])

#
df = pd.DataFrame(index=[], columns=df_cfg[['item']]) 

NUM_OF_FRAMES = 8

SUP_COM = df_cfg['sup com'].max()
print(SUP_COM)

NUM_OF_ITEMS = len(df_cfg)
print(NUM_OF_ITEMS)

data_idx = 0

for i in range(NUM_OF_FRAMES * SUP_COM):
    ii = data_idx + i
    
    df.loc[ii] = np.nan

    for index in range(3, NUM_OF_ITEMS):
        df.iat[ii, index] = ii * 100 + index


print(df)

df.to_excel('data.xlsx')






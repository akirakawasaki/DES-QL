import numpy as np
import pandas as pd

# load configuration
df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
print(df_cfg[['item']])

#
df = pd.DataFrame(index=[], columns=df_cfg[['item']]) 

df.loc[0] = np.nan
#df.loc[0] = 1
df.loc[1] = 2
df.loc[2] = 3.5
df.loc[3] = np.nan
df.loc[4] = 0.3

for index in range(len(df_cfg[['item']])):
    df.iat[3, index] = index


print(df)

df.to_excel('data.xlsx')






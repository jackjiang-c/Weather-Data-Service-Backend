import pandas as pd

df = pd.read_csv("weatherAUS.csv", usecols=[0, 1, 2, 3, 4, 5, 6, 8, 11, 12, 13, 14, 15, 16], dtype=str)
df['Date'] = pd.to_datetime(df['Date'])
df_list = {}
year = 2009
for i in range(8):
    cur_year = year + i
    mask = (df['Date'] >= str(cur_year) + '-1-1') & (df['Date'] <= str(cur_year) + '-12-31')
    cur_df = df.query('Location=="Sydney"').loc[mask]
    for k in range(1, 13):
        if k == 12:
            mask_month = (df['Date'] >= str(cur_year) + '-' + str(k))
        else:
            mask_month = (df['Date'] >= str(cur_year) + '-' + str(k)) & (df['Date'] < str(cur_year) + '-' + str(k + 1))
        month_df = cur_df.loc[mask_month]
        month_df.drop(['Date','Location'], inplace=True, axis=1)
        month_df = month_df.astype('float32')
        df_list[str(cur_year)+'-'+str(k)] = month_df

df = pd.DataFrame(columns=df_list['2009-1'].columns)

for i, key in enumerate(df_list.keys()):
    df.loc[i] = df_list[key].mean(axis=0, skipna=True)

col_name = ["temp_avg", "rainfall", "evaporation", "sunshine", "windSpeed_avg", "humidity_avg",
                "pressure_avg"]
df_climate = pd.DataFrame(columns=col_name)
df_climate["temp_avg"] = (df["MinTemp"] + df["MaxTemp"]) / 2
df_climate["rainfall"] = df["Rainfall"]
df_climate["evaporation"] = df["Evaporation"]
df_climate["sunshine"] = df["Sunshine"]
df_climate["windSpeed_avg"] = (df["WindSpeed9am"] + df["WindSpeed3pm"]) / 2
df_climate["humidity_avg"] = (df["Humidity9am"] + df["Humidity3pm"]) / 2
df_climate["pressure_avg"] = (df["Pressure9am"] + df["Pressure3pm"]) / 2
df_flu = pd.DataFrame(columns=["flu_percentage_of_year"])
df_new = pd.read_csv("FLU_From01_2009_To12_2017.csv")
df_new.drop(['Year'], inplace=True, axis=1)
total = df_new["Total"]
df_new.drop(['Total'], inplace=True, axis=1)
percents = []
for i in range(8):
    pers = df_new.iloc[i]/total[i]
    percents.extend(pers.to_list())
df_flu["flu_percentage_of_year"] = percents
df_final = pd.concat([df_climate, df_flu],axis=1, sort=False)
df_final = df_final.dropna()
df_final.to_csv('flu_raw.csv', index=False)
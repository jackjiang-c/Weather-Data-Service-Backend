from sklearn.externals import joblib
import pandas as pd

"""
# weather is the input from API
weather = [23.275,0,7.6,0.3,46.5,19.75,65.5,1017.125,7]
col_name = ["temp_avg", "rainfall" ,"evaporation", "sunshine", "windGustSpeed", "windSpeed_avg", "humidity_avg", "pressure_avg", "cloud_avg"]

data = {col_name[i]:weather[i] for i in range(len(weather))}
df_predict = pd.DataFrame(data, index=[0])
#print(df_predict.to_string())


# predict rain tomorrow

model_rain = joblib.load('rain.model')
predict_rain = model_rain.predict(df_predict)
print("The rain of predict is")
print(predict_rain)
print("-----------------------------------")

# predict wind tomorrow
model_wind = joblib.load("wind.model")
predict_wind = model_wind.predict(df_predict)
print("The wind of predict is")
print(predict_wind)
print("-----------------------------------")
# predict temp tomorrow

model_temp = joblib.load("temp.model")
predict_temp = model_temp.predict(df_predict)
print("The temp of predict is")
print(predict_temp)
print("-----------------------------------")
"""

def predictWeather(climate, rain_model_, wind_model_, temp_model_):
    _df_predict = pd.DataFrame(climate, index=[0])
    result = dict()
    result['rain'] = rain_model_.predict(_df_predict)[0]
    result['wind'] = wind_model_.predict(_df_predict)[0]
    result['temp'] = temp_model_.predict(_df_predict)[0]
    return result



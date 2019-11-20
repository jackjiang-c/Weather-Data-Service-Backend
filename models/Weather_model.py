import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.metrics import classification_report
from sklearn.externals import joblib


# data pre-process
df = pd.read_csv("result_new.csv")
df = df[:-1]
X = df.loc[:, :'cloud_avg']
Y = df.loc[:,"tomorrow_rain":]
weather_value = df.tail().loc[:, :"cloud_avg"]
# using random forest regerssor and classifier to make predictions
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, train_size=0.8, random_state=4)


# step1:  predict rainfall

Y_rain_train = Y_train["tomorrow_rain"]
Y_rain_test = Y_test["tomorrow_rain"]

model_rain = RandomForestClassifier(n_estimators=80)
model_rain.fit(X_train, Y_rain_train)
#joblib.dump(model_rain,'rain.model')
#Y_rain_predict = model_rain.predict(X_test)
#print(model_rain.predict(weather_value))
#print(classification_report(Y_rain_test, Y_rain_predict))
#print("--------------------------------------------")

# step2; predict tomorrow_wind
Y_wind_train = Y_train["tomorrow_wind"]
Y_wind_test = Y_test["tomorrow_wind"]
model_wind = RandomForestClassifier(n_estimators=100, max_depth=10)
model_wind.fit(X_train, Y_wind_train)
joblib.dump(model_wind,'wind.model')
#Y_wind_predict = model_wind.predict(X_test)
#print(model_wind.predict(weather_value))
#print(classification_report(Y_wind_test, Y_wind_predict))

#print("--------------------------------------------")

# step3: predict tomorrow_temp
Y_temp_train = Y_train["tomorrow_temp_avg"]
Y_temp_test = Y_test["tomorrow_temp_avg"]
model_temp = RandomForestRegressor(n_estimators=80)
model_temp.fit(X_train, Y_temp_train)
joblib.dump(model_temp,'temp.model')
#Y_temp_predict = model_temp.predict(X_test)
#print(model_temp.predict(weather_value))
#print("For temp random forest model")
#print(r2_score(Y_temp_test, Y_temp_predict))
#print(mean_squared_error(Y_temp_test, Y_temp_predict))
#print("--------------------------------------------")

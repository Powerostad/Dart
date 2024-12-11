import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

#model loading
model = joblib.load('catboost_model.pkl')

#loading new dataset
new_df = pd.read_csv('data/EURUSD_Candlestick_5_M_BID_01.02.2023-17.02.2024.csv')

#cleaning
new_df = new_df[new_df['Volume'] > 0]
new_df.dropna(inplace=True)

new_df['Gmt time'] = pd.to_datetime(new_df['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f', errors='coerce')
print("Before cleaning")
print(new_df['Gmt time'].isna().sum())  

new_df.dropna(subset=['Gmt time'], inplace=True)

print("After cleaning")
print(new_df['Gmt time'].isna().sum())
print(new_df['Gmt time'].dtypes)

new_df['Hour'] = new_df['Gmt time'].dt.hour
new_df['Day'] = new_df['Gmt time'].dt.day

X_new = new_df.drop(columns=['Close'])
y_actual = new_df['Close']

#predicting
y_pred = model.predict(X_new)

#calculate the error
mae = mean_absolute_error(y_actual, y_pred)
rmse = np.sqrt(mean_squared_error(y_actual, y_pred))

print(f"Mean Absolute Error: {mae}")
print(f"Root Mean Squared Error: {rmse}")


#plot
plt.figure(figsize=(10, 5))
plt.plot(y_actual.values, label='Actual', alpha=0.7)
plt.plot(y_pred, label='Predicted', alpha=0.7)
plt.legend()
plt.title('Actual vs Predicted Prices')
plt.show()

print("Prediction complete!")

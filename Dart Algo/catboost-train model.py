import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
import joblib
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

df = pd.read_csv('data/EURUSD_Candlestick_1_D_BID_01.01.2011-08.06.2024.csv')

df = df[df['Volume'] > 0]  
df.dropna(inplace=True) 

#converting the date column to datetime
df['Gmt time'] = pd.to_datetime(df['Gmt time'], dayfirst=True, errors='coerce')

# features and target   
df['Hour'] = df['Gmt time'].dt.hour
df['Day'] = df['Gmt time'].dt.day  

#cleaning the columns
df.dropna(subset=['Gmt time'], inplace=True)

X = df.drop(columns=['Close'])  #features
y = df['Close']                 #target

#split the data to train and test model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#CatBoost Model
model = CatBoostRegressor(iterations=1000, learning_rate=0.1, depth=6, loss_function='RMSE', random_seed=42, verbose=100)

model.fit(X_train, y_train, eval_set=(X_test, y_test), early_stopping_rounds=50)

joblib.dump(model, 'catboost_model.pkl')

#cleaning the data once more
df.to_csv('cleaned_data.csv', index=False)

#plot
y_pred = model.predict(X_test)
plt.figure(figsize=(10, 5))
plt.plot(y_test.values, label='Actual', alpha=0.7)
plt.plot(y_pred, label='Predicted', alpha=0.7)
plt.legend()
plt.title('Actual vs Predicted Prices')
plt.show()

print("Training complete and model saved!")
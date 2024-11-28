import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
from fpdf import FPDF

# DataSet Uploading
file_path = 'data\\EURUSD_Candlestick_1_D_BID_01.01.2011-08.06.2024.csv'

try:
    data = pd.read_csv(file_path)
    print("Data loaded successfully.")
except FileNotFoundError:
    print("Error: File not found. Check the file path.")
    exit()

# Print first few records to check structure
print("First 5 records:")
print(data.head())

# Convert date column and delete it
if 'Gmt time' in data.columns:
    data['Date'] = pd.to_datetime(data['Gmt time'].str.split(' ').str[0], format="%d.%m.%Y")
    data.drop(['Date', 'Gmt time'], axis=1, inplace=True)  # حذف ستون تاریخ
    print("Date conversion successful.")
else:
    print("Error: 'Gmt time' column not found.")
    exit()

# Drop missing values
data.dropna(inplace=True)

# Convert columns to float
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
    if col in data.columns:
        data[col] = data[col].astype(float)
    else:
        print(f"Error: Column '{col}' not found in data.")
        exit()

# Split data into features and target
X = data[['Open', 'High', 'Low', 'Volume']]
y = data['Close']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("Data split into training and testing sets.")

# Create and train model
gbmModel = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
gbmModel.fit(X_train, y_train)
print("Model training completed.")

# Predictions
y_pred = gbmModel.predict(X_test)

# Calculate error metrics
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

print(f"\nMean Squared Error: {mse:.2f}")
print(f"Root Mean Squared Error: {rmse:.2f}")
print(f"R² Score: {r2:.2f}")
print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")

# Generate PDF report
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=14)
pdf.cell(200, 10, txt="Bitcoin Price Prediction Results", ln=True, align='C')
pdf.cell(200, 10, txt=f"Mean Squared Error: {mse:.2f}", ln=True, align='L')
pdf.cell(200, 10, txt=f"Root Mean Squared Error: {rmse:.2f}", ln=True, align='L')
pdf.cell(200, 10, txt=f"R² Score: {r2:.2f}", ln=True, align='L')
pdf.cell(200, 10, txt=f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%", ln=True, align='L')
output_path = 'Prediction_Report.pdf'
pdf.output(output_path)
print(f"PDF report saved at: {output_path}")

# Plot actual vs predicted values
plt.figure(figsize=(10, 5))
plt.plot(y_test.values[:100], label='Actual', color='b')
plt.plot(y_pred[:100], label='Predicted', color='r')
plt.xlabel('Data Points')
plt.ylabel('Bitcoin Price')
plt.title('Comparison of Actual and Predicted Prices (First 100 Records)')
plt.legend()
plt.show()

# Plot residuals
residuals = y_test.values - y_pred
plt.figure(figsize=(10, 5))
plt.scatter(y_pred, residuals)
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel('Predicted Values')
plt.ylabel('Residuals')
plt.title('Residual Plot')
plt.show()

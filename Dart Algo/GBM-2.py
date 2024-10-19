import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split  # for splitting data into test cases
from sklearn.ensemble import GradientBoostingRegressor  # class for creating a boosting gradient model for regression
from sklearn.metrics import mean_squared_error, r2_score  # for calculating Mean Squared Error and R² Score
from fpdf import FPDF

# DataSet Uploading
file_path = 'BTC-USD.csv'
data = pd.read_csv(file_path)

print("First 5 records")
print(data.head())

# Converting date column and deleting (all we need is numerical data)
data['Date'] = pd.to_datetime(data['Date'])
data.drop('Date', axis=1, inplace=True)  # حذف ستون تاریخ

# Delete cells with missing data
data.dropna(inplace=True)

# Check data type and converting them
data['Open'] = data['Open'].astype(float)
data['High'] = data['High'].astype(float)
data['Low'] = data['Low'].astype(float)
data['Close'] = data['Close'].astype(float)
data['Volume'] = data['Volume'].astype(float)

# Choose attributes (X) and Goal (Y)
X = data[['Open', 'High', 'Low', 'Volume']]  # attributes
y = data['Close']  # goal

# Splitting data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Creating the GBM Model (better be for regression to work with crypto)
gbmModel = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)

# Training model
gbmModel.fit(X_train, y_train)

# Prediction
y_pred = gbmModel.predict(X_test)

# Calculate error
mse = mean_squared_error(y_test, y_pred, squared=False)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100   #درصد خطا

print(f"\nMean Squared Error: {mse:.2f}")
print(f"Root Mean Squared Error: {rmse:.2f}")
print(f"R² Score: {r2:.2f}")
print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")

# Create PDF file + add data
pdf = FPDF()
pdf.add_page()

pdf.set_font("Arial", size=14)
pdf.cell(200, 10, txt="Bitcoin Price Prediction Results", ln=True, align='C')
pdf.cell(200, 10, txt=f"Mean Squared Error: {mse:.2f}", ln=True, align='L')
pdf.cell(200, 10, txt=f"Root Mean Squared Error: {rmse:.2f}", ln=True, align='L')
pdf.cell(200, 10, txt=f"R² Score: {r2:.2f}", ln=True, align='L')
pdf.cell(200, 10, txt="Predicted vs Actual (First 100 Records):", ln=True, align='L')

# Print 100 records of predictions and real data
num_records = min(100, len(y_test))
for i in range(num_records):
    predicted = f"Predicted: {y_pred[i]:.2f}, Actual: {y_test.iloc[i]:.2f}"
    pdf.cell(200, 10, txt=predicted, ln=True, align='L')

# Save the PDF file
output_path = r'BTC_Prediction_Report.pdf'
pdf.output(output_path)
print(f"PDF report saved at: {output_path}")

# Plot comparison of actual and predicted values
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
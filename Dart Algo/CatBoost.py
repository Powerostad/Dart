import pandas as pd
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# بارگذاری دیتا‌ست
file_path = 'BTC-USD.csv'
data = pd.read_csv(file_path)

# نمایش اولین چند رکورد از دیتا‌ست برای اطمینان از بارگذاری صحیح
print("first 5 records")
print(data.head())

# جداسازی ستون هدف و ویژگی‌ها
# فرض می‌کنیم ستون هدف 'target' نام دارد
X = data.drop('target', axis=1)
y = data['target']

# پیدا کردن ستون‌های دسته‌ای
categorical_features = X.select_dtypes(include=['object']).columns.tolist()

# تقسیم‌بندی داده‌ها به داده‌های آموزشی و تست
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ایجاد مدل CatBoostRegressor
model = CatBoostRegressor(iterations=1000, learning_rate=0.1, depth=6, random_seed=42, verbose=100)

# آموزش مدل با ویژگی‌های دسته‌ای مشخص شده
model.fit(X_train, y_train, cat_features=categorical_features)

# پیش‌بینی روی داده‌های تست
y_pred = model.predict(X_test)

# ارزیابی مدل
mse = mean_squared_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse:.2f}")
print(f"Root Mean Squared Error: {rmse:.2f}")
print(f"R² Score: {r2:.2f}")

# ذخیره مدل آموزش دیده
model.save_model('catboost_model.cbm')

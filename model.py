import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# 1. Load your data
df = pd.read_csv('danger_heart_rate_data.csv')

# 2. Define Features (X) and Target (y)
# Note: The CSV uses 'danger_type' to describe the risk
X = df[['age', 'bpm', 'activity', 'stress_level']]
y = df['danger_type']

# 3. Preprocessing Setup
# Numeric columns need scaling; Categorical columns need encoding
numeric_features = ['age', 'bpm']
categorical_features = ['activity', 'stress_level']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# 4. Create the Pipeline
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 5. Train the model
pipeline.fit(X, y)

# 6. Save the model for your Flask app
joblib.dump(pipeline, 'heart_danger_pipeline.pkl')
print("Model trained successfully and saved as 'heart_danger_pipeline.pkl'")

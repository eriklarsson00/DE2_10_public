# -*- coding: utf-8 -*-
"""Final_all_models.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1kiOuIIyalLvgzL8NHjQjmrYt5R-XUiHB
"""

#!pip install ray[tune]

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from ray.tune.schedulers import ASHAScheduler
from ray.air import session
from datetime import datetime
from sklearn.ensemble import BaggingRegressor
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
# from skopt import BayesSearchCV
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import joblib
import ray
from ray import train, tune
# ray.shutdown()

start_time = datetime.now()
# Load the dataset
file_path = 'combined.csv'
data = pd.read_csv(file_path)

# Drop columns and handle missing values
data = data.drop(columns=['language', 'license', 'topics'], axis=1)
data = data.dropna().reset_index(drop=True)

main_test = pd.read_csv("5datapoints.csv")
drop = [i for i in main_test['full_name']]
# Step 3: Drop rows where 'full_name' is in values_to_drop
data = data[~data['full_name'].isin(drop)]

numerical_data = data.select_dtypes(exclude=['object'])
# Define the target column
### --------------------------------------------------- Grid search -----------------------------------------------------------
# Use ASHAScheduler for early stopping
scheduler = ASHAScheduler(metric="r2", mode="max")

ray.init(ignore_reinit_error=True)

df = numerical_data
X_original = df.drop(columns=['stars'], axis=1)
y_original = df['stars']
# X_original.describe()

# X_original, X_main_test, y_original, y_main_test = train_test_split(X_original, y_original, test_size=0.0025, random_state=42)
X_not_oversampled1, X_test, y_not_oversampled1, y_test = train_test_split(X_original, y_original, test_size=0.15, random_state=42)
X_not_oversampled, X_validation, y_not_oversampled, y_validation = train_test_split(X_not_oversampled1, y_not_oversampled1, test_size=0.15, random_state=42)
X, y = X_not_oversampled, y_not_oversampled

# Define the training function for bagging
def train_bg(config):
    bcTree = DecisionTreeRegressor()
    bc = BaggingRegressor(bcTree, n_estimators=config['n_estimators'], oob_score=True, random_state=42, max_samples=config['max_samples'], max_features=config['max_features'])
    bc.fit(X, y)
    y_pred = bc.predict(X_validation)
    accuracy= r2_score(y_validation, y_pred)
    train.report({"r2":accuracy})

# Set up the hyperparameter search space
bagging_config_space = {
    "n_estimators": tune.grid_search([150, 300]),
    "max_samples": tune.grid_search([0.8, 1.0]),
    "max_features": tune.grid_search([0.9, 1.0]),
}

def train_rf1(config):
    rf = RandomForestRegressor(
        n_estimators=config['n_estimators'],
        max_depth=config['max_depth'],
        max_features=config['max_features'],
        random_state=42
    )
    rf.fit(X, y)
    y_pred = rf.predict(X_validation)
    accuracy = r2_score(y_validation, y_pred)
    train.report({"r2": accuracy})

# Set up the hyperparameter search space
rf_config_space = {
    "n_estimators": tune.grid_search([150, 300]),
    "max_depth": tune.grid_search([10, 20, None]),
    "max_features": tune.grid_search([0.8, 1.0]),
}
# Define the training function for adaboost
def train_adaboost(config):
    adaboost_model = AdaBoostRegressor(
        n_estimators=config['n_estimators'],
        learning_rate=config['learning_rate'],
        random_state=42
    )
    adaboost_model.fit(X, y)
    y_pred = adaboost_model.predict(X_validation)
    accuracy = r2_score(y_validation, y_pred)
    train.report({"r2":accuracy})

adaboost_config_space = {
    "n_estimators": tune.grid_search([50, 100]),
    "learning_rate": tune.grid_search([0.1, 0.2])
}
# Define the training function for gradient
def train_gradboost(config):
    gradboost_model = GradientBoostingRegressor(
        learning_rate=config['learning_rate'],
        n_estimators=config['n_estimators']
    )
    gradboost_model.fit(X, y)
    y_pred = gradboost_model.predict(X_validation)
    accuracy = r2_score(y_validation, y_pred)
    train.report({"r2":accuracy})

gradboost_config_space = {
    "n_estimators": tune.grid_search([50, 100]),
    "learning_rate": tune.grid_search([0.1, 0.2])
}

# Initialize Ray
# ray.init(ignore_reinit_error=True)

print("available ray resources: ",ray.available_resources())
print("CPU: ", ray.available_resources()['CPU'])
cpu = ray.available_resources()['CPU']

analysis = tune.run(
        train_bg,
        config=bagging_config_space,
        num_samples=5,
        scheduler=scheduler,
        resources_per_trial={"cpu":1},
        verbose=1
        )

adaboost_analysis = tune.run(
    train_adaboost,
    config=adaboost_config_space,
    num_samples=5,
    scheduler=scheduler,
    resources_per_trial={"cpu": 1},
    verbose=1
)

gradboost_analysis = tune.run(
    train_gradboost,
    config=gradboost_config_space,
    num_samples=5,
    scheduler=scheduler,
    resources_per_trial={"cpu": 1},
    verbose=1
)
random_analysis = tune.run(
    train_rf1,
    config=rf_config_space,
    num_samples=5,
    scheduler=scheduler,
    resources_per_trial={"cpu": 1},
    verbose=1
)



print("--------Test results for Grid search in Ray Tune-----")
best_params = analysis.get_best_config(metric="r2", mode="max")
print("Best hyperparameters for bagging:", best_params)
# print("Best cross-validation accuracy:", best_accuracy)
bcTree = DecisionTreeRegressor()
best_bc = BaggingRegressor(bcTree, oob_score=True, random_state=42, **best_params)
best_bc.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
# best_bc.fit(X, y)
test_predictions = best_bc.predict(X_test)
bagging_accuracy = r2_score(y_test, test_predictions)
print("Bagging Test accuracy:", bagging_accuracy)
model_filename = f"./results/Bagging_grid_model.pkl"
joblib.dump(best_bc, model_filename)
print(f"Saved Bagging model to {model_filename}")

best_params = random_analysis.get_best_config(metric="r2", mode="max")
print("Best hyperparameters for Random forest:", best_params)
# Train the final model on the entire dataset
best_rf = RandomForestRegressor(**best_params,random_state=42)
best_rf.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
test_predictions = best_rf.predict(X_test)
rf_accuracy = r2_score(y_test, test_predictions)
print("Test R2 score for Random Forest Test accuracy:", rf_accuracy)
model_filename = f"./results/RandomForest_grid_model.pkl"
joblib.dump(best_rf, model_filename)
print(f"Saved Random Forest model to {model_filename}")

best_adaboost_params = adaboost_analysis.get_best_config(metric="r2", mode="max")
print("Best hyperparameters for AdaBoost Regressor:", best_adaboost_params)
# print("Best R2 score for AdaBoost Regressor:", best_adaboost_r2)
best_adaboost_model = AdaBoostRegressor(**best_adaboost_params, random_state=42)
best_adaboost_model.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
test_predictions = best_adaboost_model.predict(X_test)
adaboost_accuracy = r2_score(y_test, test_predictions)
print("Test R2 score for AdaBoost Regressor:", adaboost_accuracy)
model_filename = f"./results/Adaboost_grid_model.pkl"
joblib.dump(best_adaboost_model, model_filename)
print(f"Saved best adaboost model to {model_filename}")

best_gradboost_params = gradboost_analysis.get_best_config(metric="r2", mode="max")
print("Best hyperparameters for Gradient Boosting Regressor:", best_gradboost_params)
# print("Best R2 score for Gradient Boosting Regressor:", best_gradboost_r2)
best_gradboost_model = GradientBoostingRegressor(**best_gradboost_params)
best_gradboost_model.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
test_predictions = best_gradboost_model.predict(X_test)
gradboost_accuracy = r2_score(y_test, test_predictions)
print("Test R2 score for Gradient Boosting Regressor:", gradboost_accuracy)
model_filename = f"./results/gradboost_grid_model.pkl"
joblib.dump(best_gradboost_model, model_filename)
print(f"Saved best gradboost model to {model_filename}")


### --------------------------------------------------- Random search -----------------------------------------------------------
df = numerical_data
X = df.drop(columns=['stars'], axis=1)
y = df['stars']

# X.describe()

# print(X.isnull().sum())

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define training functions for Ray Tune
def train_lr(config):
    model = LinearRegression(fit_intercept=config["fit_intercept"])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    session.report({"r2": r2})

def train_ridge(config):
    model = Ridge(alpha=config["alpha"])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    session.report({"r2": r2})

def train_lasso(config):
    model = Lasso(alpha=config["alpha"])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    session.report({"r2": r2})

def train_rf(config):
    model = RandomForestRegressor(
        n_estimators=config["n_estimators"],
        max_depth=config["max_depth"],
        min_samples_split=config["min_samples_split"],
        random_state=42
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    session.report({"r2": r2})

def train_gb(config):
    model = GradientBoostingRegressor(
        n_estimators=config["n_estimators"],
        max_depth=config["max_depth"],
        learning_rate=config["learning_rate"],
        random_state=42
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    session.report({"r2": r2})

# Define the search space for hyperparameters
config_lr = {
    "fit_intercept": tune.choice([True, False])
}

config_ridge = {
    "alpha": tune.loguniform(1e-3, 1e2)
}

config_lasso = {
    "alpha": tune.loguniform(1e-3, 1e2)
}

config_rf = {
    "n_estimators": tune.randint(10, 100),
    "max_depth": tune.randint(1, 20),
    "min_samples_split": tune.randint(2, 10)
}

config_gb = {
    "n_estimators": tune.randint(10, 100),
    "max_depth": tune.randint(1, 10),
    "learning_rate": tune.loguniform(1e-3, 1e-1)
}


# Run hyperparameter tuning
analysis_lr = tune.run(
    train_lr,
    resources_per_trial={"cpu": 1},
    config=config_lr,
    num_samples=10,
    scheduler=scheduler
)

analysis_ridge = tune.run(
    train_ridge,
    resources_per_trial={"cpu": 1},
    config=config_ridge,
    num_samples=10,
    scheduler=scheduler
)

analysis_lasso = tune.run(
    train_lasso,
    resources_per_trial={"cpu": 1},
    config=config_lasso,
    num_samples=10,
    scheduler=scheduler
)

analysis_rf = tune.run(
    train_rf,
    resources_per_trial={"cpu": 1},
    config=config_rf,
    num_samples=10,
    scheduler=scheduler
)

analysis_gb = tune.run(
    train_gb,
    resources_per_trial={"cpu": 1},
    config=config_gb,
    num_samples=10,
    scheduler=scheduler
)

# Get the best result
best_lr = analysis_lr.get_best_config(metric="r2", mode="max")
best_ridge = analysis_ridge.get_best_config(metric="r2", mode="max")
best_lasso = analysis_lasso.get_best_config(metric="r2", mode="max")
best_rf = analysis_rf.get_best_config(metric="r2", mode="max")
best_gb = analysis_gb.get_best_config(metric="r2", mode="max")

print("Best hyperparameters for Linear Regression: ", best_lr)
print("Best hyperparameters for Ridge: ", best_ridge)
print("Best hyperparameters for Lasso: ", best_lasso)
print("Best hyperparameters for Random Forest: ", best_rf)
print("Best hyperparameters for Gradient Boosting: ", best_gb)

# Train the best models with the optimal hyperparameters
final_lr = LinearRegression(**best_lr)
final_lr.fit(X_train, y_train)
y_pred_lr = final_lr.predict(X_test)
r2_lr = r2_score(y_test, y_pred_lr)
joblib.dump(final_lr, f"./results/LinearRegression_model.pkl")

final_ridge = Ridge(**best_ridge)
final_ridge.fit(X_train, y_train)
y_pred_ridge = final_ridge.predict(X_test)
r2_ridge = r2_score(y_test, y_pred_ridge)
joblib.dump(final_ridge, f"./results/RidgeRegression_model.pkl")

final_lasso = Lasso(**best_lasso)
final_lasso.fit(X_train, y_train)
y_pred_lasso = final_lasso.predict(X_test)
r2_lasso = r2_score(y_test, y_pred_lasso)
joblib.dump(final_lasso, f"./results/LassoRegression_model.pkl")

final_rf = RandomForestRegressor(**best_rf, random_state=42)
final_rf.fit(X_train, y_train)
y_pred_rf = final_rf.predict(X_test)
r2_rf = r2_score(y_test, y_pred_rf)
joblib.dump(final_rf, f"./results/RandomForest_model.pkl")

final_gb = GradientBoostingRegressor(**best_gb, random_state=42)
final_gb.fit(X_train, y_train)
y_pred_gb = final_gb.predict(X_test)
r2_gb = r2_score(y_test, y_pred_gb)
joblib.dump(final_gb, f"./results/GradientBoosting_model.pkl")

print(f'Best Linear Regression R-squared: {r2_lr}')
print(f'Best Ridge R-squared: {r2_ridge}')
print(f'Best Lasso R-squared: {r2_lasso}')
print(f'Best Random Forest R-squared: {r2_rf}')
print(f'Best Gradient Boosting R-squared: {r2_gb}')

# Compare Models
results = {
    'Model': ['Linear Regression', 'Ridge', 'Lasso', 'Random Forest', 'Gradient Boosting'],
    'R-squared': [r2_lr, r2_ridge, r2_lasso, r2_rf, r2_gb]
}

results_df = pd.DataFrame(results)
print(results_df)
ray.shutdown()
# #Save the results to a text file
with open(os.path.join("/app/results", f"test_accuracy.txt"), 'w') as file:
    # Write the variables into the file
    file.write(f"{r2_lr} LinearRegression_model.pkl\n")
    file.write(f"{r2_ridge} RidgeRegression_model.pkl\n")
    file.write(f"{r2_lasso} LassoRegression_model.pkl\n")
    file.write(f"{r2_rf} RandomForest_model.pkl\n")
    file.write(f"{r2_gb} GradientBoosting_model.pkl\n")
    file.write(f"{bagging_accuracy} Bagging_grid_model.pkl\n")
    file.write(f"{gradboost_accuracy} gradboost_grid_model.pkl\n")
    file.write(f"{adaboost_accuracy} Adaboost_grid_model.pkl\n")
    file.write(f"{rf_accuracy} RandomForest_grid_model.pkl\n")

print("R2 scores have been written to test_accuracy.txt")
print("Time taken: ", datetime.now()-start_time)





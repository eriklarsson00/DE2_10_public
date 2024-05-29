# -*- coding: utf-8 -*-
"""Final_models_3-2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PduIM4QrWkQn2u1VP_9xmRMaYU79PRZc
"""

# !pip install scikit-optimize
# !pip install PyGithub
# !pip install ray[tune]

# from github import Githu
import os
from datetime import datetime
import json
import time
import csv
import requests
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import plotly.graph_objs as go
from plotly.offline import iplot
import plotly.express as px

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

# data = pd.read_csv("combined_3.csv")
# data = data.drop_duplicates()
# data.describe()
# data.columns
# data = pd.read_csv("combined_3.csv")
# data = data.drop_duplicates()
# data = data.drop(columns=['language'], axis=1)
# data.describe()

# data = pd.read_csv("repositories_main.csv")
# data = data.drop_duplicates()
# data.describe()
start_time = datetime.now()
data = pd.read_csv("combined.csv")
data = data.drop_duplicates()
data = data.drop(columns=['language', 'license', 'topics'], axis=1)
data = data.dropna().reset_index(drop=True)
# List of numerical features
numerical_data = data.select_dtypes(exclude=['object'])
# correlation_matrix = numerical_data.corr()
# threshold = 0.8
# correlation_features = []
# for i in range(len(correlation_matrix.columns)):
#   for j in range(i):
#     if abs(correlation_matrix.iloc[i,j]) > threshold:
#       col_name = correlation_matrix.columns[i] # columns name
#       correlation_features.append(col_name)

# print(correlation_features)


# df = numerical_data.drop(["closed"], axis=1)

df = numerical_data
X_original = df.drop(columns=['stars'], axis=1)
y_original = df['stars']
# X_original.describe()

# X_original, X_main_test, y_original, y_main_test = train_test_split(X_original, y_original, test_size=0.0025, random_state=42)
X_not_oversampled1, X_test, y_not_oversampled1, y_test = train_test_split(X_original, y_original, test_size=0.15, random_state=42)
X_not_oversampled, X_validation, y_not_oversampled, y_validation = train_test_split(X_not_oversampled1, y_not_oversampled1, test_size=0.15, random_state=42)
X, y = X_not_oversampled, y_not_oversampled
# X_main_test.head(6)

# X_original.describe()

# main_test_df = pd.concat([X_main_test, y_main_test], axis=1)
# main_test_df.to_csv('Main_test.csv', index=False)
# # main_test_df.head(6)

# X_test.describe()

# Define the training function for bagging
def train_rf(config):
    bcTree = DecisionTreeRegressor()
    bc = BaggingRegressor(bcTree, n_estimators=config['n_estimators'], oob_score=True, random_state=42, max_samples=config['max_samples'], max_features=config['max_features'])
    bc.fit(X, y)
    y_pred = bc.predict(X_validation)
    accuracy= r2_score(y_validation, y_pred)
    train.report({"r2":accuracy})

# Set up the hyperparameter search space
bagging_config_space = {
    "n_estimators": tune.grid_search([50, 150, 300]),
    "max_samples": tune.grid_search([0.8, 0.9, 1.0]),
    "max_features": tune.grid_search([0.8, 0.9, 1.0]),
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
    "n_estimators": tune.grid_search([50, 100, 150]),
    "learning_rate": tune.grid_search([0.01, 0.1, 0.2])
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
    "n_estimators": tune.grid_search([50, 100, 150]),
    "learning_rate": tune.grid_search([0.01, 0.1, 0.2])
}


# Initialize Ray
ray.init(ignore_reinit_error=True)

print("available ray resources: ",ray.available_resources())
print("CPU: ", ray.available_resources()['CPU'])
cpu = ray.available_resources()['CPU']

analysis = tune.run(
        train_rf,
        config=bagging_config_space,
        metric="r2",
        mode="max",
        num_samples=5,
        resources_per_trial={"cpu":1},
        verbose=1
        )
adaboost_analysis = tune.run(
    train_adaboost,
    config=adaboost_config_space,
    metric="r2",
    mode="max",
    num_samples=5,
    resources_per_trial={"cpu": 1},
    verbose=1
)

gradboost_analysis = tune.run(
    train_gradboost,
    config=gradboost_config_space,
    metric="r2",
    mode="max",
    num_samples=5,
    resources_per_trial={"cpu": 1},
    verbose=1
)

ray.shutdown()

best_trial = analysis.get_best_trial("r2")
best_params = best_trial.config
best_accuracy = best_trial.last_result["r2"]
print("Best hyperparameters:", best_params)
# print("Best cross-validation accuracy:", best_accuracy)
bcTree = DecisionTreeRegressor()
best_bc = BaggingRegressor(bcTree, oob_score=True, random_state=42, **best_params)
best_bc.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
# best_bc.fit(X, y)
test_predictions = best_bc.predict(X_test)
bagging_accuracy = r2_score(y_test, test_predictions)
print("Bagging Test accuracy:", bagging_accuracy)
model_filename = f"./results/Bagging_model.pkl"
joblib.dump(best_bc, model_filename)
print(f"Saved Bagging model to {model_filename}")


best_adaboost_trial = adaboost_analysis.get_best_trial("r2")
best_adaboost_params = best_adaboost_trial.config
best_adaboost_r2 = best_adaboost_trial.last_result["r2"]
print("Best hyperparameters for AdaBoost Regressor:", best_adaboost_params)
# print("Best R2 score for AdaBoost Regressor:", best_adaboost_r2)
best_adaboost_model = AdaBoostRegressor(**best_adaboost_params, random_state=42)
best_adaboost_model.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
test_predictions = best_adaboost_model.predict(X_test)
adaboost_accuracy = r2_score(y_test, test_predictions)
print("Test R2 score for AdaBoost Regressor:", adaboost_accuracy)
model_filename = f"./results/Adaboost_model.pkl"
joblib.dump(best_adaboost_model, model_filename)
print(f"Saved best adaboost model to {model_filename}")


best_gradboost_trial = gradboost_analysis.get_best_trial("r2")
best_gradboost_params = best_gradboost_trial.config
best_gradboost_r2 = best_gradboost_trial.last_result["r2"]
print("Best hyperparameters for Gradient Boosting Regressor:", best_gradboost_params)
# print("Best R2 score for Gradient Boosting Regressor:", best_gradboost_r2)
best_gradboost_model = GradientBoostingRegressor(**best_gradboost_params)
best_gradboost_model.fit(pd.concat([X, X_validation]), pd.concat([y, y_validation]))
test_predictions = best_gradboost_model.predict(X_test)
gradboost_accuracy = r2_score(y_test, test_predictions)
print("Test R2 score for Gradient Boosting Regressor:", gradboost_accuracy)
model_filename = f"./results/gradboost_model.pkl"
joblib.dump(best_gradboost_model, model_filename)
print(f"Saved best gradboost model to {model_filename}")

# bagging_accuracy = 0.2
# gradboost_accuracy = 0.5
# adaboost_accuracy = 0.8

with open(os.path.join("/app/results", f"test_accuracy.txt"), 'w') as file:
    # Write the variables into the file
    file.write(f"{bagging_accuracy} Bagging_model.pkl\n")
    file.write(f"{gradboost_accuracy} gradboost_model.pkl\n")
    file.write(f"{adaboost_accuracy} Adaboost_model.pkl\n")

print("Variables have been written to test_accuracy.txt")
print("Time taken = ", datetime.now()-start_time)

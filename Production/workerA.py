from celery import Celery

from numpy import loadtxt
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import r2_score
# from tensorflow.keras.models import model_from_json


model_file = './best_model.pkl'
data_file = './5datapoints.csv'

# def load_data():
#     dataset =  loadtxt(data_file, delimiter=',')
#     X = dataset[:,0:5]
#     y = dataset[:,5]
#     y = list(map(int, y))
#     y = np.asarray(y, dtype=np.uint8)
#     return X, y

dataset = pd.read_csv(data_file)

# for col in dataset.columns:
#     if dataset[col].dtype == 'object' and col != 'full_name':
#         dataset[col] = dataset[col].astype('category').cat.codes
dataset = dataset.select_dtypes(exclude=['object'])
        
target = 'stars'
features = dataset.columns.drop([target])

X = dataset[features].to_numpy()
y = dataset[target].to_numpy()

# load json and create model
loaded_model = joblib.load(model_file)

# Celery configuration
CELERY_BROKER_URL = 'amqp://rabbitmq:rabbitmq@rabbit:5672/'
CELERY_RESULT_BACKEND = 'rpc://'
# Initialize Celery
celery = Celery('workerA', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery.task()
def add_nums(a, b):
   return a + b

@celery.task
def get_predictions():
    results ={}
    X_df = pd.DataFrame(X, columns=features)
    names = X_df["full_name"]
    X_df = X_df.drop(columns=['full_name'])
    predictions = np.round(loaded_model.predict(X_df)).flatten().astype(np.int32)
    
    results_df = pd.DataFrame({
        'full_name': names,
        'actual': y,
        'predicted': predictions
    }).sort_values(by='predicted', ascending=False)
    
    results['data'] = results_df.to_dict(orient='records')
    return results

@celery.task
def get_accuracy():
    # X, y = load_data()
    # loaded_model = load_model()
    # loaded_model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

    # score = loaded_model.evaluate(X, y, verbose=0)
    # #print("%s: %.2f%%" % (loaded_model.metrics_names[1], score[1]*100))
    # return score[1]*100
    
    predictions = get_predictions()
    
    y = [record['actual'] for record in predictions['data']]
    predicted = [record['predicted'] for record in predictions['data']]
    accuracy = r2_score(y, predicted)
    return accuracy*100


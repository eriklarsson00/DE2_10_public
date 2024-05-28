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

def load_data():
    dataset = pd.read_csv(data_file)
    dataset = dataset.drop(columns=['language', 'license', 'topics'], axis=1)
    
    for col in dataset.columns:
        if dataset[col].dtype == 'object' and col != 'full_name':
            dataset[col] = dataset[col].astype('category').cat.codes
            
    target = 'stars'
    features = dataset.columns.drop([target])
    
    X = dataset[features].to_numpy()
    y = dataset[target].to_numpy()
    
    return X, y
        

def load_model():
    # load json and create model
    loaded_model = joblib.load(model_file)
    #print("Loaded model from disk")
    return loaded_model

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
    X, y = load_data()
    names = X[:,0]
    X = np.delete(X, 0, 1)
    loaded_model = load_model()
    predictions = np.round(loaded_model.predict(X)).flatten().astype(np.int32)
    
    results_df = pd.DataFrame({
        'full_name': names,
        'actual': y,
        'predicted': predictions
    }).sort_values(by='predicted', ascending=False)
    
    results['data'] = results_df.to_dict(orient='records')
    
    #print ('results[y]:', results['y'])
    # for i in range(len(results['y'])):
        #print('%s => %d (expected %d)' % (X[i].tolist(), predictions[i], y[i]))
        # results['predicted'].append(predictions[i].tolist()[0])
    #print ('results:', results)
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
    y = predictions['y']
    predicted = predictions['predicted']
    accuracy = r2_score(y, predicted)
    return accuracy*100


from workerA import add_nums, get_accuracy, get_predictions


from flask import (
   Flask,
   request,
   jsonify,
   Markup,
   render_template,
   url_for
)

import pandas as pd

#app = Flask(__name__, template_folder='./templates',static_folder='./static')
app = Flask(__name__)

def load_data():
    data_file = './5datapoints.csv'
    dataset = pd.read_csv(data_file)
    return dataset

@app.route("/")
def index():
    dataset = load_data()
    dataset = dataset.drop(columns=['stars', 'created_at', 'updated_at',
                                    'pushed_at', 'visibility', 'default_branch',
                                    'score', 'has_issues', 'has_projects',
                                    'has_downloads', 'has_wiki', 'has_pages',
                                    'has_discussions', 'archived', 'disabled',
                                    'allow_forking', 'is_template', 'web_commit_signoff_required'], axis=1)
    records = dataset.to_dict(orient='records')
    return render_template('index.html', records=records)

# @app.route("/accuracy", methods=['POST', 'GET'])
# def accuracy():
#     if request.method == 'POST':
#         r = get_accuracy.delay()
#         a = r.get()
#         return '<h1>The accuracy is {}</h1>'.format(a)

#     return '''<form method="POST">
#     <input type="submit">
#     </form>'''

# @app.route("/predictions", methods=['POST', 'GET'])
# def predictions():
#     if request.method == 'POST':
#         results = get_predictions.delay()
#         predictions = results.get()

#         results = get_accuracy.delay()
#         accuracy = results.get()
        
#         final_results = predictions

#         return render_template('result.html', accuracy=accuracy ,final_results=final_results) 
                    
#     return '''<form method="POST">
#     <input type="submit">
#     </form>'''

@app.route("/accuracy", methods=['POST'])
def accuracy():
    task = get_accuracy.delay()
    task.wait()  # Wait for the task to complete
    if task.state == 'SUCCESS':
        return f'<h1>The accuracy is {task.result:.2f}%</h1>'
    else:
        return f'<h1>Task {task.state}</h1>'

@app.route("/predictions", methods=['POST'])
def predictions():
    task = get_predictions.delay()
    task.wait()  # Wait for the task to complete
    if task.state == 'SUCCESS':
        predictions = task.result
        accuracy_task = get_accuracy.delay()
        accuracy_task.wait()  # Wait for the accuracy task to complete
        if accuracy_task.state == 'SUCCESS':
            accuracy = accuracy_task.result
            return render_template('result.html', accuracy=accuracy, predictions=predictions)
        else:
            return f'<h1>Accuracy Task {accuracy_task.state}</h1>'
    else:
        return f'<h1>Predictions Task {task.state}</h1>'

if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=5100,debug=True)

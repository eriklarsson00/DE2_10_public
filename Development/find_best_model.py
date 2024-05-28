import shutil

accuracy_dict = {}
best_accuracy = 0.0
best_model = None
with open('./results/test_accuracy.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        accuracy_dict[line.split()[1]] = float(line.split()[0])
        if float(line.split()[0]) > best_accuracy:
            best_accuracy = float(line.split()[0])
            best_model = line.split()[1]
file.close()

print("Best model is: ", best_model, f" with accuracy: {best_accuracy*100}%")
shutil.copyfile(f"./results/{best_model}", "/home/appuser/transfer/best_model.pkl")
print(f"Saved best model to /home/appuser/transfer/best_model.pkl")
# Public Repo for Data Engineering Pipeline

**Connected to https://github.com/Karthik1000/Data_Engineering_2**

## Model Training and Best Model Selection

- SSH into the Development server. Run the [final_all_models](pipeline/Development/final_all_models.py) file on the Ray-head container `/home/app` directory.
    ```
    sudo bash
    docker ps # returns the container details of running containers
    docker exec -it <container-id of ray-head> /bin/bash
    python3 final_all_models.py
    ```
- Results will be written to the `/DE2_10_public/results` directory, since this volume is mounted to the containers `/home/app/results` directory.
- Run the [find_best_model](pipeline/Development/find_best_model.py) on the Development server. This will push the best model to `/home/appuser/transfer` directory which is connected to the same directory in Production via git hooks.
- Add, commit, connect to remote and push the changes to Production.
    ```bash
    git add .
    git commit -m "new model"
    git remote add production appuser@<PRODUCTIONS-SERVER-IP>:/home/appuser/transfer
    git push production master
    ```
- The predictions from the new model can now be observed on the Dashboard by clicking the *Get Predictions* button.
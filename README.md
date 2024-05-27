Data and models for pipeline

Tentative structure for the ease of Dockerisation:

=Production
    - docker-compose.yml
    - Dockerfile
    - best_model.pkl
    - final_test_dataset.csv
    - requirements.txt
    - script to show final results

=Development
    - docker-compose.yml
    - Dockerfile
    - training_dataset.csv
    - requirements.txt
    = model1
        - model1.pkl
    = model2
        - model2.pkl
    = model3
        - model3.pkl
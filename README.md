civis-gcp-transition
==============================

Transition Civis jobs to Google Cloud Platform (GCP). Schedule jobs in GCP.

Project Organization
------------

    ├── LICENSE
    ├── Makefile                 <- Makefile with commands like `make data` or `make train`
    ├── README.md                <- The top-level README for developers using this project.
    │
    ├── notebooks                <- Jupyter notebooks.
    │
    ├── conda-requirements.txt   <- The requirements file for conda installs.
    ├── requirements.txt         <- The requirements file for reproducing the analysis environment, e.g.
    │                               generated with `pip freeze > requirements.txt`
    │
    ├── setup.py                 <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                      <- Scheduled scripts to run in GCP.

--------

### Starting with JupyterLab

1. Sign in with credentials. [More details on getting started here.](https://cityoflosangeles.github.io/best-practices/getting-started-github.html) 
2. Launch a new terminal and clone repository: `git clone https://github.com/CityOfLosAngeles/REPO-NAME.git`
3. Change into directory: `cd REPO-NAME`
4. Make a new branch and start on a new task: `git checkout -b new-branch`


## Starting with Docker

1. Start with Steps 1-2 above
2. Build Docker container: `docker-compose.exe build`
3. Start Docker container `docker-compose.exe up`
4. Open Jupyter Lab notebook by typing `localhost:8888/lab/` in the browser.

### Setting up a Conda Environment 

1. `conda create --name my_project_name` 
2. `source activate my_project_name`
3. `conda install --file conda-requirements.txt -c conda-forge` 
4. `pip install requirements.txt`

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>

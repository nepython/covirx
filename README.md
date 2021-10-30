# CoviRx Web App


## Project Setup (locally):
1) Clone this repository
2) Change current directory to covirx
3) Install the dependencies
```python
pip install -r requirements.txt
```
4) Change directory to CoviRx.
5) Run Migrations (this creates the database with the required tables)
```python
python manage.py migrate
```
6) Create a superuser to access admin page, later on
```python
python manage.py createsuperuser
```
7) Run server locally
```python
python manage.py runserver
```

Now you can access the web app locally at http://127.0.0.1:8000/

## Email feature:
* To use the email feature in local development, you need to create a `.env` file in your CoviRx directory
* Inside the .env file, specify the two environment varibles as below.
```code
EMAIL_HOST_USER=Your email address
EMAIL_HOST_PASSWORD=Your email password
```
(:warning: Do not forget to replace "Your email address" and "Your email password")

## Creating a new page
We have adopted a modular approach so that components need to not be coded again and again.

A template has been created which can be found at [template.html](CoviRx/templates/main/template.html).

Read the detailed [documentation](https://docs.google.com/document/d/1YSk7G0xJwP1g9P9pa-1Xs1nfogqQutzJA6QbUUDnSsA/edit).

## Deployment
1) For heroku, refer to their [offical blog](https://devcenter.heroku.com/articles/getting-started-with-python#deploy-the-app) on deployment.
2) Additionally from your CLI, execute the below command to create tables in database.
```python
heroku run python CoviRx/manage.py migrate
```
3) And also execute the below command to create superuser for admin.
```python
heroku run python CoviRx/manage.py createsuperuser
```

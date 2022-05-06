# __**CoviRx Web App**__
## **`Table of Contents`**
* [**`Setting up locally`**](#setting-up-locally)
    * [**Basic Setup**](#basic-setup)
    * [**Google OAuth and cloud services setup**](#google-oauth-and-cloud-services-setup)
    * [**Celery setup**](#celery-setup)
* [**`Setting up for production`**](#setting-up-for-production)
    * [**Apache setup**](#apache-setup)
    * [**Supervisor setup**](#supervisor-setup)
    * [**website certificate setup**](#website-certificate-setup)
* [**`Creating a new page`**](#creating-a-new-page)
* [**`Detailed documentation`**](#detailed-documentation)

## **`Setting up locally`**
### **Basic Setup**
:warning: Python3.7 or above is required!
1) Clone this repository
```
git clone https://github.com/nepython/covirx.git
```
2) Change current directory to covirx
```
cd covirx
```
3) Create and activate a virtual environment
```
sudo apt update && sudo apt install -y python3-pip
pip3 install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
```
4) Install the dependencies
```python
pip install -r requirements.txt
```
5) Change directory to CoviRx.
```
cd CoviRx
```
`NOTE:` For all steps below this, we will maintain the current directory to be `CoviRx`.

6) Run Migrations (this creates the database with the required tables)
```python
python manage.py migrate
```
7) Create a superuser to access admin page, later on
```python
python manage.py createsuperuser
```
8) Run server locally
```python
python manage.py runserver
```

Now you can access the web app locally at http://127.0.0.1:8000/

### **Google OAuth and cloud services setup**
* CoviRx uses a lot of google APIs for sending emails, logging in users, storing database backup in drive, etc.
* These APIs need credentials to make use of them:
    - log in to console.cloud.google.com
    - search for api & credentials
    - click on `Create Credentials` > `API keys`
    - create a new project `CoviRx` with redirect uri and javascript redirect uri as http://localhost:5000/ and http://localhost:5000 respectively.
    - now search for `Google Drive API` and enable it.
    - search for `Gmail API` and enable it.
* Download the `credentials.json` file and store it in `covirx/CoviRx/main/data/` directory. (Create the directory if it doesn't exist.)
* Now head over to http://www.google.com/recaptcha/admin, click on create (`+` icon), select `reCAPTCHA v2`, add domain name and note down the secret_key.
* Create a `.env` file in CoviRx
```shell
nano .env
```
Specify the values for below environment varibles as specified (Do not put any quotes around the values).
```code
EMAIL_HOST_USER=Your email address
GOOGLE_INVISIBLE_RECAPTCHA_SECRET_KEY=The secret key noted earlier
GOOGLE_CLIENT_ID=value of "client_id" in credentials.json
SECRET_KEY=any random long string which can be used by django for security
```

### **Celery setup**
* CoviRx makes use of the `celery` library to schedule and execute periodic tasks.
* TASK1: Every month, a backup is created and stored in google drive. An email with a one-click button to restore to previous version of database is also sent.
* TASK2: Articles on new assay data are mined for drugs present in CoviRx.
1) Installing broker (redis)
```
sudo apt update
sudo apt install redis-server
```
2) Run celery in a new terminal, everytime you run the server
```
celery -A CoviRx worker --loglevel=debug --concurrency=1 -E -B
```

## **`Setting up for production`**
* Repeat the same steps as in [Setting up locally:](#setting-up-locally)

### **Apache setup**
1) Installing Apache
```
sudo apt update
sudo apt install apache2 apache2-dev python3-dev libapache2-mod-wsgi-py3
```
2) Change configuration and enable headers
```
sed -i -e s/ubuntu/${USER}/g ../server_files/000-default.conf
sudo bash -c 'cat ../server_files/000-default.conf > /etc/apache2/sites-available/000-default.conf'
```
3) Enable Headers and WSGI
```
sudo a2enmod headers
sudo a2enmod wsgi
```
4) Check configuration
```
sudo apache2ctl configtest
```
5) Give proper privilege to apache
```
./manage.py collectstatic
chmod 664 db.sqlite3
sudo chown -R www-data ../../covirx
sudo ufw allow 'Apache Full'
```
6) Restart apache
```
sudo systemctl restart apache2
```
`NOTE:`
1. Apache errors can be located in `/var/log/apache2/error.log`.
2. If in the error log, you get an error `ModuleNotFoundError: No module named 'django'`, follow steps in [this link](https://stackoverflow.com/a/71057035) to resolve it.

### **Supervisor setup**
When implementing celery on a production instance it may be preferable to delegate supervisord to manage celery workers and celery beats.
1. Install supervisor and configure files
```
sudo apt-get install supervisor
chmod u+x ../server_files/celery_worker_start
mkdir /home/$USER/covirx/server_files/logs/
echo $USER
sudo nano /etc/supervisor/conf.d/covirx_supervisor.conf
```
In the editor that opens, insert below lines. However do not forget to **replace `<$USER>` with the output of `echo $USER`**.
```
[program:covirx-celery-worker]
command = /home/<$USER>/covirx/server_files/celery_worker_start
user = <$USER>
stdout_logfile = /home/<$USER>/covirx/server_files/logs/celery_worker.log
redirect_stderr = true
environment = LANG = en_US.UTF-8,LC_ALL = en_US.UTF-8
numprocs = 1
autostart = true
autorestart = true
startsecs = 10
stopwaitsecs = 600
priority = 998
```
2. Reread and update supervisor
```
sudo supervisorctl reread
sudo supervisorctl update
```
3. Some basic commands which can be used with supervisor

`NOTE:` You do not need to run below commands unless need be
```
sudo supervisorctl status
sudo supervisorctl stop covirx-celery-worker
sudo supervisorctl start
sudo supervisorctl restart covirx-celery-worker
```
### **website certificate setup**
We use Let's Encrypt SSL certificates with certbot for auto-renewal ([More Info](https://www.digitalocean.com/community/tutorials/how-to-secure-apache-with-let-s-encrypt-on-ubuntu-18-04))
```
sudo apt install certbot python3-certbot-apache
sudo certbot --apache
```
Follow the More Info link to answer the questions
```
sudo systemctl status certbot.timer
```

## **`Creating a new page`**
We have adopted a modular approach so that components need to not be coded again and again.

A template has been created which can be found at [template.html](CoviRx/templates/main/template.html).

## **`Detailed documentation`**
Read the detailed [documentation](https://docs.google.com/document/d/1YSk7G0xJwP1g9P9pa-1Xs1nfogqQutzJA6QbUUDnSsA/edit).

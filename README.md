# SoftDesk_rest_api_v2

# Installation

## Clone the repo
``` bash
git clone https://github.com/Meez25/SoftDesk_rest_api_v2
```
Then go in the SoftDesk_rest_api_v2 folder

# Create the virtual environement

``` bash
python3 -m venv env
source env/bin/activate
```

(env) should now be displayed on the left of your prompt

To download all the libraries, you can do this command 

``` bash
pip install -r requirements.txt
```

This will install all the dependancies necessary to run the Django Server

Then : 
``` bash
python manage.py runserver
```

There is an admin account which is :
username : admin@admin.com
password : toto

With the admin account, you can go to http://127.0.0.1:8000/admin to log in as
the admin

Then, all the endpoints are documented here :
https://documenter.getpostman.com/view/2s8ZDVajFy?version=latest

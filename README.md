# Final-Year-Project
Final year project github repository 


Welcome to my final year project repository! 
Here you will find the core code and programes that run my IoT air quality sensor suite. 
Only the database and env files have been excluded for security and privacy reasons. 

This is a living document and will be updated over the coming days and weeks. 


This IOT air quality device is designed to be placed in a room and used to measure the air quailty. It then ranks the air quality to air standards ratings and alerts the people in the room if they pass those hardcoded thresholds. 

## Overview: flask app,py, all_sensors.py and open database 

## To start: 
### Ensure all are running on the same network. Use a hotspot for this. 

ssh the IP address

enter the password

# How to run! 
## On terminal or cmd using the Pi(all_sensors.py) program:

## Set up Python 3.11.8. This works best with the sensor suite

### Run outside of Venv
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev \
libncurses5-dev libnss3-dev libsqlite3-dev libreadline-dev \
libffi-dev libbz2-dev wget

### Download Python 3.11.8
cd ~
wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz
tar -xf Python-3.11.8.tgz
cd Python-3.11.8

### Verify 
~/python311/bin/python3.11 --version

### Create Venv
cd ~/Documents/sensor_project

~/python311/bin/python3.11 -m venv venv311

### Activate it 

source venv311/bin/activate

### Install all libraries 
pip install --upgrade pip
pip install adafruit-blinka adafruit-circuitpython-dht adafruit-circuitpython-sgp30 paho-mqtt flask


### Activate venv 

source venv/bin/activate

## Next step is if lgpio doesn't run. (Only run if lgpio doesn't work). 
## Note this might break when using Python 3.11.8 

### If the venv has been opened run: 

deactivate

### Then run: 

rm -rf ~/venv


### Recreate the system packages: 

python3 -m venv --system-site-packages ~/venv


### Then run: 

source ~/venv/bin/activate

### Next test if lpgio is visible: 

python

import lgpio 


### If nothing shows it’s fixed 

run: exit() 

### Then install all the packages and libraries again. Other libraries are available and terminal or cmd will display an error if a package is missing: 

pip install adafruit-blinka

pip install adafruit-circuitpython-sgp30

pip install adafruit-circuitpython-dht

pip install Adafruit_DHT --config-settings="--build-option=--force-pi"

pip install paho-mqtt

pip install gpiozero

pip install board 

pip install flask

pip install busio 

pip install serial 



### Run:

python all_sensors.py

If you want to check what's been installed run: pip list 
This will show all dependencies

## For installing the app.py on the Pi:

Open a new cmd or terminal:

sudo apt update
sudo apt install python3-venv

python3 -m venv venv

source venv/bin/activate

Then run:

pip install flask

pip install -U Flask-SQLAlchemy

pip install mysql-connector-python 

pip install PyMySQL

If you want to check what's been installed run: pip list 

This will show all dependencies

Now run:

python app.py

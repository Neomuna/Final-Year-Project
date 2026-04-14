# Final-Year-Project
Final year project github repository 


Welcome to my final year project repository! 
Here you will find the core code and programes that run my IoT air quality sensor suite. 
Only the database and env files have been excluded for security and privacy reasons. 

This is a living document and will be updated over the coming days and weeks. 




This IOT air quality device is designed to be placed in a room and used to measure the air quailty. It then ranks the air quality to air standards ratings and alerts the people in the room if they pass those hardcoded thresholds. 

 
###Overview: flask app,py, all_sensors.py and open database 

To start: 
Ensure all are running on the same network. Use a hotspot for this. 

ssh the IP address

enter the password

# How to run! 

## On terminal or cmd using the Pi(all_sensors.py):

sudo apt update
sudo apt install python3-venv

Opens virtual environment:

python3 -m venv venv

Activate venv 
source venv/bin/activate

### Next step is if lgpio doesn't run 

If the venv has been opened run: 

deactivate

Then run: 

rm -rf ~/venv


Recreate the system packages: 

python3 -m venv --system-site-packages ~/venv


Then run: 

source ~/venv/bin/activate

Next test if lpgio is visible: 

python

>import lgpio 


If nothing shows it’s fixed 

run: exit() 

Then install all the packages and libraries again. Other libraries are available and terminal or cmd will display an error if a package is missing: 

pip install adafruit-blinka

pip install adafruit-circuitpython-sgp30

pip install adafruit-circuitpython-dht

pip install flask

pip install paho-mqtt

pip install gpiozero

pip install flask


Run:

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

# Flask program for database 
# Already installed: !pip install flask
# Alreadt installeld: !pip install -U Flask-SQLAlchemy
# pip install mysql-connector-python 
# pip install PyMySQL

# Notes to self:

# Activate virtual environment with: source flask_env/bin/activate
#Install everything: pip install flask flask-sqlalchemy mysql-connector-python

#Very important to check if packages are installed correctly:
#pip show flask
#pip show flask-sqlalchemy



from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone 

app = Flask(__name__) # Initialise Flask app

#  Database Config 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@86.17.112.152/Final_Year_Project' # My Macs IP address 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress warning

db = SQLAlchemy(app) # Initialise SQLAlchemy

# Generic database helper to save an object
def save(obj):
    db.session.add(obj)
    db.session.commit()

# Generic helpers 
def get_json():
    data = request.get_json()
    if not data:
        return None, (jsonify({"error": "Invalid JSON"}), 400)
    return data, None

# Generic helper to get latest entry from a model
def get_latest(model, order_field, error_msg):
    obj = model.query.order_by(order_field.desc()).first()
    if not obj:
        return None, (jsonify({"error": error_msg}), 404)
    return obj, None



# SQLAlchemy Models 
class SensorReading(db.Model): # Sensor Reading Model
    __tablename__ = 'Sensor_Readings' # Sensor Readings table 
    reading_id = db.Column(db.Integer, primary_key=True) # Unique ID for each reading
    Pi_ID = db.Column(db.Integer, db.ForeignKey("Raspberry_Pi.Pi_ID")) # Foreign key to Raspberry Pi
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Timestamp of reading
    Temperature = db.Column(db.Float) # Temperature reading
    Humidity = db.Column(db.Float) # Humidity reading
    CO2_reading = db.Column(db.Float) # CO2 level reading
    CO_Reading = db.Column(db.Float) # CO level reading
    movement = db.Column(db.Boolean) # True/False for movement detected or not 

    def to_dict(self):
        return {
            "reading_id": self.reading_id,
            "Pi_ID": self.Pi_ID,
            "timestamp": self.timestamp.isoformat(),
            "Temperature": self.Temperature,
            "Humidity": self.Humidity,
            "CO2_reading": self.CO2_reading,
            "CO_Reading": self.CO_Reading,
            "movement": self.movement
        }

# Raspberry Pi Model
class Raspberry_Pi(db.Model): # Raspberry Pi Model
    __tablename__ = "Raspberry_Pi" # Raspberry Pi table
    Pi_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each Pi
    Location_ID = db.Column(db.Integer, db.ForeignKey("location.Location_ID")) # Foreign key to Location
    IP_Address = db.Column(db.String(255)) # IP Address of the Pi
    Last_Used_Timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Last used timestsource flask_env/bin/activate


    # One-to-many relationship 
    sensor_readings = db.relationship("SensorReading", backref="pi") # Relationship to SensorReading
    alerts = db.relationship("Alerts", backref="pi") # Relationship to Alerts 

    def to_dict(self):
        return {
            "Pi_ID": self.Pi_ID,
            "Location_ID": self.Location_ID,
            "IP_Address": self.IP_Address,
            "Last_Used_Timestamp": self.Last_Used_Timestamp.isoformat()
        }

# Alerts Model
class Alerts(db.Model): # Alerts Model
    __tablename__ = "Alerts" # Alerts table
    Alert_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each alert 
    Pi_ID = db.Column(db.Integer, db.ForeignKey("Raspberry_Pi.Pi_ID"), nullable=False) # ID of the Pi generating the alert
    Threshold = db.Column(db.Float) # Threshold value that triggered the alert
    Motion = db.Column(db.Float) # Used for test sensor alongside movement
    Message_Alert = db.Column(db.String(255)) # Alert message
    Alerts_Timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Timestamp of the alert

    def to_dict(self):
        return {
            "Alert_ID": self.Alert_ID,
            "Pi_ID": self.Pi_ID,
            "Threshold": self.Threshold,
            "Motion": self.Motion,
            "Message_Alert": self.Message_Alert,
            "Alerts_Timestamp": self.Alerts_Timestamp.isoformat()
        }

# Location Model
class Location (db.Model): # Location Model
    __tablename__ = "Location" # Location table
    Location_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each location
    Building = db.Column(db.String(255)) # Building location 
    Roomname = db.Column(db.String(255)) # Name of room 

    def to_dict(self):     
        return {
            "Location_ID": self.Location_ID,
            "Building": self.Building,
            "Roomname": self.Roomname   
        }

# App route for Sensor Reading
@app.post("/api/upload/sensor") # Route to upload sensor reading
def upload_sensor(): # Upload sensor reading to database
    data, error = get_json() # Get JSON data from request
    if error: 
        return error

    reading = SensorReading( # Create new SensorReading object
        Pi_ID=data.get("Pi_ID"), # Foreign key to Raspberry Pi
        Temperature=data.get("Temperature"), # Temperature reading
        Humidity=data.get("Humidity"),  # Humidity reading
        CO2_reading=data.get("CO2_reading"), # CO2 level reading
        CO_Reading=data.get("CO_Reading"), # CO level reading
        movement=data.get("movement") # Movement detected or not
    )
 
    save(reading) # Save reading to database
    return jsonify({"status": "sensor reading added"}), 201 # Return success response


@app.get("/api/latest/sensor") # Route to get latest sensor reading
def latest_sensor(): # Get latest sensor reading from database
    reading, error = get_latest(SensorReading,SensorReading.timestamp,"No sensor readings found") # Get latest sensor reading
    if error: 
        return error

    return jsonify(reading.to_dict()) # Return latest sensor reading as JSON


# App route for Location 
@app.post("/api/upload/location") # Route to upload location
def upload_location(): # Upload location to database
    data = request.json # Get JSON data from request

    location = Location( # Create new Location object
        Location_ID=data.get("Location_ID"),   # Unique ID for location
        Building=data.get("Building"), # Building location
        Roomname=data.get("Roomname") # Name of room
    )

    db.session.add(location) # Add location to session
    db.session.commit() # Commit session to database

    return jsonify({"status": "location added"}), 201  # Return success response

@app.get("/api/latest/location") # Route to get latest location
def latest_location(): # Get latest location from database
    location = Location.query.order_by(Location.Location_ID.desc()).first() # Query latest location
    if not location: # If no location found
        return jsonify({"error": "No locations found"}), 404 # Return error response

    return jsonify({ # Return latest location as JSON
        "Location_ID": location.Location_ID, # Unique ID for location
        "Building": location.Building, # Building location
        "Roomname": location.Roomname # Name of room
    })

# Route for Raspberry Pi 
@app.post("/api/upload/pi") # Route to upload Raspberry Pi info
def upload_pi(): # Upload Raspberry Pi info to database
    data = request.json # Get JSON data from request

    pi = Raspberry_Pi( # Create new Raspberry_Pi object
        Pi_ID=data.get("Pi_ID"), # Unique ID for Raspberry Pi
        Location_ID=data.get("Location_ID"), # Foreign key to Location
        IP_Address=data.get("IP_Address"), # IP Address of the Pi
        Last_Used_Timestamp=datetime.now(timezone.utc) # Last used timestamp
    )
    db.session.add(pi) # Add Raspberry Pi to session
    db.session.commit() # Commit session to database

    return jsonify({"status": "pi registered"}), 201  # Return success response

@app.get("/api/latest/pi") # Route to get latest Raspberry Pi info
def latest_pi(): # Get latest Raspberry Pi info from database
    rpi = Raspberry_Pi.query.order_by(Raspberry_Pi.Last_Used_Timestamp.desc()).first() # Query latest Raspberry Pi
    if not rpi: # If no Raspberry Pi found
        return jsonify({"error": "No Raspberry Pis found"}), 404 # Return error response

    return jsonify({ # Return latest Raspberry Pi info as JSON
        "Pi_ID": rpi.Pi_ID, # Unique ID for Raspberry Pi
        "Location_ID": rpi.Location_ID, # Foreign key to Location
        "IP_Address": rpi.IP_Address, # IP Address of the Pi
        "Last_Used_Timestamp": rpi.Last_Used_Timestamp.isoformat() # Last used timestamp
    })

# Route for Alerts 
@app.post("/api/upload/alert") # Route to upload alert
def upload_alert(): # Upload alert to database
    data = request.json # Get JSON data from request

    alert = Alerts(  # Create new Alerts object
        Pi_ID=data.get("Pi_ID"), # ID of the Pi generating the alert
        Threshold=data.get("Threshold"), # Threshold value that triggered the alert
        Motion=data.get("Motion"), # Used for test sensor alongside movement
        Message_Alert=data.get("Message_Alert") # Alert message
    )
    db.session.add(alert) # Add alert to session
    db.session.commit() # Commit session to database

    return jsonify({"status": "alert added"}), 201 # Return success response

@app.get("/api/latest/alert") # Route to get latest alert
def latest_alert(): # Get latest alert from database
    alerts = Alerts.query.order_by(Alerts.Alerts_Timestamp.desc()).first() # Query latest alert 
    if not alerts: # If no alert found
        return jsonify({"error": "No alerts found"}), 404 # Return error response

    return jsonify({ # Return latest alert as JSON
        "Alert_ID": alerts.Alert_ID, # Unique ID for each alert
        "Pi_ID": alerts.Pi_ID, # ID of the Pi generating the alert
        "Threshold": alerts.Threshold,  # Threshold value that triggered the alert
        "Motion": alerts.Motion, # Used for test sensor alongside movement 
        "Message_Alert": alerts.Message_Alert, # Alert message
        "Alerts_Timestamp": alerts.Alerts_Timestamp.isoformat() # Timestamp of the alert
    })

# Dashboard route to view sensor readings on a web page 
@app.get("/dashboard/sensors") # Route to view sensor readings dashboard
def dashboard_sensors(): # View sensor readings dashboard
    readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(50).all() # Get latest 50 sensor readings
    return render_template("sensor_dashboard.html", readings=readings) # Render sensor dashboard template

# Run the program
if __name__ == "__main__": # Main program
    app.run(host="192.168.0.182", port=5000) # PI IP address at home
    # app.run(host="0.0.0.0", port=5000) # use instead when deploying to the Pi

# Refrences: 
# https://www.youtube.com/watch?v=hQl2wyJvK5k 
# https://www.youtube.com/watch?v=5aYpkLfkgRE&
# https://www.youtube.com/watch?v=MKG5BpZbOa4&t 
# https://flask-sqlalchemy.readthedocs.io/en/stable/ 
# https://flask-sqlalchemy.readthedocs.io/en/stable/config/ 
# https://www.youtube.com/watch?v=45P3xQPaYxc&t 



# Things I need to do:
# Add all database entries + keys - tick
# Add reading much like i did with SensorReading() - tick
# Finish ERD diagram  - need to improve a few areas 
# Need to look over where I can include keys 
# Stay clam - ish 
# Test with script on Pi 
# Profit

# This program has been refactored by CoPilot and myself. Fixing a few secuity issues and improving code structure. 



# Flask program for database 
# Already installed: !pip install flask
# Already installed: !pip install -U Flask-SQLAlchemy
# pip install mysql-connector-python 
# pip install PyMySQL


# Activate virtual environment with: source flask_env/bin/activate
#Install everything: pip install flask flask-sqlalchemy mysql-connector-python

#Very important to check if packages are installed correctly:
#pip show flask
#pip show flask-sqlalchemy

# Run the following commands in terminal to set MQTT environment variables before running the program:
"""
export MQTT_BROKER=192.168.1.10
export MQTT_PORT=1883
export MQTT_TOPIC=sensors/air_quality
""" 


from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone 
import paho.mqtt.client as mqtt
import threading
import json
import os
from typing import Tuple, Any, Dict, Optional

app = Flask(__name__) # Initialise Flask app

db = SQLAlchemy(app) # Initialise SQLAlchemy


#  Database Config - Using environment variables for security
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:"
    f"{os.getenv('DB_PASSWORD', '')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '3306')}/"
    f"{os.getenv('DB_NAME', 'Final_Year_Project')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress warning

# MQTT Listener to receive data from sensors and save to database
def mqtt_listener():
    broker = "My number url goes here" # HiveMQ Cloud broker
    port = 8883
    topic = "sensors/air_quality"

    def on_connect(client, userdata, flags, rc, properties=None):
        # Check connection status code
        if rc == 0:
            print("Connected to MQTT Broker")
            client.subscribe(topic)
        else:
            print(f"MQTT connection failed with code {rc}")  # Log connection errors

    def on_message(client, userdata, msg):
        try:  # Wrap payload parsing to prevent thread crashes
            data = json.loads(msg.payload.decode())
            print("Received via MQTT:", data)

            # Convert payload to DB model
            reading = SensorReading(
                Pi_ID=data.get("Pi_ID"),
                Temperature=data.get("Temperature"),
                Humidity=data.get("Humidity"),
                CO2_reading=data.get("CO2_reading"),
                CO_Reading=data.get("CO_Reading"),
                TVOC=data.get("TVOC"),
                Air_Quality_Status=data.get("Air_Quality_Status"),
            )

            # Save reading
            db.session.add(reading)

            # Alerts
            if data.get("Air_Quality_Status") in ["POOR", "CRITICAL"]:
                alert = Alerts(
                    Pi_ID=data.get("Pi_ID"),
                    alert_type="AIR_QUALITY",  # Added alert type
                    value=data.get("CO2_reading") or data.get("CO_Reading") or data.get("TVOC"),  # The problematic value
                    threshold=1000 if data.get("CO2_reading") else (1 if data.get("CO_Reading") else 300),  # Appropriate threshold
                    message=f"Air quality {data.get('Air_Quality_Status')}: {data.get('issues')}"  # Updated to match SQL column
                )
                db.session.add(alert)

            db.session.commit()
        except (json.JSONDecodeError, ValueError) as e:  # Handle invalid JSON
            print(f"Error parsing MQTT message: {e}")
            return  # Skip this message, continue listening
        except Exception as e:  # Catch database errors too
            print(f"Error processing sensor data: {e}")
            db.session.rollback()  # Rollback failed transaction to prevent locked state

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("MyUsername", "MyPassword")  # Set MQTT credentials
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(broker, port, 60)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT connection error: {e}")



# Added home route for testing due to issues with Flask server starting
@app.get("/") # Home route
def home(): # Home route
    try:
        readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(50).all() # Get latest 50 sensor readings
    except Exception as e:
        readings = [] # Return empty list if database connection fails
    return render_template("index.html", readings=readings) # Render sensor dashboard template   


# Database helper to save an object
def save(obj: Any) -> Optional[Tuple[Dict, int]]:  # Type hints for parameters and return
    """Save object to database. Returns error tuple if failure, None if success."""
    try: # Try to save object
        db.session.add(obj) # Add object to session
        db.session.commit() # Commit session to database
        return None  # Explicit success return instead of implicit None
    except Exception as e: # If error occurs
        db.session.rollback() # Rollback session
        return jsonify({"error": str(e)}), 500 # Return error response

# Helper to get JSON data from request
def get_json() -> Tuple[Optional[Dict], Optional[Tuple[Dict, int]]]:  # Type hints
    """Get JSON data from request. Returns (data, error) tuple."""
    data = request.get_json() # Get JSON data
    if not data: 
        return None, (jsonify({"error": "Invalid JSON"}), 400) # Return error if no data
    return data, None  

# Helper to get latest entry from a model
def get_latest(model: Any, order_field: Any, error_msg: str) -> Tuple[Optional[Any], Optional[Tuple[Dict, int]]]:  # Type hints
    """Get latest entry from model. Returns (object, error) tuple."""
    obj = model.query.order_by(order_field.desc()).first() # Query latest entry
    if not obj:
        return None, (jsonify({"error": error_msg}), 404) # Return error if no entry found
    return obj, None 

# Helper to validate required fields in JSON data
def validate_fields(data: Dict, required_fields: list) -> Optional[Tuple[Dict, int]]:  # Type hints
    """Validate required fields in JSON data. Returns error tuple or None if all fields present."""
    missing = [field for field in required_fields if data.get(field) is None]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    return None


# SQLAlchemy Models 
class SensorReading(db.Model): # Sensor Reading Model
    __tablename__ = 'Sensor_Readings' # Sensor Readings table 
    Measurement_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each reading (matches SQL)
    Pi_ID = db.Column(db.Integer, db.ForeignKey("Raspberry_Pi.Pi_ID")) # Foreign key to Raspberry Pi
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Timestamp of reading
    Temperature = db.Column(db.Float) # Temperature reading
    Humidity = db.Column(db.Float) # Humidity reading
    CO2_reading = db.Column(db.Float) # CO2 level reading
    CO_Reading = db.Column(db.Float) # CO level reading
    movement = db.Column(db.Integer, default=0) # Movement detection (matches SQL)
    TVOC = db.Column(db.Float) # Total Volatile Organic Compounds reading (added to match your code)
    Air_Quality_Status = db.Column(db.String(50)) # Air quality status based on sensor readings (added to match your code)
 
    def to_dict(self): # Convert reading to dictionary
        return { 
            "Measurement_ID": self.Measurement_ID,  # Updated to match SQL
            "Pi_ID": self.Pi_ID,
            "timestamp": self.timestamp.isoformat(),
            "Temperature": self.Temperature,
            "Humidity": self.Humidity,
            "CO2_reading": self.CO2_reading,
            "CO_Reading": self.CO_Reading,
            "movement": self.movement,
            "TVOC": self.TVOC,
            "Air_Quality_Status": self.Air_Quality_Status
        }
          


# Raspberry Pi Model
class Raspberry_Pi(db.Model): # Raspberry Pi Model
    __tablename__ = "Raspberry_Pi" # Raspberry Pi table
    Pi_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each Pi
    Location_ID = db.Column(db.String(50)) # Foreign key to Location (matches SQL varchar(50) - note: this should be int in SQL but we'll work with what's there)
    IP_Address = db.Column(db.String(50)) # IP Address of the Pi (matches SQL varchar(50))
    Last_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Last used timestamp (matches SQL column name)


    # One-to-many relationship 
    sensor_readings = db.relationship("SensorReading", backref="pi") # Relationship to SensorReading
    alerts = db.relationship("Alerts", backref="pi") # Relationship to Alerts 

    def to_dict(self):
        return {
            "Pi_ID": self.Pi_ID,
            "Location_ID": self.Location_ID,
            "IP_Address": self.IP_Address,
            "Last_used": self.Last_used.isoformat()  # Updated to match SQL column name
        }

# Alerts Model
class Alerts(db.Model): # Alerts Model
    __tablename__ = "Alerts" # Alerts table
    Alert_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each alert 
    Pi_ID = db.Column(db.Integer, db.ForeignKey("Raspberry_Pi.Pi_ID"), nullable=False) # ID of the Pi generating the alert
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Timestamp of the alert (matches SQL)
    alert_type = db.Column(db.String(50)) # Type of alert (matches SQL)
    value = db.Column(db.Float) # Value that triggered alert (matches SQL)
    threshold = db.Column(db.Float) # Threshold value (matches SQL)
    message = db.Column(db.Text) # Alert message (matches SQL)

    def to_dict(self): # Convert alert to dictionary
        return {
            "Alert_ID": self.Alert_ID,
            "Pi_ID": self.Pi_ID,
            "timestamp": self.timestamp.isoformat(),  # Updated to match SQL
            "alert_type": self.alert_type,  # Updated to match SQL
            "value": self.value,  # Updated to match SQL
            "threshold": self.threshold,  # Updated to match SQL
            "message": self.message  # Updated to match SQL
        }

# Location Model
class Location (db.Model): # Location Model
    __tablename__ = "Location" # Location table
    Location_ID = db.Column(db.Integer, primary_key=True) # Unique ID for each location
    Building = db.Column(db.String(100)) # Building location (matches SQL varchar(100))
    Roomname = db.Column(db.String(100)) # Name of room (matches SQL varchar(100))
    
    # Note: No foreign key relationship due to Location_ID being varchar in Raspberry_Pi table
    # This is a schema design issue that should be fixed in the SQL

    def to_dict(self):  # Convert location to dictionary
        return {
            "Location_ID": self.Location_ID,
            "Building": self.Building,
            "Roomname": self.Roomname   
        }

# App route for Sensor Reading
@app.post("/api/upload/sensor")
def upload_sensor():
    data, error = get_json()
    if error:
        return error

    reading = SensorReading(
        Pi_ID=data.get("Pi_ID"),
        Temperature=data.get("Temperature"),
        Humidity=data.get("Humidity"),  # Match lowercase from sensor payload
        CO2_reading=data.get("CO2_reading"),  # Match lowercase field name
        CO_Reading=data.get("CO_Reading"),  # Match lowercase field name
        TVOC=data.get("TVOC"),
        Air_Quality_Status=data.get("Air_Quality_Status"),
    )

    # Auto-generate alert
    if data.get("Air_Quality_Status") in ["POOR", "CRITICAL"]:
        alert = Alerts(
        Pi_ID=data.get("Pi_ID"),
        Message_Alert=f"Air quality {data.get('Air_Quality_Status')}: {data.get('Issues')}"
    )
    save(alert)
    err = save(reading)       # Call save, catch any error it returns
    if err: return err        # If save failed, return the error
    return jsonify({"status": "sensor reading added"}), 201  # only reaches here if save worked


@app.get("/api/latest/sensor") # Route to get latest sensor reading
def latest_sensor(): # Get latest sensor reading from database
    reading, error = get_latest(SensorReading,SensorReading.timestamp,"No sensor readings found") # Get latest sensor reading
    if error: 
        return error

    return jsonify(reading.to_dict()) # Return latest sensor reading as JSON


# App route for Location 
@app.post("/api/upload/location") # Route to upload location
def upload_location(): # Upload location to database
    data, error = get_json() # Get JSON data from request
    if error: 
        return error

    location = Location( # Create new Location object
        Location_ID=data.get("Location_ID"),   # Unique ID for location
        Building=data.get("Building"), # Building location
        Roomname=data.get("Roomname") # Name of room
    )

    save(location) # Save location to database
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
    data, error = get_json() # Get JSON data from request
    error = validate_fields(data, ["Pi_ID", "Location_ID", "IP_Address"]) # Validate required fields
    if error:
        return error 


    pi = Raspberry_Pi( # Create new Raspberry_Pi object
        Pi_ID=data.get("Pi_ID"), # Unique ID for Raspberry Pi
        Location_ID=data.get("Location_ID"), # Foreign key to Location
        IP_Address=data.get("IP_Address"), # IP Address of the Pi
    )
    save(pi) # Save Raspberry Pi info to database
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
    data, error = get_json() # Get JSON data from request
    error = validate_fields(data, ["Pi_ID", "message"]) # Validate fields required for an alert (updated to match SQL)
    if error:
        return error

    alert = Alerts( # Create new Alerts object
        Pi_ID=data.get("Pi_ID"), # ID of the Pi generating the alert
        alert_type=data.get("alert_type", "GENERAL"), # Type of alert (matches SQL)
        value=data.get("value"), # Value that triggered alert (matches SQL)
        threshold=data.get("threshold"), # Threshold value (matches SQL)
        message=data.get("message") # Alert message (matches SQL)
    )

    save(alert) # Save alert to database
    return jsonify({"status": "alert added"}), 201 # Return success response

@app.get("/api/latest/alert") # Route to get latest alert
def latest_alert(): # Get latest alert from database
    alert, error = get_latest( Alerts, Alerts.timestamp, "No alerts found" ) # Get latest alert (updated to match SQL column)
    if error: 
        return error
    return jsonify(alert.to_dict()) # Return latest alert as JSON

# Dashboard route to view sensor readings on a web page 
@app.get("/dashboard/sensors") # Route to view sensor readings dashboard
def dashboard_sensors(): # View sensor readings dashboard
    readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(50).all() # Get latest 50 sensor readings
    return render_template("sensor_dashboard.html", readings=readings) # Render sensor dashboard template

# Run the program
if __name__ == "__main__":
    try:
        # Start MQTT listener in separate thread
        thread = threading.Thread(target=mqtt_listener, name="MQTT-Listener")
        thread.daemon = True # Set thread as daemon so it exits when main program exits
        thread.start() # Start MQTT listener thread
        print("MQTT listener thread started")
        
        # Run Flask app on all interfaces, port 5000
        # debug=False for production to prevent auto-reloading (which spawns multiple MQTT threads)
        app.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise 



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
# Finish ERD diagram  - tick
# Need to look over where I can include keys - tick 
# Test all routes with Postman - tick
# Create dashboard to view readings - tick
# Deploy on Raspberry Pi - tick
# Write documentation for code - tick
# Finishing refactoring code - in progress
# Testing sensors - in progress
# Testing finished program - in progress
# Stay clam - ish  
# Profit
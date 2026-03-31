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

db = SQLAlchemy(app) # Initialise SQLAlchemy


#  Database Config 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@86.17.112.152/Final_Year_Project' # My Macs IP address 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress warning

# Added home route for testing due to issues with Flask server starting
@app.get("/") # Home route
def home(): # Home route
    try:
        readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(50).all() # Get latest 50 sensor readings
    except Exception as e:
        readings = [] # Return empty list if database connection fails
    return render_template("index.html", readings=readings) # Render sensor dashboard template   


# Database helper to save an object
def save(obj): # Save object to database
    try: # Try to save object
        db.session.add(obj) # Add object to session
        db.session.commit() # Commit session to database
    except Exception as e: # If error occurs
        db.session.rollback() # Rollback session
        return jsonify({"error": str(e)}), 500 # Return error response

# Helper to get JSON data from request
def get_json(): # Get JSON data from request
    data = request.get_json() # Get JSON data
    if not data: 
        return None, (jsonify({"error": "Invalid JSON"}), 400) # Return error if no data
    return data, None  

# Helper to get latest entry from a model
def get_latest(model, order_field, error_msg): # Get latest entry from model
    obj = model.query.order_by(order_field.desc()).first() # Query latest entry
    if not obj:
        return None, (jsonify({"error": error_msg}), 404) # Return error if no entry found
    return obj, None 

# Helper to validate required fields in JSON data
def validate_fields(data, required_fields):
    missing = [field for field in required_fields if data.get(field) is None]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    return None


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

    def to_dict(self): # Convert reading to dictionary
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

    def to_dict(self): # Convert alert to dictionary
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
        Humidity=data.get("Humidity"),
        CO2_reading=data.get("CO2_reading"),
        CO_Reading=data.get("CO_Reading"),
        movement=data.get("movement")
    )
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
    error = validate_fields(data, ["Pi_ID", "Message_Alert"]) # Validate fields required for an alert
    if error:
        return error

    alert = Alerts( # Create new Alerts object
        Pi_ID=data.get("Pi_ID"), # ID of the Pi generating the alert
        Threshold=data.get("Threshold"), # Threshold value that triggered the alert
        Motion=data.get("Motion"), # Used for test sensor alongside movement
        Message_Alert=data.get("Message_Alert") # Alert message
    )

    save(alert) # Save alert to database
    return jsonify({"status": "alert added"}), 201 # Return success response

@app.get("/api/latest/alert") # Route to get latest alert
def latest_alert(): # Get latest alert from database
    alert, error = get_latest( Alerts, Alerts.Alerts_Timestamp, "No alerts found" ) # Get latest alert
    if error: 
        return error
    return jsonify(alert.to_dict()) # Return latest alert as JSON

# Dashboard route to view sensor readings on a web page 
@app.get("/dashboard/sensors") # Route to view sensor readings dashboard
def dashboard_sensors(): # View sensor readings dashboard
    readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(50).all() # Get latest 50 sensor readings
    return render_template("sensor_dashboard.html", readings=readings) # Render sensor dashboard template

# Run the program
if __name__ == "__main__": # Main program
    app.run(host="0.0.0.0", port=5000) # use instead when deploying to the Pi

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
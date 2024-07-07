from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import sqlite3
import uuid
from datetime import datetime, date, time
import pytz

app = Flask(__name__)

UPLOAD_FOLDER = './static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['IMG_WIDTH'] = 640
app.config['IMG_UPLOAD_FOLDER'] = './data/img'
app.config['DB_LOCATION'] = 'data/db/my_feedback.db'
app.config['production'] = True 

tz = pytz.timezone('Australia/Sydney')

# Create a SQLite database and table
conn = sqlite3.connect(app.config['DB_LOCATION'])
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        detail TEXT NOT NULL,
        type_id INTEGER NOT NULL,
        sub_type TEXT NOT NULL,
        loc TEXT NOT NULL,
        img_name TEXT NOT NULL,
        created_date TEXT NOT NULL,
        CONSTRAINT fk_type  
        FOREIGN KEY (type_id) 
        REFERENCES Type(type_id) 
    )
''')
conn.commit()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
''')
conn.commit()
conn.close()

@app.route("/")
def index():
  
  return render_template("index.html")

@app.route("/add")
def add():
  conn = sqlite3.connect(app.config['DB_LOCATION'])
  cursor = conn.cursor()
  cursor.execute('SELECT id, name FROM Type') 
  types = cursor.fetchall()
  conn.close()

  return render_template("add.html",types=types)


@app.route("/insert_types", methods=['GET'])
def insert_types():
  
  if app.config['production'] is not True:
    conn = sqlite3.connect(app.config['DB_LOCATION'])
    cursor = conn.cursor()
    types= ['Restaurant', 'Grocery','Food','Experience', 'Electronics', 'Toys', 'Other']
    for name in types:
        cursor.execute("""INSERT INTO Type (name) VALUES (?)""", [name])
        conn.commit()
    conn.close()
    
    return "Inserting types data is successful"
  else:
    return "Not allowed in prod enviornment"


def resize_with_aspect_ratio(image, width=None, height=None):
    # Get the original image dimensions
    h, w = image.shape[:2]

    # Calculate the aspect ratio
    aspect_ratio = w / h

    if width is None:
        # Calculate height based on the specified width
        new_height = int(height / aspect_ratio)
        resized_image = cv2.resize(image, (height, new_height))
    else:
        # Calculate width based on the specified height
        new_width = int(width * aspect_ratio)
        resized_image = cv2.resize(image, (new_width, width))

    return resized_image

# https://pynative.com/python-sqlite-blob-insert-and-retrieve-digital-data/
def writeTofile(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)
    print("Stored blob data into: ", filename, "\n")


# https://pynative.com/python-sqlite-blob-insert-and-retrieve-digital-data/
def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData


@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    title = request.form['title'].lower()
    detail = request.form['feedback']
    type_id = request.form['type']
    sub_type = request.form['sub_type']
    loc = request.form['location']
    if title != "" and detail != "" and request.method == 'POST':
        
        f = request.files['file']

        # create a secure filename
        filename = secure_filename(f.filename)

        # save file to /static/uploads
        filepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
        f.save(filepath)
        
        # load the example image and convert it to grayscale
        image = cv2.imread(filepath)

        # Resize the image with an aspect ratio
        image = resize_with_aspect_ratio(image, width=app.config['IMG_WIDTH'] )

        # remove the original image
        os.remove(filepath)

        unique_filename = str(uuid.uuid4())
        image_name = "{}.png".format(unique_filename)

        # save the processed image in the /static/uploads directory
        ofilename = os.path.join(app.config['IMG_UPLOAD_FOLDER'],image_name)
        cv2.imwrite(ofilename, image)
        created_datetime = datetime.now(tz)

        conn = sqlite3.connect(app.config['DB_LOCATION'])
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO Feedback (title, detail, type_id, sub_type, loc, img_name, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)""", [title.lower(), detail, type_id, sub_type, loc, image_name, created_datetime])
        conn.commit()    

        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM Type') 
        types = cursor.fetchall()
        conn.close() 

        return render_template("uploaded.html", types=types)

    else:
        return render_template("error.html")

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(debug=True, host='0.0.0.0', port=port)

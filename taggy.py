from flask import Flask, request, render_template, redirect, url_for, g
from werkzeug.utils import secure_filename
import os
import csv
from flask import request, jsonify
import atexit
import pytrie
from string import ascii_lowercase, digits
import pickle
import shutil

app = Flask(__name__, static_folder='static', template_folder='templates')

# Setup the upload directory
UPLOAD_FOLDER = './static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/tags', methods=['GET'])
def tags():
    if hasattr(g, "csv_tags"):
        return jsonify(list(g.csv_tags.keys()))
    else:
        return jsonify([])

first_request = True
trie_file = 'tags_trie.pkl'

@app.before_request
def load_csv_files():
    global first_request
    if first_request:
        global csv_tags
        # Try to load the Trie from the pickle file
        try:
            with open(trie_file, 'rb') as f:
                csv_tags = pickle.load(f)
        except (FileNotFoundError, IOError):
            print("No tag pickle found, creating tag autocomplete trie database.")
            csv_tags = pytrie.StringTrie()  # Initialize the Trie

            # Walk through the directory and get all CSV files
            for root, dirs, files in os.walk('./static/tags'):
                for file in files:
                    if file.endswith('.csv'):
                        csv_filepath = os.path.join(root, file)
                        try:
                            with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
                                reader = csv.reader(csvfile)
                                for row in reader:
                                    # Add the first column of each row to the set, replacing underscores with spaces
                                    csv_tags[row[0].lower().replace('_', ' ')] = True
                        except FileNotFoundError:
                            print(f"{csv_filepath} not found.")

            # Save the Trie to the pickle file for future use
            with open(trie_file, 'wb') as f:
                pickle.dump(csv_tags, f)
        first_request = False

@app.route('/save', methods=['POST'])
def save_files():
    # Create outputs directory if it doesn't exist
    os.makedirs('./outputs', exist_ok=True)

    # Copy files from uploads to outputs
    for filename in os.listdir('./static/uploads'):
        shutil.copy(os.path.join('./static/uploads', filename),
                    os.path.join('./outputs', filename))
    return '', 200

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower().replace('_', ' ')
    if query:
        # Use the Trie's prefix method to get all keys that start with the query
        suggestions = [key for key in csv_tags.iterkeys(query)]
        suggestions = suggestions[:10]
        suggestions = [suggestion.replace(' ', '_') for suggestion in suggestions]
        return jsonify(suggestions)
    else:
        return jsonify([])
    
@app.route('/copy-to-directory', methods=['POST'])
def copy_to_directory():
    target_directory = request.json['directory']
    try:
        shutil.copytree(app.config['UPLOAD_FOLDER'], target_directory)
        return '', 200
    except Exception as e:
        return str(e), 500

@app.route('/tag-pane')
def tag_pane():
    return render_template('tag_pane.html')

@app.route('/update-file/<filename>', methods=['POST'])
def update_file(filename):
    try:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w') as file:
            file.write(request.data.decode('utf-8'))
            return '', 200
    except IOError:
        return '', 404

@app.route('/', methods=['GET', 'POST'])
def upload_display():
    image_filenames = []
    txt_filenames = []
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        files = request.files.getlist('file')
        for file in files:
            if file and file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'txt'}:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}:
                    image_filenames.append(filename)
                elif filename.rsplit('.', 1)[1].lower() == 'txt':
                    txt_filenames.append(filename)
    return render_template('index.html', filenames=image_filenames, txtFilenames=txt_filenames)

@app.route('/file/<filename>')
def file(filename):
    try:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as file:
            return file.read()
    except IOError:
        return '', 404

def cleanup():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename != 'githubmademedothis.txt':
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

atexit.register(cleanup)

if __name__ == "__main__":
    app.run()
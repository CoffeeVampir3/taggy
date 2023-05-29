from flask import Flask, request, render_template, redirect, url_for, g
from werkzeug.utils import secure_filename
import os
import csv
from flask import request, jsonify
import atexit
import datrie
from string import ascii_lowercase, digits
import pickle

app = Flask(__name__)

# Setup the upload directory
UPLOAD_FOLDER = './static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/tags', methods=['GET'])
def tags():
    if hasattr(g, "csv_tags"):
        return jsonify(list(g.csv_tags))
    else:
        return jsonify([])

first_request = True
trie_chars = ascii_lowercase + digits + ' _'
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
            csv_tags = datrie.Trie(trie_chars)  # Initialize the Trie
            csv_filenames = ["danbooru.csv", "e621.csv"]
            for csv_filename in csv_filenames:
                try:
                    with open(os.path.join('./static', csv_filename), newline='') as csvfile:
                        reader = csv.reader(csvfile)
                        for row in reader:
                            # Add the first column of each row to the set, replacing underscores with spaces
                            csv_tags[row[0].lower().replace('_', ' ')] = True
                except FileNotFoundError:
                    print(f"{csv_filename} not found.")
            # Save the Trie to the pickle file for future use
            with open(trie_file, 'wb') as f:
                pickle.dump(csv_tags, f)
        first_request = False

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower().replace('_', ' ')
    if query:
        # Use the Trie's prefix method to get all keys that start with the query
        suggestions = csv_tags.keys(query)
        suggestions = suggestions[:10]
        suggestions = [suggestion.replace(' ', '_') for suggestion in suggestions]
        return jsonify(suggestions)
    else:
        return jsonify([])

@app.route('/tag-pane')
def tag_pane():
    return render_template('tag_pane.html')

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
    return render_template('upload_display.html', filenames=image_filenames, txtFilenames=txt_filenames)


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
    app.run(debug=True)
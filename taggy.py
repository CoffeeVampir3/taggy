from flask import Flask, request, render_template, redirect, url_for, g
from werkzeug.utils import secure_filename
import os
import csv
from flask import request, jsonify


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

csv_tags = set()
first_request = True
@app.before_request
def load_csv_files():
    global first_request
    if first_request:
        csv_filenames = ["danbooru.csv", "e621.csv"]
        global csv_tags
        for csv_filename in csv_filenames:
            try:
                with open(os.path.join('./static', csv_filename), newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        csv_tags.add(row[0])  # Add the first column of each row to the set
            except FileNotFoundError:
                print(f"{csv_filename} not found.")
            first_request = False

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '')
    if query:
        print(query)
        suggestions = [tag for tag in csv_tags if tag.startswith(query)]
        print("banana")
        return jsonify(suggestions[:10])
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


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, send_file
from rembg import remove
from PIL import Image
import os
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "No file found", 400

    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    orig_name = secure_filename(file.filename)
    orig_path = os.path.join(app.config['UPLOAD_FOLDER'], orig_name)
    file.save(orig_path)

    # Background removal
    with Image.open(orig_path) as img:
        img = img.convert("RGBA")
        result = remove(img)

        # HD output
        hd_name = 'no_bg_' + os.path.splitext(orig_name)[0] + '.png'
        hd_path = os.path.join(app.config['UPLOAD_FOLDER'], hd_name)
        result.save(hd_path)

        # Standard output
        std_name = 'std_' + os.path.splitext(orig_name)[0] + '.png'
        std_path = os.path.join(app.config['UPLOAD_FOLDER'], std_name)
        result.save(std_path, format="PNG", optimize=True, quality=70)

    return redirect(url_for('result',
                            filename=hd_name,
                            std_filename=std_name,
                            original=orig_name))


@app.route('/result')
def result():
    # From upload or sample image
    sample_image = request.args.get('image')
    if sample_image:
        sample_name = secure_filename(sample_image)
        sample_path = os.path.join('static', sample_name)
        if not os.path.exists(sample_path):
            return "Sample image not found", 404

        dest_path = os.path.join(app.config['UPLOAD_FOLDER'], sample_name)
        if not os.path.exists(dest_path):
            shutil.copyfile(sample_path, dest_path)

        # Remove background
        with Image.open(dest_path) as img:
            img = img.convert("RGBA")
            result_img = remove(img)

            hd_name = 'no_bg_' + os.path.splitext(sample_name)[0] + '.png'
            hd_path = os.path.join(app.config['UPLOAD_FOLDER'], hd_name)
            result_img.save(hd_path)

            std_name = 'std_' + os.path.splitext(sample_name)[0] + '.png'
            std_path = os.path.join(app.config['UPLOAD_FOLDER'], std_name)
            result_img.save(std_path, format="PNG", optimize=True, quality=70)

        return render_template('result.html',
                               original_filename=sample_name,
                               filename=hd_name,
                               std_filename=std_name)

    # From upload flow
    filename = request.args.get('filename')
    std_filename = request.args.get('std_filename')
    original = request.args.get('original')

    if not filename or not std_filename or not original:
        return "Image missing", 400

    return render_template('result.html',
                           original_filename=original,
                           filename=filename,
                           std_filename=std_filename)


@app.route('/download/<quality>/<filename>')
def download_image(quality, filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(path):
        return f"File not found: {path}", 404

    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
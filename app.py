import os
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from watermark_pdf import watermark_image_to_pdf
import fitz  # PyMuPDF
from PIL import Image  # Tambahkan PIL untuk convert TIFF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def convert_pdf_to_tiff(pdf_path):
    doc = fitz.open(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    folder_name = os.path.join(os.path.dirname(pdf_path), base_name)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    for page_number in range(doc.page_count):
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        output_tiff_path = os.path.join(folder_name, f"page_{page_number + 1}.tiff")
        img.save(output_tiff_path, format="TIFF")

    doc.close()

@app.route('/')
def index():
    return render_template('upload_form.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    pdf_files = request.files.getlist('pdf_files')
    watermark_image = request.files['watermark_image']

    if not pdf_files or watermark_image.filename == '':
        return "No file selected", 400

    wm_name = secure_filename(watermark_image.filename)
    wm_path = os.path.join(app.config['UPLOAD_FOLDER'], wm_name)
    watermark_image.save(wm_path)

    output_files = []
    for pdf in pdf_files:
        if pdf and allowed_file(pdf.filename):
            pdf_name = secure_filename(pdf.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
            pdf.save(pdf_path)

            out_pdf = pdf_name.replace('.pdf', '_watermarked.pdf')
            out_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], out_pdf)
            
            # Watermark-kan PDF
            watermark_image_to_pdf(pdf_path, wm_path, out_pdf_path)
            
            # Hapus file PDF asli
            os.remove(pdf_path)

            # === CONVERT WATERMARKED PDF KE TIFF ===
            convert_pdf_to_tiff(out_pdf_path)

            output_files.append(out_pdf_path)

    # Kirim file hasil watermark pertama
    return send_file(output_files[0], as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

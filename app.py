from flask import Flask, render_template, url_for, request, send_file, flash
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os
import pytesseract
import cv2
import ocrmypdf
import pdfplumber
from pdf2image import convert_from_path


# pytesseract on Heroku (deployment ONLY)
pytesseract.pytesseract.tesseract_cmd = "/app/.apt/usr/bin/tesseract"

project_direction = os.path.dirname(os.path.abspath(__file__))

# Initiate the app
app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates'
            )

photos = UploadSet('photos', IMAGES)

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'key'
app.config['UPLOAD_FOLDER'] = 'static/files'
ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_PDF = {'txt', 'pdf'}


def allowed_file_img(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG


def allowed_file_pdf(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_PDF


def image_processing(img_lang):
    img = cv2.imread('static/files/test.png')
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    config = r'--oem 3 --psm 6'
    text = ''
    text = pytesseract.image_to_string(img, config=config, lang=img_lang)
    data = pytesseract.image_to_data(img, config=config, lang=img_lang)
    for i, el in enumerate(data.splitlines()):
        if i == 0:
            continue
        el = el.split()
        try:
            x, y, w, h = int(el[6]), int(el[7]), int(el[8]), int(el[9])
            cv2.rectangle(img, (x, y), (w + x, h + y), (0, 0, 255), 1)
            cv2.putText(img, el[11], (x, y), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 1)
        except IndexError:
            continue
    cv2.imwrite('static/files/test_complete.png', img)
    return text


def pdf_processing(pdf_lang):
    ocrmypdf.ocr("static/files/test.pdf", "static/files/complete_pdf.pdf", skip_text=True)
    if pdf_lang == 'eng':
        with pdfplumber.open('static/files/complete_pdf.pdf') as pdf:
            total_pages = len(pdf.pages)
            text_pdf = ''
            for i in range(0, total_pages):
                page = pdf.pages[i]
                text_pdf_temp = page.extract_text(x_tolerance=2)
                text_pdf = text_pdf + '\n' + text_pdf_temp
        return text_pdf
    else:
        pages = convert_from_path('static/files/complete_pdf.pdf', 500)
        text_pdf = ''
        for page in pages:
            page.save('static/files/pdf_img_temp.png', 'PNG')
            img = cv2.imread('static/files/pdf_img_temp.png')
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            config = r'--oem 3 --psm 6'
            text = ''
            text = pytesseract.image_to_string(img, config=config, lang=pdf_lang)
            text_pdf = text_pdf + '\n' + text
        return text_pdf


def pdf_copy():
    ocrmypdf.ocr("static/files/test.pdf", "static/files/complete_pdf.pdf", skip_text=True)
    return 0


@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/en/')
@app.route('/home/en/')
def home_en():
    return render_template("index_en.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/about/en/')
def about_en():
    return render_template("about_en.html")


@app.route('/img', methods=['GET', 'POST'])
def img_page():
    if request.method == 'POST':
        if 'photo' not in request.files:
            return render_template('500.html', text_error = 'Відбулась помилка.. Можливо ви намагаєтесь завантажити файл не відповідного формату.. '), 500
        name = 'test.png'
        photo = request.files['photo']
        if photo.filename == '':
            flash('Файл без назви')
            return render_template('500.html', text_error = 'Відбулась помилка.. Файл не було обрано.. '), 500
        if photo and allowed_file_img(photo.filename):
            path = os.path.join(app.config['UPLOAD_FOLDER'], name)
            photo.save(path)
            img_lang = request.form.get('language_img')

            lang_small = ['eng', 'ukr', 'rus']
            for i, j in enumerate(['English', 'Ukrainian', 'Russian']):
                if j == img_lang:
                    img_lang = lang_small[i]

            img_proc = image_processing(img_lang)
            return render_template("img_work.html", text=img_proc)
        else:
            return render_template('500.html', text_error='Відбулась помилка.. Можливо ви намагаєтесь завантажити файл не відповідного формату.. '), 500
    return render_template("img.html")


@app.route('/img/en/', methods=['GET', 'POST'])
def img_page_en():
    if request.method == 'POST':
        if 'photo' not in request.files:
            return render_template ('500.html', text_error = 'An error occurred. You may be trying to upload an inappropriate file.'), 500
        name = 'test.png'
        photo = request.files['photo']
        if photo.filename == '':
            flash('Untitled file')
            return render_template('500.html', text_error = 'An error occurred .. The file was not selected ..'), 500
        if photo and allowed_file_img(photo.filename):
            path = os.path.join(app.config['UPLOAD_FOLDER'], name)
            photo.save(path)
            img_lang = request.form.get('language_img')

            lang_small = ['eng', 'ukr', 'rus']
            for i, j in enumerate(['English', 'Ukrainian', 'Russian']):
                if j == img_lang:
                    img_lang = lang_small[i]

            img_proc = image_processing(img_lang)
            return render_template("img_work_en.html", text=img_proc)
        else:
            return render_template('500.html',text_error='An error occurred. You may be trying to upload an inappropriate file.'), 500
    return render_template("img_en.html")


@app.route('/pdf', methods=['GET', 'POST'])
def pdf_page():
    if request.method == 'POST':
        if 'pdf' in request.files:
            name = 'test.pdf'
            photo = request.files['pdf']
            if photo and allowed_file_pdf(photo.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER'], name)
                photo.save(path)
                pdf_lang = request.form.get('language_pdf')

                lang_small = ['eng', 'ukr', 'rus']
                for i, j in enumerate(['English', 'Ukrainian', 'Russian']):
                    if j == pdf_lang:
                        pdf_lang = lang_small[i]

                with pdfplumber.open('static/files/test.pdf') as pdf:
                    total_pages = len(pdf.pages)
                    if total_pages > 3:
                        return render_template('500.html', text_error = 'Занадто багато сторінок у файлі. Тестова версія обмежена не більше 3-ом сторінками '), 500
                    else:
                        pdf_proc = pdf_processing(pdf_lang)
                        return render_template("pdf_work.html", text_pdf=pdf_proc)
            else:
                return render_template('500.html', text_error='Відбулась помилка.. Можливо ви намагаєтесь завантажити файл не відповідного формату.. '), 500
        elif 'pdf_copy' in request.files:
            name = 'test.pdf'
            photo = request.files['pdf_copy']
            if photo and allowed_file_pdf(photo.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER'], name)
                photo.save(path)
                with pdfplumber.open('static/files/test.pdf') as pdf:
                    total_pages = len(pdf.pages)
                    if total_pages > 3:
                        return render_template('500.html', text_error = 'Занадто багато сторінок у файлі. Тестова версія обмежена не більше 3-ом сторінками '), 500
                    else:
                        ocrmypdf.ocr("static/files/test.pdf", "static/files/complete_pdf.pdf", skip_text=True)
                        return send_file('static/files/complete_pdf.pdf', as_attachment=True)
            else:
                return render_template('500.html', text_error='Відбулась помилка.. Можливо ви намагаєтесь завантажити файл не відповідного формату.. '), 500
        else:
            return render_template('500.html'), 500
    return render_template("pdf.html")


@app.route('/pdf/en/', methods=['GET', 'POST'])
def pdf_page_en():
    if request.method == 'POST':
        if 'pdf' in request.files:
            name = 'test.pdf'
            photo = request.files['pdf']
            if photo and allowed_file_pdf(photo.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER'], name)
                photo.save(path)
                pdf_lang = request.form.get('language_pdf')

                lang_small = ['eng', 'ukr', 'rus']
                for i, j in enumerate(['English', 'Ukrainian', 'Russian']):
                    if j == pdf_lang:
                        pdf_lang = lang_small[i]

                with pdfplumber.open('static/files/test.pdf') as pdf:
                    total_pages = len(pdf.pages)
                    if total_pages > 3:
                        return render_template('500_en.html', text_error = 'Too many pages in file. Test version limited to no more than 3 pages'), 500
                    else:
                        pdf_proc = pdf_processing(pdf_lang)
                        return render_template("pdf_work.html", text_pdf=pdf_proc)
            else:
                return render_template('500.html', text_error='An error occurred. You may be trying to upload an inappropriate file.'), 500
        elif 'pdf_copy' in request.files:
            name = 'test.pdf'
            photo = request.files['pdf_copy']
            if photo and allowed_file_pdf(photo.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER'], name)
                photo.save(path)
                with pdfplumber.open('static/files/test.pdf') as pdf:
                    total_pages = len(pdf.pages)
                    if total_pages > 3:
                        return render_template('500_en.html', text_error = 'Too many pages in file. Test version limited to no more than 3 pages'), 500
                    else:
                        ocrmypdf.ocr("static/files/test.pdf", "static/files/complete_pdf.pdf", skip_text=True)
                        return send_file('static/files/complete_pdf.pdf', as_attachment=True)
            else:
                return render_template('500.html', text_error='An error occurred. You may be trying to upload an inappropriate file.'), 500
        else:
            return render_template('500_en.html'), 500
    return render_template("pdf_en.html")


# Invalid page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# Server Error
@app.errorhandler(500)
def page_error(e):
    return render_template('500.html'), 500


# Server Error en
@app.errorhandler(500)
def page_error_en(e):
    return render_template('500_en.html'), 500


if __name__ == '__main__':
    app.run()
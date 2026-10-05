from flask import Flask, request, redirect, url_for, render_template_string
import PyPDF2, math, sqlite3, os, pyqrcode
from io import BytesIO

app = Flask(__name__)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'printing_orders.db')

def db():
    try:
        con = sqlite3.connect(DB)
        con.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, name TEXT, phone TEXT, papers INTEGER, price REAL, status TEXT DEFAULT 'active')''')
        con.commit(); con.close()
    except: pass
db()

CSS = "body{font-family:Arial;padding:15px;background:#f4f6f9;direction:rtl}.card{background:#fff;padding:15px;border-radius:10px;max-width:500px;margin:auto}.btn{display:block;text-align:center;color:#fff;text-decoration:none;padding:12px;border-radius:6px;margin-top:10px;font-weight:bold;border:0;width:100%;box-sizing:border-box}table{width:100%;border-collapse:collapse;margin-top:10px}th,td{padding:8px;border:1px solid #ddd;text-align:center;font-size:14px}th{background:#4CAF50;color:#fff}input,select{width:100%;padding:10px;margin:5px 0 15px;border:1px solid #ccc;border-radius:6px;box-sizing:border-box}"

@app.route('/')
def index():
    return render_template_string(f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>{CSS}</style></head><body><div class='card'><h2 style='color:#2E7D32;text-align:center'>🏠 إدارة الطباعة</h2><a href='/new' class='btn' style='background:#4CAF50'>📄 أوردر جديد</a><a href='/log' class='btn' style='background:#2196F3'>📂 سجل الحسابات</a><a href='/qr' class='btn' style='background:#333'>🔲 باركود الجروب</a></div></body></html>")

@app.route('/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        try:
            name, phone, slides = request.form['name'], request.form.get('phone') or 'لا يوجد', int(request.form['slides'])
            total_slides = sum(len(PyPDF2.PdfReader(f.stream).pages) for f in request.files.getlist('files') if f.filename.endswith('.pdf'))
            papers, price = math.ceil(total_slides / slides), math.ceil(total_slides / slides) * 0.80

            con = sqlite3.connect(DB)
            con.execute("INSERT INTO orders (date, name, phone, papers, price) VALUES (datetime('now', 'localtime'), ?, ?, ?, ?)", (name, phone, papers, price))
            con.commit(); con.close()

            return render_template_string(f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>{CSS}</style></head><body><div class='card'><h2 style='text-align:center'>🧾 ريسيت الطباعة</h2><hr><p><b>الاسم:</b> {name}</p><p><b>الموبايل:</b> {phone}</p><hr><h3 style='color:red;text-align:center'>الورق: {papers} ورقة</h3><h2 style='color:red;text-align:center'>السعر: {price:.2f} ج</h2><a href='/new' class='btn' style='background:#2196F3'>أوردر جديد</a><a href='/' class='btn' style='background:#333'>الرئيسية</a></div></body></html>")
        except Exception as e: return f"<h3 style='text-align:center;color:red'>خطأ: {e}<br><a href='/new'>رجوع</a></h3>"
    return render_template_string(f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>{CSS}</style></head><body><div class='card'><a href='/' style='float:left'>الرئيسية</a><h2>📄 أوردر جديد</h2><form method='POST' enctype='multipart/form-data'><label>اسم الطالب:</label><input type='text' name='name' required><label>الموبايل:</label><input type='text' name='phone'><label>نظام الطباعة:</label><select name='slides'><option value='2'>2 سلايد</option><option value='4' selected>4 سلايد</option><option value='6'>6 سلايد</option></select><label>ملفات PDF:</label><input type='file' name='files' accept='.pdf' multiple required><button type='submit' class='btn' style='background:#4CAF50'>حساب وإصدار الريسيت</button></form></div></body></html>")

@app.route('/log')
def log():
    try:
        con = sqlite3.connect(DB); rows = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall(); con.close()
    except: rows = []
    tr = "".join([f"<tr><td>{r[2]}</td><td>{r[4]} ورقة</td><td style='color:red;font-weight:bold'>{r[5]} ج</td><td><a href='/del/{r[0]}' style='color:red'>تسليم</a></td></tr>" for r in rows])
    return render_template_string(f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>{CSS}</style></head><body><div class='card' style='max-width:700px'><a href='/' style='float:left'>الرئيسية</a><h2>📂 السجل</h2><a href='/clear' class='btn' style='background:#F44336' onclick=\"return confirm('مسح الكل؟');\">🗑️ مسح جميع الأوردرات بضغطة</a><table><tr><th>الاسم</th><th>الورق</th><th>السعر</th><th>إجراء</th></tr>{tr}</table></div></body></html>")

@app.route('/del/<int:id>')
def delete(id):
    try:
        con = sqlite3.connect(DB); con.execute("DELETE FROM orders WHERE id=?", (id,)); con.commit(); con.close()
    except: pass
    return redirect(url_for('log'))

@app.route('/clear')

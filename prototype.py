from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

PDF_DIR = os.path.join(os.path.dirname(__file__), 'generated_pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

# 1. 【トップ画面】高校生向け：生成済み企業PDF一覧・閲覧ページ
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>鳥栖市 高校生向け企業紹介冊子</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
        .container { max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 8px; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .admin-btn { background-color: #28a745; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 14px; }
        .admin-btn:hover { background-color: #218838; }
        ul { padding-left: 20px; }
        li { margin-bottom: 12px; font-size: 16px; }
        a.pdf-link { color: #007bff; text-decoration: none; font-weight: bold; }
        a.pdf-link:hover { text-decoration: underline; }
        .no-data { color: #777; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>📖 鳥栖市 企業紹介冊子（高校生向け閲覧ページ）</h2>
            <a href="/form" class="admin-btn">企業向け入力フォームへ ➔</a>
        </div>
        
        <p>以下の企業名をクリックすると、各社の紹介PDFをブラウザで閲覧・ダウンロードできます。</p>
        
        {% if files %}
            <ul>
                {% for file in files %}
                    <li>
                        <a href="/view/{{ file }}" target="_blank" class="pdf-link">📄 {{ file.replace('_紹介シート.pdf', '') }} の紹介シート</a>
                    </li>
                {% endfor %}
            </ul>
        {% else %}
            <p class="no-data">現在、公開されている企業紹介PDFはありません。（企業フォームから情報を登録してください）</p>
        {% endif %}
    </div>
</body>
</html>
"""

# 2. 【サブ画面】企業向け：データ入力フォーム
FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>企業紹介情報 入力フォーム</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
        .container { max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #333; }
        label { display: block; margin-top: 15px; font-weight: bold; }
        input[type="text"], textarea { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        textarea { height: 120px; }
        .btn-group { margin-top: 20px; display: flex; gap: 10px; align-items: center; }
        button { background-color: #007bff; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .back-link { color: #6c757d; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h2>企業紹介データ 入力フォーム</h2>
        <!-- 確認画面（/confirm）へデータをPOSTする -->
        <form method="POST" action="/confirm">
            <label>企業名：</label>
            <input type="text" name="company_name" required placeholder="例：株式会社 鳥栖テクノロジー">
            
            <label>キャッチコピー：</label>
            <input type="text" name="catchphrase" required placeholder="例：未来を創る、技術と情熱。">
            
            <label>企業PR・事業内容：</label>
            <textarea name="description" required placeholder="会社の魅力や業務内容を記入してください"></textarea>
            
            <label>担当者連絡先：</label>
            <input type="text" name="contact" required placeholder="example@tosu.lg.jp">
            
            <div class="btn-group">
                <button type="submit">入力内容を確認する</button>
                <a href="/" class="back-link">← 閲覧ページに戻る</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

# 3. 【新設】入力内容の確認画面
CONFIRM_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>入力内容の確認</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
        .container { max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #333; }
        .info-box { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 15px; border: 1px solid #dee2e6; }
        .info-item { margin-bottom: 10px; }
        .label { font-weight: bold; color: #555; }
        .value { margin-top: 3px; white-space: pre-wrap; }
        .btn-group { margin-top: 20px; display: flex; gap: 10px; }
        button { background-color: #28a745; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #218838; }
        .back-btn { background-color: #6c757d; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; text-align: center; }
        .back-btn:hover { background-color: #5a6268; }
    </style>
</head>
<body>
    <div class="container">
        <h2>入力内容の確認</h2>
        <p>以下の内容で間違いがなければ、「この内容でPDFを生成・公開する」ボタンを押してください。</p>
        
        <div class="info-box">
            <div class="info-item">
                <div class="label">企業名：</div>
                <div class="value">{{ company_name }}</div>
            </div>
            <div class="info-item">
                <div class="label">キャッチコピー：</div>
                <div class="value">{{ catchphrase }}</div>
            </div>
            <div class="info-item">
                <div class="label">企業PR・事業内容：</div>
                <div class="value">{{ description }}</div>
            </div>
            <div class="info-item">
                <div class="label">担当者連絡先：</div>
                <div class="value">{{ contact }}</div>
            </div>
        </div>

        <!-- 実際にPDF生成を行う /generate-pdf にデータを引き継いで送るフォーム -->
        <form method="POST" action="/generate-pdf">
            <input type="hidden" name="company_name" value="{{ company_name }}">
            <input type="hidden" name="catchphrase" value="{{ catchphrase }}">
            <input type="hidden" name="description" value="{{ description }}">
            <input type="hidden" name="contact" value="{{ contact }}">
            
            <div class="btn-group">
                <button type="submit">この内容でPDFを生成・公開する</button>
                <a href="/form" class="back-btn">入力画面に戻って修正する</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    files = os.listdir(PDF_DIR)
    pdf_files = [f for f in files if f.endswith('.pdf')]
    return render_template_string(INDEX_TEMPLATE, files=pdf_files)

@app.route('/form')
def form_page():
    return render_template_string(FORM_TEMPLATE)

@app.route('/confirm', methods=['POST'])
def confirm_page():
    # フォームから受け取ったデータをそのまま確認画面テンプレートに渡す
    company_name = request.form.get('company_name')
    catchphrase = request.form.get('catchphrase')
    description = request.form.get('description')
    contact = request.form.get('contact')
    
    return render_template_string(
        CONFIRM_TEMPLATE,
        company_name=company_name,
        catchphrase=catchphrase,
        description=description,
        contact=contact
    )

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    company_name = request.form.get('company_name')
    catchphrase = request.form.get('catchphrase')
    description = request.form.get('description')
    contact = request.form.get('contact')

    filename = f"{company_name}_紹介シート.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    
    # ReportLabでA4サイズのPDFを生成して保存
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    font_path = "C:/Windows/Fonts/meiryo.ttc"
    pdfmetrics.registerFont(TTFont('Meiryo', font_path))

    c.setFont("Meiryo", 20)
    c.drawString(50, height - 60, company_name)

    c.setFont("Meiryo", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(50, height - 90, f"「 {catchphrase} 」")

    c.setStrokeColorRGB(0, 0.33, 0.7)
    c.setLineWidth(2)
    c.line(50, height - 105, width - 50, height - 105)

    c.setFont("Meiryo", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(50, height - 140, "【 企業PR・事業内容 】")
    
    text_y = height - 170
    for line in description.split('\n'):
        c.drawString(50, text_y, line)
        text_y -= 20

    c.drawString(50, text_y - 20, f"【 お問合せ先 】 {contact}")

    c.setFont("Meiryo", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 40, "鳥栖市 高校生向け企業紹介冊子")

    c.showPage()
    c.save()

    return redirect(url_for('index'))

@app.route('/view/<filename>')
def view_pdf(filename):
    return send_from_directory(PDF_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
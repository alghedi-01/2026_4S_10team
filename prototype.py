from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

# 保存フォルダの定義
PDF_DIR = os.path.join(os.path.dirname(__file__), 'generated_pdfs')          # 最終的に高校生が見る公開用PDF
PENDING_DIR = os.path.join(os.path.dirname(__file__), 'pending_requests')    # 市役所の承認待ちデータ保存用
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

# 1. 【トップ画面】高校生向け：公開済み企業PDF一覧
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
        .nav-btns { display: flex; gap: 10px; }
        .btn-form { background-color: #007bff; color: white; padding: 8px 14px; border-radius: 4px; text-decoration: none; font-size: 13px; }
        .btn-form:hover { background-color: #0056b3; }
        .btn-admin { background-color: #dc3545; color: white; padding: 8px 14px; border-radius: 4px; text-decoration: none; font-size: 13px; }
        .btn-admin:hover { background-color: #c82333; }
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
            <h2>📖 鳥栖市 企業紹介冊子（高校生向け閲覧）</h2>
            <div class="nav-btns">
                <a href="/form" class="btn-form">企業向け入力 ➔</a>
                <a href="/admin" class="btn-admin">市役所管理画面 🔒</a>
            </div>
        </div>
        
        <p>以下の企業名をクリックすると、各社の紹介PDFを閲覧・ダウンロードできます。</p>
        
        {% if files %}
            <ul>
                {% for file in files %}
                    <li>
                        <a href="/view/{{ file }}" target="_blank" class="pdf-link">📄 {{ file.replace('_紹介シート.pdf', '') }} の紹介シート</a>
                    </li>
                {% endfor %}
            </ul>
        {% else %}
            <p class="no-data">現在、公開されている企業紹介PDFはありません。</p>
        {% endif %}
    </div>
</body>
</html>
"""

# 2. 【企業向け】情報入力フォーム
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

# 3. 【企業向け】入力内容の確認画面
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
        <p>内容に間違いがなければ、「市役所にアップロード申請をする」ボタンを押してください。</p>
        
        <div class="info-box">
            <div class="info-item"><div class="label">企業名：</div><div class="value">{{ company_name }}</div></div>
            <div class="info-item"><div class="label">キャッチコピー：</div><div class="value">{{ catchphrase }}</div></div>
            <div class="info-item"><div class="label">企業PR・事業内容：</div><div class="value">{{ description }}</div></div>
            <div class="info-item"><div class="label">担当者連絡先：</div><div class="value">{{ contact }}</div></div>
        </div>

        <form method="POST" action="/submit-to-admin">
            <input type="hidden" name="company_name" value="{{ company_name }}">
            <input type="hidden" name="catchphrase" value="{{ catchphrase }}">
            <input type="hidden" name="description" value="{{ description }}">
            <input type="hidden" name="contact" value="{{ contact }}">
            
            <div class="btn-group">
                <button type="submit">市役所にアップロード申請をする</button>
                <a href="/form" class="back-btn">修正する</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

# 4. 【市役所向け】承認待ち一覧・管理画面（PDFプレビューボタン付き）
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>市役所管理画面 - アップロード承認</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
        .container { max-width: 850px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #dee2e6; padding: 12px; text-align: left; vertical-align: middle; }
        th { background-color: #f8f9fa; }
        .btn-preview { background-color: #17a2b8; color: white; padding: 6px 10px; border-radius: 4px; text-decoration: none; font-size: 13px; display: inline-block; margin-bottom: 5px; }
        .btn-preview:hover { background-color: #138496; }
        .btn-approve { background-color: #28a745; color: white; padding: 6px 10px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-approve:hover { background-color: #218838; }
        .btn-reject { background-color: #dc3545; color: white; padding: 6px 10px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-reject:hover { background-color: #c82333; }
        .action-group { display: flex; gap: 5px; align-items: center; }
        .back-link { display: inline-block; margin-top: 20px; color: #6c757d; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
        .no-data { color: #777; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔒 市役所管理者ページ（承認待ち一覧）</h2>
        <p>申請されたPDFの内容を「PDFプレビュー」で確認し、問題なければ承認してください。</p>
        
        {% if items %}
            <table>
                <tr>
                    <th>企業名</th>
                    <th>確認用PDF</th>
                    <th>アクション</th>
                </tr>
                {% for item in items %}
                <tr>
                    <td><strong>{{ item.company_name }}</strong></td>
                    <td>
                        <!-- 市役所が申請中のPDFをブラウザでプレビューするためのリンク -->
                        <a href="/admin/view/{{ item.filename }}" target="_blank" class="btn-preview">🔍 PDFプレビュー</a>
                    </td>
                    <td>
                        <div class="action-group">
                            <form method="POST" action="/admin/approve" style="display:inline;">
                                <input type="hidden" name="filename" value="{{ item.filename }}">
                                <button type="submit" class="btn-approve">承認して公開</button>
                            </form>
                            <form method="POST" action="/admin/reject" style="display:inline;">
                                <input type="hidden" name="filename" value="{{ item.filename }}">
                                <button type="submit" class="btn-reject" onclick="return confirm('本当に却下しますか？');">却下</button>
                            </form>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <p class="no-data">現在、承認待ちの企業申請はありません。</p>
        {% endif %}
        
        <br>
        <a href="/" class="back-link">← 高校生向け閲覧ページに戻る</a>
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
    return render_template_string(
        CONFIRM_TEMPLATE,
        company_name=request.form.get('company_name'),
        catchphrase=request.form.get('catchphrase'),
        description=request.form.get('description'),
        contact=request.form.get('contact')
    )

@app.route('/submit-to-admin', methods=['POST'])
def submit_to_admin():
    company_name = request.form.get('company_name')
    catchphrase = request.form.get('catchphrase')
    description = request.form.get('description')
    contact = request.form.get('contact')

    filename = f"{company_name}_紹介シート.pdf"
    filepath = os.path.join(PENDING_DIR, filename)
    
    # 承認待ちフォルダにPDFを生成
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
    c.drawString(50, 40, "鳥栖市 高校生向け企業紹介冊子（承認待ちデータ）")
    c.showPage()
    c.save()

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ja">
    <head><meta charset="UTF-8"><title>申請完了</title></head>
    <body style="font-family:sans-serif; text-align:center; margin-top:100px;">
        <h2>🎉 市役소へのアップロード申請が完了しました！</h2>
        <p>担当者による確認・承認が行われた後、高校生向けのページに公開されます。</p>
        <br><a href="/" style="color:#007bff; text-decoration:none;">トップページ（閲覧ページ）に戻る</a>
    </body>
    </html>
    """)

@app.route('/admin')
def admin_page():
    files = os.listdir(PENDING_DIR)
    items = []
    for f in files:
        if f.endswith('.pdf'):
            comp_name = f.replace('_紹介シート.pdf', '')
            items.append({
                'filename': f,
                'company_name': comp_name
            })
    return render_template_string(ADMIN_TEMPLATE, items=items)

# 【追加】市役所管理画面から承認待ちPDFをプレビュー表示するためのルート
@app.route('/admin/view/<filename>')
def admin_view_pdf(filename):
    return send_from_directory(PENDING_DIR, filename)

@app.route('/admin/approve', methods=['POST'])
def admin_approve():
    filename = request.form.get('filename')
    src_path = os.path.join(PENDING_DIR, filename)
    dst_path = os.path.join(PDF_DIR, filename)
    
    if os.path.exists(src_path):
        with open(src_path, 'rb') as src:
            content = src.read()
        with open(dst_path, 'wb') as dst:
            dst.write(content)
        os.remove(src_path)
        
    return redirect(url_for('admin_page'))

@app.route('/admin/reject', methods=['POST'])
def admin_reject():
    filename = request.form.get('filename')
    target_path = os.path.join(PENDING_DIR, filename)
    if os.path.exists(target_path):
        os.remove(target_path)
    return redirect(url_for('admin_page'))

@app.route('/view/<filename>')
def view_pdf(filename):
    return send_from_directory(PDF_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
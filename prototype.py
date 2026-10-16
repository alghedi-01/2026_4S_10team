from flask import Flask, render_template_string, request, send_file
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

# 企業が入力するためのHTMLフォーム
FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>企業紹介情報 入力フォーム</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background-color: #f4f4f9; }
        .container { max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #333; }
        label { display: block; margin-top: 15px; font-weight: bold; }
        input[type="text"], textarea { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        textarea { height: 120px; }
        button { margin-top: 20px; background-color: #007bff; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h2>企業紹介データ入力</h2>
        <form method="POST" action="/generate-pdf">
            <label>企業名：</label>
            <input type="text" name="company_name" required placeholder="例：株式会社 鳥栖テクノロジー">
            
            <label>キャッチコピー：</label>
            <input type="text" name="catchphrase" required placeholder="例：未来を創る、技術と情熱。">
            
            <label>企業PR・事業内容：</label>
            <textarea name="description" required placeholder="会社の魅力や業務内容を記入してください"></textarea>
            
            <label>担当者連絡先：</label>
            <input type="text" name="contact" required placeholder="example@tosu.lg.jp">
            
            <button type="submit">プレビューPDFを生成・ダウンロード</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FORM_TEMPLATE)

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    company_name = request.form.get('company_name')
    catchphrase = request.form.get('catchphrase')
    description = request.form.get('description')
    contact = request.form.get('contact')

    pdf_file = io.BytesIO()
    
    # ReportLabでA4サイズのPDFを作成
    c = canvas.Canvas(pdf_file, pagesize=A4)
    width, height = A4

    # ※日本語フォントのパス（Windows標準のMeiryoを使用）
    font_path = "C:/Windows/Fonts/meiryo.ttc"
    pdfmetrics.registerFont(TTFont('Meiryo', font_path))

    # 描画処理
    c.setFont("Meiryo", 20)
    c.drawString(50, height - 60, company_name)

    c.setFont("Meiryo", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(50, height - 90, f"「 {catchphrase} 」")

    # 区切り線
    c.setStrokeColorRGB(0, 0.33, 0.7)
    c.setLineWidth(2)
    c.line(50, height - 105, width - 50, height - 105)

    # 企業PRセクション
    c.setFont("Meiryo", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(50, height - 140, "【 企業PR・事業内容 】")
    
    c.setFont("Meiryo", 10)
    # テキストを改行を考慮して簡易描画
    text_y = height - 170
    for line in description.split('\n'):
        c.drawString(50, text_y, line)
        text_y -= 20

    # 連絡先セクション
    c.drawString(50, text_y - 20, f"【 お問合せ先 】 {contact}")

    # フッター
    c.setFont("Meiryo", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 40, "鳥栖市 高校生向け企業紹介冊子")

    c.showPage()
    c.save()
    
    pdf_file.seek(0)

    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{company_name}_紹介シート.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
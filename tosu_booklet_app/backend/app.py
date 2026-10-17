from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
CORS(app)  # フロントエンド（別ポート）からの通信を許可する設定

# 保存フォルダの定義
PDF_DIR = os.path.join(os.path.dirname(__file__), 'generated_pdfs')          # 最終公開用PDF
PENDING_DIR = os.path.join(os.path.dirname(__file__), 'pending_requests')    # 市役所承認待ちPDF
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

# 1. 【API】公開済みPDFの一覧を返すエンドポイント
@app.route('/api/public-pdfs', methods=['GET'])
def get_public_pdfs():
    files = os.listdir(PDF_DIR)
    pdf_files = [f for f in files if f.endswith('.pdf')]
    return jsonify({'status': 'success', 'files': pdf_files})

# 2. 【API】企業からのデータを受け取り、承認待ちPDFを仮生成するエンドポイント
@app.route('/api/submit', methods=['POST'])
def submit_data():
    data = request.json
    company_name = data.get('company_name')
    catchphrase = data.get('catchphrase')
    description = data.get('description')
    contact = data.get('contact')

    if not company_name:
        return jsonify({'status': 'error', 'message': '企業名がありません'}), 400

    filename = f"{company_name}_紹介シート.pdf"
    filepath = os.path.join(PENDING_DIR, filename)
    
    # ReportLabでPDFを仮生成
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

    return jsonify({'status': 'success', 'message': '市役所への申請が完了しました'})

# 3. 【API】市役所の管理者向け：承認待ち一覧を返す
@app.route('/api/admin/pending', methods=['GET'])
def get_pending_requests():
    files = os.listdir(PENDING_DIR)
    items = []
    for f in files:
        if f.endswith('.pdf'):
            comp_name = f.replace('_紹介シート.pdf', '')
            items.append({
                'filename': f,
                'company_name': comp_name
            })
    return jsonify({'status': 'success', 'items': items})

# 4. 【API】市役所による承認処理（承認待ち ➔ 公開用へ移動）
@app.route('/api/admin/approve', methods=['POST'])
def admin_approve():
    data = request.json
    filename = data.get('filename')
    src_path = os.path.join(PENDING_DIR, filename)
    dst_path = os.path.join(PDF_DIR, filename)
    
    if os.path.exists(src_path):
        with open(src_path, 'rb') as src:
            content = src.read()
        with open(dst_path, 'wb') as dst:
            dst.write(content)
        os.remove(src_path)
        return jsonify({'status': 'success', 'message': '承認して公開しました'})
    
    return jsonify({'status': 'error', 'message': 'ファイルが見つかりません'}), 404

# 5. 【API】市役所による却下処理
@app.route('/api/admin/reject', methods=['POST'])
def admin_reject():
    data = request.json
    filename = data.get('filename')
    target_path = os.path.join(PENDING_DIR, filename)
    if os.path.exists(target_path):
        os.remove(target_path)
        return jsonify({'status': 'success', 'message': '却下しました'})
    return jsonify({'status': 'error', 'message': 'ファイルが見つかりません'}), 404

# PDFファイルの閲覧用ルート
@app.route('/view/<filename>')
def view_pdf(filename):
    return send_from_directory(PDF_DIR, filename)

@app.route('/admin/view/<filename>')
def admin_view_pdf(filename):
    return send_from_directory(PENDING_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
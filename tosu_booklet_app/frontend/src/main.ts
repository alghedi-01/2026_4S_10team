import { fetchPublicPdfs, submitCompanyData, fetchPendingRequests, approveRequest, rejectRequest } from './api';
import './style.css';

const app = document.getElementById('app')!;

// ルーティング（簡易的な画面切り替え）
function router() {
    const path = window.location.hash;
    if (path === '#form') {
        renderFormPage();
    } else if (path === '#admin') {
        renderAdminPage();
    } else {
        renderIndexPage();
    }
}

// 1. 高校生向けトップ画面
async function renderIndexPage() {
    const files = await fetchPublicPdfs();
    
    app.innerHTML = `
        <div class="container">
            <header class="header-bar">
                <h2>📖 鳥栖市 企業紹介冊子</h2>
                <div class="nav-btns">
                    <a href="#form" class="btn btn-primary">企業向け入力 ➔</a>
                    <a href="#admin" class="btn btn-danger">市役所管理画面 🔒</a>
                </div>
            </header>
            <p>以下の企業名をクリックすると、各社の紹介PDFを閲覧・ダウンロードできます。</p>
            <ul class="pdf-list">
                ${files.length > 0 
                    ? files.map((file: string) => `
                        <li><a href="http://127.0.0.1:5000/view/${file}" target="_blank" class="pdf-link">📄 ${file.replace('_紹介シート.pdf', '')} の紹介シート</a></li>
                      `).join('')
                    : '<p class="no-data">現在、公開されている企業紹介PDFはありません。</p>'
                }
            </ul>
        </div>
    `;
}

// 2. 企業向け入力フォーム画面
function renderFormPage() {
    app.innerHTML = `
        <div class="container">
            <h2>企業紹介データ 入力フォーム</h2>
            <form id="company-form">
                <label>企業名：</label>
                <input type="text" name="company_name" required placeholder="例：株式会社 鳥栖テクノロジー">
                
                <label>キャッチコピー：</label>
                <input type="text" name="catchphrase" required placeholder="例：未来を創る、技術と情熱。">
                
                <label>企業PR・事業内容：</label>
                <textarea name="description" required placeholder="会社の魅力や業務内容を記入してください"></textarea>
                
                <label>担当者連絡先：</label>
                <input type="text" name="contact" required placeholder="example@tosu.lg.jp">
                
                <div class="btn-group">
                    <button type="submit" class="btn btn-success">市役所にアップロード申請をする</button>
                    <a href="#" class="back-link">← 閲覧ページに戻る</a>
                </div>
            </form>
        </div>
    `;

    document.getElementById('company-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target as HTMLFormElement;
        const formData = {
            company_name: (form.elements.namedItem('company_name') as HTMLInputElement).value,
            catchphrase: (form.elements.namedItem('catchphrase') as HTMLInputElement).value,
            // HTMLTextAreaElement として安全にキャストして .value を取得する
            description: (form.elements.namedItem('description') as HTMLTextAreaElement).value,
            contact: (form.elements.namedItem('contact') as HTMLInputElement).value,
        };

        const result = await submitCompanyData(formData);
        if (result.status === 'success') {
            alert('市役所へのアップロード申請が完了しました！');
            window.location.hash = '';
        } else {
            alert('エラーが発生しました。');
        }
    });
}

// 3. 市役所管理者画面
async function renderAdminPage() {
    const items = await fetchPendingRequests();

    app.innerHTML = `
        <div class="container">
            <h2>🔒 市役所管理者ページ（承認待ち一覧）</h2>
            <p>申請されたPDFの内容を確認し、問題なければ承認してください。</p>
            <table>
                <tr>
                    <th>企業名</th>
                    <th>確認用PDF</th>
                    <th>アクション</th>
                </tr>
                ${items.length > 0
                    ? items.map((item: any) => `
                        <tr>
                            <td><strong>${item.company_name}</strong></td>
                            <td><a href="http://127.0.0.1:5000/admin/view/${item.filename}" target="_blank" class="btn btn-info">🔍 PDFプレビュー</a></td>
                            <td>
                                <button class="btn btn-success approve-btn" data-filename="${item.filename}">承認して公開</button>
                                <button class="btn btn-danger reject-btn" data-filename="${item.filename}">却下</button>
                            </td>
                        </tr>
                      `).join('')
                    : '<tr><td colspan="3" class="no-data">現在、承認待ちの企業申請はありません。</td></tr>'
                }
            </table>
            <br>
            <a href="#" class="back-link">← 高校生向け閲覧ページに戻る</a>
        </div>
    `;

    // 承認ボタンのイベント設定
    document.querySelectorAll('.approve-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const filename = (e.target as HTMLElement).getAttribute('data-filename');
            if (filename) {
                await approveRequest(filename);
                renderAdminPage();
            }
        });
    });

    // 却下ボタンのイベント設定
    document.querySelectorAll('.reject-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const filename = (e.target as HTMLElement).getAttribute('data-filename');
            if (filename && confirm('本当に却下しますか？')) {
                await rejectRequest(filename);
                renderAdminPage();
            }
        });
    });
}

window.addEventListener('hashchange', router);
window.addEventListener('load', router);
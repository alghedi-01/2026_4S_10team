const API_BASE = 'http://127.0.0.1:5000/api';

// 公開済みPDF一覧の取得
export async function fetchPublicPdfs() {
    const res = await fetch(`${API_BASE}/public-pdfs`);
    const data = await res.json();
    return data.files || [];
}

// 企業情報の申請
export async function submitCompanyData(formData: {
    company_name: string;
    catchphrase: string;
    description: string;
    contact: string;
}) {
    const res = await fetch(`${API_BASE}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
    });
    return await res.json();
}

// 市役所：承認待ち一覧の取得
export async function fetchPendingRequests() {
    const res = await fetch(`${API_BASE}/admin/pending`);
    const data = await res.json();
    return data.items || [];
}

// 市役所：承認処理
export async function approveRequest(filename: string) {
    const res = await fetch(`${API_BASE}/admin/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
    });
    return await res.json();
}

// 市役所：却下処理
export async function rejectRequest(filename: string) {
    const res = await fetch(`${API_BASE}/admin/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
    });
    return await res.json();
}
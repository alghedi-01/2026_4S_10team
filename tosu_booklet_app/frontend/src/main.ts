import { renderIndexPage, renderFormPage, renderAdminPage } from './view';
import './style.css';

// ルーティング（画面切り替えのメイン制御）
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

// アプリケーションのエントリポイント（main）
function main() {
    window.addEventListener('hashchange', router);
    window.addEventListener('load', router);
}

// 実行
main();
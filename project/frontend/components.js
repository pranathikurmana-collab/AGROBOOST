const sidebarHTML = `
<aside class="sidebar">
    <div class="logo">
        <div class="logo-icon">
            <svg viewBox="0 0 24 24"><path d="M17 8C8 10 5.9 16.17 3.82 21H5.71C8 16.81 12 14 19 13L17 8Z"/><path d="M20.53 2C18.84 8 14.67 11.06 7 12L8.73 17C12.56 15.36 15.07 12.62 17 8L20.53 2Z"/></svg>
        </div>
        <h1>AgroBoost</h1>
        <p>Harvest meets opportunity</p>
    </div>
    <nav class="nav">
        <span class="nav-label">Menu</span>
        <a href="index.html" class="nav-item">Dashboard</a>
        <a href="add_farmer.html" class="nav-item">Add Farmer</a>
        <a href="production.html" class="nav-item">Add Production</a>
        <a href="logistics.html" class="nav-item">Logistics</a>
        <a href="payments.html" class="nav-item">Payments</a>
        <span class="nav-label" style="margin-top:.75rem">Records</span>
        <a href="records.html" class="nav-item">Production Records</a>
    </nav>
    <div class="sidebar-footer"><p>AgroBoost v2.0 · 2026</p></div>
</aside>
`;

function loadSidebar() {
    const appContainer = document.querySelector('.app');
    if (appContainer) {
        // Remove any manual sidebars that might have been left behind
        const existingSidebar = appContainer.querySelector('aside.sidebar');
        if (existingSidebar) existingSidebar.remove();

        appContainer.insertAdjacentHTML('afterbegin', sidebarHTML);
        
        // Auto-highlight active link
        const currentPage = window.location.pathname.split("/").pop() || "index.html";
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.getAttribute('href') === currentPage) {
                item.classList.add('active');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', loadSidebar);
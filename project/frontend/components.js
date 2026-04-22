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
    <div id="weather-box"></div>
    <div class="sidebar-footer"><p>AgroBoost v2.0 · 2026</p></div>
</aside>
`;

async function fetchWeather() {
    try {
        const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=17.38&longitude=78.48&current_weather=true');
        const data = await res.json();
        const weatherBox = document.getElementById('weather-box');
        if (weatherBox) {
            weatherBox.innerHTML = `
                <div style="margin: 20px 15px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 12px; font-size: 0.8rem; color: white;">
                    ☁️ Hyderabad: ${data.current_weather.temperature}°C<br>
                    <span style="opacity: 0.7;">Clear sky - Ideal for harvest</span>
                </div>`;
        }
    } catch (e) { console.error("Weather load failed"); }
}

function loadSidebar() {
    const appContainer = document.querySelector('.app');
    if (appContainer) {
        const existingSidebar = appContainer.querySelector('aside.sidebar');
        if (existingSidebar) existingSidebar.remove();

        appContainer.insertAdjacentHTML('afterbegin', sidebarHTML);
        
        const currentPage = window.location.pathname.split("/").pop() || "index.html";
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.getAttribute('href') === currentPage) {
                item.classList.add('active');
            }
        });
        fetchWeather();
    }
}

document.addEventListener('DOMContentLoaded', loadSidebar);
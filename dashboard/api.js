// Simple dashboard API - queries SQLite via CGI or Python backend

async function fetchData(endpoint) {
    const response = await fetch(`/api/${endpoint}`);
    return response.json();
}

async function updateDashboard() {
    // Fetch upcoming visits
    const upcoming = await fetchData('upcoming');
    const upcomingHtml = upcoming.map(v => `
        <div class="visit-card">
            <strong>${v.patient_id}</strong> - ${v.visit_name}
            <br>Scheduled: ${v.scheduled_date}
        </div>
    `).join('');
    document.getElementById('upcoming-list').innerHTML = upcomingHtml;

    // Fetch defaulters
    const defaulters = await fetchData('defaulters');
    const defaultersHtml = defaulters.map(v => `
        <div class="visit-card defaulter">
            <strong>${v.patient_id}</strong> - ${v.visit_name}
            <br>Missed: ${v.scheduled_date}
        </div>
    `).join('');
    document.getElementById('defaulters-list').innerHTML = defaultersHtml;

    // Update stats
    const stats = await fetchData('stats');
    document.getElementById('stat-active').textContent = stats.active_patients;
    document.getElementById('stat-week').textContent = stats.visits_this_week;
    document.getElementById('stat-completion').textContent = stats.completion_rate + '%';
}

// Refresh every 5 minutes
setInterval(updateDashboard, 5 * 60 * 1000);
updateDashboard();

async function loadDashboard() {
    try {
        const data = await getSummary();

        // ===== CURRENT TASK =====
        const currentTask = document.getElementById("currentTask");
        if (currentTask) {
            currentTask.textContent = data.active_task || "Menunggu Tugas";
        }

        // ===== TOTAL HOURS =====
        const totalHours = document.getElementById("totalHours");
        if (totalHours) {
            totalHours.textContent = data.total_hours || 0;
        }

        // ===== FOCUS SCORE =====
        const focusScore = document.getElementById("focusScore");
        if (focusScore) {
            focusScore.textContent = (data.focus_score || 0) + "%";
        }

        // ===== AI RECOMMENDATION =====
        const recommendation = document.getElementById("recommendation");
        if (recommendation) {
            recommendation.textContent =
                (data.recommendation || "–") + " (Rekomendasi AI)";
        }

        // ===== PHONE STATUS =====
        const phoneText = document.getElementById("phoneText");
        if (phoneText) {
            phoneText.textContent = data.phone_status || "UNKNOWN";
        }

    } catch (err) {
        console.error("Dashboard error", err);
        const recommendation = document.getElementById("recommendation");
        if (recommendation) recommendation.textContent = "ERROR";
    }
}

async function loadSessions() {
    try {
        const rows = await getSessions();
        const tbody = document.getElementById("sessionTable");
        if (!tbody) return;

        tbody.innerHTML = "";

        rows.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${s.time}</td>
                <td>${s.task}</td>
                <td>${s.focus} m</td>
                <td class="text-danger">${s.distract} m</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error("Session error", err);
    }
}

// Initial load
loadDashboard();
loadSessions();

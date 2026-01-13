// api.js
window.API = "http://localhost:5000";

async function apiGet(path) {
    const res = await fetch(window.API + path);
    if (!res.ok) throw new Error("API error");
    return res.json();
}

async function getSummary() {
    return apiGet("/api/summary");
}

async function getSessions() {
    return apiGet("/api/sessions");
}

async function getTasks() {
    return apiGet("/api/tasks/list");
}

async function getQTable() {
    return apiGet("/api/qtable");
}

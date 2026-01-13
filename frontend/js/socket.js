window.socket = io(window.API, { transports:["websocket"] });

function safe(id){ return document.getElementById(id); }

socket.on("connect", ()=>{
    console.log("🟢 Socket connected");
    const b = safe("deviceStatus");
    if(b){ b.textContent="ONLINE"; b.className="badge bg-success"; }
});

socket.on("disconnect", ()=>{
    const b = safe("deviceStatus");
    if(b){ b.textContent="OFFLINE"; b.className="badge bg-secondary"; }
});

socket.on("session_start", data=>{
    const t = safe("currentTask");
    if(t) t.textContent = data.task;
});

socket.on("phone_status_update", data=>{
    const badge = safe("phoneStatus");
    const text = safe("phoneText");
    if(!badge || !text) return;

    if(data.status=="LOCKED"){
        badge.className="badge bg-success"; badge.textContent="AMAN";
        text.textContent="HP di kotak";
    }
    else if(data.status=="REMOVED"){
        badge.className="badge bg-danger"; badge.textContent="DISTRAKSI";
        text.textContent="HP diambil!";
    }
    else{
        badge.className="badge bg-secondary"; badge.textContent="NON AKTIF";
        text.textContent="Tidak aktif";
    }
});

socket.on("refresh", ()=>{
    if(window.loadDashboard) loadDashboard();
    if(window.loadSessions) loadSessions();
    if(window.loadTasks) loadTasks();
});

socket.on("refresh_tasks", ()=>{
    if(window.loadTasks) loadTasks();
});

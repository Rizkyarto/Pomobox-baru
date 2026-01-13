async function loadTasks(){
    const res = await fetch(window.API+"/api/tasks/list");
    const tasks = await res.json();

    const tbody = document.getElementById("taskTable");
    tbody.innerHTML="";

    tasks.forEach(t=>{
        const tr = document.createElement("tr");
        tr.innerHTML=`
        <td>${t.title}</td>
        <td>${t.done}/${t.est}</td>
        <td><span class="badge ${
            t.status=="In Progress"?"bg-primary":
            t.status=="Done"?"bg-success":"bg-secondary"
        }">${t.status}</span></td>
        <td><button class="btn btn-sm btn-danger" onclick="deleteTask(${t.id})">🗑</button></td>`;
        tbody.appendChild(tr);
    });
}

async function addTask(){
    const title = taskTitle.value;
    const est = parseInt(taskEst.value);
    if(!title) return alert("Isi judul");

    await fetch(window.API+"/api/tasks",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({title,est})
    });

    taskTitle.value="";
    loadTasks();
}

async function deleteTask(id){
    await fetch(window.API+"/api/tasks/"+id,{method:"DELETE"});
    loadTasks();
}

loadTasks();

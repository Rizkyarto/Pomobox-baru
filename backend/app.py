import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_mqtt import Mqtt
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import func
import json
import random

import rl_engine
from rl_engine import ACTIONS
from models import db, Task, FocusSession, QTable


# =========================
# APP INIT
# =========================
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pomobox.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MQTT_BROKER_URL"] = "broker.hivemq.com"
app.config["MQTT_BROKER_PORT"] = 1883
app.config["MQTT_KEEPALIVE"] = 60

CORS(app, resources={r"/api/*": {"origins": "*"}})

db.init_app(app)
mqtt = Mqtt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


# =========================
# UTILS
# =========================
def get_time_slot():
    h = datetime.now().hour
    if 5 <= h < 12:
        return "MORNING"
    elif 12 <= h < 18:
        return "AFTERNOON"
    else:
        return "EVENING"


# =========================
# API — TASKS
# =========================
@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.json
    task = Task(
        title=data["title"],
        est_pomodoros=data["est"],
        completed_pomodoros=0,
        status="Waiting"
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"})
    db.session.delete(task)
    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/api/tasks/list")
def list_tasks():
    tasks = Task.query.filter(Task.status != "Done").order_by(Task.created_at.desc()).all()
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "est": t.est_pomodoros,
            "done": t.completed_pomodoros,
            "status": t.status
        } for t in tasks
    ])


# =========================
# API — SUMMARY
# =========================
@app.route("/api/summary")
def api_summary():
    active_task = Task.query.filter(Task.status != "Done").first()
    active_task_name = active_task.title if active_task else "Menunggu Tugas"

    total_sec = db.session.query(func.sum(FocusSession.actual_sec)).scalar() or 0
    total_hours = round(total_sec / 3600, 2)

    avg_fli = db.session.query(func.avg(FocusSession.fli_score)).scalar()
    focus_score = round((1 - avg_fli) * 100, 1) if avg_fli else 0

    state = f"{get_time_slot()}_LOW"
    qs = QTable.query.filter_by(state_key=state).all()

    if qs:
        best_action = max(qs, key=lambda q: q.q_value).action_id
    else:
        best_action = "A2"

    rec = ACTIONS[best_action]
    recommendation = f"{rec['work']} / {rec['short']} / {rec['long']}"

    return jsonify({
        "active_task": active_task_name,
        "total_hours": total_hours,
        "focus_score": focus_score,
        "phone_status": "UNKNOWN",
        "recommendation": recommendation,
        "action_id": best_action
    })


# =========================
# API — SESSIONS
# =========================
@app.route("/api/sessions")
def api_sessions():
    sessions = FocusSession.query.order_by(FocusSession.timestamp.desc()).limit(20).all()
    data = []

    for s in sessions:
        task = db.session.get(Task, s.task_id)
        data.append({
            "time": s.timestamp.strftime("%H:%M %d/%m"),
            "task": task.title if task else "Tanpa Judul",
            "focus": round(s.actual_sec / 60, 1),
            "distract": round(s.distract_sec / 60, 1)
        })

    return jsonify(data)


# =========================
# MQTT
# =========================
@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    mqtt.subscribe("pomobox/session_start")
    mqtt.subscribe("pomobox/session_end")
    mqtt.subscribe("pomobox/task_done")
    mqtt.subscribe("pomobox/nfc_status")
    print("MQTT Connected")


@mqtt.on_message()
def on_message(client, userdata, message):
    data = json.loads(message.payload.decode())
    topic = message.topic

    with app.app_context():

        if topic == "pomobox/session_start":
            task = db.session.get(Task, data["task_id"])
            if task:
                task.status = "In Progress"
                db.session.commit()

            socketio.emit("session_start", {
                "task": task.title if task else "Unknown",
                "use_nfc": data.get("use_nfc", True)
            })

        elif topic == "pomobox/session_end":

            fli = rl_engine.get_fli_score(
                data["distract_sec"],
                data["distract_count"],
                data["planned_sec"]
            )

            reward = rl_engine.calculate_reward(fli)
            state = f"{get_time_slot()}_LOW"

            # ===== SAFE Q =====
            q = QTable.query.filter_by(state_key=state, action_id=data["action_id"]).first()
            if not q:
                q = QTable(state_key=state, action_id=data["action_id"], q_value=0.0)
                db.session.add(q)

            max_next = db.session.query(func.max(QTable.q_value)) \
                .filter_by(state_key=state).scalar() or 0

            q.q_value = rl_engine.bellman_equation(q.q_value, reward, max_next)

            # ===== SAVE SESSION =====
            db.session.add(FocusSession(
                task_id=data["task_id"],
                time_slot=get_time_slot(),
                action_id=data["action_id"],
                planned_sec=data["planned_sec"],
                actual_sec=data["actual_sec"],
                distract_sec=data["distract_sec"],
                distract_count=data["distract_count"],
                fli_score=fli,
                reward=reward,
                timestamp=datetime.utcnow()
            ))

            # ===== UPDATE TASK =====
            t = db.session.get(Task, data["task_id"])
            if t:
                t.completed_pomodoros += 1
                if t.completed_pomodoros >= t.est_pomodoros:
                    t.status = "Done"
                else:
                    t.status = "Waiting"

            db.session.commit()
            socketio.emit("refresh")

        elif topic == "pomobox/task_done":
            t = db.session.get(Task, data["task_id"])
            if t:
                t.status = "Done"
                db.session.commit()
                socketio.emit("refresh_tasks")


# =========================
# INIT
# =========================
def seed():
    if not QTable.query.first():
        for s in ["MORNING", "AFTERNOON", "EVENING"]:
            for a in ACTIONS.keys():
                db.session.add(QTable(state_key=f"{s}_LOW", action_id=a, q_value=0.0))
        db.session.commit()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed()

    print("SERVER RUNNING ON :5000")
    socketio.run(app, host="0.0.0.0", port=5000)

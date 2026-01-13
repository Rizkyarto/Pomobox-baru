from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# =====================================
# DB INSTANCE (SATU-SATUNYA)
# =====================================
db = SQLAlchemy()


# =====================================
# TASK MODEL
# =====================================
class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

    est_pomodoros = db.Column(db.Integer, default=1)
    completed_pomodoros = db.Column(db.Integer, default=0)

    status = db.Column(db.String(20), default="Waiting")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    sessions = db.relationship("FocusSession", backref="parent_task", lazy=True)

    def __repr__(self):
        return f"<Task {self.id} - {self.title}>"


# =====================================
# FOCUS SESSION MODEL
# =====================================
class FocusSession(db.Model):
    __tablename__ = "focus_sessions"

    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True)

    time_slot = db.Column(db.String(20))        # MORNING / AFTERNOON / EVENING
    action_id = db.Column(db.String(10))        # A0, A1, A2, ...

    planned_sec = db.Column(db.Integer)
    actual_sec = db.Column(db.Integer)

    distract_sec = db.Column(db.Integer)
    distract_count = db.Column(db.Integer)

    fli_score = db.Column(db.Float)
    reward = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Session {self.id} Task={self.task_id} Action={self.action_id}>"


# =====================================
# Q-TABLE MODEL (RL BRAIN)
# =====================================
class QTable(db.Model):
    __tablename__ = "q_table"

    id = db.Column(db.Integer, primary_key=True)

    state_key = db.Column(db.String(50))   # contoh: MORNING_LOW
    action_id = db.Column(db.String(10))   # A0 - A4
    q_value = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<Q {self.state_key} {self.action_id} = {self.q_value}>"

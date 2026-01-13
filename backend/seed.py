from datetime import datetime, timedelta
import random

from app import app
from models import db, Task, FocusSession, QTable
import rl_engine
from rl_engine import ACTIONS


def seed():
    with app.app_context():

        print("🧹 Reset database...")
        db.drop_all()
        db.create_all()

        # ==============================
        # 1. TASKS
        # ==============================
        print("📋 Membuat task dummy...")

        task_names = [
            "UAS Data Science",
            "Proyek IoT PomoBox",
            "Tugas Kalkulus Lanjut",
            "Revisi Skripsi Bab 2",
            "Belajar Machine Learning",
        ]

        tasks = []
        for name in task_names:
            t = Task(
                title=name,
                est_pomodoros=random.randint(4, 10),
                completed_pomodoros=0,
                status="Waiting"
            )
            db.session.add(t)
            tasks.append(t)

        db.session.commit()

        # ==============================
        # 2. Q-TABLE (RL BRAIN)
        # ==============================
        print("🧠 Membuat Q-table awal...")

        slots = ["MORNING", "AFTERNOON", "EVENING"]
        for s in slots:
            for a in ACTIONS.keys():
                db.session.add(QTable(
                    state_key=f"{s}_LOW",
                    action_id=a,
                    q_value=0.0
                ))

        db.session.commit()

        # ==============================
        # 3. SIMULASI 30 HARI
        # ==============================
        print("📊 Simulasi 30 hari sesi fokus...")

        start = datetime.now() - timedelta(days=30)

        for day in range(30):
            current_day = start + timedelta(days=day)

            # 2–4 sesi per hari
            for _ in range(random.randint(2, 4)):

                hour = random.choice([8, 10, 14, 16, 19, 21])
                session_time = current_day.replace(hour=hour, minute=0)

                if 5 <= hour < 12:
                    slot = "MORNING"
                elif 12 <= hour < 18:
                    slot = "AFTERNOON"
                else:
                    slot = "EVENING"

                action_id = random.choice(list(ACTIONS.keys()))
                planned_min = ACTIONS[action_id]["work"]
                planned_sec = planned_min * 60

                # ===== Pola manusia =====
                if slot == "MORNING":
                    distract_sec = random.randint(0, 30)
                    distract_count = random.randint(0, 1)
                elif slot == "AFTERNOON":
                    distract_sec = random.randint(60, 300)
                    distract_count = random.randint(2, 5)
                else:
                    distract_sec = random.randint(10, 120)
                    distract_count = random.randint(1, 3)

                actual_sec = max(0, planned_sec - distract_sec)

                # ===== RL =====
                fli = rl_engine.get_fli_score(distract_sec, distract_count, planned_sec)
                reward = rl_engine.calculate_reward(fli)

                state = f"{slot}_LOW"
                q = QTable.query.filter_by(state_key=state, action_id=action_id).first()

                max_next = db.session.query(db.func.max(QTable.q_value)) \
                    .filter_by(state_key=state).scalar() or 0.0

                q.q_value = rl_engine.bellman_equation(q.q_value, reward, max_next)

                # ===== Simpan session =====
                session = FocusSession(
                    task_id=random.choice(tasks).id,
                    time_slot=slot,
                    action_id=action_id,
                    planned_sec=planned_sec,
                    actual_sec=actual_sec,
                    distract_sec=distract_sec,
                    distract_count=distract_count,
                    fli_score=fli,
                    reward=reward,
                    timestamp=session_time
                )

                db.session.add(session)

        db.session.commit()

        print("✅ SEED SELESAI! Database siap dipakai.")


if __name__ == "__main__":
    seed()

# rl_engine.py

# =========================================================
# KONFIGURASI HYPERPARAMETER AI (PUNYA ANDA)
# =========================================================
# ALPHA (Learning Rate): Seberapa cepat AI menerima informasi baru (0.3 = 30%)
# GAMMA (Discount Factor): Seberapa peduli AI dengan reward masa depan (0.9 = Sangat peduli)
ALPHA = 0.3
GAMMA = 0.9

# =========================================================
# ACTION SPACE (DAFTAR OPSI DURASI)
# =========================================================
# A0 - A4 adalah pilihan yang akan direkomendasikan AI ke ESP32.
# 'work' adalah durasi fokus dalam menit.
ACTIONS = {
    "A0": {"work": 15, "short": 3, "long": 10},
    "A1": {"work": 20, "short": 5, "long": 15},
    "A2": {"work": 25, "short": 5, "long": 15}, # Standar Pomodoro
    "A3": {"work": 30, "short": 7, "long": 20},
    "A4": {"work": 35, "short": 10, "long": 25},
}

# =========================================================
# LOGIKA PERHITUNGAN SKOR & REWARD
# =========================================================

def get_fli_score(distract_sec, distract_count, planned_sec):
    """
    Menghitung Focus Loss Index (FLI).
    Semakin kecil nilainya, semakin fokus user tersebut.
    Rentang: 0.0 (Sangat Fokus) s/d 1.0 (Sangat Terdistraksi).
    """
    if planned_sec <= 0:
        return 1.0

    # Setiap 1x angkat HP (distract_count), kena penalti tambahan setara 30 detik
    penalty = distract_count * 30
    
    # Rumus dasar: (Waktu Distraksi + Penalti) / Total Waktu Rencana
    raw_score = (distract_sec + penalty) / planned_sec
    
    # Pastikan nilai tidak keluar dari batas 0.0 - 1.0
    return max(0.0, min(1.0, raw_score))

def calculate_reward(fli):
    """
    Mengubah skor FLI menjadi Reward (Hadiah/Hukuman) untuk AI.
    AI belajar untuk mengejar nilai Reward positif.
    """
    if fli < 0.05:
        return 1.0  # Sangat Bagus (+1.0)
    elif fli < 0.15:
        return 0.5  # Cukup Bagus (+0.5)
    elif fli < 0.30:
        return 0.0  # Netral (0.0)
    else:
        return -fli # Buruk (Nilai negatif sesuai tingkat distraksi)

def bellman_equation(q, reward, max_next):
    """
    Inti dari Q-Learning (Rumus Bellman).
    Mengupdate nilai kepercayaan (Q-Value) berdasarkan pengalaman baru.
    
    Rumus: Q_baru = Q_lama + Alpha * (Reward + Gamma * Max_Q_Masa_Depan - Q_lama)
    """
    q = q or 0.0
    max_next = max_next or 0.0
    
    new_q = q + ALPHA * (reward + GAMMA * max_next - q)
    
    # Membatasi nilai agar tidak terlalu ekstrem (-5 sampai 5)
    return round(max(-5, min(5, new_q)), 4)
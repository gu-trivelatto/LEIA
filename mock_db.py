import sqlite3
import random
import math
from datetime import datetime, timedelta

# Configurações
DB_NAME = "laboratorio_mock.db"
START_DATE = datetime.now() - timedelta(days=65) # 2 meses e um pouco
END_DATE = datetime.now()
INTERVAL_MINUTES = 5
VOLTAGE_NOMINAL = 220

# Conectar ao banco (cria se não existir)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Recriar tabela limpa
cursor.execute("DROP TABLE IF EXISTS medicoes")
cursor.execute("""
    CREATE TABLE medicoes (
        timestamp TEXT,
        sensor TEXT,
        power REAL,
        reactivePower REAL,
        current REAL,
        voltage REAL
    )
""")

print("Gerando dados... (Isso pode levar alguns segundos)")

data_buffer = []
current_time = START_DATE

# Função para gerar anomalias aleatórias
def get_anomaly_factor():
    val = random.random()
    if val < 0.0005: return "BLACKOUT"      # 0.05% chance de apagão
    if val < 0.002: return "VOLTAGE_SPIKE"  # 0.2% chance de pico
    if val < 0.002: return "VOLTAGE_SAG"    # 0.2% chance de queda de tensão
    return "NORMAL"

# Loop de Tempo
while current_time <= END_DATE:
    
    # Fatores temporais
    hour = current_time.hour
    weekday = current_time.weekday() # 0=Seg, 6=Dom
    
    # Definição de Carga Base (Horário Comercial vs Noite/Fim de Semana)
    is_work_hours = 8 <= hour <= 18
    is_weekend = weekday >= 5
    
    base_load_factor = 0.3 # Carga noturna/fim de semana
    if is_work_hours and not is_weekend:
        base_load_factor = 1.0 # Carga cheia
    elif is_work_hours and is_weekend:
        base_load_factor = 0.5 # Fim de semana de dia
        
    # Anomalia Global (Afeta todas as fases ao mesmo tempo, ex: queda de rede)
    global_event = get_anomaly_factor()
    
    for i in range(1, 4): # Fases 1, 2, 3
        sensor_name = f"fase{i}"
        
        # 1. Voltagem Base (220V com flutuação normal de +/- 2%)
        voltage = VOLTAGE_NOMINAL + random.uniform(-4, 4)
        
        # 2. Potência Base (1.5 a 6.5 kW)
        # A carga varia conforme o horário + um ruído aleatório
        max_power = 6.5
        min_power = 1.5
        
        # Potência alvo baseada no horário
        target_power = min_power + (max_power - min_power) * base_load_factor
        # Adiciona ruído (+/- 10%)
        power_kw = target_power * random.uniform(0.9, 1.1)
        
        # 3. Fator de Potência (Eficiência) - Varia entre 0.85 e 0.99
        pf = random.uniform(0.85, 0.99)
        
        # --- INJEÇÃO DE CENÁRIOS ESPECÍFICOS ---
        
        # Cenário A: Blackout (Tudo zero)
        if global_event == "BLACKOUT":
            voltage = random.uniform(0, 5)
            power_kw = 0
            pf = 1
            
        # Cenário B: Pico de Tensão (Surge)
        elif global_event == "VOLTAGE_SPIKE":
            voltage = random.uniform(245, 260) # Perigo!
            
        # Cenário C: Subtensão (Sag)
        elif global_event == "VOLTAGE_SAG":
            voltage = random.uniform(180, 195) # Perigo!
            
        # Cenário D: Desbalanceamento de Fase (Fase 2 cai muito numa terça-feira específica)
        # Vamos simular que a Fase 2 perdeu carga nos ultimos 3 dias
        if sensor_name == "fase2" and current_time > (END_DATE - timedelta(days=3)):
            power_kw = power_kw * 0.2 # Fase 2 operando com 20% da carga
            
        # --- CÁLCULOS FÍSICOS ---
        
        # Se Potência ativa (P) está em kW, Current (I) = (P * 1000) / (V * FP)
        if voltage > 10:
            current = (power_kw * 1000) / (voltage * pf)
            # Potência Reativa (kVAR) -> Q = P * tan(acos(FP))
            # Usamos acos para obter o ângulo e tan para a relação
            theta = math.acos(pf)
            reactive_kvar = power_kw * math.tan(theta)
        else:
            current = 0
            reactive_kvar = 0
            power_kw = 0

        # Formatar Timestamp ISO8601
        ts_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        data_buffer.append((ts_str, sensor_name, round(power_kw, 3), round(reactive_kvar, 3), round(current, 2), round(voltage, 1)))

    # Avança 5 minutos
    current_time += timedelta(minutes=INTERVAL_MINUTES)

# Inserção em Batch (Muito mais rápido)
cursor.executemany("""
    INSERT INTO medicoes (timestamp, sensor, power, reactivePower, current, voltage)
    VALUES (?, ?, ?, ?, ?, ?)
""", data_buffer)

conn.commit()
print(f"Sucesso! {len(data_buffer)} registros inseridos em '{DB_NAME}'.")
print(f"Período: {START_DATE.strftime('%Y-%m-%d')} até {END_DATE.strftime('%Y-%m-%d')}")

# Verificação rápida
cursor.execute("SELECT count(*) FROM medicoes")
count = cursor.fetchone()[0]
print(f"Total de linhas no banco: {count}")

conn.close()
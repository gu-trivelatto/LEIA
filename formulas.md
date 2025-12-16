# Documentação Analítica: Fórmulas de Extração de Dados

Este documento descreve as fórmulas matemáticas aplicadas na classe `DataAccessRepository`, detalhando o cálculo realizado via SQL, a física por trás e os insights de negócio.

---

## 1. Consumo Acumulado (Energia Ativa)
**Método:** `get_consumo_total_kwh`

### Fórmula
A energia ($E$) é a integral da potência ($P$) ao longo do tempo. Como os dados são discretos (amostras a cada 5 minutos), utilizamos uma soma de Riemann:

$$E_{total} (kWh) = \sum_{i=1}^{n} P_i \times \Delta t$$

Onde:
- $P_i$: Leitura de potência (kW) no instante $i$.
- $\Delta t$: Intervalo de tempo. Sendo 5 minutos: $\frac{5}{60} = \frac{1}{12} h$.

### O que isso mostra
O volume total de energia consumida no período.

---

## 2. Picos de Demanda (Momentos Críticos)
**Método:** `get_picos_demanda`

### Fórmula
Busca o máximo global da função de potência $P(t)$ no intervalo $T$:

$$P_{pico} = \max_{t \in T} \{ P(t) \}$$

### O que isso mostra
O ponto de maior estresse da rede elétrica e o momento exato em que ocorreu.

---

## 3. Saúde Elétrica (Fator de Potência)
**Método:** `get_saude_eletrica`

### Fórmula
O Fator de Potência ($FP$) é a razão entre a Potência Ativa ($P$) e a Potência Aparente ($S$).

$$FP = \frac{P}{S} = \frac{P}{\sqrt{P^2 + Q^2}}$$

Onde $Q$ é a potência reativa (`reactivePower`). O sistema calcula a **média** desses valores:

$$FP_{medio} = \frac{1}{n} \sum_{i=1}^{n} \left( \frac{P_i}{\sqrt{P_i^2 + Q_i^2}} \right)$$

### O que isso mostra
A eficiência do uso da energia. Indica quanto da energia comprada está sendo convertida em trabalho real vs. desperdiçada em campos magnéticos.

### Análise dos Resultados
- **Zona de Multa:** No Brasil, $FP < 0.92$ gera multa por excedente de reativos.
- **Ação:** Baixo FP indica necessidade de instalação ou manutenção de bancos de capacitores.

---

## 4. Perfil Horário (Mapa de Calor)
**Método:** `get_perfil_horario`

### Fórmula
Calcula a potência média ($\bar{P}$) condicionada a uma hora específica ($h$), agrupando todos os dias do período.

$$\bar{P}_{h} = \frac{1}{|D|} \sum_{d \in D} P_{(d, h)}$$

---

## 5. Desbalanceamento de Fases
**Método:** `get_desbalanceamento`

### Fórmula
Mede a amplitude da dispersão entre as correntes médias ($\bar{I}$) das três fases.

$$\Delta I_{max} = \max(\bar{I}_{f1}, \bar{I}_{f2}, \bar{I}_{f3}) - \min(\bar{I}_{f1}, \bar{I}_{f2}, \bar{I}_{f3})$$

### O que isso mostra
A desigualdade na distribuição de cargas monofásicas (tomadas, luzes) entre as fases R, S e T.

### Análise dos Resultados
- **Risco Técnico:** Desbalanceamento alto gera corrente excessiva no cabo Neutro (risco de superaquecimento) e perda de eficiência em motores trifásicos.
- **Ação:** Requer eletricista para mover disjuntores de uma fase para outra no quadro.

---

## 6. Detecção de Anomalias (Voltagem)
**Método:** `get_anomalias_voltagem`

### Fórmula
Calcula o desvio percentual ($\delta\%$) da tensão ($V$) em relação à referência ($220V$).

$$\delta\% = \left( \frac{V - 220}{220} \right) \times 100$$

Filtro aplicado:
$$V > 242 \lor V < 198$$

### O que isso mostra
Eventos onde a tensão fornecida saiu da zona segura regulamentada (PRODIST).

### Análise dos Resultados
- **Subtensão (Desvio Negativo):** Perigoso para motores (puxam mais corrente para compensar, gerando calor).
- **Sobretensão (Desvio Positivo):** Perigoso para eletrônicos (queima de fontes e placas).
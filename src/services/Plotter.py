import logging
import uuid
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import seaborn as sns
from matplotlib.container import BarContainer

# Configuração de Logger
logger = logging.getLogger(__name__)

# Configuração global de estilo para ficar parecido com o Plotly
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6) # Tamanho padrão
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Garante que o diretório existe
os.makedirs("data/plots", exist_ok=True)

def _save_plot(fig, image_name):
    """Função auxiliar para salvar e fechar a figura corretamente."""
    plot_path = f"data/plots/{image_name}.png"
    try:
        fig.savefig(plot_path, bbox_inches='tight', dpi=100)
    finally:
        # Importante: Limpa a memória para não sobrepor gráficos em execuções longas
        plt.close(fig)
    return plot_path

def plot_consumo_total_kwh(data: list[dict], periodo: str, image_name: str) -> str:
    """
    Gera um gráfico de barras comparando o consumo acumulado (kWh) entre as fases.
    """
    try:
        logger.info(f"Plotting consumo total para {periodo}...")
        
        if not data:
            return "Sem dados para gerar o gráfico."

        df = pd.DataFrame(data)
        
        # Cria a figura
        fig, ax = plt.subplots()
        
        # Gera o barplot
        # Usamos uma paleta padrão para diferenciar as fases
        sns.barplot(data=df, x='fase', y='total_kwh', hue='fase', palette='viridis', ax=ax, legend=False)
        
        ax.set_title(f'Consumo Total de Energia por Fase ({periodo.replace("_", " ").title()})')
        ax.set_ylabel('Energia Acumulada (kWh)')
        ax.set_xlabel('Fase')

        # Adiciona os valores em cima das barras (equivalente ao text='total_kwh' do Plotly)
        for container in ax.containers:
            if isinstance(container, BarContainer):
                ax.bar_label(container, fmt='%.1f', padding=3)

        return _save_plot(fig, image_name)

    except Exception as e:
        logger.error(f"Error in plot_consumo_total_kwh: {e}")
        return "Erro ao gerar gráfico."


def plot_picos_demanda(data: list[dict], periodo: str, image_name: str) -> str:
    """
    Gera um gráfico de dispersão mostrando QUANDO e QUANTO foi o pico de cada fase.
    """
    try:
        logger.info(f"Plotting picos de demanda para {periodo}...")
        
        if not data:
            return "Sem dados para gerar o gráfico."

        df = pd.DataFrame(data)
        # Garante que 'momento' seja datetime para o matplotlib entender o eixo X
        if 'momento' in df.columns:
            df['momento'] = pd.to_datetime(df['momento'])

        fig, ax = plt.subplots()

        # Scatter plot com tamanhos variados
        sns.scatterplot(
            data=df, 
            x='momento', 
            y='pico_kw', 
            hue='fase', 
            size='pico_kw', 
            sizes=(100, 400), # Tamanho mínimo e máximo das bolinhas
            alpha=0.7,
            ax=ax
        )

        ax.set_title(f'Momentos de Pico de Demanda Máxima ({periodo.replace("_", " ").title()})')
        ax.set_xlabel('Horário da Ocorrência')
        ax.set_ylabel('Potência (kW)')
        
        # Formatação do eixo de datas (se necessário melhorar a visualização)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d/%m'))
        
        # Move a legenda para fora se atrapalhar
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        return _save_plot(fig, image_name)

    except Exception as e:
        logger.error(f"Error in plot_picos_demanda: {e}")
        return "Erro ao gerar gráfico."


def plot_saude_eletrica(data: list[dict], periodo: str, image_name: str) -> str:
    """
    Gera um gráfico de barras do Fator de Potência com linha de corte e cor gradiente.
    """
    try:
        logger.info(f"Plotting saude eletrica para {periodo}...")
        
        if not data:
            return "Sem dados para gerar o gráfico."

        df = pd.DataFrame(data)

        fig, ax = plt.subplots()

        # Lógica para cor contínua (Red -> Yellow -> Green) baseada no valor Y
        # Normalizamos entre 0.8 e 1.0 como no original
        norm = mcolors.Normalize(vmin=0.8, vmax=1.0)
        cmap = plt.get_cmap('RdYlGn') # Red-Yellow-Green colormap
        colors = [cmap(norm(val)) for val in df['fator_potencia_medio']]

        bars = ax.bar(df['fase'], df['fator_potencia_medio'], color=colors)

        ax.set_title(f'Eficiência Energética (Fator de Potência) - {periodo.replace("_", " ").title()}')
        ax.set_ylim(0.5, 1.1)
        ax.set_ylabel('Fator de Potência Médio')
        
        # Linha de referência
        ax.axhline(y=0.92, color='red', linestyle='--', linewidth=2, label='Limite Multa (0.92)')
        
        # Anotação da linha
        ax.text(
            x=len(df)-0.6, y=0.93, s="Limite Multa (0.92)", 
            color="red", fontsize=10, fontweight='bold'
        )

        return _save_plot(fig, image_name)

    except Exception as e:
        logger.error(f"Error in plot_saude_eletrica: {e}")
        return "Erro ao gerar gráfico."


def plot_perfil_horario(data: list[dict], periodo: str, image_name: str) -> str:
    """
    Gera um gráfico de linhas multivariado (00-23h).
    """
    try:
        logger.info(f"Plotting perfil horario para {periodo}...")
        
        if not data:
            return "Sem dados para gerar o gráfico."

        df = pd.DataFrame(data)
        
        # Mapeamento de nomes para legenda
        cols_map = {
            'media_kw_f1': 'Fase 1', 
            'media_kw_f2': 'Fase 2', 
            'media_kw_f3': 'Fase 3', 
            'media_geral_kw': 'Média Geral'
        }

        fig, ax = plt.subplots()

        # Plotar cada linha
        for col, label in cols_map.items():
            if col in df.columns:
                # Estilo diferente para a média geral
                style = '--' if col == 'media_geral_kw' else '-'
                width = 2.5 if col == 'media_geral_kw' else 1.5
                ax.plot(df['hora'], df[col], label=label, linestyle=style, linewidth=width)

        ax.set_title(f'Perfil de Carga Horária Médio ({periodo.replace("_", " ").title()})')
        ax.set_xlabel('Hora do Dia')
        ax.set_ylabel('Potência Média (kW)')
        ax.set_xticks(range(0, 24)) # Garante todas as horas no eixo X
        plt.xticks(rotation=90) # Rotaciona os labels do eixo X
        ax.legend()

        return _save_plot(fig, image_name)

    except Exception as e:
        logger.error(f"Error in plot_perfil_horario: {e}")
        return "Erro ao gerar gráfico."


def plot_desbalanceamento(data: list[dict], periodo: str, image_name: str) -> str:
    """
    Gera um gráfico comparativo das correntes (Amperes).
    """
    try:
        logger.info(f"Plotting desbalanceamento para {periodo}...")
        
        if not data:
            return "Sem dados para gerar o gráfico."

        row = data[0]
        
        # Preparar dados
        fases = ['Fase 1', 'Fase 2', 'Fase 3']
        correntes = [row['avg_amp_f1'], row['avg_amp_f2'], row['avg_amp_f3']]
        
        fig, ax = plt.subplots()
        
        # Barplot simples
        bars = ax.bar(fases, correntes, color=['#1f77b4', '#ff7f0e', '#2ca02c']) # Cores padrão plotly aprox.

        ax.set_title(f'Desbalanceamento de Corrente ({periodo.replace("_", " ").title()})')
        ax.set_ylabel('Corrente Média (A)')
        
        # Label em cima das barras
        ax.bar_label(bars, fmt='%.1f', padding=3)

        # Anotação da diferença máxima
        max_diff = row['diferenca_max_amperes']
        max_val = max(correntes)
        
        ax.annotate(
            f"Diferença Máx: {max_diff}A",
            xy=(1, max_val),
            xytext=(1, max_val * 1.1),
            ha='center',
            color='red',
            fontsize=12,
            fontweight='bold',
            arrowprops=dict(arrowstyle='-')
        )
        
        # Ajusta limite superior para caber a anotação
        ax.set_ylim(top=max_val * 1.25)

        return _save_plot(fig, image_name)

    except Exception as e:
        logger.error(f"Error in plot_desbalanceamento: {e}")
        return "Erro ao gerar gráfico."


def plot_anomalias_voltagem(data: list[dict], periodo: str, image_name: str) -> str:
    """
    Gera um gráfico timeline mostrando eventos de sub/sobretensão.
    """
    try:
        logger.info(f"Plotting anomalias voltagem para {periodo}...")
        
        # Caso: Sem anomalias (Gráfico vazio com mensagem)
        if not data:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Nenhuma anomalia detectada no período!", 
                    ha='center', va='center', fontsize=14, color='green', transform=ax.transAxes)
            ax.set_title(f"Registro de Anomalias ({periodo.replace('_', ' ').title()})")
            ax.set_axis_off() # Esconde eixos
            
            # Gera UUID se data for vazia, conforme lógica original, ou usa image_name se passado
            final_name = str(uuid.uuid4()) if not image_name else image_name
            return _save_plot(fig, final_name)

        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig, ax = plt.subplots()

        # Zona Segura (220V +/- 10% = 198 a 242)
        # Equivalente ao add_hrect
        ax.axhspan(115, 132, color='green', alpha=0.1, label='Zona Segura (127V ±10%)')

        # Scatter plot
        # Mapeando cores manualmente para garantir consistência com o original
        palette = {'ALTA': 'red', 'BAIXA': 'orange'}
        
        # Usamos 'style' para simular os diferentes formatos do Plotly
        sns.scatterplot(
            data=df,
            x='timestamp',
            y='voltage',
            hue='tipo',
            style='sensor',
            palette=palette,
            s=100, # Tamanho do ponto
            ax=ax
        )

        ax.set_title(f'Eventos de Anomalia de Tensão ({periodo.replace("_", " ").title()})')
        ax.set_ylabel('Voltagem (V)')
        ax.set_xlabel('Data/Hora')
        
        # Formatar eixo X de datas
        fig.autofmt_xdate() # Rotaciona datas para caber

        return _save_plot(fig, image_name)

    except Exception as e:
        logger.error(f"Error in plot_anomalias_voltagem: {e}")
        return "Erro ao gerar gráfico."
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx

# 1. Desliga a barra inferior do Matplotlib
plt.rcParams['toolbar'] = 'None'

# Carregar os dados geográficos dos estados do Brasil via GeoJSON público
url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
df = gpd.read_file(url)

# Margens ligeiramente maiores (0.10) para o mapa encolher só um tico e não cortar RR e RS
minx, miny, maxx, maxy = df.total_bounds
x_margin = (maxx - minx) * 0.10
y_margin = (maxy - miny) * 0.10

# Deslocamentos equilibrados para centralizar perfeitamente na vertical e levemente à esquerda
shift_x = (maxx - minx) * 0.02
shift_y = (maxy - miny) * 0.1

# 2. Construir o grafo de adjacência (quais estados fazem fronteira com quais)
df['neighbors'] = df.geometry.apply(
    lambda geom: df[df.geometry.touches(geom)].sigla.tolist()
)

G = nx.Graph()
for idx, row in df.iterrows():
    state = row['sigla']
    G.add_node(state)
    for neighbor in row['neighbors']:
        G.add_edge(state, neighbor)

# 3. Aplicar o Teorema das 4 Cores (Coloração Gulosa de Grafos)
coloring = nx.coloring.greedy_color(G, strategy='largest_first')
sorted_nodes = list(coloring.keys())

# 4. Preparar os frames da animação interativa
frames_data = []
# Frame 0: Mapa sem cor nenhuma (estado inicial)
frames_data.append(({}, "De quantas cores voce precisa pra colorir esse mapa??"))

# Frames intermediários: colorindo estado por estado
colored_so_far = {}
for node in sorted_nodes:
    colored_so_far[node] = coloring[node]
    titulo_passo = f"Colorindo estado: {node} (Cor {coloring[node] + 1})"
    frames_data.append((colored_so_far.copy(), titulo_passo))

# Frame final: Mapa totalmente colorido
total_cores_usadas = len(set(coloring.values()))
frames_data.append((coloring.copy(), f"Apenas {total_cores_usadas} cores são necessárias!"))

# 5. Configuração Visual da Janela
fig, ax = plt.subplots(figsize=(14, 8.5))
fig.canvas.manager.set_window_title('Desafio do Mapa do Brasil - Teorema das 4 Cores')
fig.subplots_adjust(top=0.86, bottom=0.08, left=0.04, right=0.96)

# Título fixo ancorado no topo esquerdo
title_text = fig.text(0.04, 0.96, "", fontsize=16, fontweight='bold', ha='left', va='top', color='black')

app_state = 'IDLE' 
ani = None

def draw_frame(frame_idx):
    global app_state
    ax.clear()
    
    colored_dict, titulo = frames_data[frame_idx]
    title_text.set_text(titulo) # Atualiza o texto dinamicamente
    
    # Mapear as cores atuais para el GeoDataFrame
    current_colors = df['sigla'].map(colored_dict)
    
    # Plotar o mapa
    df.plot(
        ax=ax,
        column=current_colors,
        cmap='Set3',
        missing_kwds={'color': '#f8f9fa', 'edgecolor': '#999999', 'linewidth': 0.8},
        edgecolor='black',
        linewidth=0.8
    )
    
    # Adicionar as siglas dos estados no centro de cada polígono
    for idx, row in df.iterrows():
        centroid = row.geometry.centroid
        ax.text(centroid.x, centroid.y, row['sigla'], fontsize=7, fontweight='bold', ha='center', va='center', color='#333333')

    # Limites ajustados para evitar cortes nas pontas de Roraima e RS
    ax.set_xlim((minx - x_margin) + shift_x, (maxx + x_margin) + shift_x)
    ax.set_ylim((miny - y_margin) - shift_y, (maxy + y_margin) - shift_y)

    ax.set_axis_off()
    ax.set_aspect('equal')

    if frame_idx == len(frames_data) - 1:
        app_state = 'DONE'

# Desenhar o estado inicial (sem cor)
draw_frame(0)

def on_press(event):
    global ani, app_state
    
    if event.key == 'escape':
        plt.close(fig)
        return

    if event.key in ['enter', 'return']:
        if app_state == 'IDLE':
            app_state = 'ANIMATING'
            ani = animation.FuncAnimation(
                fig, draw_frame, frames=len(frames_data), 
                interval=600, repeat=False, cache_frame_data=False
            )
            fig.canvas.draw_idle()
            
        elif app_state in ['DONE', 'ANIMATING']:
            if ani and hasattr(ani, 'event_source') and ani.event_source:
                ani.event_source.stop()
            ani = None 
            app_state = 'IDLE'
            draw_frame(0) # Retorna ao mapa original sem cor
            fig.canvas.draw_idle()

fig.canvas.mpl_connect('key_press_event', on_press)

# Tentar colocar em tela cheia automaticamente
mng = plt.get_current_fig_manager()
try:
    mng.full_screen_toggle()
except Exception:
    pass

plt.show()
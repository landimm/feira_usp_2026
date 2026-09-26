import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx

# 1. Desliga a barra inferior do Matplotlib
plt.rcParams['toolbar'] = 'None'

# Carregar os dados geográficos direto do servidor oficial do Natural Earth
url = "zip+https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(url)

# Padronizar nomes das colunas
world.columns = world.columns.str.lower()
if 'name' not in world.columns and 'admin' in world.columns:
    world['name'] = world['admin']

# Filtrar apenas o continente africano
df = world[world['continent'] == 'Africa'].copy()

# Criar a coluna 'sigla'
df['sigla'] = df.apply(lambda x: str(x['name'])[:3].upper() if str(x['iso_a3']) in ['-99', '-099', 'nan'] else str(x['iso_a3']), axis=1)

# --- AJUSTE DE TAMANHO E POSIÇÃO DO MAPA ---
minx, miny, maxx, maxy = df.total_bounds

# Margens mantidas em 20% para o mapa continuar num tamanho bom
x_margin = (maxx - minx) * 0.20
y_margin = (maxy - miny) * 0.20

# Deslocamento: movemos a visão para baixo, o que empurra o mapa para cima
shift_y = (maxy - miny) * 0.15  # Aumente esse número se quiser o mapa AINDA MAIS para cima

# 2. Construir o grafo de adjacência
df['neighbors'] = df.apply(
    lambda row: df[(df.geometry.intersects(row.geometry)) & (df['sigla'] != row['sigla'])]['sigla'].tolist(),
    axis=1
)

G = nx.Graph()
for idx, row in df.iterrows():
    state = row['sigla']
    G.add_node(state)
    for neighbor in row['neighbors']:
        G.add_edge(state, neighbor)

# 3. Aplicar o Teorema das 4 Cores
coloring = nx.coloring.greedy_color(G, strategy='largest_first')
sorted_nodes = list(coloring.keys())

# 4. Preparar os frames da animação
frames_data = []
frames_data.append(({}, "De quantas cores voce precisa pra colorir esse mapa?"))

colored_so_far = {}
for node in sorted_nodes:
    colored_so_far[node] = coloring[node]
    titulo_passo = f"Colorindo país: {node} (Cor {coloring[node] + 1})"
    frames_data.append((colored_so_far.copy(), titulo_passo))

total_cores_usadas = len(set(coloring.values()))
frames_data.append((coloring.copy(), f"Apenas {total_cores_usadas} cores são necessárias!"))

# 5. Configuração Visual da Janela
fig, ax = plt.subplots(figsize=(12, 8))
fig.canvas.manager.set_window_title('Desafio do Mapa da África - Teorema das 4 Cores')
fig.subplots_adjust(top=0.86, bottom=0.05, left=0.05, right=0.95)

title_text = fig.text(0.04, 0.96, "", fontsize=16, fontweight='bold', ha='left', va='top', color='black')

app_state = 'IDLE' 
ani = None

def draw_frame(frame_idx):
    global app_state
    ax.clear()
    
    colored_dict, titulo = frames_data[frame_idx]
    title_text.set_text(titulo)
    
    current_colors = df['sigla'].map(colored_dict)
    
    df.plot(
        ax=ax,
        column=current_colors,
        cmap='Set3',
        missing_kwds={'color': '#f8f9fa', 'edgecolor': '#999999', 'linewidth': 0.8},
        edgecolor='black',
        linewidth=0.8
    )
    
    for idx, row in df.iterrows():
        centroid = row.geometry.centroid
        ax.text(centroid.x, centroid.y, row['sigla'], fontsize=6, fontweight='bold', ha='center', va='center', color='#333333')

    # Aplicando o shift_y aos limites do eixo Y
    ax.set_xlim(minx - x_margin, maxx + x_margin)
    ax.set_ylim((miny - y_margin) - shift_y, (maxy + y_margin) - shift_y)
    ax.set_axis_off()
    ax.set_aspect('equal')

    if frame_idx == len(frames_data) - 1:
        app_state = 'DONE'

draw_frame(0)

# --- AJUSTE NO FUNCIONAMENTO DO ENTER ---
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
                interval=400, repeat=False
            )
            fig.canvas.draw()
            
        elif app_state == 'DONE':
            if ani and hasattr(ani, 'event_source') and ani.event_source:
                ani.event_source.stop()
            app_state = 'IDLE'
            draw_frame(0)
            fig.canvas.draw()

fig.canvas.mpl_connect('key_press_event', on_press)

mng = plt.get_current_fig_manager()
try:
    mng.full_screen_toggle()
except Exception:
    pass

plt.show()
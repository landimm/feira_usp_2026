import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
import heapq

# 1. Desliga a barra inferior
plt.rcParams['toolbar'] = 'None'

G = nx.Graph()

# Coordenadas reajustadas: mais compactas verticalmente (arestas menores)
pos = {
    'IME': (2.5, 7.5),
    'FAU': (5.5, 9.5),
    'IGC': (10.0, 9.5),
    'FFLCH': (14.0, 8.0),
    'FEA': (6.5, 6.5),
    'Bancos': (10.0, 5.5),
    'Praça do\nRelógio': (14.0, 4.5),
    'Descida\nMatão': (2.5, 5.5),
    'Av. Luciano\nGualberto': (7.5, 3.5),
    'Bandejão\nCentral': (16.5, 5.0)
}

# Arestas e pesos
arestas = [
    ('IME', 'FAU', 8),
    ('FAU', 'IGC', 2),
    ('IGC', 'FFLCH', 6),
    ('FFLCH', 'Bandejão\nCentral', 7),
    ('IME', 'FEA', 5),
    ('FEA', 'Bancos', 4),
    ('Bancos', 'Praça do\nRelógio', 3),
    ('Praça do\nRelógio', 'Bandejão\nCentral', 4),
    ('IME', 'Descida\nMatão', 10),
    ('Descida\nMatão', 'Av. Luciano\nGualberto', 5),
    ('FAU', 'FEA', 5),
    ('IGC', 'Bancos', 5),
    ('FFLCH', 'Praça do\nRelógio', 4),
    ('FEA', 'Av. Luciano\nGualberto', 3),
    ('Bancos', 'Av. Luciano\nGualberto', 3)
]

for u, v, w in arestas:
    G.add_edge(u, v, weight=w)

START = 'IME'
END = 'Bandejão\nCentral'

# 2. Dijkstra Rigoroso
dist = {node: float('inf') for node in G.nodes()}
dist[START] = 0
prev = {node: None for node in G.nodes()}
pq = [(0, START)]

frames_data = []
frames_data.append((set(), set(), [], "Você consegue achar a rota mais curta para o bandejão?"))

settled_nodes = set()
settled_edges = set()

while pq:
    current_dist, u = heapq.heappop(pq)
    
    if u in settled_nodes:
        continue
        
    settled_nodes.add(u)
    
    if prev[u] is not None:
        edge = (prev[u], u) if G.has_edge(prev[u], u) else (u, prev[u])
        settled_edges.add(edge)
        
    titulo_explorando = f"Analisando arredores de: {u.replace(chr(10), ' ')}"
    frames_data.append((settled_nodes.copy(), settled_edges.copy(), [], titulo_explorando))
    
    if u == END:
        break 
        
    for v, edge_data in G[u].items():
        w = edge_data['weight']
        if dist[u] + w < dist[v]:
            dist[v] = dist[u] + w
            prev[v] = u
            heapq.heappush(pq, (dist[v], v))

curr = END
path_edges_raw = []
while prev[curr] is not None:
    p = prev[curr]
    path_edges_raw.append((p, curr))
    curr = p

path_edges_raw.reverse()

current_path_edges = []
for edge in path_edges_raw:
    current_path_edges.append(edge)
    frames_data.append((settled_nodes.copy(), settled_edges.copy(), list(current_path_edges), "Decidindo caminho mais rápido..."))

texto_final = f"Rota mais rápida encontrada: {dist[END]} min!"
frames_data.append((settled_nodes.copy(), settled_edges.copy(), list(current_path_edges), texto_final))

# 4. Configuração Visual
fig, ax = plt.subplots(figsize=(16, 9))
fig.canvas.manager.set_window_title('Desafio da Rota - USP (IME -> Bandejão)')

fig.subplots_adjust(top=0.90, bottom=0.05, left=0.02, right=0.98)

edge_labels = nx.get_edge_attributes(G, 'weight')
app_state = 'IDLE' 
ani = None

def draw_frame(frame_idx):
    global app_state
    ax.clear()
    
    nos_explorados, arestas_exploradas, caminho_final, titulo = frames_data[frame_idx]

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#e0e0e0', width=4)

    if arestas_exploradas:
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=list(arestas_exploradas), edge_color='#ffd166', width=6)

    if caminho_final:
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=caminho_final, edge_color='#15b200', width=9)

    labels_formatados = {k: f"{v}m" for k, v in edge_labels.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_formatados, font_size=11, font_weight='bold', ax=ax, 
                                 bbox=dict(facecolor='white', edgecolor='#cccccc', alpha=0.9, pad=3, boxstyle='round,pad=0.2'))

    node_colors = []
    nodes_no_caminho = set(sum(caminho_final, ())) if caminho_final else set()

    for node in G.nodes():
        if node == START:
            node_colors.append('#00b4d8')
        elif node == END:
            node_colors.append('#00b4d8')
        elif caminho_final and node in nodes_no_caminho:
            node_colors.append("#15b200")  # Cor da rota final ótima
        elif node in nos_explorados:
            node_colors.append('#ffd166')  # Mantém a Praça do Relógio laranja/amarela (visitada pelo Dijkstra)
        else:
            node_colors.append('#f8f9fa')  # Restante não visitado

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=4200, edgecolors='#999999', linewidths=2)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_weight='bold')

    ax.text(0.38, 1.05, titulo, fontsize=24, fontweight='bold', ha='center', transform=ax.transAxes)
    ax.set_axis_off()
    ax.set_aspect('equal')
    
    # Limites da câmera
    ax.set_xlim(1, 23) 
    ax.set_ylim(0, 11)

    if frame_idx == len(frames_data) - 1:
        app_state = 'DONE'

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
                interval=700, repeat=False, cache_frame_data=False
            )
            fig.canvas.draw_idle()
            
        elif app_state in ['DONE', 'ANIMATING']:
            if ani and hasattr(ani, 'event_source') and ani.event_source:
                ani.event_source.stop()
            ani = None 
            app_state = 'IDLE'
            draw_frame(0)
            fig.canvas.draw_idle()

fig.canvas.mpl_connect('key_press_event', on_press)
print("Agora sim! A Praça do Relógio fica corretamente marcada como visitada pelo algoritmo. Aperte 'ENTER' para rodar e 'ESC' para sair.")

mng = plt.get_current_fig_manager()
try:
    mng.full_screen_toggle()
except Exception:
    pass

plt.show()
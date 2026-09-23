import cv2 # Permissões da Webcam
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import random
import numpy as np
import time
import subprocess
import re
from collections import deque

def get_screen_resolution(default=(1920, 1080)):
    try:
        output = subprocess.check_output(['xrandr']).decode()
        match = re.search(r'current (\d+) x (\d+)', output)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    return default

SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_resolution()

# --- Índices dos pontos da mão (mesmos 21 landmarks de sempre, só que sem o enum mp_hands.HandLandmark) ---
WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_FINGER_PIP, INDEX_FINGER_TIP = 6, 8
MIDDLE_FINGER_PIP, MIDDLE_FINGER_TIP = 10, 12
RING_FINGER_PIP, RING_FINGER_TIP = 14, 16
PINKY_PIP, PINKY_TIP = 18, 20

# Conexões do esqueleto da mão, pra desenhar (a API nova não vem mais com mp_drawing pronto)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # polegar
    (0, 5), (5, 6), (6, 7), (7, 8),          # indicador
    (5, 9), (9, 10), (10, 11), (11, 12),     # médio
    (9, 13), (13, 14), (14, 15), (15, 16),   # anelar
    (13, 17), (17, 18), (18, 19), (19, 20),  # mínimo
    (0, 17),                                 # base da palma
]

MODEL_PATH = 'hand_landmarker.task'

base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
hand_landmarker_options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = mp_vision.HandLandmarker.create_from_options(hand_landmarker_options)

def _distance(p1, p2):
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5

# --- Gestos estáticos (checados a partir dos landmarks do frame atual) ---
FINGER_MARGIN = 0.04  # Folga mínima (coords normalizadas) pra não confundir dedo "meio dobrado" com aberto/fechado

def _finger_open(hand_landmarks, tip_idx, pip_idx, margin=FINGER_MARGIN):
    return hand_landmarks[pip_idx].y - hand_landmarks[tip_idx].y > margin

def _finger_closed(hand_landmarks, tip_idx, pip_idx, margin=FINGER_MARGIN):
    return hand_landmarks[tip_idx].y - hand_landmarks[pip_idx].y > margin

def is_hand_open(hand_landmarks):
    try:
        return (
            _finger_open(hand_landmarks, INDEX_FINGER_TIP, INDEX_FINGER_PIP)
            and _finger_open(hand_landmarks, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP)
            and _finger_open(hand_landmarks, RING_FINGER_TIP, RING_FINGER_PIP)
            and _finger_open(hand_landmarks, PINKY_TIP, PINKY_PIP)
        )
    except Exception:
        return False

def is_thumbs_up(hand_landmarks):
    try:
        thumb_up = hand_landmarks[THUMB_MCP].y - hand_landmarks[THUMB_TIP].y > FINGER_MARGIN * 2
        return (
            thumb_up
            and _finger_closed(hand_landmarks, INDEX_FINGER_TIP, INDEX_FINGER_PIP)
            and _finger_closed(hand_landmarks, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP)
            and _finger_closed(hand_landmarks, RING_FINGER_TIP, RING_FINGER_PIP)
            and _finger_closed(hand_landmarks, PINKY_TIP, PINKY_PIP)
        )
    except Exception:
        return False

def is_peace_sign(hand_landmarks):
    try:
        return (
            _finger_open(hand_landmarks, INDEX_FINGER_TIP, INDEX_FINGER_PIP)
            and _finger_open(hand_landmarks, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP)
            and _finger_closed(hand_landmarks, RING_FINGER_TIP, RING_FINGER_PIP)
            and _finger_closed(hand_landmarks, PINKY_TIP, PINKY_PIP)
        )
    except Exception:
        return False

def is_middle_finger(hand_landmarks):
    try:
        return (
            _finger_open(hand_landmarks, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP)
            and _finger_closed(hand_landmarks, INDEX_FINGER_TIP, INDEX_FINGER_PIP)
            and _finger_closed(hand_landmarks, RING_FINGER_TIP, RING_FINGER_PIP)
            and _finger_closed(hand_landmarks, PINKY_TIP, PINKY_PIP)
        )
    except Exception:
        return False

HEART_PINCH_DISTANCE = 0.06  # Distância máxima (coords normalizadas) pra considerar dedos "se tocando"

def is_one_hand_heart(hand_landmarks):
    # Coraçãozinho estilo K-pop: polegar e indicador se tocando, resto da mão fechado
    try:
        thumb_index_close = _distance(hand_landmarks[THUMB_TIP], hand_landmarks[INDEX_FINGER_TIP]) < HEART_PINCH_DISTANCE
        return (
            thumb_index_close
            and _finger_closed(hand_landmarks, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP)
            and _finger_closed(hand_landmarks, RING_FINGER_TIP, RING_FINGER_PIP)
            and _finger_closed(hand_landmarks, PINKY_TIP, PINKY_PIP)
        )
    except Exception:
        return False

def is_two_hand_heart(left_landmarks, right_landmarks):
    # Coração com as duas mãos: polegares se tocando e indicadores se tocando no topo
    try:
        index_close = _distance(left_landmarks[INDEX_FINGER_TIP], right_landmarks[INDEX_FINGER_TIP]) < HEART_PINCH_DISTANCE
        thumb_close = _distance(left_landmarks[THUMB_TIP], right_landmarks[THUMB_TIP]) < HEART_PINCH_DISTANCE
        return index_close and thumb_close
    except Exception:
        return False

def draw_hand_landmarks(image, hand_landmarks_list):
    h, w = image.shape[:2]
    for hand_landmarks in hand_landmarks_list:
        points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
        for start_idx, end_idx in HAND_CONNECTIONS:
            cv2.line(image, points[start_idx], points[end_idx], (0, 255, 0), 2)
        for point in points:
            cv2.circle(image, point, 4, (0, 0, 255), -1)

# --- Detecção de gesto de movimento: "Six-Seven" (mãos alternando tipo balança) ---
BUFFER_LEN = 15          # Quantos frames de histórico guardar por mão (mais curto = reação mais rápida)
MAX_MISSED_FRAMES = 5    # Tolerância a sumiço momentâneo da mão antes de resetar o buffer
MIN_Y_RANGE = 0.02       # Amplitude mínima (coords normalizadas) pra considerar "movimento de verdade"
MIN_CORRELATION = -0.3   # As mãos precisam estar em oposição de fase (uma sobe, outra desce)

wrist_buffers = {"Left": deque(maxlen=BUFFER_LEN), "Right": deque(maxlen=BUFFER_LEN)}
missed_counts = {"Left": 0, "Right": 0}

def is_six_seven_gesture(left_buffer, right_buffer):
    left = np.array(left_buffer)
    right = np.array(right_buffer)

    if (left.max() - left.min()) < MIN_Y_RANGE or (right.max() - right.min()) < MIN_Y_RANGE:
        return False

    left_centered = left - left.mean()
    right_centered = right - right.mean()

    correlation = np.corrcoef(left_centered, right_centered)[0, 1]
    if np.isnan(correlation) or correlation > MIN_CORRELATION:
        return False

    # Garante que teve pelo menos uma inversão de direção (subida->descida), não só um deslize único
    diffs = np.diff(left_centered)
    signs = np.sign(diffs)
    signs = signs[signs != 0]
    if np.count_nonzero(np.diff(signs)) < 1:
        return False

    return True

def is_hand_near_top(buffer, threshold=0.3):
    # Em coordenadas de imagem, Y menor = mais alto na tela ("mão pra cima")
    arr = np.array(buffer)
    span = arr.max() - arr.min()
    if span == 0:
        return False
    return (arr[-1] - arr.min()) <= threshold * span

MIN_DISPLAY_SECONDS = 3  # Tempo mínimo que a imagem fica na tela depois de detectar o gesto

# Definindo o tamanho das imagens
MEME_WIDTH = 200
MEME_HEIGHT = 150

def load_meme_images(filenames):
    images = []
    for path in filenames:
        try:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise FileNotFoundError(f"Não foi possível carregar: {path}")

            # Redimensiona a imagem
            img_resized = cv2.resize(img, (MEME_WIDTH, MEME_HEIGHT), interpolation=cv2.INTER_AREA)

            # Processa a transparência
            if img_resized.shape[2] == 4:
                b, g, r, alpha = cv2.split(img_resized)
                img_bgr = cv2.merge((b, g, r))
                alpha_mask = alpha / 255.0
                images.append( (img_bgr, alpha_mask) )
            else: # Se não tem transparência
                images.append( (img_resized, None) )

            print(f"Sucesso ao carregar e processar: {path}")

        except Exception as e:
            print(f"ERRO ao carregar '{path}': {e}")
            print("Verifique o nome e se o arquivo existe. Pulando este arquivo.")
    return images

print("Carregando imagens...")

# Cada gesto tem seu próprio pool de imagens; a ordem da lista GESTURES define a prioridade
# quando mais de um gesto "casaria" no mesmo frame.
GESTURE_IMAGES = {
    "nu_metal": load_meme_images(['numetal.jpg', 'calma.jpg', 'avril.jpg', 'serj.jpg', 'davi.jpg']),
    "six_seven": load_meme_images(['sixseven.png', 'sixseven2.png']),
    "joia": load_meme_images(['joia1.jpg', 'joia2.jpg']),
    "paz": load_meme_images(['paz1.jpg', 'paz2.jpg']),
    "coracao": load_meme_images(['coracao.jpg', 'coracao2.jpg']),
    "triste": load_meme_images(['triste1.jpg', 'triste2.jpg']),
}
GESTURES = ["nu_metal", "six_seven", "joia", "paz", "coracao", "triste"]

if any(not images for images in GESTURE_IMAGES.values()):
    print("NENHUMA IMAGEM FOI CARREGADA PRA ALGUM GESTO. Verifique os nomes dos arquivos.")
    exit()

print(f"--- Imagens carregadas: { {name: len(imgs) for name, imgs in GESTURE_IMAGES.items()} }. Iniciando webcam. ---")

# Inicializa a Webcam
cap = cv2.VideoCapture(0)
# 720p é um bom meio-termo: bem menos pixelizado que o padrão, sem pesar demais no processamento
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

DETECTION_WIDTH = 320  # Detecção roda numa cópia menor pra ganhar FPS; os pontos são normalizados (0-1) e continuam válidos no frame grande

# Controle de estado
STABILITY_FRAMES = 6  # Quantos frames seguidos um gesto precisa se manter pra não disparar com tremedeira
stability_counters = {name: 0 for name in GESTURES}
previously_detected = {name: False for name in GESTURES}
current_image_to_display = None # Guarda a imagem aleatória escolhida
display_until = 0 # Timestamp até quando a imagem deve continuar na tela
debug_frame_counter = 0

print("Mostre um gesto (Nu Metal Pose, Six-Seven, Jóia, Paz, Coração ou Dedo do Meio)! Pressione 'q' para sair.")

WINDOW_NAME = 'Nu Metal Detector (Com Imagem!)'
cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1) # Inverte para modo selfie
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    h, w = rgb_frame.shape[:2]
    detection_height = int(h * (DETECTION_WIDTH / w))
    small_rgb_frame = cv2.resize(rgb_frame, (DETECTION_WIDTH, detection_height), interpolation=cv2.INTER_LINEAR)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=small_rgb_frame)
    detection_result = detector.detect(mp_image)

    bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

    open_hands_count = 0
    seen_this_frame = set()
    hands_by_label = {}

    found = {name: False for name in GESTURES}

    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness

    if hand_landmarks_list:
        draw_hand_landmarks(bgr_frame, hand_landmarks_list)

        for hand_landmarks, handedness in zip(hand_landmarks_list, handedness_list):
            if is_hand_open(hand_landmarks):
                open_hands_count += 1
            if is_thumbs_up(hand_landmarks):
                found["joia"] = True
            if is_peace_sign(hand_landmarks):
                found["paz"] = True
            if is_middle_finger(hand_landmarks):
                found["triste"] = True
            if is_one_hand_heart(hand_landmarks):
                found["coracao"] = True

            # Alimenta o buffer de posição do pulso pra detecção de movimento
            label = handedness[0].category_name
            wrist_y = hand_landmarks[WRIST].y
            wrist_buffers[label].append(wrist_y)
            missed_counts[label] = 0
            seen_this_frame.add(label)
            hands_by_label[label] = hand_landmarks

        # Checa se a Nu Metal Pose foi detectada (no frame congelado)
        if len(hand_landmarks_list) == 2 and open_hands_count == 2:
            found["nu_metal"] = True

        if "Left" in hands_by_label and "Right" in hands_by_label:
            if is_two_hand_heart(hands_by_label["Left"], hands_by_label["Right"]):
                found["coracao"] = True

    # Reseta o buffer da mão que sumiu de vista por muito tempo
    for label in ("Left", "Right"):
        if label not in seen_this_frame:
            missed_counts[label] += 1
            if missed_counts[label] > MAX_MISSED_FRAMES:
                wrist_buffers[label].clear()

    if len(wrist_buffers["Left"]) == BUFFER_LEN and len(wrist_buffers["Right"]) == BUFFER_LEN:
        found["six_seven"] = (
            is_six_seven_gesture(wrist_buffers["Left"], wrist_buffers["Right"])
            and (is_hand_near_top(wrist_buffers["Left"]) or is_hand_near_top(wrist_buffers["Right"]))
        )

        # DEBUG temporário: mostra os números reais pra calibrar os limiares
        debug_frame_counter += 1
        if debug_frame_counter % 5 == 0:
            l = np.array(wrist_buffers["Left"])
            r = np.array(wrist_buffers["Right"])
            l_range = l.max() - l.min()
            r_range = r.max() - r.min()
            lc, rc = l - l.mean(), r - r.mean()
            corr = np.corrcoef(lc, rc)[0, 1]
            print(f"[debug six-seven] L_range={l_range:.3f} R_range={r_range:.3f} corr={corr:.2f} -> detectado={found['six_seven']}")

    # Exige o gesto sustentado por alguns frames seguidos antes de valer (evita tremedeira/flicker)
    for name in GESTURES:
        stability_counters[name] = stability_counters[name] + 1 if found[name] else 0
    stable = {name: stability_counters[name] >= STABILITY_FRAMES for name in GESTURES}

    # O primeiro gesto da lista GESTURES que "casar" de forma estável nesse frame ganha a prioridade
    active_gesture = next((name for name in GESTURES if stable[name]), None)

    if active_gesture:
        if not previously_detected[active_gesture]:
            for name in GESTURES:
                previously_detected[name] = False
            previously_detected[active_gesture] = True
            current_image_to_display = random.choice(GESTURE_IMAGES[active_gesture])
            display_until = time.time() + MIN_DISPLAY_SECONDS
            if active_gesture == "six_seven":
                # Limpa o buffer pra exigir um novo ciclo de movimento antes de disparar de novo
                wrist_buffers["Left"].clear()
                wrist_buffers["Right"].clear()
    else:
        for name in GESTURES:
            previously_detected[name] = False

    if active_gesture or time.time() < display_until:
        if current_image_to_display:
            # Pega a imagem e a máscara
            img_bgr, img_alpha = current_image_to_display

            # Posição da imagem
            x_offset = int((bgr_frame.shape[1] - MEME_WIDTH) / 2)
            y_offset = 20

            if y_offset + MEME_HEIGHT < bgr_frame.shape[0] and x_offset + MEME_WIDTH < bgr_frame.shape[1]:
                roi = bgr_frame[y_offset : y_offset + MEME_HEIGHT, x_offset : x_offset + MEME_WIDTH]

                if img_alpha is not None: # Se é png
                    for c in range(0, 3):
                        bgr_frame[y_offset : y_offset + MEME_HEIGHT, x_offset : x_offset + MEME_WIDTH, c] = \
                            roi[:, :, c] * (1 - img_alpha) + \
                            img_bgr[:, :, c] * img_alpha
                else: # Se é jpg
                    bgr_frame[y_offset : y_offset + MEME_HEIGHT, x_offset : x_offset + MEME_WIDTH] = img_bgr

    else: # Se nenhum gesto ativo nem tempo mínimo de exibição restante
        current_image_to_display = None # Limpa a imagem

    bgr_frame = cv2.resize(bgr_frame, (SCREEN_WIDTH, SCREEN_HEIGHT), interpolation=cv2.INTER_CUBIC)
    cv2.imshow(WINDOW_NAME, bgr_frame)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

print("Fechando...")
cap.release()
cv2.destroyAllWindows()
detector.close()

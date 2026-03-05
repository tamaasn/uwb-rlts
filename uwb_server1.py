import socket
import numpy as np
import threading
import pygame
import sys

WIDTH, HEIGHT =660, 550
GRID_SIZE = 40
SCALE = 1
WIN_W, WIN_H = WIDTH * SCALE, HEIGHT * SCALE

BG_COLOR = (30, 30, 30)
GRID_COLOR = (60, 60, 60)
ANCHOR_COLOR = (255, 50, 50)
TAG_COLOR = (0, 255, 100)

anchor_pos = [
    [330, 0],
    [0, 550],
    [660, 550]
]


res_x, res_y = 0.0, 0.0
anchors_cm = [0.0, 0.0, 0.0]
addresses = [0x1782, 0x1783, 0x1784]
clients = []
is_running = True

def map(x, in_min,in_max,out_min,out_max):
    if x > in_max:
        return out_max
    return ((x-in_min) * (out_max-out_min)/(in_max-in_min)) + out_min

def trilaterate(anchors, distances):
    try:
        P1, P2, P3 = np.array(anchors[0]), np.array(anchors[1]), np.array(anchors[2])
        r1, r2, r3 = distances
        p2p1 = P2 - P1
        d = np.linalg.norm(p2p1)
        ex = p2p1 / d
        p3p1 = P3 - P1
        i = np.dot(ex, p3p1)
        ey = (p3p1 - i * ex)
        ey = ey / np.linalg.norm(ey)
        j = np.dot(ey, p3p1)
        x = (r1**2 - r2**2 + d**2) / (2*d)
        y = (r1**2 - r3**2 + i**2 + j**2) / (2*j) - (i/j)*x
        pos = P1 + x * ex + y * ey
        return pos[0], pos[1]
    except Exception:
        return 0, 0

def accept_client(s):
    global clients, is_running
    while is_running:
        try:
            client, addr = s.accept()
            #type_ = client.recv(256).decode().strip()
            clients.append({"client": client, "type": "uwb"})
            print(f"Connected: {client} at {addr}")
        except Exception as e:
            print(e)
            break

def get_position_logic():
    global res_x, res_y, anchors_cm, is_running
    while is_running:
        for client in clients:
            if client["type"] == "uwb":
                try:
                    raw = client["client"].recv(256).decode().split(";")[0]
                    print(raw)
                    data = raw.split("|")
                    if len(data) < 2: continue
                    
                    addr_val = int(data[0])
                    dist_cm = float(data[1]) * 100
                    #dist_cm = map(dist_cm, -40,,0,280)

                    for i in range(len(addresses)):
                        if addr_val == addresses[i]:
                            anchors_cm[i] = dist_cm
                            break

                    if all(d > 0 for d in anchors_cm):
                        res_x, res_y = trilaterate(anchor_pos, anchors_cm)
                except Exception as e:
                    print(e)
                    continue

def main():
    global is_running
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("UWB Real-Time Tracking")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 1150))
    s.listen(5)

    threading.Thread(target=accept_client, args=(s,), daemon=True).start()
    threading.Thread(target=get_position_logic, daemon=True).start()

    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

        screen.fill(BG_COLOR)

        for x in range(0, WIDTH + 1, GRID_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x*SCALE, 0), (x*SCALE, HEIGHT*SCALE))
        for y in range(0, HEIGHT + 1, GRID_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y*SCALE), (WIDTH*SCALE, y*SCALE))

        for i, (ax, ay) in enumerate(anchor_pos):
            px, py = int(ax * SCALE), int(ay * SCALE)
            pygame.draw.circle(screen, ANCHOR_COLOR, (px, py), 8)
            
            label = font.render(f"A{i+1}: {anchors_cm[i]:.1f}cm", True, (255, 255, 255))
            text_w, text_h = label.get_size()
            
            # Default offset: bottom-right of the anchor
            text_x = px + 10
            text_y = py + 10
            
            # If it goes off the RIGHT side, flip it to the left
            if text_x + text_w > WIN_W:
                text_x = px - text_w - 10
                
            # If it goes off the BOTTOM side, flip it up
            if text_y + text_h > WIN_H:
                text_y = py - text_h - 10
                
            # If it goes off the TOP side, push it down
            if text_y < 0:
                text_y = py + 10
                
            screen.blit(label, (text_x, text_y))

        tx, ty = int(res_x * SCALE), int(res_y * SCALE)
        tx = max(0, min(WIN_W, tx))
        ty = max(0, min(WIN_H, ty))
        
        pygame.draw.circle(screen, TAG_COLOR, (tx, ty), 12)
        pos_text = font.render(f"Tag: ({res_x:.1f}, {res_y:.1f})", True, TAG_COLOR)
        screen.blit(pos_text, (tx + 15, ty + 15))

        pygame.display.flip()
        clock.tick(30) 

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
import pgzrun
import random
from pygame import Rect

import os
os.environ['SDL_VIDEO_CENTERED'] = '1'


# Configuração da janela
WIDTH = 1200
HEIGHT = 800

# Criando um ator para a bolha
bou = Actor("bou")
bou.pos = (WIDTH // 2, HEIGHT // 1.2)

# Criando um ator para o espinho
spikes = []
spike = Actor("spike")
spawn_time = 0
spawn_interval = 120

floor = Rect((0, HEIGHT - 30), (WIDTH, 30))
start_button = Rect((WIDTH // 2 - 100, HEIGHT // 2 - 20), (200, 50))
music_button = Rect((WIDTH - 70, 10), (60, 60))
sounds.menu_theme.play(-1)  # música do menu
progress = 0  # controle de progresso (pontuação)
velocity = 5  # Velocidade de movimento
velocity_y = 0  # Velocidade vertical
gravity = 0.5  # força que puxa para baixo
jump_force = -15  # impulso do pulo
deep = HEIGHT - 30  # limite do "chão" (altura)
no_floor = False
sound_flag = True  # controle de som
double_jump = False  # controle de pulo duplo
touched_floor = False  # controle se tocou o chão
game_over_flag = False
end_game = False
game_started = False
walking = False  # controle de animação de caminhada
time = 0
end_time = 0


# Controle da câmera
camera_y = 0

# Plataformas
platform_space = 120  # distância vertical entre plataformas
plataforms = []

# Animação simples da bolha
frames_bou = ["bou", "bou2", "bou3", "bou2", "bou"]
frames_spike = ["spike", "spike2", "spike3", "spike2", "spike"]
frame_actual = 0
count = 0
animation_velocity = 10  # velocidade da animação


def draw():
    if game_started:
        screen.clear()
        if progress <= 20:
            screen.fill((0, 0, 60))
        elif progress <= 40:
            screen.fill((0, 0, 100))
        elif progress <= 60:
            screen.fill((0, 0, 140))
        elif progress <= 80:
            screen.fill((0, 0, 180))
        else:
            screen.fill((0, 0, 220))

        screen.draw.text(f"Progresso: {progress}%", (WIDTH // 2 - 60, 10),
                         color="white", fontsize=30)
        screen.draw.text(f"Tempo: {time} segundos", topright=(WIDTH - 10, 10),
                         color="white", fontsize=30)
        screen.draw.text("Pressione ESC para sair", midbottom=(85, 55),
                         color="white", fontsize=20)
        screen.draw.text("e M para música", midbottom=(60, 80),
                         color="white", fontsize=20)
        screen.draw.text("Use A e D para mover e Espaço para pular",
                         (10, 10), color="white")

        # desenhar chão (ajustado pela câmera)
        screen.draw.filled_rect(floor.move(0, camera_y), (100, 50, 0))

        for s in spikes:
            s.draw()

        # desenhar o Bou
        bou.draw()

        # desenhar plataformas (ajustadas pela câmera)
        for p in plataforms:
            screen.draw.filled_rect(
                Rect(p.x, p.y + camera_y, p.w, p.h), (0, 200, 0))

        if game_over_flag:
            screen.fill((0, 0, 0))
            screen.draw.text("Game Over! Reiniciando...", center=(
                WIDTH // 2, HEIGHT // 2), color="red", fontsize=60)
            screen.draw.text(f"Seu progresso: {progress}%", center=(
                WIDTH // 2, HEIGHT // 2 + 80), color="white", fontsize=40)
            screen.draw.text(f"Tempo: {end_time} segundos", center=(
                WIDTH // 2, HEIGHT // 2 + 130), color="white", fontsize=40)
            return

        if end_game:
            screen.fill((0, 0, 0))
            screen.draw.text("Parabéns! Você venceu!", center=(
                WIDTH // 2, HEIGHT // 2), color="yellow", fontsize=60)
            screen.draw.text(f"Tempo: {end_time} segundos", center=(
                WIDTH // 2, HEIGHT // 2 + 80), color="white", fontsize=40)
            return
    else:  # menu principal
        screen.clear()
        screen.fill((0, 0, 220))
        screen.draw.text("Bou Bolha", center=(WIDTH // 2, HEIGHT // 2 - 80),
                         color="white", fontsize=80)
        screen.draw.textbox("Start", start_button,
                            color="black")
        if not sound_flag:
            screen.draw.textbox("Música desligada", music_button,
                                color="black")
        elif sound_flag:
            screen.draw.textbox("Música ligada", music_button,
                                color="black")
        screen.draw.text("Use A e D para mover e Espaço para pular", center=(
            WIDTH // 2, HEIGHT // 2 + 80), color="white", fontsize=30)


def update():

    global velocity_y, double_jump, touched_floor, camera_y, no_floor, spawn_time, spawn_interval, progress, end_game, time, game_started

    if not game_started:
        main_menu()
        if keyboard.space:
            restart()
        return

    if game_started:
        animate()

        touched_floor = False

        # Gravidade
        if velocity_y < 15:  # limite de velocidade de queda
            velocity_y += gravity
        bou.y += velocity_y

        # Spawn de spikes
        spawn_time += 1
        if spawn_time >= spawn_interval:
            spawn_time = 0
            spawn_spike()
            if spawn_interval > 40:
                spawn_interval -= 2  # aumenta a dificuldade com o tempo

        # Movimento dos spikes
        for s in spikes[:]:
            s.y += 5
            if s.top > HEIGHT:
                spikes.remove(s)
            elif bou.colliderect(s):  # Colisão com espinho
                game_over()

        # Colisão com o chão
        for p in plataforms:
            # desloca a plataforma para onde ela realmente está em relação ao Bou
            plataform_adjusted = p.move(0, camera_y)
            if bou.colliderect(plataform_adjusted) and velocity_y >= 0 and bou.bottom < plataform_adjusted.top + 20:
                bou.bottom = plataform_adjusted.top
                velocity_y = 0
                double_jump = False
                touched_floor = True

        if bou.y > deep:  # caiu no chão
            bou.y = deep
            velocity_y = 0
            double_jump = False
            touched_floor = True
            if no_floor:  # caiu no buraco
                game_over()

        # desenhar plataformas (ajustadas pela câmera)
        for p in plataforms:
            screen.draw.filled_rect(
                Rect(p.x, p.y + camera_y, p.w, p.h), (0, 200, 0))

        # Movimento com setas
        if keyboard.a:
            bou.image = "bou_l"
            bou_walk()
            if bou.x > 30:
                bou.x -= velocity
        if keyboard.d:
            bou.image = "bou_r"
            bou_walk()
            if bou.x < WIDTH - 30:
                bou.x += velocity

        # Movimento da câmera (acompanha o Bou quando ele sobe)
        if bou.y < HEIGHT // 2 and progress < 100:
            diff = HEIGHT // 2 - bou.y
            bou.y = HEIGHT // 2
            camera_y += diff
            for s in spikes[:]:
                s.y += diff

        # Gerar mais plataformas quando a tela sobe
        if min(p.top for p in plataforms) + camera_y > 0 and progress < 100:
            generate_plataforms(3)
            progress += 1  # aumenta o progresso (pontuação)
            no_floor = True

        if progress == 100 and bou.y <= 0:
            game_win()

        # Remover plataformas muito abaixo da tela
        plataforms[:] = [
            p for p in plataforms if p.y + camera_y < HEIGHT + 100]


def on_mouse_down(pos):
    global sound_flag, game_started
    if not game_started:
        if music_button.collidepoint(pos):
            if sound_flag:  # se estava com som, desliga o som
                sound_flag = False
                sounds.menu_theme.stop()
            else:   # se estava sem som, liga o som
                sound_flag = True
                sounds.menu_theme.play(-1)

        if start_button.collidepoint(pos):
            restart()


def bou_walk():
    global walking
    walking = True
    clock.schedule_unique(bou_idle, 0.2)


def bou_idle():
    global walking
    walking = False
    bou.image = "bou"


def spawn_spike():
    if len(spikes) < 4:
        x = random.randint(50, WIDTH - 50)
        spike = Actor("spike", (x, -50))
        spikes.append(spike)


def on_key_down(key):
    global velocity_y, double_jump, tocou_chao, sound_flag
    if key == keys.SPACE:

        if touched_floor:  # Pulo normal
            if sound_flag:
                sounds.jump.play()
            velocity_y = jump_force
            double_jump = False  # reseta para permitir um novo duplo
        elif not double_jump:  # Está no ar, mas ainda não usou o duplo
            if sound_flag:
                sounds.jump.play()
            velocity_y = jump_force
            double_jump = True   # gasta o duplo
    if key == keys.ESCAPE and game_started:
        sounds.background_music.stop()
        main_menu()

    if key == keys.M:  # tecla M para ligar/desligar som
        if sound_flag:  # se estava com som, desliga o som
            sound_flag = False
            sounds.background_music.stop()
            sounds.menu_theme.stop()
        else:   # se estava sem som, liga o som
            sound_flag = True
            if not game_started:
                sounds.menu_theme.play(-1)


def animate():
    """Troca as imagens dos personagens para criar a animação de 5 frames"""
    global count, frame_actual, walking
    count += 1
    if count >= animation_velocity:
        count = 0
        frame_actual = (frame_actual + 1) % len(frames_bou)
        if not walking:
            bou.image = frames_bou[frame_actual]
        for i, s in enumerate(spikes):
            s.image = frames_spike[(frame_actual + i) % len(frames_spike)]


def generate_plataforms(qtd=8):
    """Cria plataformas iniciais ou adicionais"""
    global plataforms
    if not plataforms:  # primeira geração
        y = HEIGHT - 40
    else:
        y = min(p.top for p in plataforms) - platform_space

    for _ in range(qtd):
        largura = random.randint(100, 200)
        x = random.randint(50, WIDTH - largura - 50)
        plataforms.append(Rect((x, y), (largura, 20)))
        y -= platform_space


def game_over():
    global game_over_flag, no_floor, time, end_time, end_game
    if game_over_flag or end_game:
        return  # Evita múltiplas chamadas
    end_time = time  # captura o tempo final
    sounds.background_music.stop()
    if sound_flag:
        sounds.game_over_sound.play()
    no_floor = False
    game_over_flag = True
    clock.schedule_unique(restart, 1)


def game_win():
    global end_game, end_time, time
    if end_game or game_over_flag:
        return  # Evita múltiplas chamadas
    end_time = time  # captura o tempo final
    end_game = True
    sounds.background_music.stop()
    if sound_flag:
        sounds.bubble_pop.play()
    clock.schedule_unique(main_menu, 3)


def restart():
    """Reinicia o jogo"""
    global plataforms, camera_y, spikes, game_over_flag, spawn_interval, progress, time, game_started, end_game

    sounds.menu_theme.stop()

    if not game_started:
        game_started = True

    progress = 0  # reseta a pontuação
    if sound_flag:
        sounds.background_music.play(-1)  # reinicia a música de fundo
    bou.pos = (WIDTH // 2, HEIGHT // 1.2)
    spawn_interval = 120
    plataforms = []
    generate_plataforms()
    camera_y = 0
    time = 0
    end_game = False
    spikes.clear()
    game_over_flag = False
    tick()  # reinicia o contador de tempo


def main_menu():
    """Volta para o menu principal (aqui apenas reinicia o jogo)"""
    global game_started
    if not game_started:
        return  # já está no menu
    game_started = False
    sounds.background_music.stop()
    if sound_flag:
        sounds.menu_theme.play(-1)  # música do menu


def tick():
    global time
    time += 1
    if not game_over_flag and not end_game:
        clock.schedule_unique(tick, 1)


# Plataformas iniciais
generate_plataforms()

# Agendar o tick para começar o contador de tempo
clock.schedule(tick, 1)

# Rodar o jogo
pgzrun.go()

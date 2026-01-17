import random
import sys

import pygame

# --- KONFIGURACJA (SETTINGS) ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
TILE_SIZE = 48

# Fizyka i Ruch
GRAVITY = 0.8
WALK_SPEED = 7
SPRINT_SPEED = 12  # Nowa prędkość sprintu
JUMP_POWER = -22
TERMINAL_VELOCITY = 15
ENEMY_SPEED = 3

# Typy kafelków
TYPE_GROUND = 0
TYPE_BRICK = 1
TYPE_HARD = 2
TYPE_PIPE = 3
TYPE_FLAG_POLE = 98  # Maszt
TYPE_FLAG_TOP = 99  # Sama flaga


# --- DEFINICJE MOTYWÓW POZIOMÓW (COLORS) ---
class LevelTheme:
    def __init__(self, bg, ground, brick, pipe, enemy):
        self.bg_color = bg
        self.ground_color = ground
        self.brick_color = brick
        self.pipe_color = pipe
        self.enemy_color = enemy


# Motyw 1: Klasyczny Mario
THEME_DAY = LevelTheme(
    bg=(107, 140, 255),  # Sky Blue
    ground=(200, 76, 12),  # Brownish
    brick=(180, 50, 0),
    pipe=(0, 180, 0),
    enemy=(165, 42, 42),
)

# Motyw 2: Jaskinia / Noc
THEME_NIGHT = LevelTheme(
    bg=(20, 20, 40),  # Dark Navy
    ground=(100, 100, 110),  # Grey Stone
    brick=(80, 80, 120),  # Blueish Bricks
    pipe=(0, 120, 0),  # Darker Pipe
    enemy=(120, 30, 30),  # Dark Red
)

# Kolory stałe
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (255, 0, 0)
PIPE_HIGHLIGHT = (50, 220, 50)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE - 10, TILE_SIZE - 4))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.alive = True
        self.finished_level = False  # Czy dotknął flagi

    def update(self, tiles, enemies, flags):
        if not self.alive:
            return

        keys = pygame.key.get_pressed()
        self.vel_x = 0

        # --- STEROWANIE ---
        # Sprint (Shift)
        current_speed = WALK_SPEED
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = SPRINT_SPEED

        # Lewo (Strzałka lub A)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -current_speed
        # Prawo (Strzałka lub D)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = current_speed

        # Skok (Spacja, W lub Strzałka w górę)
        if (
            keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        ) and self.on_ground:
            self.jump()

        # Grawitacja
        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY

        # Ruch X
        self.rect.x += self.vel_x
        self.collide_tiles(tiles, "x")

        # Ruch Y
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collide_tiles(tiles, "y")

        # Interakcje
        self.collide_enemies(enemies)
        self.collide_flags(flags)

        # Śmierć od upadku
        if self.rect.top > SCREEN_HEIGHT + TILE_SIZE:
            self.alive = False

    def jump(self):
        self.vel_y = JUMP_POWER

    def bounce(self):
        self.vel_y = JUMP_POWER * 0.7

    def collide_tiles(self, tiles, direction):
        hits = pygame.sprite.spritecollide(self, tiles, False)
        for tile in hits:
            # Ignoruj kolizję z elementami flagi (można przez nie przenikać)
            if tile.tile_type in [TYPE_FLAG_POLE, TYPE_FLAG_TOP]:
                continue

            if direction == "x":
                if self.vel_x > 0:
                    self.rect.right = tile.rect.left
                elif self.vel_x < 0:
                    self.rect.left = tile.rect.right
            if direction == "y":
                if self.vel_y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = tile.rect.bottom
                    self.vel_y = 0

    def collide_enemies(self, enemies):
        hits = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hits:
            if enemy.alive:
                if self.vel_y > 0 and self.rect.bottom < enemy.rect.centery + 15:
                    enemy.die()
                    self.bounce()
                else:
                    self.alive = False

    def collide_flags(self, flags):
        # Sprawdzenie czy dotknęliśmy flagi
        if pygame.sprite.spritecollide(self, flags, False):
            self.finished_level = True


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)

        # Oczy
        pygame.draw.rect(self.image, BLACK, (5, 10, 10, 15))
        pygame.draw.rect(self.image, BLACK, (TILE_SIZE - 15, 10, 10, 15))

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = -ENEMY_SPEED
        self.vel_y = 0
        self.alive = True

    def update(self, tiles):
        if not self.alive:
            self.kill()
            return

        self.vel_y += GRAVITY
        self.rect.x += self.vel_x

        hits_x = pygame.sprite.spritecollide(self, tiles, False)
        # Ignoruj kolizje z flagami dla wrogów też
        hits_x = [
            t for t in hits_x if t.tile_type not in [TYPE_FLAG_POLE, TYPE_FLAG_TOP]
        ]

        if hits_x:
            if self.vel_x > 0:
                self.rect.right = hits_x[0].rect.left
                self.vel_x = -ENEMY_SPEED
            else:
                self.rect.left = hits_x[0].rect.right
                self.vel_x = ENEMY_SPEED

        self.rect.y += self.vel_y
        hits_y = pygame.sprite.spritecollide(self, tiles, False)
        hits_y = [
            t for t in hits_y if t.tile_type not in [TYPE_FLAG_POLE, TYPE_FLAG_TOP]
        ]

        if hits_y:
            if self.vel_y > 0:
                self.rect.bottom = hits_y[0].rect.top
                self.vel_y = 0

        if self.rect.y > SCREEN_HEIGHT + 200:
            self.alive = False

    def die(self):
        self.alive = False


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type, theme):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        # Obsługa przezroczystości dla flagi
        self.image.set_colorkey((255, 0, 255))
        self.image.fill((255, 0, 255))

        self.tile_type = tile_type
        self.theme = theme
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.draw_texture()

    def draw_texture(self):
        if self.tile_type == TYPE_GROUND:
            self.image.fill(self.theme.ground_color)
            pygame.draw.rect(self.image, BLACK, (0, 0, TILE_SIZE, TILE_SIZE), 1)

        elif self.tile_type == TYPE_BRICK:
            self.image.fill(self.theme.brick_color)
            pygame.draw.line(
                self.image, BLACK, (0, TILE_SIZE // 2), (TILE_SIZE, TILE_SIZE // 2), 2
            )
            pygame.draw.line(
                self.image,
                BLACK,
                (TILE_SIZE // 2, 0),
                (TILE_SIZE // 2, TILE_SIZE // 2),
                2,
            )
            pygame.draw.line(
                self.image,
                BLACK,
                (TILE_SIZE // 4, TILE_SIZE // 2),
                (TILE_SIZE // 4, TILE_SIZE),
                2,
            )
            pygame.draw.rect(self.image, BLACK, (0, 0, TILE_SIZE, TILE_SIZE), 1)

        elif self.tile_type == TYPE_PIPE:
            self.image.fill(self.theme.pipe_color)
            pygame.draw.rect(self.image, PIPE_HIGHLIGHT, (5, 0, 10, TILE_SIZE))
            pygame.draw.rect(self.image, BLACK, (0, 0, TILE_SIZE, TILE_SIZE), 2)

        elif self.tile_type == TYPE_HARD:
            self.image.fill((80, 80, 80))
            pygame.draw.rect(self.image, BLACK, (0, 0, TILE_SIZE, TILE_SIZE), 1)

        elif self.tile_type == TYPE_FLAG_POLE:
            # Rysujemy szary maszt
            pygame.draw.rect(
                self.image, (200, 200, 200), (TILE_SIZE // 2 - 2, 0, 4, TILE_SIZE)
            )

        elif self.tile_type == TYPE_FLAG_TOP:
            # Szczyt masztu + flaga
            pygame.draw.rect(
                self.image, (200, 200, 200), (TILE_SIZE // 2 - 2, 0, 4, TILE_SIZE)
            )
            # Trójkątna flaga
            pygame.draw.polygon(
                self.image,
                (255, 255, 0),
                [
                    (TILE_SIZE // 2 + 2, 2),
                    (TILE_SIZE - 2, TILE_SIZE // 4),
                    (TILE_SIZE // 2 + 2, TILE_SIZE // 2),
                ],
            )


class LevelGenerator:
    def __init__(self, level_length_screens=10):
        self.level_width_tiles = (SCREEN_WIDTH // TILE_SIZE) * level_length_screens
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.flags = pygame.sprite.Group()  # Nowa grupa dla flagi
        self.current_x = 0
        self.floor_y = (SCREEN_HEIGHT // TILE_SIZE) - 3
        self.current_theme = THEME_DAY

    def set_theme(self, theme):
        self.current_theme = theme

    def generate(self, difficulty=1):
        """Generuje poziom. difficulty wpływa na szansę na dziury i wrogów."""
        self.tiles.empty()
        self.enemies.empty()
        self.flags.empty()
        self.current_x = 0

        # 1. Start (bezpieczna strefa)
        self.create_flat_ground(8)

        # 2. Proceduralna część
        while self.current_x < self.level_width_tiles:
            # Zmieniona logika losowania - mniej hord, więcej różnorodności
            options = ["flat", "flat", "pipe", "gap", "stairs", "bricks"]
            if difficulty > 1:
                options.extend(["gap", "pipe"])  # Trudniej w poziomie 2

            pattern = random.choice(options)

            if pattern == "flat":
                length = random.randint(3, 8)
                # Zmniejszona szansa na wroga (0.2 zamiast 0.3)
                self.create_flat_ground(length, spawn_enemy_chance=0.2 * difficulty)
            elif pattern == "gap":
                length = random.randint(2, 3 if difficulty == 1 else 4)
                self.create_gap(length)
            elif pattern == "pipe":
                self.create_pipe(height=random.randint(2, 4))
            elif pattern == "stairs":
                self.create_stairs(direction=random.choice([1, -1]))
            elif pattern == "bricks":
                self.create_floating_platform()

        # 3. Meta (Flaga)
        self.create_finish_line()

        return (
            self.tiles,
            self.enemies,
            self.flags,
            (100, (self.floor_y - 2) * TILE_SIZE),
        )

    def _add_tile(self, x, y, type):
        t = Tile(x * TILE_SIZE, y * TILE_SIZE, type, self.current_theme)
        if type in [TYPE_FLAG_POLE, TYPE_FLAG_TOP]:
            self.flags.add(t)
        self.tiles.add(t)

    def _fill_ground_column(self, x, start_y):
        for y in range(start_y, self.floor_y + 5):
            self._add_tile(x, y, TYPE_GROUND)

    def create_flat_ground(self, width, spawn_enemy_chance=0.0):
        for _ in range(width):
            self._add_tile(self.current_x, self.floor_y, TYPE_GROUND)
            self._fill_ground_column(self.current_x, self.floor_y + 1)

            # Spawnowanie wroga - dodano warunek odstępu, aby nie byli na sobie
            if random.random() < spawn_enemy_chance:
                # Tylko jeśli ostatni element dodany nie jest wrogiem (uproszczone)
                enemy = Enemy(
                    self.current_x * TILE_SIZE,
                    (self.floor_y - 1) * TILE_SIZE,
                    self.current_theme.enemy_color,
                )
                self.enemies.add(enemy)

            self.current_x += 1

    def create_gap(self, width):
        self.current_x += width

    def create_pipe(self, height):
        self._add_tile(self.current_x, self.floor_y, TYPE_GROUND)
        self._fill_ground_column(self.current_x, self.floor_y + 1)

        pipe_top_y = self.floor_y - height
        for y in range(pipe_top_y, self.floor_y):
            self._add_tile(self.current_x, y, TYPE_PIPE)

        self.current_x += 1
        self.create_flat_ground(2)

    def create_stairs(self, direction=1):
        height = random.randint(3, 5)
        if direction == 1:
            for h in range(height):
                for y in range(self.floor_y - h, self.floor_y + 1):
                    self._add_tile(self.current_x, y, TYPE_HARD)
                self._fill_ground_column(self.current_x, self.floor_y + 1)
                self.current_x += 1
        else:
            for h in range(height - 1, -1, -1):
                for y in range(self.floor_y - h, self.floor_y + 1):
                    self._add_tile(self.current_x, y, TYPE_HARD)
                self._fill_ground_column(self.current_x, self.floor_y + 1)
                self.current_x += 1
        self.create_flat_ground(2)

    def create_floating_platform(self):
        width = random.randint(3, 6)
        plat_height = random.randint(3, 4)
        start_x = self.current_x
        self.create_flat_ground(width)

        for i in range(width):
            self._add_tile(start_x + i, self.floor_y - plat_height, TYPE_BRICK)

    def create_finish_line(self):
        # Mała platforma przed flagą
        self.create_flat_ground(3)

        # Flaga (szczyt)
        self._add_tile(self.current_x, self.floor_y - 3, TYPE_FLAG_TOP)
        # Maszt (środek)
        self._add_tile(self.current_x, self.floor_y - 2, TYPE_FLAG_POLE)
        # Maszt (dół)
        self._add_tile(self.current_x, self.floor_y - 1, TYPE_FLAG_POLE)

        # Podstawa (blok twardy)
        self._add_tile(self.current_x, self.floor_y, TYPE_HARD)
        self._fill_ground_column(self.current_x, self.floor_y + 1)

        self.current_x += 1
        self.create_flat_ground(5)  # Za flagą
        self.current_x += 5  # Bufor, żeby kamera dojechała


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)
        x = min(0, x)
        self.camera = pygame.Rect(x, 0, self.width, self.height)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Pygame Bros - Advanced")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 48)
        self.small_font = pygame.font.SysFont("Arial", 24)

        self.level_gen = LevelGenerator(level_length_screens=8)
        self.current_level_num = 1
        self.running = True

        self.start_new_game()

    def start_new_game(self):
        self.current_level_num = 1
        self.load_level()

    def load_level(self):
        # Konfiguracja poziomu w zależności od numeru
        if self.current_level_num == 1:
            theme = THEME_DAY
            difficulty = 1
        else:
            theme = THEME_NIGHT
            difficulty = 2

        self.level_gen.set_theme(theme)

        # Generowanie
        self.tiles, self.enemies, self.flags, spawn_pos = self.level_gen.generate(
            difficulty
        )

        # Gracz
        self.player = Player(spawn_pos[0], spawn_pos[1])
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.game_over = False
        self.win = False

        # Wymuszamy czyszczenie eventów, żeby postać nie skoczyła sama po restarcie
        pygame.event.clear()

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.events()
            if not self.game_over:
                self.update()
            self.draw()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset gry od poziomu 1
                    self.start_new_game()
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                # Jeśli wygraliśmy i naciskamy spację -> następny poziom
                if self.win and self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.current_level_num += 1
                        self.load_level()

    def update(self):
        # Aktualizacja wszystkich sprite'ów
        self.all_sprites.update(self.tiles, self.enemies, self.flags)
        self.enemies.update(self.tiles)
        self.camera.update(self.player)

        # Sprawdzenie czy gracz żyje
        if not self.player.alive:
            self.game_over = True
            self.win = False

        # Sprawdzenie czy gracz dotarł do flagi
        if self.player.finished_level:
            self.game_over = True
            self.win = True

    def draw(self):
        # Tło zależne od motywu
        self.screen.fill(self.level_gen.current_theme.bg_color)

        # Rysowanie grup
        for sprite in self.tiles:
            shifted = self.camera.apply(sprite)
            if -TILE_SIZE < shifted.x < SCREEN_WIDTH + TILE_SIZE:
                self.screen.blit(sprite.image, shifted)

        for sprite in self.flags:
            shifted = self.camera.apply(sprite)
            if -TILE_SIZE < shifted.x < SCREEN_WIDTH + TILE_SIZE:
                self.screen.blit(sprite.image, shifted)

        for sprite in self.enemies:
            shifted = self.camera.apply(sprite)
            if -TILE_SIZE < shifted.x < SCREEN_WIDTH + TILE_SIZE:
                self.screen.blit(sprite.image, shifted)

        if self.player.alive:
            self.screen.blit(self.player.image, self.camera.apply(self.player))

        # UI
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        if self.game_over:
            if self.win:
                msg1 = f"POZIOM {self.current_level_num} UKOŃCZONY!"
                msg2 = "Naciśnij SPACJĘ aby grać dalej"
                color = (255, 215, 0)
            else:
                msg1 = "GAME OVER"
                msg2 = "Naciśnij R aby zrestartować"
                color = (255, 50, 50)

            text1 = self.font.render(msg1, True, color)
            text2 = self.small_font.render(msg2, True, WHITE)

            # Cień tekstu dla czytelności
            rect1 = text1.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20))
            rect2 = text2.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))

            pygame.draw.rect(
                self.screen,
                BLACK,
                (
                    rect1.x - 10,
                    rect1.y - 10,
                    rect1.width + 20,
                    rect1.height + rect2.height + 60,
                ),
            )

            self.screen.blit(text1, rect1)
            self.screen.blit(text2, rect2)

        else:
            lvl_text = self.small_font.render(
                f"Level: {self.current_level_num}", True, WHITE
            )
            controls_text = self.small_font.render(
                "WASD/Strzałki - Ruch | Shift - Sprint | R - Reset", True, WHITE
            )
            self.screen.blit(lvl_text, (20, 20))
            self.screen.blit(controls_text, (20, 50))


if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()

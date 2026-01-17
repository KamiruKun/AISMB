import random
import sys

import pygame

# --- KONFIGURACJA (SETTINGS) ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 40  # Rozmiar kafelka (bloku)

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GROUND_COLOR = (101, 67, 33)  # Brązowy
GRASS_COLOR = (34, 139, 34)  # Zielony
PLAYER_COLOR = (255, 0, 0)  # Czerwony (Mario)
PLATFORM_COLOR = (255, 165, 0)  # Pomarańczowe platformy

# Fizyka
GRAVITY = 0.8
PLAYER_SPEED = 5
JUMP_POWER = -16
TERMINAL_VELOCITY = 15  # Maksymalna prędkość spadania


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE - 10, TILE_SIZE - 10))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.alive = True

    def update(self, tiles):
        if not self.alive:
            return

        # 1. Obsługa wejścia (Sterowanie)
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
        if keys[pygame.K_SPACE] and self.on_ground:
            self.jump()

        # 2. Grawitacja
        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY

        # 3. Ruch w osi X i kolizje
        self.rect.x += self.vel_x
        self.collide(tiles, "x")

        # 4. Ruch w osi Y i kolizje
        self.rect.y += self.vel_y
        self.on_ground = False  # Reset flagi przed sprawdzeniem
        self.collide(tiles, "y")

        # 5. Sprawdzenie śmierci (spadnięcie z mapy)
        if self.rect.top > SCREEN_HEIGHT * 2:  # Margines błędu
            self.alive = False

    def jump(self):
        self.vel_y = JUMP_POWER

    def collide(self, tiles, direction):
        hits = pygame.sprite.spritecollide(self, tiles, False)
        if hits:
            if direction == "x":
                if self.vel_x > 0:  # Ruch w prawo
                    self.rect.right = hits[0].rect.left
                elif self.vel_x < 0:  # Ruch w lewo
                    self.rect.left = hits[0].rect.right

            if direction == "y":
                if self.vel_y > 0:  # Spadanie
                    self.rect.bottom = hits[0].rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Skok w sufit
                    self.rect.top = hits[0].rect.bottom
                    self.vel_y = 0


class Tile(pygame.sprite.Sprite):
    """Podstawowy budulec poziomu"""

    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        # Dodajmy obramowanie żeby widzieć kafelki
        pygame.draw.rect(self.image, BLACK, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class LevelGenerator:
    """
    MODUŁ AI GENERUJĄCY POZIOM
    Działa jak prosty 'walker' - idzie w prawo i decyduje o wysokości terenu.
    """

    def __init__(self, level_length=200):
        self.level_length = level_length
        self.tiles = pygame.sprite.Group()
        self.spawn_point = (100, 100)

    def generate(self):
        self.tiles.empty()

        # Startowa platforma (płaska, żeby gracz nie spadł od razu)
        current_height = 10  # W jednostkach kafelków od góry (im więcej tym niżej)
        ground_floor = 15  # Poziom "dna"

        for x in range(0, 10):  # Pierwsze 10 klocków bezpieczne
            self._create_column(x, current_height, ground_floor)
            if x == 2:
                self.spawn_point = (x * TILE_SIZE, (current_height - 2) * TILE_SIZE)

        # Proceduralna generacja reszty poziomu
        last_x = 10

        while last_x < self.level_length:
            # Algorytm decyzyjny (AI)
            action = random.choice(["flat", "flat", "up", "down", "gap", "platform"])

            # Zapobieganie wyjściu poza ekran (góra/dół)
            if current_height < 4:
                action = "down"
            if current_height > 12:
                action = "up"

            if action == "flat":
                self._create_column(last_x, current_height, ground_floor)
                last_x += 1

            elif action == "up":
                current_height -= 1  # Idziemy w górę
                self._create_column(last_x, current_height, ground_floor)
                last_x += 1

            elif action == "down":
                current_height += 1  # Idziemy w dół
                self._create_column(last_x, current_height, ground_floor)
                last_x += 1

            elif action == "gap":
                # Tworzenie dziury (1-3 klocki szerokości)
                gap_width = random.randint(2, 3)
                last_x += gap_width
                # Po dziurze musi być ląd, najlepiej na podobnej wysokości lub niżej
                self._create_column(last_x, current_height, ground_floor)

            elif action == "platform":
                # Dodatkowa platforma w powietrzu
                plat_height = current_height - random.randint(3, 4)
                plat_width = random.randint(2, 4)
                for px in range(plat_width):
                    self.tiles.add(
                        Tile(
                            (last_x + px) * TILE_SIZE,
                            plat_height * TILE_SIZE,
                            PLATFORM_COLOR,
                        )
                    )

                # Kontynuujemy ziemię pod spodem lub nie
                self._create_column(last_x, current_height, ground_floor)
                last_x += 1

        # Ściana końcowa
        for y in range(0, 20):
            self.tiles.add(Tile(last_x * TILE_SIZE, y * TILE_SIZE, GRASS_COLOR))

        return self.tiles, self.spawn_point

    def _create_column(self, x, height_index, bottom_limit):
        """Pomocnicza funkcja tworząca pionowy słup terenu"""
        # Wierzch (trawa)
        self.tiles.add(Tile(x * TILE_SIZE, height_index * TILE_SIZE, GRASS_COLOR))

        # Ziemia poniżej aż do pewnej głębokości
        for y in range(height_index + 1, height_index + 5):
            self.tiles.add(Tile(x * TILE_SIZE, y * TILE_SIZE, GROUND_COLOR))


class Camera:
    """
    MODUŁ KAMERY
    Przesuwa świat względem gracza
    """

    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Wylicz przesunięcie: chcemy gracza na środku ekranu
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)

        # Ograniczenia kamery (żeby nie wyjeżdżała za bardzo w górę/dół jeśli chcesz)
        # Tutaj proste śledzenie
        self.camera = pygame.Rect(x, 0, self.width, self.height)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Procedural Platformer - Mario Style")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        self.running = True
        self.level_gen = LevelGenerator(level_length=300)  # Długość poziomu
        self.reset_game()

    def reset_game(self):
        # Generuj NOWY świat
        self.tiles, spawn_pos = self.level_gen.generate()
        self.player = Player(spawn_pos[0], spawn_pos[1])
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        # Tiles są w osobnej grupie, ale nie dodajemy ich do all_sprites dla wydajności rysowania (rysowanie tylko widocznych)

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Ręczny reset
                    self.reset_game()

    def update(self):
        self.all_sprites.update(self.tiles)
        self.camera.update(self.player)

        # Sprawdź czy gracz przegrał
        if not self.player.alive:
            # Opóźnienie lub natychmiastowy reset
            print("Game Over! Generowanie nowego poziomu...")
            self.reset_game()

    def draw(self):
        self.screen.fill(SKY_BLUE)

        # Rysuj tylko kafelki widoczne na ekranie (optymalizacja)
        for tile in self.tiles:
            # Prosta optymalizacja: jeśli kafelek jest w zasięgu kamery + margines
            shifted_rect = self.camera.apply(tile)
            if -TILE_SIZE < shifted_rect.x < SCREEN_WIDTH + TILE_SIZE:
                self.screen.blit(tile.image, shifted_rect)

        # Rysuj gracza
        self.screen.blit(self.player.image, self.camera.apply(self.player))

        # UI
        score_text = self.font.render(
            "Sterowanie: Strzałki + Spacja. 'R' - Reset mapy", True, BLACK
        )
        self.screen.blit(score_text, (10, 10))

        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()

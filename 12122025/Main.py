# Main.py - single-file Space Invaders variant (assets in Graphics/)
import os
import random
import pygame
import sys

# ---------- Config / Asset helpers ----------
ASSET_DIR = "Graphics"  # folder where your assets live

def asset_path(name):
    return os.path.join(ASSET_DIR, name)

def load_image_try(choices, convert_alpha=True):
    for name in choices:
        p = asset_path(name)
        if os.path.exists(p):
            try:
                img = pygame.image.load(p)
                return img.convert_alpha() if convert_alpha else img.convert()
            except Exception:
                continue
    return None

def load_sound_try(choices):
    for name in choices:
        p = asset_path(name)
        if os.path.exists(p):
            try:
                return pygame.mixer.Sound(p)
            except Exception:
                continue
    return None

# ---------- Pygame init ----------
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

SCREEN_W, SCREEN_H = 600, 700
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Space Invaders - Holly's Version")
clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 24)

# ---------- Events ----------
MYSTERYSHIP = pygame.USEREVENT + 1
ALIEN_FIRE_EVENT = pygame.USEREVENT + 2

# mystery ship interval (reset each spawn)
pygame.time.set_timer(MYSTERYSHIP, random.randint(4000, 8000))
# alien firing timer (aliens attempt to fire every 600ms)
pygame.time.set_timer(ALIEN_FIRE_EVENT, 600)

# ---------- Base Laser classes ----------
class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, speed, color=(243,216,63)):
        super().__init__()
        self.image = pygame.Surface((4, 15))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0 or self.rect.top > SCREEN_H:
            self.kill()

class AlienLaser(Laser):
    def __init__(self, pos, speed=5, color=(255, 100, 100)):
        super().__init__(pos, -speed, color)  # we will flip sign usage: override update
        # to use positive speed downwards, set speed_down
        self.speed_down = speed

    def update(self):
        self.rect.y += self.speed_down
        if self.rect.top > SCREEN_H:
            self.kill()

# ---------- Player spaceship ----------
class Spaceship(pygame.sprite.Sprite):
    def __init__(self, screen_w, screen_h, offset=10):
        super().__init__()
        self.offset = offset
        self.screen_w = screen_w
        self.screen_h = screen_h

        img = load_image_try(["spaceship.png", "spaceship.PNG", "ship.png", "player.png"])
        if img:
            self.image = img
        else:
            self.image = pygame.Surface((50, 24))
            self.image.fill((255, 225, 60))
        self.rect = self.image.get_rect(midbottom=((screen_w + offset)//2, screen_h - 18))

        self.speed = 6
        self.lasers = pygame.sprite.Group()
        self.laser_ready = True
        self.laser_time = 0
        self.laser_delay = 300
        self.laser_sound = load_sound_try(["laser.ogg", "laser.wav"])

    def get_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed

        if keys[pygame.K_SPACE] and self.laser_ready:
            self.fire()

    def fire(self):
        self.laser_ready = False
        self.laser_time = pygame.time.get_ticks()
        l = Laser(self.rect.midtop, 8, color=(243,216,63))
        self.lasers.add(l)
        if self.laser_sound:
            try:
                self.laser_sound.play()
            except Exception:
                pass

    def update(self):
        self.get_input()
        self.constrain()
        self.lasers.update()
        if not self.laser_ready:
            if pygame.time.get_ticks() - self.laser_time >= self.laser_delay:
                self.laser_ready = True

    def constrain(self):
        if self.rect.left < self.offset:
            self.rect.left = self.offset
        if self.rect.right > self.screen_w:
            self.rect.right = self.screen_w

    def reset(self):
        # move back to center
        self.rect.midbottom = ((self.screen_w + self.offset)//2, self.screen_h - 18)
        self.lasers.empty()
        self.laser_ready = True
        self.laser_time = 0

# ---------- Mystery Ship ----------
class MysteryShip(pygame.sprite.Sprite):
    def __init__(self, screen_w, y_offset=40, speed=-3):
        super().__init__()
        img = load_image_try(["mystery.png", "mysteryship.png", "mystery.PNG"])
        if img:
            self.image = img
        else:
            self.image = pygame.Surface((60, 28))
            self.image.fill((255, 200, 50))
        # start off right edge
        self.rect = self.image.get_rect(midleft=(screen_w + 40, y_offset))
        self.speed = speed
        self.screen_w = screen_w

    def update(self):
        self.rect.x += self.speed
        # if fully gone off left, remove
        if self.rect.right < -10 or self.rect.left > self.screen_w + 50:
            self.kill()

# ---------- Block / Obstacles (green shields) ----------
CELL_SIZE = 4
class Block(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill((0, 220, 0))   # Green bunkers
        self.rect = self.image.get_rect(topleft=(x, y))

# simple shield grid used to produce shield shapes (works like your original grid but scaled)

big_grid = [
[0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
[0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
[0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
[0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1],
[1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1]
]

class Shield:
    def __init__(self, x, y):
        self.blocks = pygame.sprite.Group()
        for r in range(len(big_grid)):
            for c in range(len(big_grid[0])):
                if big_grid[r][c] == 1:
                    bx = x + c * CELL_SIZE
                    by = y + r * CELL_SIZE
                    block = Block(bx, by)
                    self.blocks.add(block)

# ---------- Alien ----------
class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, color_name="green"):
        super().__init__()
        # choose image by color
        if color_name == "red":
            img = load_image_try(["red.png", "red.PNG"])
        elif color_name == "yellow":
            img = load_image_try(["yellow.png", "yellow.PNG"])
        else:
            img = load_image_try(["green.png", "green.PNG"])
        if img:
            self.image = img
        else:
            # fallback pixel-art rectangle
            surf = pygame.Surface((36, 28))
            surf.fill((200, 50, 50) if color_name == "red" else (200,200,50) if color_name=="yellow" else (50,200,50))
            self.image = surf
        self.rect = self.image.get_rect(topleft=(x, y))
        self.color_name = color_name

    def update(self):
        # In this simplified demo aliens are stationary horizontally (single row)
        pass

# ---------- Game wrapper ----------
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.screen_w = SCREEN_W
        self.screen_h = SCREEN_H

        # groups
        self.player = Spaceship(self.screen_w, self.screen_h, offset=10)
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.mystery_group = pygame.sprite.Group()
        self.alien_group = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        self.shields = []  # list of Shield instances
        self.all_shield_blocks = pygame.sprite.Group()

        self.score = 0
        self.spawn_aliens_row()
        self.create_shields()
        # sounds
        self.explosion_sound = load_sound_try(["explosion.ogg", "explosion.wav"])
        self.alien_laser_sound = load_sound_try(["laser.ogg", "laser.wav"])

        # background music if present
        music = asset_path("music.ogg")
        if os.path.exists(music):
            try:
                pygame.mixer.music.load(music)
                pygame.mixer.music.play(-1)
            except Exception:
                pass

    def spawn_aliens_row(self):
        # single row of aliens, colored red, green, yellow, repeating
        padding_left = 40
        spacing_x = 70
        y = 40
        colors = ["red","green","yellow"]
        for i in range(6):  # 6 aliens like screenshot
            color = colors[i % len(colors)]
            x = padding_left + i * spacing_x
            a = Alien(x, y, color)
            self.alien_group.add(a)

    def create_shields(self):
        # place four shields mid-bottom, above player
        shield_count = 4
        total_width = shield_count * (len(big_grid[0]) * CELL_SIZE) + (shield_count-1)*40
        start_x = (self.screen_w - total_width) // 2
        y = self.screen_h - 180  # mid-bottom area
        for i in range(shield_count):
            x = start_x + i * ((len(big_grid[0]) * CELL_SIZE) + 40)
            s = Shield(x, y)
            self.shields.append(s)
            self.all_shield_blocks.add(*s.blocks.sprites())

    def create_mystery(self):
        # spawn at top with a little vertical offset (40)
        ms = MysteryShip(self.screen_w, y_offset=30, speed=-3)
        self.mystery_group.add(ms)

    def alien_try_fire(self):
        # pick a random alien and fire downwards if exists
        if len(self.alien_group.sprites()) == 0:
            return
        shooter = random.choice(self.alien_group.sprites())
        # create laser from alien midbottom (downwards)
        pos = shooter.rect.midbottom
        laser = AlienLaser(pos, speed=5, color=(255,220,50))
        self.alien_lasers.add(laser)
        if self.alien_laser_sound:
            try:
                self.alien_laser_sound.play()
            except Exception:
                pass

    def handle_collisions(self):
        # Player lasers vs aliens
        for laser in self.player.lasers:
            hit_aliens = pygame.sprite.spritecollide(laser, self.alien_group, dokill=True)
            if hit_aliens:
                if self.explosion_sound:
                    try: self.explosion_sound.play()
                    except: pass
                laser.kill()
                self.score += 100 * len(hit_aliens)

            # also check mystery ship
            if pygame.sprite.spritecollide(laser, self.mystery_group, dokill=True):
                if self.explosion_sound:
                    try: self.explosion_sound.play()
                    except: pass
                laser.kill()
                self.score += 300

            # player laser vs shields
            hit_blocks = pygame.sprite.spritecollide(laser, self.all_shield_blocks, dokill=True)
            if hit_blocks:
                laser.kill()

        # Alien lasers vs shields
        for a_laser in self.alien_lasers:
            hit_blocks = pygame.sprite.spritecollide(a_laser, self.all_shield_blocks, dokill=True)
            if hit_blocks:
                a_laser.kill()
                if self.explosion_sound:
                    try: self.explosion_sound.play()
                    except: pass
                continue
            # alien laser vs player
            if pygame.sprite.spritecollide(a_laser, self.player_group, dokill=False):
                a_laser.kill()
                # simple effect: reset player position and clear player's lasers
                self.player.reset()
                if self.explosion_sound:
                    try: self.explosion_sound.play()
                    except: pass
                # optionally reduce score/lives; this demo just resets

        # Aliens vs shields collisions are not necessary in this single-row setup

    def update(self):
        self.player_group.update()
        self.mystery_group.update()
        self.alien_group.update()
        self.player.lasers.update()
        self.alien_lasers.update()
        self.handle_collisions()

    def draw(self):
        self.screen.fill((18, 10, 12))  # very dark background like screenshot

        # score
        score_surf = FONT.render(f"Score: {self.score}", True, (230,230,230))
        self.screen.blit(score_surf, (10, 8))

        # draw aliens (top)
        self.alien_group.draw(self.screen)

        # draw mystery
        self.mystery_group.draw(self.screen)

        # draw shields
        self.all_shield_blocks.draw(self.screen)

        # draw player and lasers
        self.player_group.draw(self.screen)
        self.player.lasers.draw(self.screen)

        # draw alien lasers
        self.alien_lasers.draw(self.screen)

    def run_frame(self):
        self.update()
        self.draw()

# ---------- Main loop ----------
game = Game(screen)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == MYSTERYSHIP:
            # only spawn if none currently and game running
            if len(game.mystery_group) == 0:
                game.create_mystery()
            # reset timer to random interval for next spawn
            pygame.time.set_timer(MYSTERYSHIP, random.randint(4000, 8000))

        if event.type == ALIEN_FIRE_EVENT:
            game.alien_try_fire()

        if event.type == pygame.KEYDOWN:
            # space is handled by player class; keep this for optional debug killing alien
            if event.key == pygame.K_k:
                # debug: remove a random alien
                if len(game.alien_group.sprites())>0:
                    random.choice(game.alien_group.sprites()).kill()

    # run frame and flip
    game.run_frame()
    pygame.display.flip()
    clock.tick(60)


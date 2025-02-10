import pygame
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("map", type=str, nargs="?", default="map1.map")  # Измените на нужную карту
args = parser.parse_args()
map_file = args.map
pygame.init()

clock = pygame.time.Clock()

# Увеличиваем размер экрана
screen_size = (1280, 720)  # Установливаем размеры экрана
screen = pygame.display.set_mode(screen_size)
FPS = 10

all_sprites = pygame.sprite.Group()


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


tile_images = {
    'wall': load_image('stena.png'),
    'empty': load_image('grass.png')
}


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, scale=1):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows, scale)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(topleft=(x, y))

    def cut_sheet(self, sheet, columns, rows, scale):
        original_width = sheet.get_width() // columns
        original_height = sheet.get_height() // rows

        for j in range(rows):
            for i in range(columns):
                frame_location = (original_width * i, original_height * j)
                frame = sheet.subsurface(pygame.Rect(frame_location, (original_width, original_height)))
                if scale != 1:
                    frame = pygame.transform.scale(frame, (int(original_width * scale), int(original_height * scale)))
                self.frames.append(frame)

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


class SpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()


class Sprite(pygame.sprite.Sprite):
    def __init__(self, group):
        super().__init__(group)
        self.rect = None


class Tile(Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(sprite_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Player(Sprite):
    def __init__(self, pos_x, pos_y):
        self.sprite_sheet = load_image("Pink_Monster_Walk_6.png")
        super().__init__(hero_group)
        self.animated_sprite = AnimatedSprite(self.sprite_sheet, 6, 1, 0, 0, scale=1.5)
        self.rect = self.animated_sprite.image.get_rect(topleft=(tile_width * pos_x, tile_height * pos_y))
        self.pos = (pos_x, pos_y)

    def update(self):
        self.animated_sprite.update()
        self.image = self.animated_sprite.image

    def move(self, x, y):
        self.pos = (x, y)
        self.rect.topleft = (tile_width * self.pos[0], tile_height * self.pos[1])


class Coin(Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(sprite_group)
        self.image = load_image('monetka.png')  # Текстура монетки
        self.rect = self.image.get_rect(topleft=(tile_width * pos_x, tile_height * pos_y))
        self.collected = False  # Флаг, указывающий, собрана ли монетка

    def collect(self):
        if not self.collected:
            self.image = tile_images['empty']  # Меняем текстуру на траву
            self.collected = True  # Отмечаем, что монетка собрана
            update_score()  # Обновляем счет


sprite_group = SpriteGroup()
hero_group = SpriteGroup()


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    intro_text = ["Rabbit Money"]
    fon = load_image('fon.jpg')
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 74)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


def load_level(filename):
    filename = os.path.join('data', filename)
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: list(x.ljust(max_width, '.')), level_map))


def generate_level(level):
    new_players = []
    global max_x, max_y
    max_y = len(level)
    max_x = len(level[0]) if max_y else 0

    for y in range(max_y):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_players.append(Player(x, y))
                level[y][x] = "."
            elif level[y][x] == '&':
                Coin(x, y)  # Генерация монетки
                level[y][x] = "."

    return new_players


def clear_level():
    sprite_group.empty()
    hero_group.empty()


def update_score():
    global score
    score += 1


def check_coin(hero):
    global score
    for coin in sprite_group:
        if isinstance(coin, Coin) and not coin.collected and hero.rect.colliderect(coin.rect):
            coin.collect()  # Собираем монетку
            break


def move(hero, movement):
    x, y = hero.pos
    if movement == "up":
        if y > 0 and level_map[y - 1][x] == ".":
            hero.move(x, y - 1)
            check_coin(hero)
    elif movement == "down":
        if y < max_y - 1 and level_map[y + 1][x] == ".":
            hero.move(x, y + 1)
            check_coin(hero)
    elif movement == "left":
        if x > 0 and level_map[y][x - 1] == ".":
            hero.move(x - 1, y)
            check_coin(hero)
    elif movement == "right":
        if x < max_x - 1 and level_map[y][x + 1] == ".":
            hero.move(x + 1, y)
            check_coin(hero)


def load_new_level(new_map_file):
    clear_level()
    global level_map
    level_map = load_level(new_map_file)
    return generate_level(level_map)


tile_width = tile_height = 50  # Размер тайлов
score = 0  # Счетчик очков


def main():
    k = 10
    maps = ["map1.map", "map2.map", "map3.map"]  # Убедитесь, что карты соответствуют размеру
    current_map_index = maps.index(map_file)

    start_screen()
    players = load_new_level(maps[current_map_index])

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Управление игроком 1
                if event.key == pygame.K_UP:
                    move(players[0], "up")
                elif event.key == pygame.K_DOWN:
                    move(players[0], "down")
                elif event.key == pygame.K_LEFT:
                    move(players[0], "left")
                elif event.key == pygame.K_RIGHT:
                    move(players[0], "right")

                # Управление игроком 2
                if len(players) > 1:
                    if event.key == pygame.K_w:
                        move(players[1], "up")
                    elif event.key == pygame.K_s:
                        move(players[1], "down")
                    elif event.key == pygame.K_a:
                        move(players[1], "left")
                    elif event.key == pygame.K_d:
                        move(players[1], "right")

                # Переключение карт
                if score == k:
                    current_map_index = (current_map_index + 1) % len(maps)
                    players = load_new_level(maps[current_map_index])
                    k += 10
                if score == 30:
                    pygame.quit()
                    exit()


        screen.fill(pygame.Color("black"))
        sprite_group.update()  # Обновление спрайтов для анимации
        hero_group.update()  # Обновление анимации игрока
        sprite_group.draw(screen)
        hero_group.draw(screen)

        # Отображаем счет
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {score}', True, pygame.Color('white'))
        screen.blit(score_text, (10, 10))  # Позиция на экране

        clock.tick(FPS)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
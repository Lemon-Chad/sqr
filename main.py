import pygame
import sys
import random

from bullets import FriendlyProjectile, EnemyProjectile
from player import Player
from objects import Ninja, Grunt, Heavy, Rico
import helper
import math

pygame.init()
mosaic = pygame.font.Font("assets/fonts/PaletteMosaic-Regular.ttf", 72)
maven = pygame.font.Font("assets/fonts/MavenPro-Bold.ttf", 72)
clock = pygame.time.Clock()
screen_width, screen_height = 1920, 1080
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.mouse.set_visible(False)

zoom = 1
decay_zoom = 0
shake = 0
decay_shake = 0
display = pygame.Surface((screen_width, screen_height))

NUMBER_KEYS = {
    pygame.K_0: 0,
    pygame.K_1: 1,
    pygame.K_2: 2,
    pygame.K_3: 3,
    pygame.K_4: 4,
    pygame.K_5: 5,
    pygame.K_6: 6,
    pygame.K_7: 7,
    pygame.K_8: 8,
    pygame.K_9: 9
}


def decay():
    global decay_zoom, decay_shake
    decay_zoom = max(0, decay_zoom - 0.01)
    decay_shake = max(0, decay_shake - 1)


def render(centerx=None, centery=None):
    if centerx is None:
        centerx = screen_width / 2
    if centery is None:
        centery = screen_height / 2
    real_zoom = decay_zoom + zoom
    real_shake = int(decay_shake + shake)
    screen.blit(pygame.transform.scale(display, (int(screen_width * real_zoom), int(screen_height * real_zoom))),
                (-int(centerx * (real_zoom - 1)) + random.randint(0, real_shake),
                 -int(centery * (real_zoom - 1)) + random.randint(0, real_shake)))


def bar(progress, fg, bg, x, y, width, height):
    helper.bar(screen, progress, fg, bg, x, y, width, height)


def center_bar(progress, fg, bg, stack):
    helper.center_bar(screen, progress, fg, bg, stack)


def arena():
    global decay_zoom, zoom, shake, decay_shake

    player = Player(screen_width / 2, screen_height / 2, 32, 100, 100, 3, 8)

    enemies = []
    enemy_timer = 0

    def new_enemy():
        typen = random.randint(0, 100)
        pos = random.randint(int(player.x - 600), int(player.x + 600)), \
            random.randint(int(player.y - 600), int(player.y + 600))
        if typen < 12:
            enemies.append(Ninja(*pos))
        elif typen < 35:
            enemies.append(Heavy(*pos))
        elif typen < 36:
            enemies.append(Rico(*pos))
        else:
            enemies.append(Grunt(*pos))

    objects = []
    bullets = []

    killstreak = 0
    last_kill_timer = 0
    score = 0
    kill_delay = 200

    while True:
        if killstreak:
            player.insanity = killstreak

        last_kill_timer -= 1
        if last_kill_timer < 0:
            killstreak = 0

        mx, my = pygame.mouse.get_pos()
        display.fill((30, 30, 30))
        helper.checkerboard(display, (player.x, player.y))
        # noinspection PyTypeChecker
        decay()
        attack_location = None

        enemy_timer -= random.randint(1, 5) * 0.66
        if enemy_timer <= 0:
            new_enemy()
            enemy_timer = random.randint(120, 150)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    attack_location = player.swipe()
            elif event.type == pygame.MOUSEMOTION:
                pygame.mouse.set_pos(helper.clamp(0, mx, screen_width), helper.clamp(0, my, screen_height))
                pygame.event.set_grab(True)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if player.phase():
                        decay_zoom = 0.25
                elif event.key == pygame.K_f:
                    player.blood_event(screen)
                elif event.key in NUMBER_KEYS:
                    player.equip(NUMBER_KEYS[event.key])
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

        keys = pygame.key.get_pressed()

        if pygame.mouse.get_pressed(3)[0]:
            s = player.shoot()
            bullets += s
            if s:
                if player.equipped == "shotgun":
                    decay_shake = 50
                elif player.equipped == "pistol":
                    decay_shake = 5

        if keys[pygame.K_LSHIFT]:
            player.run()
        else:
            player.walk()

        zoom = max(1, (player.speed - player.walks) / (player.runs - player.walks) / 6 + 1)
        mouse_pos = pygame.mouse.get_pos()
        player.set_angle(*mouse_pos)

        if keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_s] or keys[pygame.K_w]:
            player.moving = True
        else:
            player.moving = False
            player.speed = 0

        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

        if keys[pygame.K_a]:
            player.xv = -player.speed
        elif keys[pygame.K_d]:
            player.xv = player.speed
        else:
            player.xv = 0
        if keys[pygame.K_s]:
            player.yv = player.speed
        elif keys[pygame.K_w]:
            player.yv = -player.speed
        else:
            player.yv = 0

        for obj in objects:
            obj.main(display, player)

        final = []
        for enemy in enemies.copy():
            if attack_location:
                if helper.segment_to_point(*attack_location, player.x, player.y, enemy.x, enemy.y) < 75:
                    decay_shake = 15
                    enemy.damage(30)
                    if player.siphon:
                        player.hp = min(player.mhp, player.hp + 5)
            if enemy.hp <= 0:
                enemies.remove(enemy)
                killstreak += 1
                last_kill_timer = kill_delay
                decay_shake += killstreak
                score += enemy.score * 100 + random.randint(0, 99)
                player.blood_meter = min(player.blood_meter + enemy.score ** (0.5 if player.active_blood else 1),
                                         player.blood_max)
                continue
            move_change_x, move_change_y, enemy_bullets = enemy.main(display, player)
            bullets += enemy_bullets
            enemy.dodge(bullets)
            total_change = move_change_x, move_change_y
            if helper.dist(enemy.x, enemy.y, player.x, player.y) < enemy.s:
                player.damage(enemy.dmg)
                evade_direction = math.radians(random.randint(0, 360))

                evade_x = math.cos(evade_direction) * enemy.speed * 4
                evade_y = math.sin(evade_direction) * enemy.speed * 4

                enemy.dcxv += evade_x
                enemy.dcyv += evade_y

            tolerance = 16
            for target in final:
                if enemy == target: continue
                if helper.dist(target.x, target.y, enemy.x, enemy.y) < tolerance:
                    if (target.x == enemy.x and target.y == enemy.y) or (total_change[0] == 0 and total_change[1] == 0):
                        enemy.x -= target.s
                        enemy.y -= target.s
                    else:
                        enemy.x -= total_change[0]
                        enemy.y -= total_change[1]
                    break
            enemy.draw(display, player)
            final.append(enemy)

        for bullet in bullets.copy():
            bullet.main(display, player)

            if type(bullet) == FriendlyProjectile:
                for enemy in enemies.copy():
                    if helper.dist(enemy.x + enemy.s / 2, enemy.y + enemy.s / 2, bullet.x, bullet.y) < enemy.s * 0.9:
                        bullet.xv *= 1 - enemy.s / 150
                        bullet.yv *= 1 - enemy.s / 150
                        enemy.damage(bullet.damage)
                        if player.siphon:
                            player.hp = min(player.mhp, player.hp + 0.3)
                        break
            elif type(bullet) == EnemyProjectile:
                if helper.dist(player.x + player.width / 2, player.y + player.height / 2, bullet.x, bullet.y) < \
                        math.sqrt(player.width ** 2 + player.height ** 2):
                    bullets.remove(bullet)
                    player.damage(bullet.damage)
                    break

            if bullet not in bullets:
                continue
            if helper.dist(player.x, player.y, bullet.x, bullet.y) > 1500 or bullet.speed() < 1:
                bullets.remove(bullet)

        player.main(display)

        if player.active_blood:
            tint = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA).convert_alpha()
            tint.fill((255, 0, 0, player.blood_meter / player.blood_max * 100))
            display.blit(tint, (0, 0))

        render(player.rx, player.ry)

        center_bar(player.stamina / player.max_stamina, (255, 255, 255), (50, 50, 50), 1)
        center_bar(player.hp / player.mhp, (255 * (player.mhp - player.hp) / player.mhp,
                                            255 * player.hp / player.mhp, 0),
                   (80 * (player.mhp - player.hp) / player.mhp,
                    80 * player.hp / player.mhp, 0), 2)
        center_bar(player.blood_meter / player.blood_max, (255, 0, 0), (75, 50, 50), 3)

        screen.blit(mosaic.render(f"Score: {score}", True, (255, 255, 255)), (16, 0))

        bar(last_kill_timer / kill_delay, (255, 255, 255), (50, 50, 50), 16, 168, 200, 8)
        screen.blit(mosaic.render(f"x{killstreak}", True, (255, 255, 255)), (16, 72))

        if player.hp <= 0:
            tint = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA).convert_alpha()
            tint.fill((0, 0, 0, 100))
            screen.blit(tint, (0, 0))

            t = mosaic.render("GAME OVER", True, (255, 255, 255))
            screen.blit(t, (screen_width / 2 - t.get_width() / 2, screen_height / 2 - 144))
            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                        else:
                            waiting = False
                            break
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        waiting = False
            break

        clock.tick(60)
        pygame.display.flip()


def menu():
    fonts144 = [
        pygame.font.Font(f"assets/fonts/{x}.ttf", 144)
        for x in ("Jo_wrote_a_lovesong", "MavenPro-Bold", "Monofett-Regular", "PaletteMosaic-Regular")
    ]
    fonts72 = [
        pygame.font.Font(f"assets/fonts/{x}.ttf", 72)
        for x in ("Jo_wrote_a_lovesong", "MavenPro-Bold", "Monofett-Regular", "PaletteMosaic-Regular")
    ]

    options = ["start", "quit"]
    index = 0
    font144 = random.choice(fonts144)
    font72 = random.choice(fonts72)
    fonttimer = 10
    while True:
        fonttimer -= 1
        if fonttimer < 0:
            newfont144 = font144
            while newfont144 == font144:
                newfont144 = random.choice(fonts144)
            newfont72 = font72
            while newfont72 == font72:
                newfont72 = random.choice(fonts72)
            font72, font144 = newfont72, newfont144
            fonttimer = 10
        helper.checkerboard(display, (screen_width / 2, screen_height / 2))
        render()
        title = font144.render("SQR", False, (255, 255, 255))
        screen.blit(title, (screen_width / 2 - title.get_width() / 2, 16))

        for i in range(len(options)):
            option = font72.render(options[i].upper(), False,
                                                   (255, 255, 0) if i == index else (255, 255, 255))
            screen.blit(option, (screen_width / 2 - option.get_width() / 2, 256 + 72 * i))

        done = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_w or event.key == pygame.K_UP:
                    index = min(0, index - 1)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    index = max(len(options) - 1, index + 1)
                elif event.key == pygame.K_RETURN:
                    done = True
                    break
        if done: break

        clock.tick(60)
        pygame.display.flip()
    selection = options[index]
    if selection == "quit":
        pygame.quit()
        sys.exit()
    elif selection == "start":
        return


if __name__ == "__main__":
    while True:
        menu()
        arena()

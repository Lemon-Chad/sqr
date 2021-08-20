import pygame
import math
import random
import helper
from bullets import FriendlyProjectile
import sys

pygame.mixer.init()
items = {
    k: {
        "sprite": pygame.transform.scale(pygame.image.load(f"assets/items/{k}.png"), (48, 48)),
        "equip": pygame.mixer.Sound(f"assets/sounds/{k}_equip.mp3"),
        "fire": pygame.mixer.Sound(f"assets/sounds/{k}_fire.mp3")
    }
    for k in ["pistol", "shotgun", "sniper"]
}
SPREAD = int(math.pi / 4 * 100)


class Player:
    def __init__(self, x, y, s, hp, stam, walk_speed, run_speed):
        self.speed_multi = 1
        self.damage_multi = 1
        self.cooldown_multi = 1
        self.stamina_multi = 1

        self.blood_meter = 0
        self.blood_max = 100
        self.active_blood = False
        self.siphon = False

        self.x = x
        # Render X
        self.rx = x - s / 2
        # X Velocity
        self.xv = 0
        # Decaying X Velocity
        self.dcxv = 0

        self.angle = 0
        self.angle2 = 0

        self.inventory = [None, "pistol", "shotgun", "sniper"]
        self.equipped = "pistol"

        self.moving = False
        self.left = False
        self.up = False

        self.y = y
        # Render Y
        self.ry = y - s / 2
        # Y Velocity
        self.yv = 0
        # Decaying Y Velocity
        self.dcyv = 0

        self.default_left_hand_pos = self.x - 12, self.ry + 27
        self.default_right_hand_pos = self.x + 12, self.ry + 27

        self.left_hand_pos = self.default_left_hand_pos
        self.right_hand_pos = self.default_right_hand_pos

        self.width = s
        self.height = s

        self.recoil = 0
        self.cooldowns = {
            k: 0
            for k in self.inventory
            if k
        }

        self.insanity = 100

        self.hp = hp
        self.mhp = hp
        self.iframes = 0

        self.stamina = stam
        self.max_stamina = stam

        self.walks = walk_speed
        self.runs = run_speed
        self.speed = 0

        self.running = False
        self.friction = 1

    def draw_shadow(self, color, opacity, i, display):
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((color[0], color[1], color[2], opacity))
        display.blit(s, (self.width * i, 0))

    def draw_shadows(self, display, color, xs, ys):
        shadow_opacity = (self.speed - self.walks + math.sqrt(self.dcxv ** 2 + self.dcyv ** 2)) / \
                         (self.runs - self.walks) / 4
        shadow_surface = pygame.Surface((self.width * 4, self.height), pygame.SRCALPHA).convert_alpha()
        shadow_surface.fill((0, 0, 0, 0))

        pygame.draw.polygon(shadow_surface,
                            (color[0], color[1], color[2], helper.clamp(0, int(shadow_opacity * 4 / 3 * 255), 255)),
                            [(self.width * 4, self.height / 2),
                             (self.width * 3, self.height + 10),
                             (self.width * 3, -10)])

        for i in range(1, 4):
            self.draw_shadow(color, helper.clamp(0, int(shadow_opacity * i / 3 * 255), 255), i - 1, shadow_surface)

        angle = math.degrees(math.atan2(ys, xs))
        pivot = [self.rx + self.width / 2, self.ry + self.height / 2]
        offset = pygame.math.Vector2(-self.width * 3 / 2, 0)
        display.blit(*helper.offset_rotation(shadow_surface, angle, pivot, offset))

    def equip(self, index):
        if index < 0 or index >= len(self.inventory):
            self.equipped = None
        else:
            self.equipped = self.inventory[index]
            pygame.mixer.Sound.play(items[self.equipped]["equip"])

    def main(self, display):
        self.iframes -= 1
        self.recoil = max(0, self.recoil - 1 * self.cooldown_multi)
        self.cooldowns = {k: max(0, c - 1 * self.cooldown_multi) for k, c in self.cooldowns.items()}
        self.insanity = max(0, self.insanity - 0.5)

        if self.active_blood:
            self.blood_meter = max(0, self.blood_meter - 0.1)
            if self.blood_meter == 0:
                self.active_blood = False
                self.speed_multi = 1
                self.damage_multi = 1
                self.cooldown_multi = 1
                self.siphon = False
                self.stamina_multi = 1

        if not self.running or not self.moving:
            self.stamina = min(self.stamina + 1 * self.stamina_multi, self.max_stamina * self.stamina_multi)

        self.dcxv = max(0, abs(self.dcxv) - self.friction) * (abs(self.dcxv) / self.dcxv if self.dcxv else 1)
        self.dcyv = max(0, abs(self.dcyv) - self.friction) * (abs(self.dcyv) / self.dcyv if self.dcyv else 1)

        self.xv *= self.speed_multi
        self.yv *= self.speed_multi

        xs = self.xv + self.dcxv
        ys = self.yv + self.dcyv
        self.x += xs
        self.y += ys

        color = (int(255 * (self.mhp - self.hp) / self.mhp), int(255 * self.hp / self.mhp), 0)
        if self.iframes > 0 and self.iframes % 10 > 5:
            color = (255, 255, 255)
        self.draw_shadows(display, color, xs, ys)
        self.draw(display)

        self.left_hand_pos = helper.move_towards(self.left_hand_pos, self.default_left_hand_pos)
        self.right_hand_pos = helper.move_towards(self.right_hand_pos, self.default_right_hand_pos)

        pygame.draw.circle(display, (255, 255, 255), self.angle_pos(), 2)

    def draw(self, display):
        color = (int(255 * (self.mhp - self.hp) / self.mhp), int(255 * self.hp / self.mhp), 0)
        if self.iframes > 0 and self.iframes % 10 > 5:
            color = (255, 255, 255)
        pygame.draw.rect(display, color, (self.rx, self.ry, self.width, self.height))

        pygame.draw.rect(display, tuple(int(0.8 * x) for x in color),
                         (self.left_hand_pos[0] - 8 + random.randint(0, 10 + int(self.insanity)) / 8,
                          self.left_hand_pos[1] - 8 + random.randint(0, 10 + int(self.insanity)) / 8, 16, 16))

        recoil_factor = 1 if -math.pi / 2 < self.angle < math.pi / 2 else -1
        if self.equipped is None:
            pygame.draw.rect(display, tuple(int(0.8 * x) for x in color),
                             (self.right_hand_pos[0] - 8 + random.randint(0, 10 + int(self.insanity)) / 8,
                              self.right_hand_pos[1] - 8 + random.randint(0, 10 + int(self.insanity)) / 8, 16, 16))
        else:
            hand = pygame.Surface((48, 48), pygame.SRCALPHA).convert_alpha()
            hand.fill((255, 0, 0, 0))
            hand.blit(items[self.equipped]["sprite"], (0, 0))

            pos = (self.right_hand_pos[0] - 8 + random.randint(0, 10 + int(self.insanity)) / 8,
                   self.right_hand_pos[1] - 24 + random.randint(0, 10 + int(self.insanity)) / 8)

            mx, my = pygame.mouse.get_pos()
            angle = math.degrees(math.atan2(pos[1] - my, mx - pos[0])) + self.recoil * recoil_factor

            if recoil_factor == 1:
                rotated_item = pygame.transform.rotate(hand, angle)
            else:
                rotated_item = pygame.transform.rotate(pygame.transform.flip(hand, False, True), angle)

            display.blit(rotated_item,
                         (pos[0] - (rotated_item.get_width() - 48),
                          pos[1] - (rotated_item.get_height() - 48)))

    def run(self):
        if not self.moving:
            return

        if self.stamina > 45 or (self.running and self.stamina > 5):
            self.stamina = max(self.stamina - 0.015, 0)
            self.running = True
            self.speed = min(self.speed + 0.1, self.runs)
        else:
            self.walk()

    def angle_pos(self, x=None, y=None):
        if x is None:
            x = self.rx
        if y is None:
            y = self.ry

        recoil_factor = 1 if -math.pi / 2 < self.angle < math.pi / 2 else -1
        bloom = math.radians(random.randint(-int(self.insanity / 3), int(self.insanity / 3)))
        return x + self.width / 2 + math.cos(self.angle + bloom - math.radians(self.recoil) * recoil_factor) * 50, \
            y + self.height / 2 + math.sin(self.angle + bloom - math.radians(self.recoil) * recoil_factor) * 50

    def phase(self):
        if self.stamina > 10:
            self.stamina -= 10
            self.iframes = 20

            self.dcxv = self.xv * 3
            self.dcyv = self.yv * 3

            return True
        return False

    def walk(self):
        self.running = False

        if not self.moving:
            self.speed = max(0.0, self.speed - 0.1)
            return

        if self.speed > self.walks:
            self.speed = max(self.speed - 0.5, self.walks)
        else:
            self.speed = min(self.speed + 0.1, self.walks)

    def set_angle(self, mx, my):
        self.angle = math.atan2(my - self.ry - self.height / 2, mx - self.rx - self.width / 2)
        self.angle2 = math.atan2(self.ry - my - self.height / 2, mx - self.rx - self.width / 2)

    def swipe(self):
        if self.stamina > 10:
            self.stamina -= 10
            p = self.angle_pos()
            if random.randint(0, 1) == 1:
                self.left_hand_pos = p
            else:
                self.right_hand_pos = p
            return self.x + p[0] - self.rx, self.y + p[1] - self.ry
        return None

    def damage(self, amt):
        if self.iframes > 0:
            return
        self.hp = max(self.hp - amt, 0)
        self.iframes = 30

    def make_projectile(self, precoil, recoil_factor, damage, speed=5, x_off=0, y_off=0, xv_off=0, yv_off=0):
        bloom = math.radians(random.randint(-int(self.insanity / 3), int(self.insanity / 3)))
        return FriendlyProjectile(self.x + self.width / 2 + x_off, self.y + self.height / 2 + y_off,
                                  math.cos(self.angle + bloom - math.radians(precoil) * recoil_factor) * speed
                                  + self.xv + xv_off,
                                  math.sin(self.angle + bloom - math.radians(precoil) * recoil_factor) * speed
                                  + self.yv + yv_off,
                                  damage * self.damage_multi)

    def shoot(self):
        if self.equipped and self.cooldowns[self.equipped] > 0:
            return []

        precoil = self.recoil
        recoil_factor = 1 if -math.pi / 2 < self.angle < math.pi / 2 else -1

        if self.equipped is not None:
            pygame.mixer.Sound.play(items[self.equipped]["fire"])

        if self.equipped == "pistol":
            self.recoil += 15
            self.cooldowns["pistol"] = 15
            return [self.make_projectile(precoil, recoil_factor, 5, 15)]
        elif self.equipped == "shotgun":
            self.recoil += 45
            self.cooldowns["shotgun"] = 60

            procs = []
            for _ in range(10):
                randangle = self.angle + random.randint(-SPREAD, SPREAD) / 100
                intensity = random.randint(5, 15)
                procs.append(self.make_projectile(precoil, recoil_factor, 3, 7,
                                                  xv_off=math.cos(randangle) * intensity,
                                                  yv_off=math.sin(randangle) * intensity))

            self.dcxv = math.cos(self.angle + math.pi) * 30
            self.dcyv = math.sin(self.angle + math.pi) * 30
            return procs
        elif self.equipped == "sniper":
            self.recoil += 80
            self.cooldowns["sniper"] = 80

            self.dcxv = math.cos(self.angle + math.pi) * 30
            self.dcyv = math.sin(self.angle + math.pi) * 30

            procs = []
            for _ in range(3):
                randangle = self.angle + random.randint(-SPREAD, SPREAD) / 100
                intensity = random.randint(1, 5)
                procs.append(self.make_projectile(precoil, recoil_factor, 50, 60,
                                                  xv_off=math.cos(randangle) * intensity,
                                                  yv_off=math.sin(randangle) * intensity))

            return procs
        return []

    def blood_event(self, screen):
        if self.blood_meter < self.blood_max:
            return
        self.insanity += 50
        clock = pygame.time.Clock()
        maven = pygame.font.Font("assets/fonts/PaletteMosaic-Regular.ttf", 96)
        options = ["rampage", "siphon", "speed demon"]
        index = 0
        sw = screen.get_width()
        while True:
            screen.fill((25, 25, 25))
            helper.checkerboard(screen, (self.x, self.y))
            for i in range(len(options)):
                text = options[i].upper()
                if i == index:
                    text += " <"
                rend = maven.render(text, False, (255, 255, 255))
                width = rend.get_width()
                screen.blit(rend, (sw / 2 - width / 2, 144 * i))
            self.draw(screen)

            done = False
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        index = max(0, index - 1)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        index = min(len(options) - 1, index + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        done = True
                        break
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            if done:
                break

            clock.tick(60)
            pygame.display.flip()
        self.active_blood = True

        selection = options[index]
        if selection == "rampage":
            self.cooldown_multi = 2
            self.damage_multi = 2
            self.speed_multi = 2
        elif selection == "siphon":
            self.siphon = True
        elif selection == "speed demon":
            self.speed_multi = 2
            self.stamina_multi = 3

import pygame
import helper
import math
import random

from bullets import EnemyProjectile


class Block:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def screenspace(self, player) -> tuple[int, int]:
        return int(self.x - player.x + player.rx), int(self.y - player.y + player.ry)

    def main(self, display, player):
        pass


class Square(Block):
    s: int

    def __init__(self, x, y, s, color):
        super().__init__(x - s / 2, y - s / 2)
        self.s = int(s)
        self.color = color

    def main(self, display, player):
        x, y = self.screenspace(player)
        pygame.draw.rect(display, self.color, (x, y, self.s, self.s))


class Enemy(Square):
    def __init__(self, x, y, s, hp, damage, speed, color=(255, 0, 0)):
        super().__init__(x, y, s, color)
        self.dcolor = color
        self.hit = 0
        self.speed = speed
        self.hp = hp
        self.mhp = hp
        self.blood = hp * 2
        self.score = 1
        self.dmg = damage
        self.dcxv = 0
        self.dcyv = 0
        self.friction = 1
        self.flash = 0
        self.stagger = 0

    def main(self, display, player):
        self.stagger -= 1
        if helper.dist(self.x, self.y, player.x, player.y) < 2:
            player.damage(self.dmg)

        if self.flash > 0:
            self.color = (255, 255, 255)
        else:
            self.color = self.dcolor
        self.flash -= 1

        self.dcxv = max(0, abs(self.dcxv) - self.friction) * (abs(self.dcxv) / self.dcxv if self.dcxv else 1)
        self.dcyv = max(0, abs(self.dcyv) - self.friction) * (abs(self.dcyv) / self.dcyv if self.dcyv else 1)

        return self.chase(player)

    def chase(self, player):
        return 0, 0, []

    def dodge(self, bullets):
        pass

    def draw(self, display, player):
        super().main(display, player)

    def damage(self, amt):
        self.hp -= amt
        self.flash = 5


class Grunt(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 15, 3, 4, (255, 0, 0))

    def chase(self, player):
        if self.stagger > 0:
            return 0, 0, []
        angle = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(angle) * self.speed + self.dcxv
        self.y += math.sin(angle) * self.speed + self.dcyv
        return math.cos(angle) * self.speed, math.sin(angle) * self.speed, []


class Ninja(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 1, 8, 4, (50, 30, 30))
        self.dodge_cooldown = 0
        self.score = 25

    def chase(self, player):
        angle = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(angle) * self.speed + self.dcxv
        self.y += math.sin(angle) * self.speed + self.dcyv
        return math.cos(angle) * self.speed, math.sin(angle) * self.speed, []

    def dodge(self, bullets):
        change = 0, 0
        self.dodge_cooldown -= 1
        if self.dodge_cooldown > 0:
            return change

        for bullet in bullets:
            future = bullet.x + bullet.xv * 6, bullet.y + bullet.yv * 6
            if helper.segment_to_point(bullet.x, bullet.y, *future, self.x, self.y) < 64:
                self.dodge_cooldown = 45
                bullet_angle = math.atan2(bullet.y - self.y, bullet.x - self.x)
                evade_angle = bullet_angle + math.pi + random.randint(0, 1) * 2 - 1
                change = math.cos(evade_angle) * self.speed * 4, math.sin(evade_angle) * self.speed * 4
                self.dcxv += int(change[0])
                self.dcyv += int(change[1])
                break

        return change


class Heavy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 48, 60, 1, 3, (255, 122, 0))
        self.fire_cooldown = 0
        self.shot_timer = 0
        self.shots_left = 0
        self.score = 5

    def chase(self, player):
        if self.stagger > 0:
            return 0, 0, []
        self.fire_cooldown -= 1
        self.shot_timer -= 1

        if self.fire_cooldown <= 0:
            self.shots_left = 4
            self.fire_cooldown = 250

        direction = -1 if helper.dist(player.x, player.y, self.x, self.y) <= 400 else 1
        angle = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(angle) * self.speed * direction + self.dcxv
        self.y += math.sin(angle) * self.speed * direction + self.dcyv

        proj = []
        if self.shots_left > 0 and self.shot_timer <= 0:
            self.shots_left -= 1
            self.shot_timer = 30
            proj.append(EnemyProjectile(self.x + self.s / 2, self.y + self.s / 2,
                                        math.cos(angle) * 10, math.sin(angle) * 10,
                                        3))

        return math.cos(angle) * self.speed * direction, math.sin(angle) * self.speed * direction, proj


class Rico(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 250, 2500, 1, 2, (255, 0, 96))
        self.shot_timer = 0
        self.score = 500
        self.maxhp = 2500

    def main(self, display, player):
        helper.bar(display, self.hp / self.maxhp, (255, 255, 255), (50, 50, 50),
                   display.get_width() / 2 - 384, 48, 768, 32)
        return super().main(display, player)

    def chase(self, player):
        self.shot_timer -= 1
        angle = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(angle) * self.speed + self.dcxv
        self.y += math.sin(angle) * self.speed + self.dcyv

        proj = []
        if self.shot_timer <= 0:
            self.shot_timer = 15
            proj.append(EnemyProjectile(self.x + self.s / 2, self.y + self.s / 2,
                                        math.cos(angle) * 10, math.sin(angle) * 10,
                                        5))

        return math.cos(angle) * self.speed, math.sin(angle) * self.speed, proj

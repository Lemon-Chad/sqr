import pygame
import math


class Projectile:
    def __init__(self, x, y, xv, yv, s, color):
        self.color = color
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.s = s
        self.damage = 0

    def screenspace(self, player) -> tuple[int, int]:
        return int(self.x - player.x + player.rx), int(self.y - player.y + player.ry)

    def main(self, display, player):
        self.x += self.xv
        self.y += self.yv
        x, y = self.screenspace(player)
        pygame.draw.circle(display, self.color, (x, y), self.s)

    def speed(self):
        return math.sqrt(self.xv ** 2 + self.yv ** 2)


class FriendlyProjectile(Projectile):
    def __init__(self, x, y, xv, yv, dmg):
        super().__init__(x, y, xv, yv, 5, (255, 255, 255))
        self.damage = dmg


class EnemyProjectile(Projectile):
    def __init__(self, x, y, xv, yv, dmg):
        super().__init__(x, y, xv, yv, 10, (255, 122, 122))
        self.damage = dmg

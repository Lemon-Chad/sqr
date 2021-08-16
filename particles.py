import pygame
import helper


class Particle:
    def __init__(self, color, x, y, xv, yv, size, friction=0, decay=60):
        self.color = color
        self.s = size
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.friction = friction
        self.decay = decay
        self.life = 0

    def screenspace(self, player) -> tuple[int, int]:
        return int(self.x - player.x + player.rx), int(self.y - player.y + player.ry)

    def main(self, display, player):
        surf = pygame.Surface((self.s * 2, self.s * 2)).convert_alpha()
        surf.fill((0, 0, 0, 0))

        alpha = (1 - helper.clamp(0, (self.life - self.decay) / self.decay, 1)) * 255
        pygame.draw.circle(surf, list(self.color) + [alpha], (self.s, self.s), self.s)

        x, y = self.screenspace(player)
        display.blit(surf, (x, y))

        self.x += self.xv
        self.y += self.yv

        self.xv, self.yv = helper.move_towards((self.xv, self.yv), (0, 0), self.friction)

        self.life += 1
        if self.life >= self.decay * 2:
            return True
        return False

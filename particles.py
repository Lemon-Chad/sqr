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


class DamageNumber:
    def __init__(self, value, font, x, y, enemy):
        self.value = max(0, value)
        self.font: pygame.font.Font = font
        self.lifespan = 0
        self.x = x
        self.y = y
        self.decay = 15
        self.color = (
            255,
            max(0, 255 * (200 - value) / 200),
            max(0, 255 * (100 - value) / 100)
        )
        self.enemy = enemy

    def stack(self, v):
        self.value = max(0, self.value + v)
        self.color = (
            255,
            max(0, 255 * (200 - self.value) / 200),
            max(0, 255 * (100 - self.value) / 100)
        )
        self.lifespan = max(0, self.lifespan - 15)

    def screenspace(self, player) -> tuple[int, int]:
        return int(self.x - player.x + player.rx), int(self.y - player.y + player.ry)

    def main(self, display, player):
        alpha = (1 - helper.clamp(0, (self.lifespan - self.decay) / self.decay, 1)) * 255

        t = self.font.render(str(self.value), True, self.color)

        surf = pygame.Surface(t.get_size(), pygame.SRCALPHA)
        surf.fill((255, 255, 255, alpha))

        t.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        display.blit(t, self.screenspace(player))

        self.y -= 1

        self.lifespan += 1

        if self.lifespan > self.decay * 2:
            if self.enemy.dmgnum == self:
                self.enemy.dmgnum = None
            return True


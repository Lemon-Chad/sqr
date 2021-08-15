import math
import pygame


def dist(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def clamp(end, value, start):
    return max(end, min(start, value))


def move_towards(a, b, roc=1):
    new = []
    for i in range(2):
        if a[i] == b[i]:
            new.append(a[i])
        elif a[i] < b[i]:
            new.append(min(a[i] + roc, b[i]))
        elif a[i] > b[i]:
            new.append(max(a[i] - roc, b[i]))
    return tuple(new)


def offset_rotation(surf, angle, pivot, offset):
    offset = offset.rotate(angle)
    rotate = pygame.transform.rotate(surf, -angle)
    rect = rotate.get_rect(center=(pivot[0] + offset.x, pivot[1] + offset.y))
    return rotate, rect


def segment_to_point(x1, y1, x2, y2, x3, y3):
    px = x2-x1
    py = y2-y1

    norm = px*px + py*py

    u = ((x3 - x1) * px + (y3 - y1) * py) / float(norm)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    dst = (dx*dx + dy*dy)**.5

    return dst


def nearest_point(t, u, m, b):
    x = (-b * m + m * u + t) / (m ** 2 + 1)
    y = m * x + b
    return x, y


def line_to_point(t, u, m, b):
    return dist(t, u, *nearest_point(t, u, m, b))


def checkerboard(display, origin, size=64):
    ox, oy = origin[0] % (size * 2), origin[1] % (size * 2)
    for i in range(-3, display.get_width() // size + 3):
        for j in range(-3, display.get_height() // size + 3):
            color = (30, 30, 30) if (i + j) % 2 else (20, 20, 20)
            pygame.draw.rect(display, color, (i * size - ox, j * size - oy, size, size))


def bar(screen, progress, fg, bg, x, y, width, height):
    pygame.draw.rect(screen, bg, (x, y, width, height))
    pygame.draw.rect(screen, fg, (x, y, width * progress, height))


def center_bar(screen, progress, fg, bg, stack):
    bar(screen, progress, fg, bg, screen.get_width() / 2 - 384, screen.get_height() - 48 * stack, 768, 32)


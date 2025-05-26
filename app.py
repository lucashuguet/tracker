#!/usr/bin/env python3

import pygame
import time
import cv2
import sys
import csv

CIRCLE_RADIUS = 2

video = cv2.VideoCapture(sys.argv[1])
success, frame = video.read()
fps = video.get(cv2.CAP_PROP_FPS)

w, h = 1920, 1080
window = pygame.display.set_mode((w, h), pygame.RESIZABLE)
clock = pygame.time.Clock()

width, height = frame.shape[1::-1]
ratio = width / height

offsetx, offsety = 0, 0
moving = False
next_frame = False
fixed_mousex, fixed_mousey = 0, 0

scale = 1.0
last_scale = None
new = True

image = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
scaled = image

points = [[None, None]] # tracked, origin

def draw_circle_alpha(surface, color, center, radius):
    target_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)

run = success
while run:
    nw, nh = pygame.display.get_surface().get_size()
    if nw != w or nh != h:
        w, h = nw, nh

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                next_frame = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                next_frame = True

            if event.key == pygame.K_BACKSPACE:
                offsetx, offsety = 0, 0
                scale = 1.0
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: # scroll up
                scale = min(scale * 1.1, 10.0)
            elif event.button == 5: # scroll down
                scale = max(scale * 0.9, 0.1)
            elif event.button == 1 or event.button == 3: # left click / right click
                mousex, mousey = pygame.mouse.get_pos()

                if not 0 <= mousex - x - offsetx <= scaled.get_width():
                    continue
                if not 0 <= mousey - y - offsety <= scaled.get_height():
                    continue

                relativex = (mousex - x - offsetx) * width / scaled.get_width()
                relativey = (mousey - y - offsety) * height / scaled.get_height()
                points[-1][event.button // 2] = (int(relativex), int(relativey)) # tracked -> left click / origin -> right click
            elif event.button == 2:
                moving = True
                mousex, mousey = pygame.mouse.get_pos()
                fixed_mousex = mousex - offsetx
                fixed_mousey = mousey - offsety
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                moving = False

    if next_frame:
        if not points[-1][0] and points[-1][1]: # if an origin is set, expect a tracked point
            continue

        success, frame = video.read()
        image = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
        new = True

        points.append([None, points[-1][1]])

    if not success:
        run = False

    if last_scale != scale or new:
        scaled = pygame.transform.scale(image, (ratio * h * scale, h * scale))
        last_scale = scale
        new = False

    if moving:
        mousex, mousey = pygame.mouse.get_pos()
        offsetx = mousex - fixed_mousex
        offsety = mousey - fixed_mousey

    x = int((w - scaled.get_width()) / 2)
    y = int((h - scaled.get_height()) / 2)

    window.fill((0, 0, 0))
    window.blit(scaled, (x + offsetx, y + offsety))

    opacity = 10;
    for tracked, origin in reversed(points):
        if opacity == 0:
            break

        if origin:
            realx = int(scaled.get_width() / width * origin[0]) + x + offsetx
            realy = int(scaled.get_height() / height * origin[1]) + y + offsety
            draw_circle_alpha(window, (0, 255, 0, int(opacity / 10 * 255)), (realx, realy), CIRCLE_RADIUS * scale)
        if tracked:
            realx = int(scaled.get_width() / width * tracked[0]) + x + offsetx
            realy = int(scaled.get_height() / height * tracked[1]) + y + offsety
            draw_circle_alpha(window, (255, 0, 0, int(opacity / 10 * 255)), (realx, realy), CIRCLE_RADIUS * scale)
        opacity -= 2

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()

data = []

t = 0
for tracked, origin in points:
    if not origin:
        continue

    try:
        data.append([t, tracked[0] - origin[0], tracked[1] - origin[1]])
    except Exception:
        break

    t = round(t + 1 / fps, 3)

with open("data.csv", "w") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerow(["Time", "X", "Y"])
    writer.writerows(data)

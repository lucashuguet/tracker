#!/usr/bin/env python3

import colorsys
import pygame
import cv2
import sys
import csv

CIRCLE_RADIUS = 2
SHOW_LAST_POINTS = 5

def gen_colors(n):
    colors = []
    for i in range(n):
        hue = i / n
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors

def draw_circle_alpha(surface, color, center, radius):
    target_frame_pos_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    shape_surf = pygame.Surface(target_frame_pos_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_frame_pos_rect)

video = cv2.VideoCapture(sys.argv[1])
success, frame = video.read()
fps = video.get(cv2.CAP_PROP_FPS)
frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

if x := input("fps [" + str(fps) + "]: "):
    fps = float(x)

w, h = 1920, 1080 # width and height of the window
width, height = frame.shape[1::-1] # width and height of the frame
ratio = width / height

offsetx, offsety = 0, 0
moving = False
next_frame = False # if the key for next frame is currently held
one_frame = False # frame per frame
fixed_mousex, fixed_mousey = 0, 0

scale = 1.0
last_scale = None # if frame has to be scaled
new = True # if frame has to be refreshed

n = 1
if x := input("number of points [1]: "):
    n = int(x)

colors = gen_colors(n+1)
points = [[None] * (n+1)] # origin, tracked_1, ..., tracked_n
index = 1 # next point to be placed

time = 0.0

window = pygame.display.set_mode((w, h), pygame.RESIZABLE)
clock = pygame.time.Clock()

image = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
scaled = image

pygame.init()
font = pygame.font.Font("./liberationmono.ttf", 32)

run = success
while run:
    frame_idx = int(video.get(cv2.CAP_PROP_POS_FRAMES))
    frame_pos_text = font.render(str(frame_idx) + "/" + str(frame_count), True, (255, 255, 255), (0, 0, 0))
    frame_pos_rect = frame_pos_text.get_rect()

    time_text = font.render(str(round(time, 3)), True, (255, 255, 255), (0, 0, 0))
    time_rect = time_text.get_rect()

    nw, nh = pygame.display.get_surface().get_size()
    if nw != w or nh != h:
        w, h = nw, nh

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RIGHT:
                next_frame = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RIGHT]:
                next_frame = True

            if event.key in [pygame.K_f, pygame.K_1, pygame.K_6]:
                one_frame = True

            if event.key == pygame.K_BACKSPACE:
                offsetx, offsety = 0, 0
                scale = 1.0
                index = 1
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: # scroll up
                scale = min(scale * 1.1, 10.0)
            elif event.button == 5: # scroll down
                scale = max(scale * 0.9, 0.1)
            elif (event.button == 1 or event.button == 3): # left click / right click
                mousex, mousey = pygame.mouse.get_pos()

                if not 0 <= mousex - x - offsetx <= scaled.get_width():
                    continue
                if not 0 <= mousey - y - offsety <= scaled.get_height():
                    continue

                relativex = (mousex - x - offsetx) * width / scaled.get_width()
                relativey = (mousey - y - offsety) * height / scaled.get_height()

                if event.button == 1:
                    i = index
                    index = index % n + 1
                else:
                    i = 0

                points[-1][i] = (int(relativex), int(relativey)) # tracked -> left click / origin -> right click
            elif event.button == 2:
                moving = True
                mousex, mousey = pygame.mouse.get_pos()
                fixed_mousex = mousex - offsetx
                fixed_mousey = mousey - offsety
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                moving = False

    if (next_frame or one_frame) and points[-1][0]: # if an origin is set, expect all tracked point
        for i in range(1, n+1):
            if not points[-1][i]:
                next_frame = False
                one_frame = False
                break

    if next_frame or one_frame:
        try:
            success, frame = video.read()
            image = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
        except Exception:
            print("reached video end")
            run = False
        new = True
        one_frame = False


        if points[-1][0]:
            time += 1 / fps

        points.append([points[-1][0]] + [None] * n)

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

    opacity = SHOW_LAST_POINTS;
    for p in reversed(points):
        # print("points:", p, "opacity:", opacity)
        if opacity == 0:
            break

        for i in range(1, len(p)):
            if tracked := p[i]:
                # print(i, "tracked: ", tracked, "color: ", colors[i])
                realx = int(scaled.get_width() / width * tracked[0]) + x + offsetx
                realy = int(scaled.get_height() / height * tracked[1]) + y + offsety
                draw_circle_alpha(window, colors[i] + (int(opacity / SHOW_LAST_POINTS * 255),), (realx, realy), CIRCLE_RADIUS * scale)
        opacity -= 1

    if origin := points[-1][0]:
        # print("origin:", origin, "color:", colors[0])
        realx = int(scaled.get_width() / width * origin[0]) + x + offsetx
        realy = int(scaled.get_height() / height * origin[1]) + y + offsety
        draw_circle_alpha(window, colors[0] + (255.,), (realx, realy), CIRCLE_RADIUS * scale)

    frame_pos_rect.center = (150, 20)
    window.blit(frame_pos_text, frame_pos_rect)

    time_rect.center = (w / 2, 20)
    window.blit(time_text, time_rect)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()

data = []

t = 0
for p in points:
    if not p[0]:
        continue

    try:
        row = [t]
        for i in range(1, len(p)):
            row.append(p[i][0] - p[0][0]) # tracked x - origin x
            row.append(p[i][1] - p[0][1]) # tracked y - origin y
        data.append(row)
    except Exception:
        break

    t = round(t + 1 / fps, 3)

with open("data.csv", "w") as f:
    writer = csv.writer(f, delimiter=",")
    headers = ["Time"]
    for i in range(1, n+1):
        headers += ["X" + str(i), "Y" + str(i)]
    writer.writerow(headers)
    writer.writerows(data)

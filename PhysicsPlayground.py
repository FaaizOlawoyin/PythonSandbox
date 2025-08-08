import pygame
import pymunk
import pymunk.pygame_util
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
space = pymunk.Space()
space.gravity = (0, 900)
draw_options = pymunk.pygame_util.DrawOptions(screen)

font = pygame.font.SysFont("Arial", 24)
menu_open = False

WALL_THICKNESS = 20
WIDTH, HEIGHT = screen.get_size()

# Create walls and roof
def create_static_segment(p1, p2):
    seg = pymunk.Segment(space.static_body, p1, p2, WALL_THICKNESS)
    seg.elasticity = 0.5
    seg.friction = 1.0
    space.add(seg)

create_static_segment((0, 0), (0, HEIGHT))
create_static_segment((WIDTH, 0), (WIDTH, HEIGHT))
create_static_segment((0, HEIGHT), (WIDTH, HEIGHT))
create_static_segment((0, 0), (WIDTH, 0))

# Gravity control
gravity_enabled = True
GRAVITY_ON = (0, 900)
GRAVITY_OFF = (0, 0)

# Time control
slow_motion = False
frozen = False
normal_dt = 1 / 60.0
slow_dt = normal_dt * 0.5

# Shape creation
def spawn_circle(x, y):
    body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 30))
    body.position = (x, y)
    shape = pymunk.Circle(body, 30)
    shape.elasticity = 0.4
    shape.friction = 0.8
    space.add(body, shape)

def spawn_box(x, y):
    size = (60, 60)
    body = pymunk.Body(1, pymunk.moment_for_box(1, size))
    body.position = (x, y)
    shape = pymunk.Poly.create_box(body, size)
    shape.elasticity = 0.4
    shape.friction = 0.8
    space.add(body, shape)

def spawn_triangle(x, y):
    verts = [(-40, -30), (40, -30), (0, 40)]
    body = pymunk.Body(1, pymunk.moment_for_poly(1, verts))
    body.position = (x, y)
    shape = pymunk.Poly(body, verts)
    shape.elasticity = 0.4
    shape.friction = 0.8
    space.add(body, shape)

def spawn_segment(x, y):
    body = pymunk.Body(1, pymunk.moment_for_segment(1, (-40, 0), (40, 0), 5))
    body.position = (x, y)
    shape = pymunk.Segment(body, (-40, 0), (40, 0), 5)
    shape.elasticity = 0.4
    shape.friction = 0.8
    space.add(body, shape)

# Menu button logic
button_rects = []
def draw_menu():
    global button_rects
    button_rects = []
    shapes = ["Circle", "Box", "Triangle", "Segment", "Delete"]
    for i, shape in enumerate(shapes):
        rect = pygame.Rect(20, 50 + i * 60, 200, 50)
        pygame.draw.rect(screen, (100, 100, 255), rect)
        text = font.render(shape, True, (255, 255, 255))
        screen.blit(text, (rect.x + 10, rect.y + 10))
        button_rects.append((rect, shape))

def handle_menu_click(pos):
    global menu_open
    for rect, shape in button_rects:
        if rect.collidepoint(pos):
            if shape == "Circle":
                spawn_circle(WIDTH // 2, 100)
            elif shape == "Box":
                spawn_box(WIDTH // 2, 100)
            elif shape == "Triangle":
                spawn_triangle(WIDTH // 2, 100)
            elif shape == "Segment":
                spawn_segment(WIDTH // 2, 100)
            elif shape == "Delete":
                for body in [b for b in space.bodies if b.body_type == pymunk.Body.DYNAMIC]:
                    for s in body.shapes:
                        space.remove(s)
                    space.remove(body)
            menu_open = False
            break

# Dragging variables
dragging = False
dragged_body = None
mouse_joint = None

# Main loop
running = True
while running:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        elif event.type == KEYDOWN:
            if event.key == K_q:
                menu_open = not menu_open
            elif event.key == K_t:
                slow_motion = not slow_motion
            elif event.key == K_f:
                frozen = not frozen
            elif event.key == K_g:
                gravity_enabled = not gravity_enabled
                space.gravity = GRAVITY_ON if gravity_enabled else GRAVITY_OFF
            elif event.key == K_ESCAPE:
                running = False

        elif event.type == MOUSEBUTTONDOWN:
            if menu_open:
                handle_menu_click(pygame.mouse.get_pos())
            else:
                p = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
                hit = space.point_query_nearest(p, 5, pymunk.ShapeFilter())
                if hit and hit.shape.body.body_type == pymunk.Body.DYNAMIC:
                    dragged_body = hit.shape.body
                    mouse_joint = pymunk.PivotJoint(space.static_body, dragged_body, p)
                    mouse_joint.max_force = 50000
                    space.add(mouse_joint)
                    dragging = True

        elif event.type == MOUSEBUTTONUP:
            if dragging:
                dragging = False
                if mouse_joint:
                    space.remove(mouse_joint)
                    mouse_joint = None
                dragged_body = None

        elif event.type == MOUSEMOTION:
            if dragging and mouse_joint:
                new_p = pymunk.pygame_util.from_pygame(event.pos, screen)
                mouse_joint.anchor_a = new_p

    if menu_open:
        draw_menu()

    # Time step
    if not frozen:
        dt = slow_dt if slow_motion else normal_dt
        space.step(dt)

    space.debug_draw(draw_options)

    # UI text
    status_text = "Slow Motion ON (T to toggle)" if slow_motion else "Normal Speed (T to toggle)"
    gravity_text = "Gravity ON (G to toggle)" if gravity_enabled else "Gravity OFF (G to toggle)"
    freeze_text = "TIME FROZEN (F to resume)" if frozen else "Time Running (F to freeze)"

    screen.blit(font.render(status_text, True, (255, 255, 255)), (WIDTH - 380, 10))
    screen.blit(font.render(gravity_text, True, (255, 255, 255)), (WIDTH - 380, 40))
    screen.blit(font.render(freeze_text, True, (255, 255, 255)), (WIDTH - 380, 70))

    # Guide text
    guide_lines = [
        "Press Q to toggle spawn menu",
        "Press T to toggle slow motion",
        "Press F to freeze/unfreeze time",
        "Press G to toggle gravity",
        "Press ESC to quit"
    ]
    for i, line in enumerate(guide_lines):
        guide_surface = font.render(line, True, (200, 200, 200))
        screen.blit(guide_surface, (20, 10 + i * 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

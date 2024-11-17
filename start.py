import pygame
import math
import random
import sys
import subprocess

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)  # Black background
BUTTON_COLOR = (119, 119, 119)  # Button color (Dodger Blue)
BUTTON_HOVER_COLOR = (85, 85, 85)  # Hover effect (Cornflower Blue)
TEXT_COLOR = (255, 255, 255)  # White text
FONT_SIZE = 80
BUTTON_FONT_SIZE = 36  # Smaller font size for buttons
NUM_RAYS = 360
WOOD_COLOR = (139, 69, 19)  # Wood color for walls

# Setup display and fonts
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Laser Music Machine")
font = pygame.font.Font(None, FONT_SIZE)
button_font = pygame.font.Font(None, BUTTON_FONT_SIZE)
small_font = pygame.font.Font(None, 36)

# Global state for recording
recording = False


# Helper functions
def draw_text(text, font, color, surface, x, y):
    """Draw centered text on the screen."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)


# Classes
class Ray:
    def __init__(self, x1, y1, dirX, dirY):
        self.x1 = x1
        self.y1 = y1
        self.dirX = dirX
        self.dirY = dirY

    def collide(self, wall):
        """Check for collision with a wall."""
        wx1, wy1, wx2, wy2 = wall.get_coordinates()
        rx3, ry3 = self.x1, self.y1
        rx4, ry4 = self.x1 + self.dirX, self.y1 + self.dirY

        n = (wx1 - rx3) * (ry3 - ry4) - (wy1 - ry3) * (rx3 - rx4)
        d = (wx1 - wx2) * (ry3 - ry4) - (wy1 - wy2) * (rx3 - rx4)

        if d == 0:
            return False

        t = n / d
        u = ((wx2 - wx1) * (wy1 - ry3) - (wy2 - wy1) * (wx1 - rx3)) / d

        if 0 < t < 1 and u > 0:
            px = wx1 + t * (wx2 - wx1)
            py = wy1 + t * (wy2 - wy1)
            return (px, py)
        return False


class Wall:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def get_coordinates(self):
        """Return the coordinates of the wall."""
        return self.x1, self.y1, self.x2, self.y2

    def show(self, surface):
        """Draw the wall with wood color."""
        pygame.draw.line(surface, WOOD_COLOR, (self.x1, self.y1), (self.x2, self.y2), 5)


class Light:
    def __init__(self, x1, y1, num_rays):
        self.x1, self.y1 = x1, y1
        self.rays = [
            Ray(self.x1, self.y1, math.cos(math.radians(i)), math.sin(math.radians(i)))
            for i in range(0, 360, int(360 / num_rays))
        ]

    def show(self, surface, walls):
        """Cast rays from the light source and check for collisions with walls."""
        for ray in self.rays:
            ray.x1, ray.y1 = self.x1, self.y1
            closest = float("inf")
            closest_point = None
            for wall in walls:
                intersection = ray.collide(wall)
                if intersection:
                    distance = math.sqrt(
                        (ray.x1 - intersection[0]) ** 2
                        + (ray.y1 - intersection[1]) ** 2
                    )
                    if distance < closest:
                        closest = distance
                        closest_point = intersection
            if closest_point:
                pygame.draw.line(
                    surface, (255, 0, 0), (ray.x1, ray.y1), closest_point
                )  # Red lasers


class Button:
    def __init__(self, text, x, y, width, height, color=BUTTON_COLOR):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = BUTTON_HOVER_COLOR

    def draw(self, surface):
        """Draw the button with hover effect."""
        mouse_pos = pygame.mouse.get_pos()
        current_color = (
            self.color if not self.rect.collidepoint(mouse_pos) else self.hover_color
        )
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        text_surface = button_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def click(self):
        """Check if the button was clicked."""
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)


# Game Logic
def draw_random_notes(surface, music_notes, music_note_timer):
    """Draw music notes one by one."""
    if music_note_timer < len(music_notes):
        note = music_notes[music_note_timer]
        note_surface = small_font.render(note, True, TEXT_COLOR)
        x = random.randint(600, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        surface.blit(note_surface, (x, y))
        music_note_timer += 1
    return music_note_timer


# Initialize Buttons
start_button = Button("Start", WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 70)
toggle_button = Button(
    "Recording: OFF", WIDTH // 2 - 100, HEIGHT // 2, 250, 100
)  # Increased button size

# Initialize walls and light source
walls = [
    Wall(0, 0, WIDTH - 1, 0),
    Wall(0, 0, 0, HEIGHT - 1),
    Wall(0, HEIGHT - 1, WIDTH - 1, HEIGHT - 1),
    Wall(WIDTH - 1, 0, WIDTH - 1, HEIGHT - 1),
]
for i in range(random.randint(0, 10)):
    walls.append(
        Wall(
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
        )
    )

light = Light(500, 500, NUM_RAYS)

# Music note list
notes = ["♪", "♫", "♬", "♩", "♬"]
music_notes = random.choices(notes, k=10)
music_note_timer = 0

# Main Game Loop
running = True
while running:
    screen.fill(BACKGROUND_COLOR)

    # Draw title
    draw_text("Laser Music Machine", font, TEXT_COLOR, screen, WIDTH // 2, HEIGHT // 8)

    # Draw walls
    for wall in walls:
        wall.show(screen)

    # Update light source and show rays
    light.x1, light.y1 = pygame.mouse.get_pos()
    light.show(screen, walls)

    # Draw UI elements
    toggle_button.draw(screen)
    draw_random_notes(screen, music_notes, music_note_timer)
    start_button.draw(screen)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if toggle_button.click():
                recording = not recording
                toggle_button.text = "Recording: ON" if recording else "Recording: OFF"
                toggle_button.color = (0, 255, 0) if recording else (255, 0, 0)
            if start_button.click():
                pygame.quit()
                subprocess.run(["python", "main.py"])  # Run another script
                sys.exit()

    pygame.display.flip()

pygame.quit()
sys.exit()

import pygame
import sys
import subprocess

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 800
screen_height = 600

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)

# Fonts
font = pygame.font.SysFont(None, 55)
small_font = pygame.font.SysFont(None, 35)

# Screen setup
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Laser Music Machine")

# Global flag for recording
recording = False


def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)


def main_menu():
    global recording
    while True:
        screen.fill(white)

        draw_text(
            "Laser Music Machine",
            font,
            black,
            screen,
            screen_width // 2,
            screen_height // 3,
        )

        # Toggle button
        button_text = "Recording: ON" if recording else "Recording: OFF"
        button_color = green if recording else red
        button_rect = pygame.Rect(screen_width // 2 - 100, screen_height // 2, 200, 50)
        pygame.draw.rect(screen, button_color, button_rect)
        draw_text(
            button_text,
            small_font,
            white,
            screen,
            screen_width // 2,
            screen_height // 2 + 25,
        )

        # Start button
        start_button_rect = pygame.Rect(
            screen_width // 2 - 100, screen_height // 2 + 100, 200, 50
        )
        pygame.draw.rect(screen, black, start_button_rect)
        draw_text(
            "Start",
            small_font,
            white,
            screen,
            screen_width // 2,
            screen_height // 2 + 125,
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    recording = not recording
                if start_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    subprocess.run(["python", "main.py"])
                    sys.exit()

        pygame.display.flip()


if __name__ == "__main__":
    main_menu()

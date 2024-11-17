import pygame
import csv
import time
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

pygame.init()  # Initialize all Pygame modules

pygame.mixer.init()

note_sounds = {
    "A": pygame.mixer.Sound("A.MP3"),
    "B": pygame.mixer.Sound("B.MP3"),
    "C": pygame.mixer.Sound("C.MP3"),
    "D": pygame.mixer.Sound("D.MP3"),
    "E": pygame.mixer.Sound("E.MP3"),
    "F": pygame.mixer.Sound("F.MP3"),
}

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
pygame.display.set_caption("Playback Options")


def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)


def play_recording(filename):
    if not os.path.exists(filename):
        print("No recordings found.")
        return

    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip header
        recording_data = list(csvreader)

    if not recording_data:
        print("No recordings found.")
        return

    start_time = float(recording_data[0][0])
    for record in recording_data:
        note_time = float(record[0])
        note = record[1]
        time.sleep(note_time - start_time)
        note_sounds[note].play()
        start_time = note_time


def main_menu():
    while True:
        screen.fill(white)

        draw_text(
            "Playback Options",
            font,
            black,
            screen,
            screen_width // 2,
            screen_height // 3,
        )

        # Play recent recording button
        recent_button_rect = pygame.Rect(
            screen_width // 2 - 150, screen_height // 2 - 50, 300, 50
        )
        pygame.draw.rect(screen, green, recent_button_rect)
        draw_text(
            "Play Recent Recording",
            small_font,
            white,
            screen,
            screen_width // 2,
            screen_height // 2 - 25,
        )

        # Play from CSV button
        csv_button_rect = pygame.Rect(
            screen_width // 2 - 150, screen_height // 2 + 50, 300, 50
        )
        pygame.draw.rect(screen, red, csv_button_rect)
        draw_text(
            "Play from CSV",
            small_font,
            white,
            screen,
            screen_width // 2,
            screen_height // 2 + 75,
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if recent_button_rect.collidepoint(event.pos):
                    play_recording("recording.csv")
                if csv_button_rect.collidepoint(event.pos):
                    # Open file explorer dialog
                    Tk().withdraw()  # Hide the root window
                    filename = askopenfilename(filetypes=[("CSV files", "*.csv")])
                    if filename:
                        play_recording(filename)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:  # Q key pressed
                    pygame.quit()
                    return

        pygame.display.flip()


if __name__ == "__main__":
    main_menu()

import shutil
import time
from art import text2art
from termcolor import colored
import pygame
import os
import sys

def is_running_in_docker():
    """
    Checks if the application is running inside a Docker container.
    """
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                return True
    except Exception:
        return False
    return False

def play_music():
    # Initialize the mixer and play the music only if not in Docker
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("var/music/ssi-intro.mp3")  # Load your music file
        pygame.mixer.music.play(-1)  # Play the music in a loop
    except Exception as e:
        print(f"Error playing music: {e}")

def display_intro():
    # Main text to display
    main_text = text2art("Nucleon", font="block")
    main_text_colored = colored(main_text, "green")  # Green for retro look

    # ASCII art for the bird and the computer
    bird = [
        "       _.--.__                                             _.--.",
        "    ./'       `--.__                                   ..-'   ,'",
        "  ,/               |`-.__                            .'     ./",
        " :,                 :    `--_    __                .'   ,./'_.....",
        " :                  :   /    `-:' _\\.            .'   ./..-'   _.'",
        " :                  ' ,'       : / \\ :         .'    `-'__...-'",
        " `.               .'  .        : \\@/ :       .'       '------.,",
        "    ._....____  ./    :     .. `     :    .-'      _____.----'",
        "              `------------' : |     `..-'        `---.",
        "                         .---'  :    ./      _._-----'",
        ".---------._____________ `-.__/ : /`      ./_-----/':",
        "`---...--.              `-_|    `.`-._______-'  /  / ,-----.__----.",
        "   ,----' ,__.  .          |   /  `\\.________./  ====__....._____.",
        "   `-___--.-' ./. .-._-'----\\.                  ./.---..____.--.",
        "         :_.-' '-'            `..            .-'===.__________. '",
        "                                 `--...__.--'"
    ]

    computer = [
        "                   .----.",
        "      .---------. | == |",
        "      |.-\"\"\"\"\"-.| |----|",
        "      ||       || | == |",
        "      ||       || |----|",
        "      |'-.....-'| |::::|",
        "      `\"\"\"\"\"\"\"\"\"` |___.|",
        "     /:::::::::::\\\" _  \"",
        "    /:::=======:::\\`\\`\\",
        "jgs `\"\"\"\"\"\"\"\"\"\"\"\"\"`  '-'"
    ]

    # Colors for the animation
    bird_color = "yellow"
    computer_color = "blue"

    # Get the terminal width
    terminal_width = shutil.get_terminal_size().columns

    # Ensure there's enough room for both the main text and the animations
    if terminal_width < 60:
        return

    # Adjust positions based on terminal width
    bird_start = terminal_width - len(bird[0])
    computer_start = -len(computer[0])
    text_offset = (terminal_width - len(main_text.split('\n')[0])) // 2

    # Animation loop
    for frame in range(terminal_width + len(bird[0])):
        print("\033c", end="")  # Clear the screen

        # Print the main text centered
        print(" " * text_offset + main_text_colored)

        # Calculate the positions for the bird and computer
        bird_pos = max(0, bird_start - frame)
        computer_pos = min(terminal_width - len(computer[0]), computer_start + frame)

        # Draw the bird
        for line in bird:
            print(f"{' ' * bird_pos}{colored(line, bird_color)}")

        # Draw the computer
        for line in computer:
            print(f"{' ' * computer_pos}{colored(line, computer_color)}")

        # Pause before the next frame
        time.sleep(0.1)

if __name__ == "__main__":
    if not is_running_in_docker():
        play_music()  # Play the intro music if not in Docker
    display_intro()

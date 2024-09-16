import shutil
import time
import os

try:
    from art import text2art
except ImportError:
    print("The 'art' module is not installed. Install it using 'pip install art'.")
    exit(1)

try:
    from termcolor import colored
except ImportError:
    print("The 'termcolor' module is not installed. Install it using 'pip install termcolor'.")
    exit(1)

try:
    import pygame
except ImportError:
    print("The 'pygame' module is not installed. Install it using 'pip install pygame'.")
    exit(1)


def is_running_in_docker():
    """
    Checks if the application is running inside a Docker container.
    """
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except Exception:
        return False


def play_music():
    """
    Initializes the mixer and plays the music if the music file exists.
    """
    music_file = "var/music/ssi-intro.mp3"
    if not os.path.exists(music_file):
        print(f"Music file '{music_file}' not found.")
        return
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Error playing music: {e}")


def clear_screen():
    """
    Clears the terminal screen in a cross-platform way.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def display_intro():
    """
    Displays the introductory ASCII art animation with the Nucleon logo.
    """
    # Main text to display
    try:
        main_text = text2art("Nucleon", font="block")
    except Exception as e:
        print(f"Error generating text art: {e}")
        main_text = "NUCLEON"
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

    frame = 0
    try:
        while True:
            clear_screen()
            # Recalculate terminal width to handle resizing
            terminal_width = shutil.get_terminal_size().columns

            # Ensure there's enough room for both the main text and the animations
            if terminal_width < 60:
                print("Terminal too small for animation.")
                break

            # Adjust positions based on terminal width
            bird_start = terminal_width - len(bird[0])
            computer_start = -len(computer[0])
            text_offset = (terminal_width - len(main_text.split('\n')[0])) // 2

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
            frame += 1
            # Stop the animation when the bird and computer have crossed the screen
            if bird_pos <= 0 and computer_pos >= terminal_width - len(computer[0]):
                break
    except KeyboardInterrupt:
        pass  # Exit gracefully on Ctrl+C


if __name__ == "__main__":
    if not is_running_in_docker():
        play_music()  # Play the intro music if not in Docker
    try:
        display_intro()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.mixer.quit()
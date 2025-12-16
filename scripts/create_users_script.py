import pyautogui
import time
from pynput import keyboard


def create_user(first_name, last_name, gender):
    assert gender in ["m", "w"], "Gender must be either 'm' or 'w'"
    username = first_name.lower()[0] + last_name.lower()
    # Go to first name field:
    pyautogui.press("tab", presses=16)
    pyautogui.write(first_name)

    # Go to last name field
    pyautogui.press("tab", presses=2)
    pyautogui.write(last_name)

    # Go to gender selection
    pyautogui.press("tab")

    # Select gender
    if gender == "w":
        pyautogui.press("right")
    elif gender == "m":
        pyautogui.press("right", presses=2)

    # Go to username field
    pyautogui.press("tab", presses=2)
    pyautogui.write(username)

    # Go to password field
    pyautogui.press("tab")
    pyautogui.write("SuperSavePwd123!")

    # Confirm password
    pyautogui.press("tab")
    pyautogui.write("SuperSavePwd123!")
    print(username)

    # Go to doctor checkbox
    pyautogui.press("tab", presses=20)
    pyautogui.press("space")

    # Go to save button
    pyautogui.press("tab", presses=22)
    pyautogui.press("enter")

def on_press(key, injected):
    try:
        if key.char == "#":
            create_user("Florian", "Hauptmann", "m")

    except AttributeError:
        print('special key {} pressed'.format(
            key))

def on_release(key, injected):
    if key == keyboard.Key.esc:
        # Stop listener
        return False

if __name__ == '__main__':
   with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
    listener.start()

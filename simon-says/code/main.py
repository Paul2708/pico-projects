import machine
import utime
import random


# Define components
green_led = machine.Pin(0, machine.Pin.OUT)
yellow_led = machine.Pin(6, machine.Pin.OUT)
red_led = machine.Pin(14, machine.Pin.OUT)
blue_led = machine.Pin(15, machine.Pin.OUT)

blue_button = machine.Pin(17, machine.Pin.IN)
red_button = machine.Pin(18, machine.Pin.IN)
yellow_button = machine.Pin(19, machine.Pin.IN)
green_button = machine.Pin(20, machine.Pin.IN)

colors = [(blue_button, blue_led, "blue"),
         (red_button, red_led, "red"),
         (yellow_button, yellow_led, "yellow"),
         (green_button, green_led, "green")]


def set_leds(value):
    for _, led, _ in colors:
        led.value(value)


def await_button_press():
    down_state = set()
    
    while True:
        for button, led, color in colors:
            led.value(button.value())
            
            if color in down_state and button.value() == 0:
                down_state.remove(color)
                return color
            elif button.value() == 1:
                down_state.add(color)
        
        utime.sleep(0.05)


def show_sequence(sequence):
    for button, led, color in sequence:
        led.toggle()
        utime.sleep(1)
        led.toggle()
        utime.sleep(0.25)


def await_game_start():
    down_state = set()
    ticks = 0
    
    while True:
        # Play animation
        if ticks == 20:
            green_led.value(1)
        elif ticks == 40:
            yellow_led.value(1)
        elif ticks == 60:
            red_led.value(1)
        elif ticks == 80:
            blue_led.value(1)
        elif ticks == 100:
            set_leds(0)
            ticks = 0
        
        # Check if button pressed
        for button, _, color in colors:
            if color in down_state and button.value() == 0:
                down_state.remove(color)
                return
            elif button.value() == 1:
                down_state.add(color)
        
        ticks += 1
        utime.sleep(0.01)


def show_game_over():    
    for _ in range(4):
        set_leds(1)
        utime.sleep(0.5)    
        set_leds(0)
        utime.sleep(0.5) 


# Define game states
running = False
color_sequence = []

# Game start
machine.Pin("LED", machine.Pin.OUT).value(1)
set_leds(0)

while True:
    if not running:
        await_game_start()
        
        set_leds(0)
        
        color_sequence = []
        running = True
    else:
        utime.sleep(1.5)
        
        color_sequence.append(random.choice(colors))
        show_sequence(color_sequence)
    
        for button, led, color in color_sequence:
            pressed_color = await_button_press()
        
            if pressed_color != color:
                show_game_over()
                running = False
                break

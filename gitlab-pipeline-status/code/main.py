from machine import Pin
import utime
import network
import uasyncio
import urequests

import secrets


# Define LEDs
status_led = Pin("LED", Pin.OUT)

yellow_led = Pin(15, Pin.OUT)
green_led = Pin(14, Pin.OUT)
red_led = Pin(8, Pin.OUT)

# Get credentials
SSID = secrets.SSID
PASSWORD = secrets.PASSWORD

GITLAB_ACCESS_TOKEN = secrets.GITLAB_ACCESS_TOKEN
GITLAB_PROJECT_ID = secrets.GITLAB_PROJECT_ID

GITLAB_REQUEST_PERIOD = 10 # in seconds
GITLAB_ENDPOINT = f"https://{secrets.GITLAB_HOST}/api/v4/projects/{GITLAB_PROJECT_ID}/pipelines/latest"

PIPELINE_IDLE = "idle"
PIPELINE_RUNNING = "running"
PIPELINE_FAILED = "failed"
PIPELINE_SUCCEEDED = "succeeded"


def connect_to_wlan(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        
        max_wait -= 1
        print("Waiting for WLAN connection...")
        time.sleep(1)

    if wlan.status() != 3:
        print("Network connection failed.")
    else:
        print(f"Connected to {SSID} ({wlan.ifconfig()[0]})")


def extract_datetime_components(timestamp):
    date_part, time_part = timestamp.split('T')
    
    year, month, day = map(int, date_part.split('-'))
    
    time_part = time_part.rstrip('Z')
    
    hours, minutes, seconds = map(float, time_part.split(':'))
    
    return year, month, day, int(hours), int(minutes), int(seconds), 0, 0


def is_before(timestamp_value):
    now_milli = utime.mktime(utime.gmtime())
    timestamp = utime.mktime(extract_datetime_components(timestamp_value))
    
    return now_milli - timestamp >= 7200 + 60


async def check_pipeline_status():
    response = urequests.get(url=GITLAB_ENDPOINT, headers = { "PRIVATE-TOKEN": GITLAB_ACCESS_TOKEN }).json()
    status = response["status"]
    finished_at = response["finished_at"]
    
    print(f"Debug: {status}, {finished_at}")
    
    if finished_at is None or finished_at == "null":
        return PIPELINE_RUNNING
    else:
        if is_before(finished_at):
            return PIPELINE_IDLE
        elif status == "success":
            return PIPELINE_SUCCEEDED
        elif status in ["canceled", "skipped", "failed"]:
            return PIPELINE_FAILED
        else:
            return PIPELINE_RUNNING


idle_counter = 0

def idle():
    global idle_counter
    
    if idle_counter == 0:
        yellow_led.value(1)
    elif idle_counter == 1:
        green_led.value(1)
    elif idle_counter == 2:
        red_led.value(1)
    else:
        yellow_led.value(0)
        green_led.value(0)
        red_led.value(0)
    
    idle_counter = idle_counter + 1
    idle_counter = idle_counter % 4


def running():
    green_led.value(0)
    red_led.value(0)
    yellow_led.toggle()


def succeeded():
    yellow_led.value(0)
    red_led.value(0)
    green_led.value(1)


def failed():
    yellow_led.value(0)
    green_led.value(0)
    red_led.value(1)


async def main():
    red_led.value(0)
    yellow_led.value(0)
    green_led.value(0)
    
    status_led.value(0)
    
    connect_to_wlan(SSID, PASSWORD)
    pipeline_status = PIPELINE_IDLE
    
    status_led.value(1)
    
    timer = 4 * 10 - 2
    task = None
    
    while True:
        if task != None and task.done():
            pipeline_status = f"{task.data}"
            task = None
            print(f"Received new status: {pipeline_status}")
        
        if pipeline_status == PIPELINE_IDLE:
            idle()
        elif pipeline_status == PIPELINE_RUNNING:
            running()
        elif pipeline_status == PIPELINE_SUCCEEDED:
            succeeded()
        elif pipeline_status == PIPELINE_FAILED:
            failed()
            
        await uasyncio.sleep_ms(250)
        timer += 1
        
        if timer == 4 * GITLAB_REQUEST_PERIOD:
            timer = 0
            print("Submit new task to fetch latest status...")
            task = uasyncio.create_task(check_pipeline_status())
            print("Submission completed.")
    
        
uasyncio.run(main())

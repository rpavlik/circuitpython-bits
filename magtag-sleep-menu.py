# Copyright 2021, Ryan Pavlik <ryan.pavlik@gmail.com>
# SPDX-License-Identifier: Unlicense

magtag = MagTag(rotation=180)

magtag_graphics = magtag.graphics

BUTTON_0_POS = 30
BUTTON_SPACING = (magtag_graphics.display.height - BUTTON_0_POS) // 4

for i in range(4):
    y = BUTTON_0_POS + i * BUTTON_SPACING
    magtag.add_text(
        text_font=FONT,
        text_position=(10, y),
        is_data=False,
    )
    magtag.set_text("", auto_refresh=False)

    
def get_button_states():
    return [not x.value for x in magtag.peripherals.buttons]


def get_button_pressed_index_if_any():
    states = get_button_states()
    if any(states):
        return states.index(True)
    return None


class MenuItem:
    "An item in a menu, perhaps with sub-items."

    def __init__(self, label, submenu=None, leaf_id=None):
        self.leaf_id = leaf_id
        self.label = label
        # self.children = children  # type: Optional[List["MenuItem"]]
        if submenu:
            self.submenu = submenu
        else:
            self.submenu = []

    def set_magtag_text(self):
        for i in range(4):
            magtag.set_text("", i, auto_refresh=False)
        if not self.submenu:
            return
        n = len(self.submenu)
        for i in range(4):
            if i < n:
                magtag.set_text(self.submenu[i].label, i, auto_refresh=False)

    def select(self):
        if not self.submenu:
            return self
        self.set_magtag_text()
        while magtag.peripherals.any_button_pressed:
            pass
        magtag.refresh()
        while not magtag.peripherals.any_button_pressed:
            pass
        button_values = [x.value for x in magtag.peripherals.buttons]
        index = button_values.index(False)
        print("Selected index %d" % index)
        return self.submenu[index].select()


menu = MenuItem(
    None,
    # Top level can only have two items, due to limit on number of wake-inducing buttons.
    [
        MenuItem(
            "a",
            submenu=[
                MenuItem("b", leaf_id=0),
                MenuItem("c", leaf_id=1),
                MenuItem(
                    "d",
                    submenu=[
                        MenuItem("e", leaf_id=10),
                        MenuItem("f", leaf_id=11),
                        MenuItem("g", leaf_id=12),
                        MenuItem("h", leaf_id=13),
                    ],
                ),
            ],
        ),
        MenuItem(
            "i",
            submenu=[
                MenuItem("j", leaf_id=20),
                MenuItem("k", leaf_id=21),
            ],
        ),
    ],
)


menu_entrypoint = menu


wake_buttons = [
    board.BUTTON_A,
    board.BUTTON_B,
]
triggered_alarm = alarm.wake_alarm
if isinstance(triggered_alarm, alarm.pin.PinAlarm):
    # hey we got woken up, find out why
    pin = triggered_alarm.pin
    index = wake_buttons.index(pin)
    print(index)
    magtag.set_text("got button index %d" % index)

    # We jump into the menu not at the root level.
    menu_entrypoint = menu.submenu[index]
    while magtag.peripherals.any_button_pressed:
        time.sleep(0.01)

pressed = get_button_pressed_index_if_any()
if pressed is not None:
    menu_entrypoint = menu.submenu[pressed]

selected = menu_entrypoint.select()
print(selected.leaf_id)

time.sleep(2)

# Display the root menu again
menu.set_magtag_text()
magtag.refresh()

# Needed otherwise alarm creation will complain pin in use.
magtag.peripherals.deinit()
alarms = [alarm.pin.PinAlarm(pin=x, value=False, pull=True) for x in wake_buttons]

time.sleep(2)
alarm.exit_and_deep_sleep_until_alarms(*alarms)

const output = document.getElementById('output');
const socket = io();

const KEYBOARD_GAMEPAD_MAP = {
    KeyQ: 8,
    KeyE: 9,
    KeyW: 12,
    KeyS: 13,
    KeyA: 14,
    KeyD: 15,
};

let lastButtonState = [];
let keyboardState = {};

function selectedDevice() {
    return document.getElementById('input_device').value;
}

function controllerIndex() {
    return parseInt(document.getElementById('controller_index').value);
}

function emit(controller, button, pressed) {
    const data = { controller, button, pressed };
    socket.emit('controller', data);
    output.textContent = JSON.stringify(data, null, 2);
}

function updateGamepad() {
    if (selectedDevice() !== 'gamepad') return;
    const controller = controllerIndex();
    const gp = navigator.getGamepads()[0];
    if (!gp) return;
    const buttons = gp.buttons.map(b => b.pressed);

    for (let i = 0; i < buttons.length; i++) {
        if (buttons[i] !== lastButtonState[i]) {
            emit(controller, i, buttons[i]);
        }
    }
    lastButtonState = buttons;
}

window.addEventListener('keydown', (e) => {
    if (selectedDevice() !== 'keyboard') return;
    if (!(e.code in KEYBOARD_GAMEPAD_MAP)) return;
    if (keyboardState[e.code]) return;
    keyboardState[e.code] = true;
    emit(controllerIndex(), KEYBOARD_GAMEPAD_MAP[e.code], true);
});

window.addEventListener('keyup', (e) => {
    if (selectedDevice() !== 'keyboard') return;
    if (!(e.code in KEYBOARD_GAMEPAD_MAP)) return;
    keyboardState[e.code] = false;
    emit(controllerIndex(), KEYBOARD_GAMEPAD_MAP[e.code], false);
});

function update() {
    updateGamepad();
    requestAnimationFrame(update);
}

socket.on('connect', () => {
    update();
});

// async function sendCommand(action, controller = 0, value = 0) {
//     await fetch(`/${action}`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ controller: parseInt(controller), value: parseInt(value) })
//     });
// }

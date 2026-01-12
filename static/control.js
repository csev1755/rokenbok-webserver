const socket = io();

const inputElement = document.getElementById('input');
const inputTemplate = document.getElementById('input-template');

const playersElement = document.getElementById('players');
const playerTemplate = document.getElementById('player-template');

const KEYBOARD_GAMEPAD_MAP = {
    KeyQ: 8,
    KeyE: 9,
    KeyW: 12,
    KeyS: 13,
    KeyA: 14,
    KeyD: 15,
};

let lastGamepadButtons = [];
const keyboardState = {};

function getSelectedDevice() {
    return document.getElementById('input_device').value;
}

function renderInput(button, pressed) {
    const fragment = inputTemplate.content.cloneNode(true);
    fragment.querySelector('[data-button]').textContent = button;
    fragment.querySelector('[data-state]').textContent = pressed ? 'Pressed' : 'Released';
    inputElement.replaceChildren(fragment);
}

function renderPlayers(players) {
    playersElement.replaceChildren();

    players.forEach((player, index) => {
        const fragment = playerTemplate.content.cloneNode(true);

        fragment.querySelector('[data-slot]').textContent = index + 1;
        fragment.querySelector('[data-controller]').textContent = player.controller;
        fragment.querySelector('[data-player-id]').textContent = player.player_id ?? '—';
        fragment.querySelector('[data-selection]').textContent = player.selection;
        
        playersElement.appendChild(fragment);
    });
}

function emitControllerEvent(button, pressed) {
    renderInput(button, pressed);
    socket.emit('controller', { button, pressed });
}

function pollGamepad() {
    if (getSelectedDevice() !== 'gamepad') return;

    const gamepad = navigator.getGamepads()[0];
    if (!gamepad) return;

    const buttons = gamepad.buttons.map(b => b.pressed);

    buttons.forEach((pressed, index) => {
        if (pressed !== lastGamepadButtons[index]) {
            emitControllerEvent(index, pressed);
        }
    });

    lastGamepadButtons = buttons;
}

window.addEventListener('keydown', e => {
    if (getSelectedDevice() !== 'keyboard') return;
    if (!(e.code in KEYBOARD_GAMEPAD_MAP)) return;
    if (keyboardState[e.code]) return;

    keyboardState[e.code] = true;
    emitControllerEvent(KEYBOARD_GAMEPAD_MAP[e.code], true);
});

window.addEventListener('keyup', e => {
    if (getSelectedDevice() !== 'keyboard') return;
    if (!(e.code in KEYBOARD_GAMEPAD_MAP)) return;

    keyboardState[e.code] = false;
    emitControllerEvent(KEYBOARD_GAMEPAD_MAP[e.code], false);
});

function loop() {
    pollGamepad();
    requestAnimationFrame(loop);
}

socket.on('connect', loop);

socket.on('players', data => {
    renderPlayers(data.players);
});

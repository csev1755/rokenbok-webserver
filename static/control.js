const socket = io();

const inputElement = document.getElementById('input');
const inputTemplate = document.getElementById('input-template');

const playersElement = document.getElementById('players');
const playerTemplate = document.getElementById('player-template');

const CONTROLS = [
    { name: 'A_BUTTON', button: 8,  key_default: 'KeyF', gamepad_default: 0 },
    { name: 'B_BUTTON', button: 9,  key_default: 'KeyG', gamepad_default: 1 },
    { name: 'X_BUTTON', button: 10,  key_default: 'KeyR', gamepad_default: 2 },
    { name: 'Y_BUTTON', button: 11,  key_default: 'KeyT', gamepad_default: 3 },
    { name: 'LEFT_TRIGGER', button: 1,  key_default: 'Digit1', gamepad_default: 4 },
    { name: 'RIGHT_TRIGGER', button: 12,  key_default: 'Digit3', gamepad_default: 5 },
    { name: 'DPAD_UP', button: 4, key_default: 'KeyW', gamepad_default: 12 },
    { name: 'DPAD_DOWN', button: 5, key_default: 'KeyS', gamepad_default: 13 },
    { name: 'DPAD_LEFT', button: 7, key_default: 'KeyA', gamepad_default: 14 },
    { name: 'DPAD_RIGHT', button: 6, key_default: 'KeyD', gamepad_default: 15 },
    { name: 'SELECT_UP', button: 13, key_default: 'KeyE', gamepad_default: 9 },
    { name: 'SELECT_DOWN', button: 14, key_default: 'KeyQ', gamepad_default: 8 },
];

const mappingBody = document.getElementById('mapping-body');

CONTROLS.forEach(control => {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${control.name}</td>
        <td>
            <input id="map_kb_${control.name}" class="map-key" size="6" value="${control.key_default}">
        </td>
        <td>
            <input id="map_gp_${control.name}" class="map-btn" size="1" value="${control.gamepad_default}">
        </td>
    `;
    mappingBody.appendChild(row);
});

let lastGamepadButtons = [];
const keyboardState = {};

function getPlayerName() {
    return document.getElementById('player_name').value;
}

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

        fragment.querySelector('[data-player-name]').textContent = player.player_name;
        fragment.querySelector('[data-selection]').textContent = player.selection;
        fragment.querySelector('[data-vehicle-name]').textContent = player.selection_name;
        
        playersElement.appendChild(fragment);
    });
}

function emitControllerEvent(button, pressed) {
    const player_name = getPlayerName();
    socket.emit('controller', { button, pressed, player_name });
}

function pollGamepad() {
    if (getSelectedDevice() !== 'gamepad') return;

    const gamepad = navigator.getGamepads()[0];
    if (!gamepad) return;

    const buttons = gamepad.buttons.map(b => b.pressed);

    buttons.forEach((pressed, index) => {
        const control = CONTROLS.find(c => 
            Number(document.getElementById(`map_gp_${c.name}`).value) === index
        );

        if (pressed !== lastGamepadButtons[index] && control) {
            renderInput(index, pressed);
            emitControllerEvent(control.button, pressed);
        }
    });

    lastGamepadButtons = buttons;
}

window.addEventListener('keydown', e => {
    if (getSelectedDevice() !== 'keyboard' || keyboardState[e.code]) return;
    const control = CONTROLS.find(c => 
        document.getElementById(`map_kb_${c.name}`).value === e.code
    );

    keyboardState[e.code] = true;
    renderInput(e.code, true);
    emitControllerEvent(control.button, true);
});

window.addEventListener('keyup', e => {
    if (getSelectedDevice() !== 'keyboard') return;
    const control = CONTROLS.find(c => 
        document.getElementById(`map_kb_${c.name}`).value === e.code
    );

    keyboardState[e.code] = false;
    renderInput(e.code, false);
    emitControllerEvent(control.button, false);
});

function loop() {
    pollGamepad();
    requestAnimationFrame(loop);
}

socket.on('connect', loop);

socket.on('players', data => {
    renderPlayers(data.players);
});

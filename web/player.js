const socket = io();

function loop() {
    pollGamepad();
    requestAnimationFrame(loop);
}

socket.on('connect', loop);

// Video stream iframe element
const videoStream = document.getElementById("stream-iframe");

// ============================================================================
// UI Panel
// ============================================================================
const panel = document.querySelector('.ui-panel');

// Update video stream source
function updateStream(stream) {
    videoStream.src = stream;
}

// Load or switch camera stream
document.addEventListener("DOMContentLoaded", function() {
    const selectedStream = document.getElementById("stream-selector").value;
    updateStream(selectedStream);
});

// UI panel elements
const inputElement = document.getElementById('input');
const inputTemplate = document.getElementById('input-template');
const playersElement = document.getElementById('players');
const playerTemplate = document.getElementById('player-template');
const mappingBody = document.getElementById('mapping-body');

// Tracks whether the panel is being dragged
let isDragging = false;

// Mouse X offset from panel edge during drag
let offsetX = 0;

// Mouse Y offset from panel edge during drag
let offsetY = 0;

// Grab panel
panel.addEventListener('mousedown', (e) => {
    // Don't initiate drag if clicking on interactive elements
    if (e.target.closest('input, select, button, textarea')) return;
    
    isDragging = true;
    offsetX = e.clientX - panel.offsetLeft;
    offsetY = e.clientY - panel.offsetTop;
    document.body.style.userSelect = 'none'; // Prevent text selection during drag
});

// Update panel position
document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    panel.style.left = `${e.clientX - offsetX}px`;
    panel.style.top  = `${e.clientY - offsetY}px`;
});

// Release panel
document.addEventListener('mouseup', () => {
    isDragging = false;
    document.body.style.userSelect = ''; // Re-enable text selection
});

// Get player name from input field
function getPlayerName() {
    return document.getElementById('player_name').value;
}

// Get device type from dropdown
function getSelectedDevice() {
    return document.getElementById('input_device').value;
}

// Default input maps
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

// Control mapping table and fields
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

/**
 * Update UI with current input state
 * @param {string|number} button - The button identifier (key code or button index)
 * @param {boolean} pressed - State of the button
 */
function renderInput(button, pressed) {
    const fragment = inputTemplate.content.cloneNode(true);
    fragment.querySelector('[data-button]').textContent = button;
    fragment.querySelector('[data-state]').textContent = pressed ? 'Pressed' : 'Released';
    inputElement.replaceChildren(fragment);
}

/**
 * @typedef {Object} PlayerData
 * @property {string} player_name - Player name
 * @property {number} selection - Selected vehicle ID
 * @property {string} selection_name - Selected vehicle name
 */

/**
 * Renders list of connected players
 * @param {PlayerData[]} players - Array of player data
 */
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

// ============================================================================
// Controller Input
// ============================================================================

// Get player data from server and render it
socket.on('players', data => {
    renderPlayers(data.players);
});

/**
 * Send a controller event to the server
 * @param {number} button - Button ID
 * @param {boolean} pressed - Button state
 */
function emitControllerEvent(button, pressed) {
    const player_name = getPlayerName();
    socket.emit('controller', { button, pressed, player_name });
}

/** @type {boolean[]} - Previous gamepad button states for change detection */
let lastGamepadButtons = [];

// Handle gamepad input
function pollGamepad() {
    if (getSelectedDevice() !== 'gamepad') return;

    // Get first connected gamepad
    const gamepad = navigator.getGamepads()[0];
    if (!gamepad) return;

    // Get button states
    const buttons = gamepad.buttons.map(b => b.pressed);

    // Check each button for state changes
    buttons.forEach((pressed, index) => {
        // Map control
        const control = CONTROLS.find(c => 
            Number(document.getElementById(`map_gp_${c.name}`).value) === index
        );

        // Send event if button state changed and the button is mapped
        if (pressed !== lastGamepadButtons[index] && control) {
            renderInput(index, pressed);
            emitControllerEvent(control.button, pressed);
        }
    });

    // Store state for next comparison
    lastGamepadButtons = buttons;
}

/** @type {Object.<string, boolean>} - Current keyboard key states */
const keyboardState = {};

// Handle keyboard key press
window.addEventListener('keydown', e => {
    // Make sure key isn't already held
    if (getSelectedDevice() !== 'keyboard' || keyboardState[e.code]) return;
    
    // Map key
    const control = CONTROLS.find(c => 
        document.getElementById(`map_kb_${c.name}`).value === e.code
    );

    // Mark key as pressed and send event
    keyboardState[e.code] = true;
    renderInput(e.code, true);
    emitControllerEvent(control.button, true);
});

// Handle keyboard key release
window.addEventListener('keyup', e => {
    // Only process if keyboard is selected
    if (getSelectedDevice() !== 'keyboard') return;
    
    // Map key
    const control = CONTROLS.find(c => 
        document.getElementById(`map_kb_${c.name}`).value === e.code
    );

    // Mark key as released and send event
    keyboardState[e.code] = false;
    renderInput(e.code, false);
    emitControllerEvent(control.button, false);
});

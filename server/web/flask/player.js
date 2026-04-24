const socket = io();

// Main floating panel
const panel = document.querySelector('.floating-panel');
const openSettingsButton = document.getElementById('open-settings');
const playersElement = document.getElementById('players');
const playerTemplate = document.getElementById('player-template');

// Settings window
const settingsWindow = document.getElementById('settings-window');

const playerNameInput = document.getElementById('player_name');
const inputDeviceSelect = document.getElementById('input_device');

const inputElement = document.getElementById('input');
const inputTemplate = document.getElementById('input-template');
const mappingBody = document.getElementById('mapping-body');
const saveSettingsButton = document.getElementById('save-settings');
const cancelSettingsButton = document.getElementById('cancel-settings');

// Get the streams if the HTML elements exist
const streamLabel = document.getElementById('stream-label');
const STREAMS = streamLabel
    ? Object.entries(JSON.parse(streamLabel.dataset.streams))
        .map(([name, url]) => ({ name, url }))
    : [];

// Default input maps
const CONTROLS = [
    { button: 'A_BUTTON', key_default: 'KeyF', gamepad_default: 0 },
    { button: 'B_BUTTON', key_default: 'KeyG', gamepad_default: 1 },
    { button: 'X_BUTTON', key_default: 'KeyR', gamepad_default: 2 },
    { button: 'Y_BUTTON', key_default: 'KeyT', gamepad_default: 3 },
    { button: 'LEFT_TRIGGER', key_default: 'Digit1', gamepad_default: 6 },
    { button: 'RIGHT_TRIGGER', key_default: 'Digit3', gamepad_default: 7 },
    { button: 'DPAD_UP', key_default: 'KeyW', gamepad_default: 12 },
    { button: 'DPAD_DOWN', key_default: 'KeyS', gamepad_default: 13 },
    { button: 'DPAD_LEFT', key_default: 'KeyA', gamepad_default: 14 },
    { button: 'DPAD_RIGHT', key_default: 'KeyD', gamepad_default: 15 },
    { button: 'SELECT_UP', key_default: 'KeyE', gamepad_default: 9 },
    { button: 'SELECT_DOWN', key_default: 'KeyQ', gamepad_default: 8 },
    { button: 'CAM_NEXT', key_default: 'Period', gamepad_default: 5 },
    { button: 'CAM_PREV', key_default: 'Comma', gamepad_default: 4 },
];

// Save client settings
function saveSettings() {
    const mappings = {};
    CONTROLS.forEach(({ button }) => {
        mappings[button] = {
            keyboard: document.getElementById(`map_kb_${button}`).value,
            gamepad: document.getElementById(`map_gp_${button}`).value,
        };
    });
    localStorage.setItem('playerSettings', JSON.stringify({
        playerName:  playerNameInput.value,
        inputDevice: inputDeviceSelect.value,
        mappings,
    }));
    // Send these settings to the server
    emitControllerEvent('UPDATE', true);
}

// Load client settings
function loadSettings() {
    const saved = localStorage.getItem('playerSettings');
    if (!saved) return;
    const settings = JSON.parse(saved);

    if (settings.playerName) {
        playerNameInput.value = settings.playerName;
    }
    if (settings.inputDevice) {
        inputDeviceSelect.value = settings.inputDevice;
    }
    if (settings.mappings) {
        CONTROLS.forEach(control => {
            if (settings.mappings[control.button]) {
                document.getElementById(`map_kb_${control.button}`).value = settings.mappings[control.button].keyboard;
                document.getElementById(`map_gp_${control.button}`).value = settings.mappings[control.button].gamepad;
            }
        });
    }
}

function openSettings() {
    settingsWindow.classList.remove('hidden');
}

function closeSettings() {
    settingsWindow.classList.add('hidden');
}

/**
 * Update settings window with current input state
 * @param {string} button - Button identifier
 * @param {boolean} pressed - Button state
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

    players.forEach((player) => {
        const fragment = playerTemplate.content.cloneNode(true);

        fragment.querySelector('[data-player-name]').textContent = player.player_name;
        fragment.querySelector('[data-selection]').textContent = player.selection;
        fragment.querySelector('[data-vehicle-name]').textContent = player.selection_name;

        playersElement.appendChild(fragment);
    });
}

let streamIndex = 0;

// Update video stream source
function updateStream(url) {
    const iframe = document.getElementById('stream-iframe');
    if (iframe) iframe.src = url;
}

// Cycle through streams
function cycleStream(direction) {
    if (!STREAMS.length) return;
    streamIndex = (streamIndex + direction + STREAMS.length) % STREAMS.length;
    streamLabel.textContent = STREAMS[streamIndex].name;
    updateStream(STREAMS[streamIndex].url);
}

/**
 * Send a controller event to the server
 * @param {string} button - Button identifier
 * @param {boolean} pressed - Button state
 */
function emitControllerEvent(button, pressed) {
    socket.emit('controller', {button, pressed, player_name: playerNameInput.value,});
}

/** @type {boolean[]} - Previous gamepad button states for change detection */
let lastGamepadButtons = [];

// Handle gamepad input
function pollGamepad() {
    if (inputDeviceSelect.value !== 'gamepad') return;

    // Get first connected gamepad
    const gamepad = navigator.getGamepads()[0];
    if (!gamepad) return;

    gamepad.buttons.forEach((btn, index) => {
        if (btn.pressed === lastGamepadButtons[index]) return;

        const control = CONTROLS.find(c => 
                Number(document.getElementById(`map_gp_${c.button}`).value) === index
        );

        renderInput(index, btn.pressed);

        if (control) {
            if (control.button === 'CAM_NEXT' && btn.pressed) cycleStream(1);
            if (control.button === 'CAM_PREV' && btn.pressed) cycleStream(-1);
            
            // Don't send input events if settings window is open
            if (!settingsWindow.classList.contains('hidden')) return;
            
            emitControllerEvent(control.button, btn.pressed);
        }
    });

    // Store state for next comparison
    lastGamepadButtons = gamepad.buttons.map(b => b.pressed);
}

/** @type {Object.<string, boolean>} - Current keyboard key states */
const keyboardState = {};

// Handle keyboard key press
function handleKeydown(e) {
    // Make sure key isn't already held
    if (inputDeviceSelect.value !== 'keyboard' || keyboardState[e.code]) return;

    const control = CONTROLS.find(c => 
            document.getElementById(`map_kb_${c.button}`).value === e.code
    );

    keyboardState[e.code] = true;
    renderInput(e.code, true);

    if (!control) return;
    if (control.button === 'CAM_NEXT') cycleStream(1);
    if (control.button === 'CAM_PREV') cycleStream(-1);

    // Don't send input events if settings window is open
    if (!settingsWindow.classList.contains('hidden')) return;
    
    emitControllerEvent(control.button, true);
}

// Handle keyboard key release
function handleKeyup(e) {
    // Only process if keyboard is selected
    if (inputDeviceSelect.value !== 'keyboard') return;

    const control = CONTROLS.find(
        c => document.getElementById(`map_kb_${c.button}`).value === e.code
    );

    keyboardState[e.code] = false;
    renderInput(e.code, false);

    // Don't send input events if settings window is open
    if (!settingsWindow.classList.contains('hidden')) return;

    if (control) emitControllerEvent(control.button, false);
}

// Panel dragging functionality
function initDrag() {
    let isDragging = false;
    let offsetX = 0;
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
}

function initUI() {
    // Build the control mapping table and fields
    CONTROLS.forEach(({ button, key_default, gamepad_default }) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${button}</td>
            <td><input id="map_kb_${button}" class="map-key" size="6" value="${key_default}"></td>
            <td><input id="map_gp_${button}" class="map-btn" size="1"  value="${gamepad_default}"></td>
        `;
        mappingBody.appendChild(row);
    });

    // Event listeners
    openSettingsButton.addEventListener('click', openSettings);
    saveSettingsButton.addEventListener('click', () => {
        saveSettings();
        closeSettings();
    });
    cancelSettingsButton.addEventListener('click', closeSettings);

    settingsWindow.addEventListener('click', (e) => {
        if (e.target === settingsWindow) closeSettings();
    });

    initDrag();
}

function init() {
    initUI();

    loadSettings();

    window.addEventListener('keydown', handleKeydown);
    window.addEventListener('keyup', handleKeyup);

    socket.on('players', ({ players }) => renderPlayers(players));

    if (STREAMS.length) updateStream(STREAMS[0].url);

    emitControllerEvent('UPDATE', true);

    const loop = () => { pollGamepad(); requestAnimationFrame(loop); };
    socket.on('connect', loop);
}

document.addEventListener('DOMContentLoaded', init);

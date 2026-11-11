const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socket = new WebSocket(`${protocol}//${window.location.host}/ws`);

// Main floating panel
const panel = document.querySelector('.floating-panel');
const openSettingsButton = document.getElementById('open-settings');
const playersElement = document.getElementById('players');
const playerTemplate = document.getElementById('player-template');

// Settings window
const settingsWindow = document.getElementById('settings-window');

const playerNameInput = document.getElementById('player_name');
const inputDeviceSelect = document.getElementById('input_device');
const videoToggleInputs = document.querySelectorAll('input[name="video_toggle"]');

const inputElement = document.getElementById('input');
const inputTemplate = document.getElementById('input-template');
const mappingBody = document.getElementById('mapping-body');
const buttonFeedbackElement = document.getElementById('button-feedback');
const saveSettingsButton = document.getElementById('save-settings');
const cancelSettingsButton = document.getElementById('cancel-settings');
const defaultSettingsButton = document.getElementById('default-settings');

let videoToggle = true;
let currentPlayerId = null;

/**
 * Get the streams if the HTML elements exist
 * @type {Array<{name: string, url: string}>}
 */
const streamLabel = document.getElementById('stream-label');
const STREAMS = streamLabel ? Object.entries(JSON.parse(streamLabel.dataset.streams)).map(([ name, url ]) => ({name, url})) : [];

/**
 * Default input maps
 * @type {Array<{button: string, key_default: string, gamepad_default: number}>}
 */
const CONTROLS = [
    {button : 'A_BUTTON', key_default : 'KeyF', gamepad_default : 0},
    {button : 'B_BUTTON', key_default : 'KeyG', gamepad_default : 1},
    {button : 'X_BUTTON', key_default : 'KeyR', gamepad_default : 2},
    {button : 'Y_BUTTON', key_default : 'KeyT', gamepad_default : 3},
    {button : 'LEFT_TRIGGER', key_default : 'Digit1', gamepad_default : 6},
    {button : 'RIGHT_TRIGGER', key_default : 'Digit3', gamepad_default : 7},
    {button : 'DPAD_UP', key_default : 'KeyW', gamepad_default : 12},
    {button : 'DPAD_DOWN', key_default : 'KeyS', gamepad_default : 13},
    {button : 'DPAD_LEFT', key_default : 'KeyA', gamepad_default : 14},
    {button : 'DPAD_RIGHT', key_default : 'KeyD', gamepad_default : 15},
    {button : 'SELECT_UP', key_default : 'KeyE', gamepad_default : 9},
    {button : 'SELECT_DOWN', key_default : 'KeyQ', gamepad_default : 8},
    {button : 'CAM_NEXT', key_default : 'Period', gamepad_default : 5},
    {button : 'CAM_PREV', key_default : 'Comma', gamepad_default : 4},
];

// Save client settings
function saveSettings()
{
    const mappings = {};
    CONTROLS.forEach(({button}) => {
        mappings[button] = {
            keyboard : getButtonMap(button, 'keyboard'),
            gamepad : getButtonMap(button, 'gamepad'),
        };
    });
    const saved = localStorage.getItem('playerSettings');
    const settings = saved ? JSON.parse(saved) : {};
    localStorage.setItem('playerSettings', JSON.stringify({
        ...settings,
        playerName : playerNameInput.value,
        inputDevice : inputDeviceSelect.value,
        mappings,
    }));
    // Send these settings to the server
    emitInputEvent('UPDATE', true);
}

// Load client settings
function loadSettings()
{
    const saved = localStorage.getItem('playerSettings');
    const settings = saved ? JSON.parse(saved) : {};

    if (settings.playerName)
    {
        playerNameInput.value = settings.playerName;
    }
    if (settings.inputDevice)
    {
        inputDeviceSelect.value = settings.inputDevice;
    }
    if (settings.mappings)
    {
        CONTROLS.forEach(control => {
            if (settings.mappings[control.button])
            {
                setButtonMap(control.button, 'keyboard', settings.mappings[control.button].keyboard);
                setButtonMap(control.button, 'gamepad', settings.mappings[control.button].gamepad);
                getButtonMap(control.button);
            }
        });
    }
    if (settings.videoToggle !== undefined)
    {
        videoToggle = settings.videoToggle;
        videoToggleInputs.forEach(input => { input.checked = input.value === (videoToggle ? 'on' : 'off'); });
    }
}

function openSettings()
{
    settingsWindow.classList.remove('hidden');
}

function closeSettings()
{
    settingsWindow.classList.add('hidden');
}

/**
 * Update the text content and visibility of the button feedback element
 * @param {string} message - The feedback message to display
 */
function updateButtonFeedback(message)
{
    if (buttonFeedbackElement)
    {
        buttonFeedbackElement.textContent = message;
        buttonFeedbackElement.parentElement.style.visibility = message ? 'visible' : 'hidden';
    }
}

// Clear button feedback
function clearButtonFeedback()
{
    updateButtonFeedback('');
}

/**
 * // Update or clear button feedback based on input device
 * @param {string} value - The button mapping value
 * @param {string} [device] - The target input device ('keyboard' or 'gamepad')
 */
function getButtonFeedback(value, device)
{
    if (!value || (device && device !== inputDeviceSelect.value))
    {
        clearButtonFeedback();
        return;
    }
    updateButtonFeedback(value);
}

/**
 * Get the mapping for a button and device
 * @param {string} button - Button identifier
 * @param {string} [device] - 'keyboard' or 'gamepad'
 * @returns {string} The mapping value
 */
function getButtonMap(button, device)
{
    const mapEl = document.getElementById(`map_${button}`);
    if (!mapEl)
        return '';
    device = device || inputDeviceSelect.value;
    return device === 'keyboard' ? mapEl.dataset.kb : mapEl.dataset.gp;
}

/**
 * Set the mapping value for a button and device.
 * @param {string} button - Button identifier
 * @param {string} device - 'keyboard' or 'gamepad'
 * @param {string} value - The mapping value
 * @returns {string|void}
 */
function setButtonMap(button, device, value)
{
    const mapEl = document.getElementById(`map_${button}`);
    if (!mapEl)
        return '';
    const key = device === 'keyboard' ? 'kb' : 'gp';
    mapEl.dataset[key] = value;
    if (inputDeviceSelect.value === device)
        mapEl.textContent = value;
}

/**
 * Player data from the server
 * @typedef {Object} PlayerData
 * @property {number} player_id - Unique player identifier
 * @property {string} player_name - Player name
 * @property {number} selection - Selected vehicle ID
 * @property {string} selection_name - Selected vehicle name
 */

/**
 * Renders list of connected players
 * @param {PlayerData[]} players - Array of player data
 */
function renderPlayers(players)
{
    playersElement.replaceChildren();

    const sortedPlayers = [...players ].sort((a, b) => {
        if (a.player_id === currentPlayerId)
            return -1;
        if (b.player_id === currentPlayerId)
            return 1;
        return 0;
    });

    sortedPlayers.forEach((player) => {
        const fragment = playerTemplate.content.cloneNode(true);

        fragment.querySelector('[data-player-name-label]').textContent =
            player.player_id === currentPlayerId ? 'Your Name:' : 'Player Name:';

        fragment.querySelector('[data-player-name]').textContent = player.player_name;
        fragment.querySelector('[data-selection]').textContent = player.selection;
        fragment.querySelector('[data-vehicle-name]').textContent = player.selection_name;

        playersElement.appendChild(fragment);
    });
}

let streamIndex = 0;

// Update video stream source
function updateStream(url)
{
    const iframe = document.getElementById('stream-iframe');
    if (iframe && videoToggle)
        iframe.src = url;
}

// Toggle video stream
function toggleVideo()
{
    const iframe = document.getElementById('stream-iframe');
    if (!iframe)
        return;

    if (videoToggle && STREAMS.length)
    {
        iframe.src = STREAMS[streamIndex].url;
        if (streamLabel)
            streamLabel.textContent = STREAMS[streamIndex].name;
    }
    else
    {
        iframe.src = '';
        if (streamLabel)
            streamLabel.textContent = 'Video Disabled';
    }
}

/**
 * Cycle through streams
 * @param {number} direction - Direction step value (e.g., 1 or -1)
 */
function cycleStream(direction)
{
    if (!STREAMS.length || !videoToggle)
        return;
    streamIndex = (streamIndex + direction + STREAMS.length) % STREAMS.length;
    streamLabel.textContent = STREAMS[streamIndex].name;
    updateStream(STREAMS[streamIndex].url);
}

/**
 * Send an input event to the server
 * @param {string} button - Button identifier
 * @param {boolean} pressed - Button state
 */
function emitInputEvent(button, pressed)
{
    if (socket.readyState === WebSocket.OPEN)
    {
        socket.send(JSON.stringify({button, pressed, player_name : playerNameInput.value}));
    }
}

/** @type {boolean[]} - Previous gamepad button states for change detection */
let lastGamepadButtons = [];

/**
 * Holds a new desired button map while in the settings window along with the element and its previous text
 * @type {{button: string, device: 'keyboard'|'gamepad', btn: HTMLElement, prevText: string} | null}
 */
let newButtonMap = null;

// Clear the pending button map
function clearButtonMap()
{
    if (newButtonMap)
    {
        newButtonMap.btn.textContent = newButtonMap.prevText;
        newButtonMap = null;
    }
}

/**
 * Checks if the new mapping for targetButton is already in use elsewhere.
 * If it is, the function clears the mapping on all conflicting buttons.
 * @param {string} targetButton - The button in the process of being mapped
 * @param {string} device - 'keyboard' or 'gamepad'
 * @param {string} value - The key code or button index value
 */
function resolveMappingConflicts(targetButton, device, value)
{
    CONTROLS.forEach(control => {
        if (control.button !== targetButton) // Don't evaluate for the targetButton
        {
            if (getButtonMap(control.button, device) === value) // Check for conflict
            {
                setButtonMap(control.button, device, ''); // Clear mapping on detected conflict
            }
        }
    });
}

// Handle gamepad input
function pollGamepad()
{
    if (inputDeviceSelect.value !== 'gamepad')
        return;

    // Get first connected gamepad
    const gamepad = navigator.getGamepads()[0];
    if (!gamepad)
        return;

    // Store the latest buttonpress if changing a setting
    if (newButtonMap && newButtonMap.device === 'gamepad')
    {
        gamepad.buttons.forEach((btn, index) => {
            if (btn.pressed && !lastGamepadButtons[index])
            {
                resolveMappingConflicts(newButtonMap.button, 'gamepad', String(index));
                setButtonMap(newButtonMap.button, 'gamepad', String(index));
                const btnEl = document.getElementById(`set_${newButtonMap.button}`);
                if (btnEl)
                    btnEl.textContent = 'Set';
                newButtonMap = null;
            }
        });
        return;
    }

    // Update button feedback
    const pressedIndex = gamepad.buttons.findIndex((btn, index) => btn.pressed && !lastGamepadButtons[index]);
    if (pressedIndex >= 0)
    {
        getButtonFeedback(String(pressedIndex), 'gamepad');
    }
    else if (!gamepad.buttons.some((btn) => btn.pressed))
    {
        clearButtonFeedback();
    }

    gamepad.buttons.forEach((btn, index) => {
        if (btn.pressed === lastGamepadButtons[index])
            return;

        const control = CONTROLS.find(c => Number(getButtonMap(c.button, 'gamepad')) === index);

        if (control)
        {
            if (control.button === 'CAM_NEXT' && btn.pressed)
                cycleStream(1);
            if (control.button === 'CAM_PREV' && btn.pressed)
                cycleStream(-1);

            // Don't send input events if settings window is open
            if (!settingsWindow.classList.contains('hidden'))
                return;

            emitInputEvent(control.button, btn.pressed);
        }
    });

    // Store state for next comparison
    lastGamepadButtons = gamepad.buttons.map(b => b.pressed);
}

/** @type {Object.<string, boolean>} - Current keyboard key states */
const keyboardState = {};

/**
 * Handle keyboard key press
 * @param {KeyboardEvent} e - Keyboard event object
 */
function handleKeydown(e)
{

    // Store the latest keypress if changing a setting
    if (newButtonMap && newButtonMap.device === 'keyboard')
    {
        resolveMappingConflicts(newButtonMap.button, 'keyboard', e.code);
        setButtonMap(newButtonMap.button, 'keyboard', e.code);
        const btnEl = document.getElementById(`set_${newButtonMap.button}`);
        if (btnEl)
            btnEl.textContent = 'Set';
        newButtonMap = null;
        e.preventDefault();
        return;
    }

    // Show pressed button feedback
    if (inputDeviceSelect.value === 'keyboard' && !settingsWindow.classList.contains('hidden'))
    {
        getButtonFeedback(e.code, 'keyboard');
    }

    // Make sure key isn't already held
    if (inputDeviceSelect.value !== 'keyboard' || keyboardState[e.code])
        return;

    const control = CONTROLS.find(c => getButtonMap(c.button, 'keyboard') === e.code);

    keyboardState[e.code] = true;

    if (!control)
        return;
    if (control.button === 'CAM_NEXT')
        cycleStream(1);
    if (control.button === 'CAM_PREV')
        cycleStream(-1);

    // Don't send input events if settings window is open
    if (!settingsWindow.classList.contains('hidden'))
        return;

    emitInputEvent(control.button, true);
}

/**
 * Handle keyboard key release
 * @param {KeyboardEvent} e - Keyboard event object
 */
function handleKeyup(e)
{
    // Only process if keyboard is selected
    if (inputDeviceSelect.value !== 'keyboard')
        return;

    const control = CONTROLS.find(c => getButtonMap(c.button, 'keyboard') === e.code);

    keyboardState[e.code] = false;

    // Clear released button feedback
    if (inputDeviceSelect.value === 'keyboard' && !settingsWindow.classList.contains('hidden'))
    {
        clearButtonFeedback();
    }

    // Don't send input events if settings window is open
    if (!settingsWindow.classList.contains('hidden'))
        return;

    if (control)
        emitInputEvent(control.button, false);
}

// Panel dragging functionality
function initDrag()
{
    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;

    // Grab panel
    panel.addEventListener('mousedown', (e) => {
        // Don't initiate drag if clicking on interactive elements
        if (e.target.closest('input, select, button, textarea'))
            return;

        isDragging = true;
        offsetX = e.clientX - panel.offsetLeft;
        offsetY = e.clientY - panel.offsetTop;
        document.body.style.userSelect = 'none'; // Prevent text selection during drag
    });

    // Update panel position
    document.addEventListener('mousemove', (e) => {
        if (!isDragging)
            return;
        panel.style.left = `${e.clientX - offsetX}px`;
        panel.style.top = `${e.clientY - offsetY}px`;
    });

    // Release panel
    document.addEventListener('mouseup', () => {
        isDragging = false;
        document.body.style.userSelect = ''; // Re-enable text selection
    });
}

function initUI()
{
    // Build the control mapping table and fields in two columns
    for (let i = 0; i < CONTROLS.length; i += 2)
    {
        const first = CONTROLS[i];
        const second = CONTROLS[i + 1];
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${first.button}</td>
            <td><span id="map_${first.button}" data-kb="${first.key_default}" data-gp="${first.gamepad_default}">${
            inputDeviceSelect.value === 'keyboard' ? first.key_default : first.gamepad_default}</span></td>
            <td><button id="set_${first.button}">Set</button></td>
            <td>${second ? second.button : ''}</td>
            <td>${
            second ? `<span id="map_${second.button}" data-kb="${second.key_default}" data-gp="${second.gamepad_default}">${
                         inputDeviceSelect.value === 'keyboard' ? second.key_default : second.gamepad_default}</span>`
                   : ''}</td>
            <td>${second ? `<button id="set_${second.button}">Set</button>` : ''}</td>
        `;
        mappingBody.appendChild(row);
    }

    loadSettings();
    toggleVideo();

    // Event listeners
    openSettingsButton.addEventListener('click', openSettings);

    saveSettingsButton.addEventListener('click', () => {
        saveSettings();
        clearButtonMap();
        closeSettings();
    });

    cancelSettingsButton.addEventListener('click', () => {
        clearButtonMap();
        loadSettings();
        closeSettings();
    });

    defaultSettingsButton.addEventListener('click', () => {
        clearButtonMap();
        CONTROLS.forEach(control => {
            setButtonMap(control.button, 'keyboard', control.key_default);
            setButtonMap(control.button, 'gamepad', control.gamepad_default);
        });
    });

    // Add event listeners to each set button
    CONTROLS.forEach(({button}) => {
        const setBtn = document.getElementById(`set_${button}`);
        if (!setBtn)
            return;
        setBtn.addEventListener('click', (e) => {
            clearButtonMap();
            const btn = e.currentTarget;
            const prevText = btn.textContent;
            btn.textContent = 'Waiting...';
            newButtonMap = {button, btn, prevText, device : inputDeviceSelect.value};
        });
    });

    // Load new settings on input device selection
    inputDeviceSelect.addEventListener('change', () => {
        saveSettings();
        loadSettings();
        clearButtonFeedback();
    });

    videoToggleInputs.forEach(input => {
        input.addEventListener('change', () => {
            const value = input.value === 'on';
            videoToggle = value;
            const saved = localStorage.getItem('playerSettings');
            const settings = saved ? JSON.parse(saved) : {};
            localStorage.setItem('playerSettings', JSON.stringify({
                ...settings,
                videoToggle : value,
            }));
            toggleVideo();
        });
    });

    initDrag();
}

function init()
{
    initUI();

    window.addEventListener('keydown', handleKeydown);
    window.addEventListener('keyup', handleKeyup);

    // Release all keyboard controls when focus is lost
    window.addEventListener('blur', () => {
        if (inputDeviceSelect.value === 'keyboard')
        {
            Object.entries(keyboardState).forEach(([ code, isPressed ]) => {
                if (isPressed)
                {
                    const control = CONTROLS.find(c => getButtonMap(c.button, 'keyboard') === code);
                    if (control)
                    {
                        emitInputEvent(control.button, false);
                    }
                    keyboardState[code] = false;
                }
            });
        }
    });

    // Release all gamepad controls when the window is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && inputDeviceSelect.value === 'gamepad')
        {
            lastGamepadButtons.forEach((isPressed, index) => {
                if (isPressed)
                {
                    const control = CONTROLS.find(c => Number(getButtonMap(c.button, 'gamepad')) === index);
                    if (control)
                    {
                        emitInputEvent(control.button, false);
                    }
                }
            });
        }
    });

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.player_id !== undefined)
        {
            currentPlayerId = message.player_id;
        }

        if (message.players)
        {
            renderPlayers(message.players);
        }
    };

    if (STREAMS.length)
        updateStream(STREAMS[0].url);

    socket.onopen = () => {
        emitInputEvent('UPDATE', true);
        const loop = () => {
            pollGamepad();
            requestAnimationFrame(loop);
        };
        loop();
    };
}

document.addEventListener('DOMContentLoaded', init);

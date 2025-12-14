const output = document.getElementById('output');
const socket = io();

let lastButtonState = [];

function update() {
    const gp = navigator.getGamepads()[0];
    if (gp) {
        const buttons = gp.buttons.map(b => b.pressed);
        
        for (let i = 0; i < buttons.length; i++) {
            if (buttons[i] !== lastButtonState[i]) {
                gamepadIndex = document.getElementById('gamepad-index').value
                const data = {
                    controller: parseInt(gamepadIndex),
                    button: i,
                    pressed: buttons[i]
                };
                socket.emit('gamepad', data);
                output.textContent = JSON.stringify(data, null, 2);
            }
        }
        lastButtonState = buttons;
    }
    requestAnimationFrame(update);
}

socket.on('connect', () => {
    update();
});

async function sendCommand(action) {
    const controller = document.getElementById('controller').value;
    const button = document.getElementById('button').value;

    await fetch(`/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ controller: parseInt(controller), button: parseInt(button) })
    });
}

async function editSelection() {
    const controller = document.getElementById('edit-controller').value;
    const selection = document.getElementById('selection').value;

    await fetch('/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ controller: parseInt(controller), selection: parseInt(selection) })
    });
}

async function toggleController(action) {
    const controller = document.getElementById('enable-controller').value;

    await fetch(`/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ controller: parseInt(controller) })
    });
}

async function resetPort() {
    await fetch(`/reset`, {
        method: 'POST',
    });
}

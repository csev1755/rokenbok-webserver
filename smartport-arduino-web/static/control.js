const output = document.getElementById('output');
const socket = io();

let lastButtonState = [];

function update() {
    const gp = navigator.getGamepads()[0];
    if (gp) {
        const buttons = gp.buttons.map(b => b.pressed);
        
        for (let i = 0; i < buttons.length; i++) {
            if (buttons[i] !== lastButtonState[i]) {
                gamepadIndex = document.getElementById('gamepad_index').value
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

async function sendCommand(action, controller = 0, value = 0) {
    await fetch(`/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ controller: parseInt(controller), value: parseInt(value) })
    });
}

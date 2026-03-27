// input.js — Keyboard input handler

const Input = (() => {
    const keys = {};

    function init() {
        window.addEventListener('keydown', (e) => {
            keys[e.key] = true;
            // Prevent scrolling with arrow keys / space
            if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(e.key)) {
                e.preventDefault();
            }
        });
        window.addEventListener('keyup', (e) => {
            keys[e.key] = false;
        });
    }

    function isDown(key) {
        return !!keys[key];
    }

    // Check movement direction. Returns {dx, dy, dir} or null if no movement.
    // dir: 0=down, 1=up, 2=left, 3=right
    function getMovement() {
        let dx = 0, dy = 0, dir = null;

        if (isDown('ArrowUp') || isDown('w') || isDown('W')) {
            dy = -1; dir = 1;
        } else if (isDown('ArrowDown') || isDown('s') || isDown('S')) {
            dy = 1; dir = 0;
        }

        if (isDown('ArrowLeft') || isDown('a') || isDown('A')) {
            dx = -1; dir = 2;
        } else if (isDown('ArrowRight') || isDown('d') || isDown('D')) {
            dx = 1; dir = 3;
        }

        if (dx === 0 && dy === 0) return null;
        return { dx, dy, dir };
    }

    function isActionPressed() {
        return isDown(' ') || isDown('Enter') || isDown('z') || isDown('Z');
    }

    return { init, isDown, getMovement, isActionPressed };
})();

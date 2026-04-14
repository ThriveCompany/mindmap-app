let currentGame = null;
let messageHistory = [];

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) {
        return;
    }

    initializeGame();
});

function initializeGame() {
    const minRangeInput = document.getElementById('min-range');
    const maxRangeInput = document.getElementById('max-range');
    const userNumberInput = document.getElementById('user-number');
    const guessInput = document.getElementById('guess-input');

    [minRangeInput, maxRangeInput, userNumberInput].forEach((input) => {
        input.addEventListener('input', syncSetupInputs);
    });

    guessInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            submitGuess();
        }
    });

    syncSetupInputs();
    renderMessages();
    updateSuggestions(1, 100);
    updateHelper(1, 100);
}

function syncSetupInputs() {
    const minRange = Number.parseInt(document.getElementById('min-range').value, 10);
    const maxRange = Number.parseInt(document.getElementById('max-range').value, 10);
    const userNumberInput = document.getElementById('user-number');
    const setupHelper = document.getElementById('setup-helper');

    if (Number.isInteger(minRange)) {
        userNumberInput.min = String(minRange);
        document.getElementById('max-range').min = String(minRange + 1);
    }

    if (Number.isInteger(maxRange)) {
        userNumberInput.max = String(maxRange);
    }

    if (!Number.isInteger(minRange) || !Number.isInteger(maxRange) || minRange >= maxRange) {
        setupHelper.textContent = 'Set a valid minimum and maximum range to begin.';
        return;
    }

    const totalNumbers = maxRange - minRange + 1;
    setupHelper.textContent = `Choose a number between ${minRange} and ${maxRange}. That gives you ${totalNumbers} possible values to work with.`;
}

function showPanelMessage(elementId, message, variant = 'error') {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.classList.remove('hidden', 'error', 'success');
    element.classList.add(variant);
}

function hidePanelMessage(elementId) {
    const element = document.getElementById(elementId);
    element.textContent = '';
    element.classList.add('hidden');
}

function setButtonState(buttonId, disabled) {
    const button = document.getElementById(buttonId);
    if (!button) {
        return;
    }
    button.disabled = disabled;
}

function backToDashboard() {
    window.location.href = 'dashboard.html';
}

async function startGame() {
    hidePanelMessage('setup-feedback');

    const minRange = Number.parseInt(document.getElementById('min-range').value, 10);
    const maxRange = Number.parseInt(document.getElementById('max-range').value, 10);
    const userNumber = Number.parseInt(document.getElementById('user-number').value, 10);

    if (!Number.isInteger(minRange) || !Number.isInteger(maxRange) || minRange >= maxRange) {
        showPanelMessage('setup-feedback', 'Choose a valid minimum and maximum range before starting.');
        return;
    }

    if (!Number.isInteger(userNumber) || userNumber < minRange || userNumber > maxRange) {
        showPanelMessage('setup-feedback', `Your secret number must stay between ${minRange} and ${maxRange}.`);
        return;
    }

    setButtonState('start-game-btn', true);

    try {
        const response = await authFetch('/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                min_range: minRange,
                max_range: maxRange,
                user_number: userNumber,
            }),
        });

        if (!response.ok) {
            showPanelMessage('setup-feedback', await getErrorMessage(response, 'Failed to start the game.'));
            return;
        }

        currentGame = await response.json();
        messageHistory = [...(currentGame.messages || [])];
        showGameUI(currentGame);
    } catch (error) {
        showPanelMessage('setup-feedback', error.message || 'Error starting the game.');
    } finally {
        setButtonState('start-game-btn', false);
    }
}

function showGameUI(game) {
    document.getElementById('setup-card').classList.add('hidden');
    document.getElementById('game-ui').classList.remove('hidden');
    document.getElementById('guess-input').value = '';
    hidePanelMessage('game-feedback');
    renderGameState(game);
}

function renderGameState(game) {
    updateRange(game.current_min, game.current_max);
    updateHelper(game.current_min, game.current_max);
    updateSuggestions(game.current_min, game.current_max);
    renderMessages();

    const isActive = game.status === 'active';
    document.getElementById('guess-input').disabled = !isActive;
    setButtonState('submit-guess-btn', !isActive);
}

function updateRange(min, max) {
    document.getElementById('current-range').textContent = `${min} – ${max}`;
    const guessInput = document.getElementById('guess-input');
    guessInput.min = String(min);
    guessInput.max = String(max);
    guessInput.placeholder = `Enter a guess between ${min} and ${max}`;
}

function renderMessages() {
    const chat = document.getElementById('chat-messages');
    chat.innerHTML = '';

    if (messageHistory.length === 0) {
        const placeholder = document.createElement('div');
        placeholder.className = 'message system';
        placeholder.textContent = '[System] Your move log will appear here once the match begins.';
        chat.appendChild(placeholder);
        return;
    }

    messageHistory.forEach((message) => {
        const row = document.createElement('div');
        row.className = 'message system';
        row.textContent = `[System] ${message}`;
        chat.appendChild(row);
    });

    chat.scrollTop = chat.scrollHeight;
}

function appendMessages(messages) {
    if (!Array.isArray(messages) || messages.length === 0) {
        return;
    }

    messageHistory.push(...messages);
    renderMessages();
}

function updateSuggestions(min, max) {
    const suggestionsDiv = document.getElementById('suggestions');
    const buttonsDiv = document.getElementById('suggestion-buttons');
    const remaining = max - min + 1;

    if (remaining <= 10) {
        suggestionsDiv.style.display = 'block';
        buttonsDiv.innerHTML = '';

        for (let guess = min; guess <= max; guess += 1) {
            const button = document.createElement('button');
            button.className = 'suggestion-btn';
            button.type = 'button';
            button.textContent = String(guess);
            button.onclick = () => setGuess(guess);
            buttonsDiv.appendChild(button);
        }
        return;
    }

    suggestionsDiv.style.display = 'none';
    buttonsDiv.innerHTML = '';
}

function updateHelper(min, max) {
    const midpoint = Math.floor((min + max) / 2);
    const remaining = max - min + 1;

    document.getElementById('helper-text').textContent = `Midpoint suggestion: ${midpoint}`;
    document.getElementById('range-size-text').textContent = `${remaining} number${remaining === 1 ? '' : 's'} remaining in the valid range.`;
}

function setGuess(number) {
    document.getElementById('guess-input').value = String(number);
    hidePanelMessage('game-feedback');
}

async function submitGuess() {
    if (!currentGame || currentGame.status !== 'active') {
        return;
    }

    hidePanelMessage('game-feedback');

    const guess = Number.parseInt(document.getElementById('guess-input').value, 10);
    if (!Number.isInteger(guess) || guess < currentGame.current_min || guess > currentGame.current_max) {
        showPanelMessage('game-feedback', `Enter a valid guess between ${currentGame.current_min} and ${currentGame.current_max}.`);
        return;
    }

    setButtonState('submit-guess-btn', true);

    try {
        const response = await authFetch(`/games/${currentGame.id}/guess`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ guess }),
        });

        if (!response.ok) {
            showPanelMessage('game-feedback', await getErrorMessage(response, 'Failed to submit your guess.'));
            return;
        }

        currentGame = await response.json();
        appendMessages(currentGame.messages);
        document.getElementById('guess-input').value = '';
        renderGameState(currentGame);

        if (currentGame.status === 'won') {
            showPanelMessage('game-feedback', 'Correct guess. You won the match.', 'success');
            window.setTimeout(backToDashboard, 1800);
            return;
        }

        if (currentGame.status !== 'active') {
            showPanelMessage('game-feedback', 'This match has ended. Returning to the dashboard.', 'success');
            window.setTimeout(backToDashboard, 1800);
        }
    } catch (error) {
        showPanelMessage('game-feedback', error.message || 'Error submitting your guess.');
        renderGameState(currentGame);
    } finally {
        if (currentGame && currentGame.status === 'active') {
            setButtonState('submit-guess-btn', false);
        }
    }
}

function endGame() {
    backToDashboard();
}

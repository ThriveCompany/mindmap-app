document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeDashboard();
});

function initializeDashboard() {
    const userNameEl = document.getElementById('dashboard-username');
    const winsEl = document.getElementById('stat-wins');
    const lossesEl = document.getElementById('stat-losses');
    const gamesEl = document.getElementById('stat-games');
    const winRateEl = document.getElementById('stat-winrate');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('dashboard-content');

    const token = getToken();
    if (!token) {
        logout();
        return;
    }

    loadingState.classList.remove('hidden');
    mainContent.classList.add('hidden');
    emptyState.classList.add('hidden');

    fetch(`${API_BASE}/me`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    })
        .then(async (response) => {
            if (!response.ok) {
                throw new Error('Unable to load profile.');
            }
            return response.json();
        })
        .then((data) => {
            userNameEl.textContent = data.username || 'Player';
            const wins = Number(data.wins ?? 0);
            const losses = Number(data.losses ?? 0);
            const totalGames = Number(data.games_played ?? wins + losses);
            const winRate = totalGames > 0 ? Math.round((wins / totalGames) * 100) : 0;

            winsEl.textContent = wins;
            lossesEl.textContent = losses;
            gamesEl.textContent = totalGames;
            winRateEl.textContent = `${winRate}%`;

            if (totalGames === 0) {
                emptyState.classList.remove('hidden');
                mainContent.classList.add('hidden');
            } else {
                emptyState.classList.add('hidden');
                mainContent.classList.remove('hidden');
            }
        })
        .catch(() => {
            emptyState.querySelector('p').textContent = 'Unable to load your stats right now. Please try again later.';
            emptyState.classList.remove('hidden');
        })
        .finally(() => {
            loadingState.classList.add('hidden');
        });
}

function startGame() {
    window.location.href = 'game.html';
}

function practiceMode() {
    window.location.href = 'game.html?mode=practice';
}

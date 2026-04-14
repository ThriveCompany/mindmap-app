document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) {
        return;
    }
    initializeActionCards();
    initializeDashboard();
});

function initializeActionCards() {
    document.querySelectorAll('.action-card[role="button"]').forEach((card) => {
        card.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                card.click();
            }
        });
    });
}

async function initializeDashboard() {
    const userNameEl = document.getElementById('dashboard-username');
    const winsEl = document.getElementById('stat-wins');
    const lossesEl = document.getElementById('stat-losses');
    const gamesEl = document.getElementById('stat-games');
    const winRateEl = document.getElementById('stat-winrate');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('dashboard-content');
    const summaryEl = document.getElementById('dashboard-summary');

    const token = getToken();
    if (!token) {
        logout();
        return;
    }

    loadingState.classList.remove('hidden');
    mainContent.classList.add('hidden');
    emptyState.classList.add('hidden');

    try {
        const data = await fetchCurrentUser();
        const wins = Number(data.wins ?? 0);
        const losses = Number(data.losses ?? 0);
        const totalGames = Number(data.games_played ?? wins + losses);
        const winRate = totalGames > 0 ? Math.round((wins / totalGames) * 100) : 0;

        userNameEl.textContent = data.username || 'Player';
        winsEl.textContent = String(wins);
        lossesEl.textContent = String(losses);
        gamesEl.textContent = String(totalGames);
        winRateEl.textContent = `${winRate}%`;

        if (totalGames === 0) {
            emptyState.querySelector('p').textContent = 'No games yet. Start your first guided match and begin building your range strategy.';
            emptyState.classList.remove('hidden');
            summaryEl.textContent = 'Open a match, lock your number inside the chosen range, and use each response to narrow the interval with discipline.';
        } else {
            emptyState.classList.add('hidden');
            summaryEl.textContent = `You have played ${totalGames} match${totalGames === 1 ? '' : 'es'} with a ${winRate}% win rate. Keep focusing on shrinking the range every turn.`;
        }
    } catch (error) {
        emptyState.querySelector('p').textContent = error.message || 'Unable to load your stats right now. Please try again later.';
        emptyState.classList.remove('hidden');
        summaryEl.textContent = 'You can still start a guided match while we reconnect your profile data.';
    } finally {
        loadingState.classList.add('hidden');
        mainContent.classList.remove('hidden');
    }
}

function startGame() {
    window.location.href = 'game.html';
}

function scrollToStrategyTips() {
    document.getElementById('strategy-panel').scrollIntoView({
        behavior: 'smooth',
        block: 'start',
    });
}

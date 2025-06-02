document.addEventListener('DOMContentLoaded', () => {
    const gameBoardDiv = document.getElementById('game-board');
    const entityDetailsPanel = document.getElementById('entity-details-panel');
    const detailsContentDiv = document.getElementById('details-content');
    const nextTurnButton = document.getElementById('next-turn-btn');
    const turnInfoDiv = document.getElementById('turn-info');

    const API_BASE_URL = ''; // Assuming FastAPI runs on the same host/port
    const currentGameId = "default_game"; // Configuration for current game ID

    // Function to fetch and render board state
    async function fetchBoardState() {
        try {
            const response = await fetch(`${API_BASE_URL}/game/${currentGameId}/board`);
            if (!response.ok) {
                console.error('Failed to fetch board data:', response.status, await response.text());
                gameBoardDiv.innerHTML = '<p>Error loading board data. Check console.</p>';
                return;
            }
            const boardData = await response.json();
            renderBoard(boardData);
            updateTurnInfo(boardData.turn);
        } catch (error) {
            console.error('Error fetching board data:', error);
            gameBoardDiv.innerHTML = '<p>Error loading board data. Check console.</p>';
        }
    }

    // Function to render the board based on data from API
    function renderBoard(boardData) {
        gameBoardDiv.innerHTML = ''; // Clear previous board

        // Ensure boardData.board_width and boardData.board_height are available
        const boardWidth = boardData.board_width || 10; // Default if not provided
        const boardHeight = boardData.board_height || 10; // Default if not provided

        gameBoardDiv.style.gridTemplateColumns = `repeat(${boardWidth}, 30px)`;
        gameBoardDiv.style.gridTemplateRows = `repeat(${boardHeight}, 30px)`;
        // Optional: Set fixed size for the board container if entities are sparse
        // gameBoardDiv.style.width = `${boardWidth * 30}px`;
        // gameBoardDiv.style.height = `${boardHeight * 30}px`;

        const entitiesMap = new Map();
        // Ensure boardData.entities is an array
        if (Array.isArray(boardData.entities)) {
            boardData.entities.forEach(entity => {
                // Assuming entity has x and y, place it in a map for quick lookup
                entitiesMap.set(`${entity.x}-${entity.y}`, entity);
            });
        }

        for (let y = 0; y < boardHeight; y++) {
            for (let x = 0; x < boardWidth; x++) {
                const cellDiv = document.createElement('div');
                cellDiv.classList.add('cell');
                cellDiv.dataset.x = x;
                cellDiv.dataset.y = y;

                const entity = entitiesMap.get(`${x}-${y}`);
                if (entity) {
                    cellDiv.dataset.entityId = entity.id; // Store API ID
                    // Use entity.name for primary display, fallback to type's first char
                    cellDiv.textContent = entity.name ? entity.name.charAt(0).toUpperCase() : entity.type.charAt(0).toUpperCase();

                    // Add class for general type (unit/plant) and specific name (e.g., Predator, BasicPlant)
                    cellDiv.classList.add(entity.type.toLowerCase()); // "unit" or "plant"
                    if (entity.name) {
                         // Normalize name for CSS class: lowercase, remove spaces
                        cellDiv.classList.add(entity.name.toLowerCase().replace(/\s+/g, ''));
                    }

                    cellDiv.addEventListener('click', () => fetchEntityDetails(entity.id));
                }
                gameBoardDiv.appendChild(cellDiv);
            }
        }
    }

    // Function to fetch and display details of a specific entity
    async function fetchEntityDetails(entityId) {
        if (!entityId) {
            detailsContentDiv.innerHTML = 'No entity selected.';
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/game/${currentGameId}/entity/${entityId}`);
            if (!response.ok) {
                console.error('Failed to fetch entity data:', response.status, await response.text());
                detailsContentDiv.innerHTML = '<p>Error loading entity details. Check console.</p>';
                return;
            }
            const entityData = await response.json();
            displayEntityStats(entityData);
        } catch (error) {
            console.error('Error fetching entity data:', error);
            detailsContentDiv.innerHTML = '<p>Error loading entity details. Check console.</p>';
        }
    }

    // Function to display entity statistics in the details panel
    function displayEntityStats(entityData) {
        detailsContentDiv.innerHTML = ''; // Clear previous stats

        const ul = document.createElement('ul');
        for (const [key, value] of Object.entries(entityData)) {
            const li = document.createElement('li');
            let displayValue = value;
            if (value === null || value === undefined) {
                displayValue = 'N/A';
            } else if (Array.isArray(value)) {
                displayValue = value.join(', ');
            } else if (typeof value === 'object') {
                // For nested objects (like 'traits' if it's an object, though model makes it Set[str])
                // Simple stringify for now, could be more elaborate
                displayValue = JSON.stringify(value);
            }
            li.innerHTML = `<strong>${key.replace(/_/g, ' ')}:</strong> ${displayValue}`;
            ul.appendChild(li);
        }
        detailsContentDiv.appendChild(ul);
    }

    // Function to update the game state by one turn
    async function updateGame() {
        try {
            const response = await fetch(`${API_BASE_URL}/game/${currentGameId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add any other headers like CSRF tokens if needed by FastAPI setup
                },
                // body: JSON.stringify({}), // POST body if needed, not for this endpoint
            });
            if (!response.ok) {
                console.error('Failed to update game state:', response.status, await response.text());
                // Optionally, display an error message to the user on the page
                return;
            }
            const updatedBoardData = await response.json();
            renderBoard(updatedBoardData); // Re-render board with new state from POST response
            updateTurnInfo(updatedBoardData.turn);
            detailsContentDiv.innerHTML = 'Select an entity to see its details.'; // Clear details panel
        } catch (error) {
            console.error('Error updating game state:', error);
        }
    }

    function updateTurnInfo(turn) {
        if (turnInfoDiv) {
            turnInfoDiv.textContent = `Turn: ${turn}`;
        }
    }

    // Event listener for the "Next Turn" button
    if (nextTurnButton) {
        nextTurnButton.addEventListener('click', updateGame);
    }

    // Initial fetch of the board state when the page loads
    fetchBoardState();
});

document.addEventListener('DOMContentLoaded', () => {
    const gameBoardDiv = document.getElementById('game-board');
    const statsSidebarDiv = document.getElementById('stats-sidebar');
    const statsContentDiv = document.getElementById('stats-content');

    const API_BASE_URL = ''; // Assuming FastAPI runs on the same host/port

    async function fetchBoard() {
        try {
            const response = await fetch(`${API_BASE_URL}/board`);
            if (!response.ok) {
                console.error('Failed to fetch board data:', response.status, await response.text());
                gameBoardDiv.innerHTML = '<p>Error loading board data.</p>';
                return;
            }
            const boardData = await response.json();
            renderBoard(boardData);
        } catch (error) {
            console.error('Error fetching board data:', error);
            gameBoardDiv.innerHTML = '<p>Error loading board data.</p>';
        }
    }

    function renderBoard(boardData) {
        gameBoardDiv.innerHTML = ''; // Clear previous board
        gameBoardDiv.style.gridTemplateColumns = `repeat(${boardData.width}, 30px)`; // Adjust cell size as needed
        gameBoardDiv.style.gridTemplateRows = `repeat(${boardData.height}, 30px)`;
        gameBoardDiv.style.width = `${boardData.width * 30}px`; // Container width

        const entitiesMap = new Map();
        boardData.entities.forEach(entity => {
            entitiesMap.set(`${entity.x}-${entity.y}`, entity);
        });

        for (let y = 0; y < boardData.height; y++) {
            for (let x = 0; x < boardData.width; x++) {
                const cellDiv = document.createElement('div');
                cellDiv.classList.add('cell');
                cellDiv.dataset.x = x;
                cellDiv.dataset.y = y;

                const entity = entitiesMap.get(`${x}-${y}`);
                if (entity) {
                    cellDiv.dataset.entityId = entity.id;
                    console.log(`Rendered entity ${entity.id} at (${x},${y}) with type ${entity.type}`);
                    if (entity.type === 'unit') {
                        cellDiv.textContent = entity.unit_type ? entity.unit_type.charAt(0).toUpperCase() : 'U';
                        cellDiv.classList.add('unit');
                        if (entity.unit_type) {
                             cellDiv.classList.add(entity.unit_type.toLowerCase());
                        }
                    } else if (entity.type === 'plant') {
                        cellDiv.textContent = entity.symbol || 'P';
                        cellDiv.classList.add('plant');
                    }
                }
                cellDiv.addEventListener('click', handleCellClick);
                gameBoardDiv.appendChild(cellDiv);
            }
        }
    }

    async function handleCellClick(event) {
        console.log('handleCellClick triggered. Clicked target:', event.target, 'Listener on (currentTarget):', event.currentTarget);
        const cell = event.currentTarget; // The element the listener is attached to
        const entityId = cell.dataset.entityId;
        console.log('Retrieved entityId from cell dataset:', entityId);

        if (entityId) {
            try {
                const response = await fetch(`${API_BASE_URL}/entity/${entityId}`);
                console.log(`API call to /entity/${entityId} - Status: ${response.status}, OK: ${response.ok}`);
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`Failed to fetch entity data for ID ${entityId}:`, response.status, errorText);
                    statsContentDiv.innerHTML = `<p>Error loading entity data for ID ${entityId}. Status: ${response.status}</p>`;
                    showStatsSidebar();
                    return;
                }
                const entityData = await response.json();
                console.log('Successfully fetched entity data:', entityData);
                displayStats(entityData);
            } catch (error) {
                console.error(`Error during fetch or processing for entity ID ${entityId}:`, error);
                statsContentDiv.innerHTML = '<p>An error occurred while fetching entity data.</p>';
                showStatsSidebar();
            }
        } else {
            console.log('No entityId found on clicked cell. Hiding sidebar.');
            hideStatsSidebar();
        }
    }

    function displayStats(entityData) {
        console.log('Displaying stats for:', entityData);
        statsContentDiv.innerHTML = ''; // Clear previous stats

        const ul = document.createElement('ul');
        for (const [key, value] of Object.entries(entityData)) {
            const li = document.createElement('li');
            let displayValue = value;
            if (Array.isArray(value)) {
                displayValue = value.join(', ');
            } else if (typeof value === 'object' && value !== null) {
                displayValue = JSON.stringify(value);
            }
            li.innerHTML = `<strong>${key.replace(/_/g, ' ')}:</strong> ${displayValue}`;
            ul.appendChild(li);
        }
        statsContentDiv.appendChild(ul);
        showStatsSidebar();
    }

    function showStatsSidebar() {
        statsSidebarDiv.classList.remove('hidden');
    }

    function hideStatsSidebar() {
        statsSidebarDiv.classList.add('hidden');
    }

    // Initial fetch
    fetchBoard();
});

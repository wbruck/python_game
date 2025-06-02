// Global variables
const API_BASE_URL = ''; // Assuming FastAPI runs on the same host/port
let gameId = null;
let entityTypes = {
    units: [],
    plants: []
};

// Create inputs for entity counts
function createEntityCountInputs() {
    console.log('Creating entity count inputs with types:', entityTypes);
    const entityCountsDiv = document.getElementById('entity-counts');
    if (!entityCountsDiv) {
        console.error('Could not find entity-counts div');
        return;
    }
    console.log('Found entity-counts div:', entityCountsDiv);
    
    entityCountsDiv.innerHTML = ''; // Clear existing inputs

    // Add unit count inputs
    if (entityTypes.units && entityTypes.units.length > 0) {
        console.log('Adding unit inputs for types:', entityTypes.units);
        const unitGroup = document.createElement('div');
        unitGroup.innerHTML = '<h4>Units</h4>';
        entityTypes.units.forEach(type => {
            console.log('Creating input for unit type:', type);
            const countDiv = document.createElement('div');
            countDiv.className = 'entity-count';
            countDiv.innerHTML = `
                <label for="${type}-count">${type}:</label>
                <input type="number" id="${type}-count" min="0" value="0" required>
            `;
            unitGroup.appendChild(countDiv);
        });
        entityCountsDiv.appendChild(unitGroup);
        console.log('Added unit inputs to entity-counts div');
    } else {
        console.warn('No unit types available in entityTypes:', entityTypes);
    }

    // Add plant count inputs
    if (entityTypes.plants && entityTypes.plants.length > 0) {
        console.log('Adding plant inputs for types:', entityTypes.plants);
        const plantGroup = document.createElement('div');
        plantGroup.innerHTML = '<h4>Plants</h4>';
        entityTypes.plants.forEach(type => {
            console.log('Creating input for plant type:', type);
            const countDiv = document.createElement('div');
            countDiv.className = 'entity-count';
            countDiv.innerHTML = `
                <label for="${type}-count">${type}:</label>
                <input type="number" id="${type}-count" min="0" value="0" required>
            `;
            plantGroup.appendChild(countDiv);
        });
        entityCountsDiv.appendChild(plantGroup);
        console.log('Added plant inputs to entity-counts div');
    } else {
        console.warn('No plant types available in entityTypes:', entityTypes);
    }
}

// Fetch available entity types
async function fetchEntityTypes() {
    try {
        console.log('Fetching entity types...');
        const response = await fetch(`${API_BASE_URL}/game/entity-types`);
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to fetch entity types:', response.status, errorText);
            return;
        }
        
        const data = await response.json();
        console.log('Received entity types:', data);
        
        if (!data.units || !data.plants) {
            console.error('Invalid entity types data:', data);
            return;
        }
        
        entityTypes = data;
        console.log('Updated entityTypes:', entityTypes);
        
        // Create entity count inputs
        console.log('About to create entity count inputs...');
        createEntityCountInputs();
        console.log('Finished creating entity count inputs');
    } catch (error) {
        console.error('Error fetching entity types:', error);
        console.error('Error stack:', error.stack);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM Content Loaded');
    // Fetch entity types first, before any other setup
    await fetchEntityTypes();
    console.log('Finished initial fetchEntityTypes');

    const gameBoardDiv = document.getElementById('game-board');
    const entityDetailsPanel = document.getElementById('entity-details-panel');
    const detailsContentDiv = document.getElementById('details-content');
    const nextTurnButton = document.getElementById('next-turn-btn');
    const turnInfoDiv = document.getElementById('turn-info');


    // Function to get random empty position
    function getRandomEmptyPosition(width, height, occupiedPositions) {
        let x, y;
        do {
            x = Math.floor(Math.random() * width);
            y = Math.floor(Math.random() * height);
        } while (occupiedPositions.has(`${x},${y}`));
        occupiedPositions.add(`${x},${y}`);
        return { x, y };
    }

    // Handle form submission
    document.getElementById('config-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const width = parseInt(document.getElementById('board-width').value);
        const height = parseInt(document.getElementById('board-height').value);
        
        const entities = [];
        const occupiedPositions = new Set();

        // Collect unit counts and create entities
        entityTypes.units.forEach(type => {
            const count = parseInt(document.getElementById(`${type}-count`).value) || 0;
            for (let i = 0; i < count; i++) {
                const pos = getRandomEmptyPosition(width, height, occupiedPositions);
                entities.push({
                    type: 'unit',
                    name: type,
                    x: pos.x,
                    y: pos.y
                });
            }
        });

        // Collect plant counts and create entities
        entityTypes.plants.forEach(type => {
            const count = parseInt(document.getElementById(`${type}-count`).value) || 0;
            for (let i = 0; i < count; i++) {
                const pos = getRandomEmptyPosition(width, height, occupiedPositions);
                entities.push({
                    type: 'plant',
                    name: type,
                    x: pos.x,
                    y: pos.y
                });
            }
        });
        
        const config = {
            width,
            height,
            entities
        };
        
        try {
            // Create new game instance
            const response = await fetch('/game/new', { method: 'POST' });
            if (!response.ok) {
                throw new Error('Failed to create new game');
            }
            const data = await response.json();
            gameId = data.game_id;
            console.log('Created new game with ID:', gameId);
            
            // Configure the game
            const configResponse = await fetch(`/game/${gameId}/configure`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            if (configResponse.ok) {
                // Hide config panel and show game board
                document.getElementById('config-panel').style.display = 'none';
                document.getElementById('game-controls').style.display = 'block';
                
                // Initial board render
                await fetchAndRenderBoard();
            } else {
                alert('Failed to configure game. Please try again.');
            }
        } catch (error) {
            console.error('Error configuring game:', error);
            alert('Error configuring game. Please try again.');
        }
    });

    // Function to create a new entity item
    function createEntityItem() {
        const entityItem = document.createElement('div');
        entityItem.className = 'entity-item';
        
        const typeSelect = document.createElement('select');
        typeSelect.innerHTML = `
            <option value="">Select Type</option>
            <optgroup label="Units">
                ${entityTypes.units.map(type => `<option value="unit:${type}">${type}</option>`).join('')}
            </optgroup>
            <optgroup label="Plants">
                ${entityTypes.plants.map(type => `<option value="plant:${type}">${type}</option>`).join('')}
            </optgroup>
        `;
        
        const xInput = document.createElement('input');
        xInput.type = 'number';
        xInput.placeholder = 'X';
        xInput.min = '0';
        xInput.required = true;
        
        const yInput = document.createElement('input');
        yInput.type = 'number';
        yInput.placeholder = 'Y';
        yInput.min = '0';
        yInput.required = true;
        
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.onclick = () => entityItem.remove();
        
        entityItem.appendChild(typeSelect);
        entityItem.appendChild(xInput);
        entityItem.appendChild(yInput);
        entityItem.appendChild(removeBtn);
        
        return entityItem;
    }

    // Function to fetch and render board state
    async function fetchBoardState() {
        if (!gameId) {
            console.log('No game ID available yet');
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/game/${gameId}/board`);

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
i
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

        if (!entityId || !gameId) {

            detailsContentDiv.innerHTML = 'No entity selected.';
            return;
        }
        try {

            const response = await fetch(`${API_BASE_URL}/game/${gameId}/entity/${entityId}`);

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
        if (!gameId) {
            console.error('No game ID available');
            return;
        }
        try {
            console.log('Updating game state for game:', gameId);
            const response = await fetch(`${API_BASE_URL}/game/${gameId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            if (!response.ok) {
                console.error('Failed to update game state:', response.status, await response.text());
                return;
            }
            const updatedBoardData = await response.json();
            console.log('Received updated board data:', updatedBoardData);
            renderBoard(updatedBoardData);
            updateTurnInfo(updatedBoardData.turn);
            detailsContentDiv.innerHTML = 'Select an entity to see its details.';
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

});

// Update fetchAndRenderBoard to use gameId
async function fetchAndRenderBoard() {
    if (!gameId) {
        console.error('No game ID available');
        return;
    }
    try {
        console.log('Fetching board state for game:', gameId);
        const response = await fetch(`/game/${gameId}/board`);
        if (!response.ok) {
            throw new Error(`Failed to fetch board state: ${response.status}`);
        }
        const data = await response.json();
        console.log('Received board data:', data);
        
        // Update turn info
        document.getElementById('turn-info').textContent = `Turn: ${data.turn}`;
        
        // Render board
        const board = document.getElementById('game-board');
        board.innerHTML = '';
        board.style.gridTemplateColumns = `repeat(${data.board_width}, 30px)`;
        
        for (let y = 0; y < data.board_height; y++) {
            for (let x = 0; x < data.board_width; x++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                
                const entity = data.entities.find(e => e.x === x && e.y === y);
                if (entity) {
                    cell.classList.add(entity.type.toLowerCase());
                    if (entity.name) {
                        cell.classList.add(entity.name.toLowerCase().replace(/\s+/g, ''));
                    }
                    cell.dataset.entityId = entity.id;
                    cell.textContent = entity.name ? entity.name.charAt(0).toUpperCase() : entity.type.charAt(0).toUpperCase();
                    cell.onclick = () => fetchEntityDetails(entity.id);
                }
                
                board.appendChild(cell);
            }
        }
    } catch (error) {
        console.error('Error fetching board state:', error);
        document.getElementById('game-board').innerHTML = '<p>Error loading board. Please try again.</p>';
    }
}

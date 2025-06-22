// app/static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const startScreenOverlay = document.getElementById('start-screen-overlay');
    const nameForm = document.getElementById('name-form');
    const playerNameInput = document.getElementById('player-name-input');
    
    const gameHeader = document.querySelector('.game-header');
    const gameContainer = document.querySelector('.game-container');
    
    const dialogueTextElement = document.getElementById('dialogue-text');
    const choicesBoxElement = document.getElementById('choices-box');
    const backgroundDivElement = document.querySelector('.game-container');
    const characterNameElement = document.getElementById('character-name');
    const backButton = document.getElementById('back-button');
    const restartButton = document.getElementById('restart-button');
    
    const confirmationModalElement = document.getElementById('confirmationModal');
    const confirmationModal = new bootstrap.Modal(confirmationModalElement);

    const inlineInputForm = document.getElementById('inline-input-form');
    const inlinePlayerInput = document.getElementById('inline-player-input');

    // --- Game State & Modal Controller ---
    let currentNodeId = null;
    let modalConfirmController;

    // --- Event Listeners ---
    nameForm.addEventListener('submit', handleNameSubmit);
    backButton.addEventListener('click', goBack);
    restartButton.addEventListener('click', handleRestartClick);
    inlineInputForm.addEventListener('submit', handleTextInputSubmit);
    
    // --- Core Functions ---

    function handleRestartClick(e) {
        e.preventDefault();
        const title = e.currentTarget.dataset.modalTitle;
        const body = e.currentTarget.dataset.modalBody;
        showConfirmationModal(title, body, () => {
            window.location.reload();
        });
    }

    /**
     * Handles the submission of the player's name, which starts the game.
     * @param {Event} e - The form submission event.
     */
    async function handleNameSubmit(e) {
        e.preventDefault();
        const playerName = playerNameInput.value;
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: playerName, 
                    locale: document.body.dataset.locale
                })
            });
            if (!response.ok) throw new Error('Failed to start game');
            const startNode = await response.json();
            
            startScreenOverlay.style.display = 'none';
            gameHeader.style.display = 'flex';
            gameContainer.style.display = 'flex';
            
            currentNodeId = startNode.id;
            updateUI(startNode);
        } catch (error) {
            console.error("Couldn't start game:", error);
            alert("Error starting the game. Please try again.");
        }
    }

    /**
     * Handles the submission of the in-game text input form.
     */
    async function handleTextInputSubmit(e) {
        e.preventDefault();
        const userAnswer = inlinePlayerInput.value;
        
        inlinePlayerInput.value = ''; // Clear the input field

        try {
            const response = await fetch('/api/submit_answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    answer: userAnswer,
                    node_id: currentNodeId 
                })
            });
            if (!response.ok) throw new Error('Failed to submit answer');
            const nextNode = await response.json();
            
            currentNodeId = nextNode.id;
            updateUI(nextNode);
        } catch (error) {
            console.error("Couldn't submit answer:", error);
            alert("Error submitting answer. Please try again.");
        }
    }

    /**
     * Sends the player's choice to the server and updates the UI with the next node.
     * @param {number} choiceIndex - The index of the choice the player clicked.
     */
    async function makeChoice(choiceIndex) {
        try {
            const response = await fetch('/api/choose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    node_id: currentNodeId,
                    choice_index: choiceIndex
                })
            });
            if (!response.ok) throw new Error(`Network error: ${response.statusText}`);
            const nextNode = await response.json();

            currentNodeId = nextNode.id;
            updateUI(nextNode);
        } catch (error) {
            console.error('Failed to make choice:', error);
            dialogueTextElement.textContent = "Error: Could not process choice.";
        }
    }

    /**
     * Handles the back button click by calling the backend API.
     */
    async function goBack() {
        try {
            const response = await fetch('/api/back', { method: 'POST' });
            if (!response.ok) {
                console.log("Server indicated no more history available.");
                return;
            }
            const previousNode = await response.json();

            currentNodeId = previousNode.id;
            updateUI(previousNode);
        } catch (error) {
            console.error('Failed to go back:', error);
        }
    }

    /**
     * A scalable function to show our confirmation modal.
     * @param {string} title - The text for the modal's title.
     * @param {string} body - The text for the modal's body.
     * @param {Function} onConfirm - The function to execute when the confirm button is clicked.
     */
    function showConfirmationModal(title, body, onConfirm) {
        if (modalConfirmController) {
            modalConfirmController.abort();
        }
        modalConfirmController = new AbortController();

        const modalTitle = document.getElementById('modalTitle');
        const modalBodyText = document.getElementById('modalBodyText');
        const modalConfirmButton = document.getElementById('modalConfirmButton');

        modalTitle.textContent = title;
        modalBodyText.textContent = body;

        modalConfirmButton.addEventListener('click', () => {
            onConfirm();
            confirmationModal.hide();
        }, { signal: modalConfirmController.signal });

        confirmationModal.show();
    }

    /**
     * Updates all visual elements on the page based on the current node data.
     * @param {object} nodeData - The node object received from the backend.
     */
    function updateUI(nodeData) {
        console.log("Updating UI with node data:", nodeData);

        const illustrationContainer = document.getElementById('illustration-container');
        if (illustrationContainer) {
            if (nodeData.illustration) {
                let img = illustrationContainer.querySelector('img');
                if (!img) {
                    img = document.createElement('img');
                    illustrationContainer.appendChild(img);
                }
                img.src = nodeData.illustration;
                illustrationContainer.style.display = 'flex';
            } else {
                illustrationContainer.style.display = 'none';
            }
        }
    
        if (nodeData.background) {
            backgroundDivElement.style.backgroundImage = `url(${nodeData.background})`;
        }

        backgroundDivElement.style.backgroundImage = nodeData.background ? `url(${nodeData.background})` : '';
        characterNameElement.textContent = nodeData.character || '';
        characterNameElement.parentElement.style.display = nodeData.character ? 'block' : 'none';
        dialogueTextElement.textContent = nodeData.text || '';

        choicesBoxElement.style.display = 'none';
        inlineInputForm.style.display = 'none';
    
        choicesBoxElement.innerHTML = '';
        if (nodeData.input_prompt){
            inlineInputForm.style.display = 'flex';
            inlinePlayerInput.focus();
            backButton.style.display = 'none';

        } else if (nodeData.choices && nodeData.choices.length > 0) {
            choicesBoxElement.innerHTML = ''; 
            choicesBoxElement.style.display = 'grid';

            nodeData.choices.forEach((choice, index) => {
                const button = document.createElement('button');
                button.className = 'btn btn-primary';
                button.textContent = choice.text;
                button.onclick = () => makeChoice(index);
                choicesBoxElement.appendChild(button);
            });

            backButton.style.display = 'block';
        } else {
            choicesBoxElement.innerHTML = `<p class="text-center fst-italic">The End.</p>`;
            choicesBoxElement.style.display = 'block';
            backButton.style.display = 'block';
        }

        if (nodeData.id === 'start') {
            backButton.style.display = 'none';
        }
    }
});
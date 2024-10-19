document.addEventListener('DOMContentLoaded', function () {
    const meetFutureSelfButton = document.getElementById('meet-future-self');
    const futureSelfSection = document.getElementById('future-self-section');
    const selfAnalysisResult = document.getElementById('self-analysis-result');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    meetFutureSelfButton.addEventListener('click', function () {
        futureSelfSection.style.display = 'block';
        this.style.display = 'none';
        performSelfAnalysis();
    });

    function performSelfAnalysis() {
        fetch('/future_self_analysis', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                selfAnalysisResult.innerHTML = `
                    <h3>自己分析結果</h3>
                    <p><strong>強み:</strong> ${data.strength}</p>
                    <p><strong>弱み:</strong> ${data.weakness}</p>
                    <p><strong>機会:</strong> ${data.opportunity}</p>
                    <p><strong>脅威:</strong> ${data.threat}</p>
                `;
            });
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessageToChat('user', message);
            getAIResponse(message);
            userInput.value = '';
        }
    }

    function addMessageToChat(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender}-message`;
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function getAIResponse(message) {
        fetch('/get_ai_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: message }),
        })
            .then(response => response.json())
            .then(data => {
                addMessageToChat('ai', data.response);
            });
    }
});
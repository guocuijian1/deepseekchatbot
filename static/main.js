function sendMessage() {
    let inputField = document.getElementById('textInput');
    let message = inputField.value.trim();
    if (message === '') return;

    let chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="message user">${message}</div>`;
    let original =chatBox.innerHTML;
    chatBox.innerHTML = original + `<div><span id="bot-input-animation-1">&nbsp;</span>
    <span id="bot-input-animation-2">&nbsp;</span>
    <span id="bot-input-animation-3">&nbsp;</span></div>`
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
        .then(response => response.json())
        .then(data => {
            chatBox.innerHTML = original + `${data.response}`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });

    inputField.value = '';
}

function newTopic() {
    fetch('/chat/new_topic', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            showNotification(data.response)
        })
}

function onDocumentLoaded(event) {
    let inputEle = document.getElementById('textInput')
    inputEle.innerText = ""

    let textInput = document.getElementById('textInput')
    textInput.addEventListener("keydown", function (event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    })

    let newTopicBtn = document.getElementById('newTopicBtn')
    newTopicBtn.addEventListener('click', function () {
        newTopic()
    })

    let sendButton = document.getElementById('sendMessageBtn')
    sendButton.addEventListener('click', function () {
        sendMessage()
    })
}

function showNotification(message) {
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = message;
    msgDiv.classList.add('show');
    setTimeout(() => msgDiv.classList.remove('show'), 1000);
}
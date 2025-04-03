 function sendMessage() {
    const stream = window.localStorage.getItem("enable_chat_stream")
    let inputField = document.getElementById('textInput');
    let message = inputField.value.trim();
    if (message === '') return;

    let chatBox = document.getElementById('chat-box');
    let userMessage = createUserMessageDiv(message);
    chatBox.appendChild(userMessage);

    let loadingElement = createLoadingMessageDiv();
    chatBox.appendChild(loadingElement);

    let url = '/chat'
    fetch(url, {
        method: 'POST',
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: message, stream: stream})
    })
        .then(response => {
            response.json().then(data => {
                chatBox.removeChild(loadingElement);
                let messageElement = createMessageElement(stream);
                chatBox.appendChild(messageElement);
                if (stream) {
                    const sessionId = data.response;
                    const stream_url = `/stream/${sessionId}`;
                    const eventSource = new EventSource(stream_url);

                    let content = ''
                    eventSource.addEventListener("message", e => {
                        const jsonObj = JSON.parse(e.data);
                        const data = jsonObj.value;
                        if (data.trim() === "Finish") {
                            console.log("Is about close event source!");
                            eventSource.close();
                        } else {
                            content += data
                            //messageElement.innerHTML = marked.parse(content);
                            messageElement.innerHTML = content;
                            chatBox.scrollTop = chatBox.scrollHeight;
                        }
                    })

                    eventSource.addEventListener('status', (e) => {
                        console.log('Status update:', e.data);
                    });

                    eventSource.onerror = () => {
                        if (eventSource.readyState === EventSource.CLOSED) {
                            console.log('Connection permanently closed');
                        } else {
                            console.log('Temporary error - will reconnect');
                        }
                    }

                    fetch(stream_url).then(r => {

                    })

                } else {
                    messageElement.innerHTML = marked.parse(data.response);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            })
        })

    inputField.value = '';
}

function newTopic() {
    const stream = window.localStorage.getItem("enable_chat_stream");
    const url = `/chat/new_topic?stream=${stream}`;
    fetch(url, {
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

    let clearBtn = document.getElementById('clearHistoryBtn')
    clearBtn.addEventListener("click", function (event) {
        let chatBox = document.getElementById('chat-box');
        chatBox.innerHTML = '';
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

function createUserMessageDiv(message) {
    const tempDiv = document.createElement('div');
    tempDiv.classList.add('message','user');
    tempDiv.textContent = message;

    return tempDiv
}

function createLoadingMessageDiv() {
    const tempDiv = document.createElement('div');
    const span1 = document.createElement('span');
    span1.id = 'bot-input-animation-1';
    span1.innerHTML = '&nbsp;'
    const span2 = document.createElement('span');
    span2.id = 'bot-input-animation-2';
    span2.innerHTML = '&nbsp;'
    const span3 = document.createElement('span');
    span3.id = 'bot-input-animation-3';
    span3.innerHTML = '&nbsp;'
    tempDiv.appendChild(span1)
    tempDiv.appendChild(span2)
    tempDiv.appendChild(span3)
    return tempDiv
}

function createMessageElement(stream) {
    if (stream) {
        return document.createElement('pre');
    } else {
        return document.createElement('div');
    }
}

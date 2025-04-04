function getCookie(name) {
    const values = document.cookie.split(';');
    for (let i = 0; i < values.length; i++) {
        const value = values[i].split('=');
        if (value[0] === name) {
            return value[1]
        }
    }
}

function handleSendMessage() {
    const isStreamEnabled = window.localStorage.getItem("enable_chat_stream") === "true";
    let messageInputElement = document.getElementById('user-message-input');
    let user_message = messageInputElement.value.trim();
    if (user_message === '') return;

    let chatBoxElement = document.getElementById('chat-box-container');
    let userMessageElement = createUserMessageElement(user_message);
    chatBoxElement.appendChild(userMessageElement);

    let loadingMessageElement = createLoadingMessageElement();
    chatBoxElement.appendChild(loadingMessageElement);
    chatBoxElement.scrollTop = chatBoxElement.scrollHeight;

    let url = '/chat'
    fetch(url, {
        method: 'POST',
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: user_message, stream: isStreamEnabled})
    })
        .then(response => {
            response.json().then(data => {
                let chatMessageElement = createChatMessageElement(isStreamEnabled);
                if (isStreamEnabled) {
                    const sessionId = getCookie('session_id');
                    const stream_url = `/stream/${sessionId}`;
                    const eventSource = new EventSource(stream_url);

                    let content = '';

                    eventSource.addEventListener("message", e => {
                        if (loadingMessageElement) {
                            chatBoxElement.removeChild(loadingMessageElement);
                            loadingMessageElement = null;
                            chatBoxElement.appendChild(chatMessageElement);
                            chatBoxElement.scrollTop = chatBoxElement.scrollHeight;
                        }
                        const jsonObj = JSON.parse(e.data);
                        const data = jsonObj.value;
                        if (data.trim() === "Finish") {
                            console.log("Is about close event source!");
                            eventSource.close();
                        } else {
                            content += data
                            chatMessageElement.innerHTML = marked.parse(content);
                            chatBoxElement.scrollTop = chatBoxElement.scrollHeight;
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

                    fetch(stream_url).then();

                } else {
                    chatBoxElement.removeChild(loadingMessageElement);
                    chatBoxElement.appendChild(chatMessageElement);
                    chatMessageElement.innerHTML = marked.parse(data.response);
                    chatBoxElement.scrollTop = chatBoxElement.scrollHeight;
                }
            })
        })

    messageInputElement.value = '';
}

function handleClearChatHistory() {
    const sessionId = getCookie('session_id');
    const url = `/chat/clear_history?session_id=${sessionId}`;
    fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            showSystemNotification(data.response)
        })
}

function initializeChatInterface(event) {
    let userMessageInputElement = document.getElementById('user-message-input')
    userMessageInputElement.innerText = ""

    userMessageInputElement.addEventListener("keydown", function (event) {
        if (event.key === 'Enter') {
            handleSendMessage();
        }
    })

    let clearUIHistoryBtn = document.getElementById('clearUIHistoryBtn')
    clearUIHistoryBtn.addEventListener("click", function (event) {
        let chatBoxElement = document.getElementById('chat-box-container');
        chatBoxElement.innerHTML = '';
    })

    let clearChatHistoryBtn = document.getElementById('clearChatHistoryBtn')
    clearChatHistoryBtn.addEventListener('click', function () {
        handleClearChatHistory()
    })

    let sendUserMessageBtn = document.getElementById('sendUserMessageBtn')
    sendUserMessageBtn.addEventListener('click', function () {
        handleSendMessage()
    })
}

function showSystemNotification(message) {
    const systemMessageDiv = document.getElementById('system-message');
    systemMessageDiv.textContent = message;
    systemMessageDiv.classList.add('show');
    setTimeout(() => systemMessageDiv.classList.remove('show'), 1000);
}

function createUserMessageElement(user_message) {
    const tempDiv = document.createElement('div');
    tempDiv.classList.add('message','user');
    tempDiv.textContent = user_message;

    return tempDiv
}

function createLoadingMessageElement() {
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

function createChatMessageElement(stream) {
    if (stream) {
        return document.createElement('pre');
    } else {
        return document.createElement('div');
    }
}

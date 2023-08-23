const chatOwnerSlug = JSON.parse(document.getElementById('chat-owner-slug').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);
const userUsernameSlug = JSON.parse(document.getElementById('username-slug').textContent);
const moderSlugs = JSON.parse(document.getElementById('moder-slugs').textContent);
const userHasAdminPrivileges = JSON.parse(document.getElementById('admin-privileges-granted').textContent);
let chatIsOpen = JSON.parse(document.getElementById('chat-is-open').textContent);
const url = `ws://${window.location.host}/ws/room/${chatOwnerSlug}/`;
const chatSocket = new WebSocket(url);

const messageInputBlock = document.querySelector('#chat-message-input');
const chatBlock = document.getElementById('chat');
const sendMessageButton = document.querySelector('#chat-message-submit');
const chatManagamentButton = document.getElementById('btn-chat-management');


document.addEventListener("DOMContentLoaded", scrollChatToBottom);

messageInputBlock.onkeydown = function(e) {
	if(e.keyCode == 13) sendMassegeToServer();
}
sendMessageButton.onclick = sendMassegeToServer;

if (chatManagamentButton) {
	chatManagamentButton.onclick = sendManagementMessageToServer;
}


// recieving message and writing it to chat or handling system message
chatSocket.onmessage = function(e) {

	// parsing and writing message to chat
	const data = JSON.parse(e.data);
	let messageDiv = null;

	switch (data.messageType) {
		case 'chatroom_message':
			messageDiv = addUserMessage(data);
			break;
		case 'system_message': {
			handleSystemCommand(data);
			messageDiv = addSystemMessage(data);
			break;
		}
	}

	// scrolling, if chat was scrolled all way down
	if(chatBlock.scrollTop >= chatBlock.scrollHeight - chatBlock.clientHeight - messageDiv.scrollHeight * 2) {
		scrollChatToBottom();
	}
}

function handleSystemCommand(data) {
	switch (data.command) {
		case 'open_chat':
			executeCommandOpenChat();
			break;
		case 'close_chat':
			executeCommandCloseChat();
			break;
		case 'ban_chat':
			executeCommandBanChat();
			break;
	}
}

function addUserMessage(data) {
	const messageAuthor = document.createElement('span');
	messageAuthor.textContent = data.senderUsername+":";
	messageAuthor.className = ('fw-bold me-1 px-1 message-author');
	messageAuthor.setAttribute("data-sender-slug", data.senderUsernameSlug);
	messageAuthor.addEventListener("contextmenu", showChatContextMenu);

	const messageText = document.createTextNode(data.message);

	const messageDiv = document.createElement('div');
	messageDiv.className = ('pt-2 px-3');
	messageDiv.append(messageAuthor);
	messageDiv.append(messageText);
	chatBlock.append(messageDiv);
	return messageDiv;
}

function addSystemMessage(data) {
	const messageText = document.createElement('span');
	messageText.textContent = data.message
	messageText.className = ('badge bg-danger');

	const messageDiv = document.createElement('div');
	messageDiv.className = ('p-3 text-center');
	messageDiv.append(messageText);
	chatBlock.append(messageDiv);
	return messageDiv;
}


// sending message function
function sendMassegeToServer(e) {
	if (!chatIsOpen) return;

	const message = messageInputBlock.value;
	if (message) {
		chatSocket.send(JSON.stringify({message, userUsername, userUsernameSlug, messageType: 'message'}));
		messageInputBlock.value = '';
	}
	messageInputBlock.focus();
}

function sendManagementMessageToServer(e) {
	command = e.currentTarget.dataset.command;
	chatSocket.send(JSON.stringify({command, messageType: 'management'}));
}

function executeCommandOpenChat() {
	chatIsOpen = true;
	messageInputBlock.removeAttribute('disabled');
	sendMessageButton.removeAttribute('disabled');
	if (chatManagamentButton && chatOwnerSlug == userUsernameSlug) {
		chatManagamentButton.dataset.command = 'close_chat';
		chatManagamentButton.textContent = 'Close Chat';
	}
}

function executeCommandCloseChat() {
	chatIsOpen = false;
	sendMessageButton.setAttribute('disabled', '');
	messageInputBlock.setAttribute('disabled', '');
	if (chatManagamentButton && chatOwnerSlug == userUsernameSlug) {
		chatManagamentButton.dataset.command = 'open_chat';
		chatManagamentButton.textContent = 'Open Chat';
	}
}

function executeCommandBanChat() {
	chatIsOpen = false;
	sendMessageButton.setAttribute('disabled', '');
	messageInputBlock.setAttribute('disabled', '');
	if (chatManagamentButton) {
		chatManagamentButton.setAttribute('disabled', '');
		if (chatOwnerSlug == userUsernameSlug) {
			chatManagamentButton.dataset.command = 'open_chat';
			chatManagamentButton.textContent = 'Open Chat';
		}
	}
}

function scrollChatToBottom(e) {
	chatBlock.scrollTop = chatBlock.scrollHeight - chatBlock.clientHeight;
}

const chatOwnerSlug = JSON.parse(document.getElementById('chat-owner-slug').textContent);
const chatOwnerUsername = JSON.parse(document.getElementById('chat-owner-username').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);
const moderUsernames = JSON.parse(document.getElementById('moder-usernames').textContent);
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
	chatManagamentButton.onclick = sendChatManagementMessageToServer;
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
		case 'system_message':
			handleSystemCommand(data);
			messageDiv = addSystemMessage(data);
			break;
		case 'private_message':
			messageDiv = addPrivateMessage(data);
			break;
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
		case 'add_user_to_black_list':
			executeCommandAddUserToBlackList(data.userUsername);
			break;
	}
}

function addUserMessage(data) {
	const messageAuthor = document.createElement('span');
	messageAuthor.textContent = data.senderUsername+":";
	messageAuthor.className = 'fw-bold me-1 px-1 message-author';
	messageAuthor.setAttribute("data-sender-username", data.senderUsername);
	messageAuthor.addEventListener("contextmenu", showChatContextMenu);

	const messageText = document.createTextNode(data.message);

	const messageDiv = document.createElement('div');
	messageDiv.className = 'pt-2 px-3';
	messageDiv.append(messageAuthor);
	messageDiv.append(messageText);
	chatBlock.append(messageDiv);
	return messageDiv;
}

function addSystemMessage(data) {
	const messageText = document.createElement('span');
	messageText.textContent = data.message
	messageText.className = 'badge bg-danger';

	const messageDiv = document.createElement('div');
	messageDiv.className = 'p-3 text-center';
	messageDiv.append(messageText);
	chatBlock.append(messageDiv);
	return messageDiv;
}

function addPrivateMessage(data) {
	const messageOuterDiv = document.createElement('div');
	const messageInnerDiv = document.createElement('div');
	const messageHead = document.createElement('div');
	// const messageBody = document.createElement('div');
	let messagePrefix = null;
	const messageAuthor = document.createElement('span');
	const messageText = document.createTextNode(data.message);

	messageOuterDiv.className = 'p-2 d-flex';
	messageInnerDiv.className = 'p-3 col-8 d-flex flex-column';
	messageAuthor.className = 'fw-bold px-1';

	switch (userUsername) {
		case data.recipientUsername:
			messageOuterDiv.classList.add('justify-content-start');
			messageInnerDiv.classList.add('private-message-to-me');
			messagePrefix = document.createTextNode('From');
			messageAuthor.textContent = data.senderUsername+":";
			messageAuthor.classList.add('message-author');
			messageAuthor.setAttribute("data-sender-username", data.senderUsername);
			messageAuthor.addEventListener("contextmenu", showChatContextMenu);
			break;
		case data.senderUsername:
			messageOuterDiv.classList.add('justify-content-end');
			messageInnerDiv.classList.add('private-message-from-me');
			messagePrefix = document.createTextNode('To');
			messageAuthor.textContent = data.recipientUsername+":";
			messageAuthor.classList.add('message-author');
			messageAuthor.setAttribute("data-sender-username", data.recipientUsername);
			messageAuthor.addEventListener("contextmenu", showChatContextMenu);
			break;
		default:
			return;
	}
	messageHead.append(messagePrefix);
	messageHead.append(messageAuthor);
	messageInnerDiv.append(messageHead);
	messageInnerDiv.append(messageText);
	messageOuterDiv.append(messageInnerDiv);
	chatBlock.append(messageOuterDiv);
	return messageOuterDiv;
}

function scrollChatToBottom(e) {
	chatBlock.scrollTop = chatBlock.scrollHeight - chatBlock.clientHeight;
}

// sending message function
function sendMassegeToServer(e) {
	if (!chatIsOpen) return;

	const message = messageInputBlock.value;
	if (message) {
		chatSocket.send(JSON.stringify({message, userUsername, messageType: 'message'}));
		messageInputBlock.value = '';
	}
	messageInputBlock.focus();
}

function sendChatManagementMessageToServer(e) {
	sendCommandToServer(e.currentTarget.dataset.command);
}

function sendCommandToServer(command, commandData=null) {
	sendData = {command, messageType: 'management'}
	if (commandData) {
		for (let key in commandData) {
			sendData[key] = commandData[key]
		}
	}

	chatSocket.send(JSON.stringify(sendData));
}

function executeCommandOpenChat() {
	chatIsOpen = true;
	messageInputBlock.removeAttribute('disabled');
	sendMessageButton.removeAttribute('disabled');
	if (chatManagamentButton && chatOwnerUsername == userUsername) {
		chatManagamentButton.dataset.command = 'close_chat';
		chatManagamentButton.textContent = 'Close Chat';
	}
}

function executeCommandCloseChat() {
	chatIsOpen = false;
	sendMessageButton.setAttribute('disabled', '');
	messageInputBlock.setAttribute('disabled', '');
	if (chatManagamentButton && chatOwnerUsername == userUsername) {
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
		if (chatOwnerUsername == userUsername) {
			chatManagamentButton.dataset.command = 'open_chat';
			chatManagamentButton.textContent = 'Open Chat';
		}
	}
}

function executeCommandAddUserToBlackList(userUsername) {
	deleteAllSpecificUserMessagesFromChat(userUsername);
}

function addUserToBlackListListener(event) {
	sendCommandToServer(
		'add_user_to_black_list',
		{'username': event.currentTarget.parentElement.getAttribute('data-sender-username')},
	);
	event.currentTarget.parentElement.remove();
}

function initiatePrivateMessageListener(event) {
	const targetUsername = event.currentTarget.parentElement.getAttribute('data-sender-username');
	messageInputBlock.value = `@${targetUsername}, `+messageInputBlock.value;
	messageInputBlock.focus();
	event.currentTarget.parentElement.remove();
}

function demoteModeratorListener(event) {
	console.log('demoteModerator');
}

function appointModeratorListener(event) {
	console.log('appointModerator');
}

function expandBanMenuListener(event) {
	console.log('expandBanMenu');
}

function deleteAllSpecificUserMessagesFromChat(userUsername) {
	let messageDiv = null;
	for (let i=chatBlock.children.length-1; i>=0; --i) {
		messageDiv = chatBlock.children[i]
		if (messageDiv.firstElementChild.getAttribute("data-sender-username") == userUsername) {
			messageDiv.remove();
		}
	}
}

const chatOwnerSlug = JSON.parse(document.getElementById('chat-owner-slug').textContent);
const chatOwnerUsername = JSON.parse(document.getElementById('chat-owner-username').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);

let userIsModer = JSON.parse(document.getElementById('am-moder').textContent);
let userIsBanned = JSON.parse(document.getElementById('am-banned').textContent);
const userHasAdminPrivileges = JSON.parse(document.getElementById('admin-privileges-granted').textContent);
const userIsSuperuser = JSON.parse(document.getElementById('superuser-privileges-granted').textContent);

let chatIsOpen = JSON.parse(document.getElementById('chat-is-open').textContent);
const chatUserStatuses = JSON.parse(document.getElementById('user-statuses').textContent);

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
	if(messageDiv && chatBlock.scrollTop >= chatBlock.scrollHeight - chatBlock.clientHeight - messageDiv.scrollHeight * 2) {
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
		case 'appoint_moderator':
			executeCommandAppointModerator(data.userUsername);
			break;
		case 'demote_moderator':
			executeCommandDemoteModerator(data.userUsername);
			break;
		case 'ban_user':
			executeCommandBanUser(data.userUsername);
			break;
	}
}

function addUserMessage(data) {
	const messageAuthor = document.createElement('span');
	messageAuthor.textContent = data.senderUsername+":";
	messageAuthor.className = 'fw-bold me-1 px-1 message-author';
	messageAuthor.setAttribute("data-sender-username", data.senderUsername);
	messageAuthor.setAttribute("data-sender-status", data.senderStatus);
	messageAuthor.addEventListener("contextmenu", showChatContextMenu);

	const messageText = document.createTextNode(data.message);

	const messageDiv = document.createElement('div');
	messageDiv.className = 'pt-2 px-3 chat-message';
	messageDiv.append(messageAuthor);
	messageDiv.append(messageText);
	chatBlock.append(messageDiv);
	return messageDiv;
}

function addSystemMessage(data) {
	if (!data.message) return;

	const messageText = document.createElement('span');
	messageText.textContent = data.message
	bageColorClass = data.command == 'ban_user' ? 'bg-danger' : 'bg-warning text-black';
	messageText.className = `badge ${bageColorClass}`;

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

	messageOuterDiv.className = 'p-2 d-flex private-message';
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

function sendMassegeToServer(e) {
	if (!chatIsOpen || userIsBanned) return;

	const message = messageInputBlock.value;
	if (message) {
		chatSocket.send(JSON.stringify({message, messageType: 'message'}));
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
	messageInputBlock.disabled = sendMessageButton.disabled = false;
	if (chatManagamentButton && chatOwnerUsername == userUsername) {
		chatManagamentButton.dataset.command = 'close_chat';
		chatManagamentButton.textContent = 'Close Chat';
	}
}

function executeCommandCloseChat() {
	chatIsOpen = false;
	messageInputBlock.disabled = sendMessageButton.disabled = true;
	if (chatManagamentButton && chatOwnerUsername == userUsername) {
		chatManagamentButton.dataset.command = 'open_chat';
		chatManagamentButton.textContent = 'Open Chat';
	}
}

function executeCommandBanChat() {
	chatIsOpen = false;
	messageInputBlock.disabled = sendMessageButton.disabled = true;
	if (chatManagamentButton) {
		chatManagamentButton.disabled = true;
		if (chatOwnerUsername == userUsername) {
			chatManagamentButton.dataset.command = 'open_chat';
			chatManagamentButton.textContent = 'Open Chat';
		}
	}
}

function executeCommandAddUserToBlackList(username) {
	deleteAllSpecificUserMessagesFromChat(username);
	deleteAllSpecificUserPrivateMessagesFromChat(username);
}

function executeCommandAppointModerator(username) {
	if (username == userUsername) userIsModer=true;
	for (messageAuthorSpanElement of document.querySelectorAll(`[data-sender-username="${username}"]`)) {
		messageAuthorSpanElement.setAttribute('data-sender-status', chatUserStatuses[3]);
	}
}

function executeCommandDemoteModerator(username) {
	if (username == userUsername) userIsModer=false;
	for (messageAuthorSpanElement of document.querySelectorAll(`[data-sender-username="${username}"]`)) {
		messageAuthorSpanElement.setAttribute('data-sender-status', chatUserStatuses[4]);
	}
}

function executeCommandBanUser(username) {
	if (username == userUsername) {
		messageInputBlock.disabled = sendMessageButton.disabled = true;
		userIsBanned = true;
	}
	deleteAllSpecificUserMessagesFromChat(username);
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
	sendCommandToServer(
		'demote_moderator',
		{'username': event.currentTarget.parentElement.getAttribute('data-sender-username')},
	);
	event.currentTarget.parentElement.remove();
}

function appointModeratorListener(event) {
	sendCommandToServer(
		'appoint_moderator',
		{'username': event.currentTarget.parentElement.getAttribute('data-sender-username')},
	);
	event.currentTarget.parentElement.remove();
}

function banListener(event) {
	event.preventDefault();

	const username = event.currentTarget.parentElement.parentElement.getAttribute('data-sender-username');
	const termOfBan = Number(event.currentTarget.term_input.value);
	const termTypeOfBan = event.currentTarget.term_type_input.value
	const commandData = {username, chatOwnerUsername, termOfBan, termTypeOfBan};
	
	if (event.currentTarget.ban_indefinitely) {
		commandData['indefinitely'] = event.currentTarget.ban_indefinitely.checked;
	}
	if (event.currentTarget.ban_in_all_chats) {
		commandData['inAllChats'] = event.currentTarget.ban_in_all_chats.checked;
	}

	if (commandData.indefinitely || commandData.inAllChats) {
		questionBanDuration = event.currentTarget.ban_indefinitely.checked ? 'indefinitely' : `for ${termOfBan} ${termTypeOfBan}`;
		questionBanLocation = event.currentTarget.ban_in_all_chats ? 'all chats' : `${chatOwnerUsername == userUsername ? 'your' : chatOwnerUsername} chat?`;
		if (confirm(`Are you sure you want to ban ${username} ${questionBanDuration} in ${questionBanLocation}`)) {
			sendCommandToServer('ban_user', commandData);
		}
	}
	else {
		sendCommandToServer('ban_user', commandData);
	}
	event.currentTarget.parentElement.parentElement.remove();
}

function deleteAllSpecificUserMessagesFromChat(username) {
	for (messageDiv of document.querySelectorAll('.chat-message')) {
		if (messageDiv.firstElementChild.getAttribute("data-sender-username") == username) {
			messageDiv.remove();
		}
	}
}

function deleteAllSpecificUserPrivateMessagesFromChat(username) {
	for (messageDiv of document.querySelectorAll('.private-message')) {
		if (messageDiv.firstElementChild.firstElementChild.firstElementChild.getAttribute("data-sender-username") == username) {
			messageDiv.remove();
		}
	}
}
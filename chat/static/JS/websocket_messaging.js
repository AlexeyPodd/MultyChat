const chatOwnerSlug = JSON.parse(document.getElementById('chat-owner-slug').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);
const url = `ws://${window.location.host}/ws/room/${chatOwnerSlug}/`;
const chatSocket = new WebSocket(url);

const messageInputBlock = document.querySelector('#chat-message-input');
const chatBlock = document.getElementById('chat')

messageInputBlock.onkeydown = function(e) {
	if(e.keyCode == 13) sendMassegeToServer();
}
document.querySelector('#chat-message-submit').onclick = sendMassegeToServer;


// recieving message and writing it to chat
chatSocket.onmessage = function(e) {

	// parsing and writing message to chat
	const data = JSON.parse(e.data);

	const message_author = document.createElement('span');
	message_author.textContent = data.senderUsername+":";
	message_author.className = ('fw-bold pe-2');

	const message_text = document.createTextNode(data.message);

	const message_div = document.createElement('div');
	message_div.className = ('pt-2 px-3');
	message_div.append(message_author);
	message_div.append(message_text);
	chatBlock.append(message_div);

	// scrolling, if chat was scrolled all way down
	if(chatBlock.scrollTop >= chatBlock.scrollHeight - chatBlock.clientHeight - message_div.scrollHeight * 2) {
		chatBlock.scrollTop = chatBlock.scrollHeight - chatBlock.clientHeight;
	}
}


// sending message function
function sendMassegeToServer(e) {
	const message = messageInputBlock.value;
	if (message) {
		chatSocket.send(JSON.stringify({message, userUsername}));
		messageInputBlock.value = '';
	}
	messageInputBlock.focus();

}

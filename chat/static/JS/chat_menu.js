chat_block = document.getElementById('chat');

chat_block.addEventListener("contextmenu", function(event) {
	console.log("Context menu");
	event.preventDefault();
});

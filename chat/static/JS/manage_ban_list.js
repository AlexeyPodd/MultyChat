const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value;
const unbanURL = JSON.parse(document.getElementById('unban-url').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);
let chatOwnerUsername = userUsername;

const bansTableBody = document.getElementById('bans-table-body');


if (bansTableBody) {
	bansTableBody.addEventListener('click', function(event) {
		if (!event.target.classList.contains('btn-unban')) return;

		const bannedUsername = event.target.getAttribute('data-banned-username');

		if (!window.confirm(`Are you sure you want to unban ${bannedUsername} in ${chatOwnerUsername == userUsername ? 'your' : chatOwnerUsername+'\'s'} chat?`)) return;

		$.ajax({
	        type: 'POST',
	        url: unbanURL,
	        data: {
	            csrfmiddlewaretoken: csrfToken,
	            bannedUsername,
	            chatOwnerUsername,
	        },
	        success: function() {
	            event.target.parentElement.parentElement.remove();
	        },
	    });
	});
}
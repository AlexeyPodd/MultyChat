const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value;
const unbanURL = JSON.parse(document.getElementById('unban-url').textContent);
const getBannedModerDataListURL = JSON.parse(document.getElementById('banned-moder-data-list-url').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);
let chatOwnerUsername = userUsername;

const bansTableBody = document.getElementById('bans-table-body');
const chatOwnerSelect = document.getElementById('chat-owner-select');


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


if (chatOwnerSelect) {
	chatOwnerSelect.addEventListener('change', function(event) {
		bansTableBody.innerHTML = '';
		chatOwnerUsername = event.currentTarget.value;

		const timeout = setTimeout(() => {
			const tabeHead = bansTableBody.previousElementSibling;
			
			const row = document.createElement('tr');			
			row.className = 'table-light';
			bansTableBody.append(row);
			const cell = document.createElement('td');
			cell.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
			cell.colSpan = tabeHead.firstElementChild.children.length;
			row.append(cell);
		}, 400);

		$.ajax({
	        type: 'GET',
	        url: getBannedModerDataListURL,
	        data: {
	            'owner': chatOwnerUsername,
	        },
	        success: function(response) {
	            clearTimeout(timeout);
	            console.log(response.data);
	        },
	    });
	});
}
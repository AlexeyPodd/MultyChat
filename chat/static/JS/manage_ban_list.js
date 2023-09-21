const bansTableBody = document.getElementById('bans-table-body');
const bansTableHead = document.getElementById('bans-table-head');
const chatOwnerSelect = document.getElementById('chat-owner-select');

const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value;
const unbanURL = JSON.parse(document.getElementById('unban-url').textContent);
const getBannedModerDataListURL = JSON.parse(document.getElementById('banned-moder-data-list-url').textContent);
const userUsername = JSON.parse(document.getElementById('username').textContent);
let chatOwnerUsername = chatOwnerSelect ? chatOwnerSelect.value : userUsername;

const isAdminTable = bansTableHead.firstElementChild.children[1].textContent=="Chat Owner";
const expiredMark = "Expired";
const indefiniteMark = 'Indefinite';
const inAllChatsMark = 'All Chats';

const dateTimeFormat = {
	weekday: 'short',
	year: 'numeric',
	month: 'short',
	day: 'numeric',
	hour: 'numeric',
	minute: 'numeric',
	second: 'numeric',
}


if (bansTableBody) {
	bansTableBody.addEventListener('click', unbanButtonListener);
}


if (chatOwnerSelect) {
	chatOwnerSelect.addEventListener('change', function(event) {
		chatOwnerUsername = event.currentTarget.value;
		loadBansTable();
	});
}

document.addEventListener("DOMContentLoaded", loadBansTable);

function loadBansTable() {
	// Setting spiner
	const timeout = setTimeout(() => {
		bansTableBody.innerHTML = '';
		const tabeHead = bansTableBody.previousElementSibling;
		
		const row = document.createElement('tr');			
		row.className = 'table-light';
		bansTableBody.append(row);
		const cell = document.createElement('td');
		cell.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
		cell.colSpan = tabeHead.firstElementChild.children.length;
		row.append(cell);
	}, 400);

	// loading data and building table body
	$.ajax({
	    type: 'GET',
	    url: getBannedModerDataListURL,
	    data: {
	        'owner': chatOwnerUsername,
	    },
	    success: function(response) {
	    	const newBansTableRows = [];
	    	const timeNow = Date.now();
	        for (banData of response.data) {
	        	newBansTableRows.push(createBansTableRow(banData, timeNow));
	        }
	        clearTimeout(timeout);
	        bansTableBody.innerHTML = '';
	        newBansTableRows.forEach((row) => bansTableBody.append(row));
	    },
	});
}

function createBansTableRow(rowData, timeNow, allBans=false, isSecondaryBan=false) {
	const timeStart = new Date(rowData.time_start);
	const timeEnd = rowData.time_end ? new Date(rowData.time_end) : null;

	const row = document.createElement('tr');
	if (!timeEnd) row.className = 'table-danger';

	const cellUsername = document.createElement('th');
	cellUsername.scope = 'row';
	cellUsername.textContent = rowData.banned_user__username;

	const cellRemaining = document.createElement('td');
	if (timeEnd) {
		cellRemaining.textContent = getDateDifferenceFormated(timeNow, timeEnd);
	}

	const cellDuration = document.createElement('td');
	if (timeEnd) cellDuration.textContent = getDateDifferenceFormated(timeStart, timeEnd);

	const cellDateEnd = document.createElement('td');
	cellDateEnd.textContent = timeEnd ? timeEnd.toLocaleString('en-us', dateTimeFormat) : indefiniteMark;

	const cellDateStart = document.createElement('td');
	cellDateStart.textContent = timeStart.toLocaleString('en-us', dateTimeFormat);

	const cellbannedBy = document.createElement('td');
	cellbannedBy.textContent = rowData.banned_by__username;

	const cellUnbanButton = document.createElement('td');
	const cellInnerUnbunButton = document.createElement('div');
	cellInnerUnbunButton.className = 'd-grid gap-2 d-block';
	cellUnbanButton.append(cellInnerUnbunButton);
	if (timeEnd || userUsername == chatOwnerUsername || isAdminTable) {
		const unbanButton = document.createElement('button');
		unbanButton.type = 'button';
		unbanButton.className = "btn btn-sm btn-info btn-unban";
		unbanButton.setAttribute('data-banned-username', rowData.banned_user__username);
		unbanButton.setAttribute('data-ban-chat-owner', rowData.chat_owner__username ? rowData.chat_owner__username : '');
		unbanButton.textContent = 'Unban';
		cellInnerUnbunButton.append(unbanButton);
	}

	row.append(cellUsername);
	row.append(cellRemaining);
	row.append(cellDuration);
	row.append(cellDateEnd);
	row.append(cellDateStart);
	row.append(cellbannedBy);
	row.append(cellUnbanButton);

	if (isAdminTable) {
		const cellOwnerUsername = document.createElement('td');
		cellOwnerUsername.textContent = rowData.chat_owner__username ? rowData.chat_owner__username : inAllChatsMark;

		cellUsername.after(cellOwnerUsername);

		if (allBans && timeEnd && timeEnd < timeNow) {
			cellRemaining.textContent = expiredMark;
			row.className = 'table-secondary';
			Array.from(cellInnerUnbunButton.children).forEach((element) => element.remove());
		}

		if (allBans && isSecondaryBan) {
			cellInnerUnbunButton.lastElementChild.remove();
		}

		if (allBans && !(timeEnd && timeEnd < timeNow)) {
			const delBanButton = document.createElement('button');
			delBanButton.type = 'button';
			delBanButton.className = "btn btn-sm btn-danger btn-del-ban";
			delBanButton.setAttribute('data-ban-id', rowData.id);
			delBanButton.setAttribute('data-banned-username', rowData.banned_user__username);
			delBanButton.setAttribute('data-ban-chat-owner', rowData.chat_owner__username ? rowData.chat_owner__username : '');
			delBanButton.textContent = 'Delete';
			cellInnerUnbunButton.append(delBanButton);
		}
	}

	return row;
}

function getDateDifferenceFormated(dateStart, dateEnd) {
	const diff = dateEnd - dateStart;
	const days = Math.floor(diff / (1000 * 60 * 60 * 24));
	const hours = Math.floor(diff / (1000 * 60 * 60)) - days * 24;
	if (days) return `${days} days, ${hours} hours`;
	const minutes = Math.floor(diff / (1000 * 60) - days * 24 - hours * 60);
	if (hours) return `${hours} hours, ${minutes} minutes`;
	else return `${minutes} minutes`
}

function unbanButtonListener(event) {
	if (!event.target.classList.contains('btn-unban')) return;

	const bannedUsername = event.target.getAttribute('data-banned-username');
	const chatOwnerUsernameInner = chatOwnerUsername ? chatOwnerUsername : event.target.getAttribute('data-ban-chat-owner');
	
	ownerName = chatOwnerUsernameInner == userUsername ? 'your' : chatOwnerUsernameInner;
	console.log(ownerName, typeof ownerName);
	askingName = ownerName ? ownerName : inAllChatsMark;
	if (!window.confirm(`Are you sure you want to unban ${bannedUsername} in ${askingName}`)) return;

	$.ajax({
        type: 'POST',
        url: unbanURL,
        data: {
            csrfmiddlewaretoken: csrfToken,
            chatOwnerUsername: chatOwnerUsernameInner,
            bannedUsername,
        },
        success: function() {
        	const rows_to_remove = [];
            let row = event.target.parentElement.parentElement.parentElement;

            do {
            	rows_to_remove.push(row);
            	row = row.nextElementSibling;
            }
            while (isAdminTable && row && row.firstElementChild.textContent == bannedUsername && row.children[1].textContent == chatOwnerUsernameInner && row.children[2].textContent != expiredMark);
            
            rows_to_remove.forEach((element) => element.remove());
        },
    });	
}
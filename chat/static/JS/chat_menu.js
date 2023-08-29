const minBanLimitMinutes = 20;
const maxBanLimitMinutes = 180;
const minBanLimitHours = 1;
const maxBanLimitHours = 48;
const minBanLimitDays = 1;
const maxBanLimitDays = 30;


document.getElementById('chat').addEventListener("contextmenu", (e)=> e.preventDefault());

document.querySelectorAll('.message-author').forEach((element) => {
	element.addEventListener("contextmenu", showChatContextMenu);
});

window.addEventListener('mousedown', (event) => {
	const contextMenu = document.getElementById('chat-user-dropdown-menu');
	if (contextMenu) contextMenu.remove();
});


function showChatContextMenu(event) {
	event.preventDefault();

	const contextMenu = createUserContextMenu(event.currentTarget.getAttribute('data-sender-username'));
	document.body.append(contextMenu);

	if (event.clientX + contextMenu.offsetWidth > document.documentElement.clientWidth) {
		contextMenu.style.left = event.clientX-contextMenu.offsetWidth+"px";
	}
	else{
		contextMenu.style.left = event.clientX+"px";	
	}

	if (event.clientY + contextMenu.offsetHeight > document.documentElement.clientHeight) {
		contextMenu.style.top = event.clientY-contextMenu.offsetHeight+"px";
	}
	else {
		contextMenu.style.top = event.clientY+"px";
	}
}

function createUserContextMenu(senderUsername) {
	menuDiv = document.createElement('div');
	menuDiv.id = 'chat-user-dropdown-menu';
	menuDiv.setAttribute('data-sender-username', senderUsername);

	if (senderUsername != userUsername) {

		// Private messages item
		if (chatIsOpen) {
			menuDiv.append(createContextMenuItem('Write Private Message', initiatePrivateMessageListener));
		}
		
		// Black list item
		menuDiv.append(createContextMenuItem('Add to Black List', addUserToBlackListListener));

		// Moderators management items
		if (userUsername == chatOwnerUsername) {
			if (moderUsernames.has(senderUsername)) {
				menuDiv.append(createContextMenuItem('Demote Moderator', demoteModeratorListener));
			}
			else {
				menuDiv.append(createContextMenuItem('Appoint Moderator', appointModeratorListener));
			}
		}

		// Ban management items
		if (moderUsernames.has(senderUsername) || userUsername == chatOwnerUsername || userHasAdminPrivileges) {
			menuDiv.append(createContextMenuItem('Ban User', showBanMenuListener));
		}
	}

	menuDiv.addEventListener('mousedown', (event) => event.stopPropagation());
	menuDiv.addEventListener('contextmenu', (event) => event.preventDefault());

	return menuDiv;
}

function createContextMenuItem(label, action) {
	const menuItem = document.createElement('div');
	menuItem.className = 'menu-item';
	menuItem.textContent = label;
	menuItem.addEventListener('click', action);
	return menuItem;
}

function showBanMenuListener(event) {
	event.preventDefault();

	let banMenu = document.getElementById('ban-menu');
	if (banMenu) {
		banMenu.remove();
		return;
	}

	const contextMenu = event.currentTarget.parentElement;
	const contextMenuStyle = contextMenu.getBoundingClientRect();

	banMenu = createBanMenu(contextMenu);
	contextMenu.append(banMenu);

	// positioning
	if (document.documentElement.clientHeight - contextMenuStyle.bottom > banMenu.offsetHeight) {
		banMenu.style.top = contextMenuStyle.bottom+'px';
		banMenu.style.left = contextMenuStyle.left+'px';
	}
	else {
		banMenu.style.top = contextMenuStyle.top + contextMenuStyle.height / 3 + 'px';
		if (document.documentElement.clientWidth - contextMenuStyle.right > banMenu.offsetWidth) {
			banMenu.style.left = contextMenuStyle.right+'px';
		}
		else {
			banMenu.style.left = contextMenuStyle.left-banMenu.offsetWidth+'px';
		}
	}
}

function createBanMenu(parentMenu) {
	menuDiv = document.createElement('div');
	menuDiv.id = 'ban-menu';

	form = document.createElement('form');
	form.name = 'ban-menu-form';

	menuDivInner = document.createElement('div');
	menuDivInner.id = 'ban-menu-inner';
	menuDivInner.className = 'text-end';

	termTypeInput = document.createElement('select');
	termTypeInput.name = 'term_type_input';
	termTypeInput.id = 'ban-term-type';

	termTypeOptionMinutes = document.createElement('option');
	termTypeOptionMinutes.value = termTypeOptionMinutes.textContent = 'minutes';
	termTypeOptionHours = document.createElement('option');
	termTypeOptionHours.value = termTypeOptionHours.textContent = 'hours';
	termTypeOptionDays = document.createElement('option');
	termTypeOptionDays.value = termTypeOptionDays.textContent = 'days';

	termTypeInput.append(termTypeOptionMinutes);
	termTypeInput.append(termTypeOptionHours);
	termTypeInput.append(termTypeOptionDays);

	termTypeInput.value = 'minutes';

	termInput = document.createElement('input');
	termInput.id = 'ban-term';
	termInput.name = 'term_input';
	termInput.type = 'number';
	termInput.min = minBanLimitMinutes;
	termInput.max = maxBanLimitMinutes;
	termInput.required = true;

	termTypeInput.onchange = (event) => {
		switch (event.currentTarget.value) {
			case termTypeOptionMinutes.value:
				termInput.min = minBanLimitMinutes;
				termInput.max = maxBanLimitMinutes;
				break;
			case termTypeOptionHours.value:
				termInput.min = minBanLimitHours;
				termInput.max = maxBanLimitHours;
				break;
			case termTypeOptionDays.value:
				termInput.min = minBanLimitDays;
				termInput.max = maxBanLimitDays;
				break;
		}
		if (Number(termInput.value) < Number(termInput.min)) termInput.value = termInput.min;
		if (Number(termInput.value) > Number(termInput.max)) termInput.value = termInput.max;
	}

	submitButton = document.createElement('input');
	submitButton.type = 'submit';
	submitButton.value = 'Ban';
	submitButton.id = 'ban-button';
	submitButton.className = 'btn btn-sm btn-danger m-2 text-center w-50';

	menuDivInner.append(termInput);
	menuDivInner.append(termTypeInput);
	menuDivInner.append(submitButton);
	form.append(menuDivInner);

	form.onsubmit = banListener;

	menuDiv.append(form);
	return menuDiv;
}

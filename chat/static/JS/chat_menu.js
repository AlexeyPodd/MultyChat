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

	const contextMenu = createUserContextMenu(
		event.currentTarget.getAttribute('data-sender-username'),
		event.currentTarget.getAttribute('data-sender-status'),
	);
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

function createUserContextMenu(senderUsername, senderStatus) {
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
			if (senderStatus == 'moderator') {
				menuDiv.append(createContextMenuItem('Demote Moderator', demoteModeratorListener));
			}
			if (senderStatus == 'user') {
				menuDiv.append(createContextMenuItem('Appoint Moderator', appointModeratorListener));
			}
		}

		// Ban management items
		if (amModer || userUsername == chatOwnerUsername || userHasAdminPrivileges) {
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
		if (document.documentElement.clientHeight - contextMenuStyle.bottom + contextMenuStyle.height * 2 / 3 > banMenu.offsetHeight) {
			banMenu.style.top = contextMenuStyle.top + contextMenuStyle.height / 3 + 'px';
		}
		else {
			banMenu.style.bottom = 0;
		}
		if (document.documentElement.clientWidth - contextMenuStyle.right > banMenu.offsetWidth) {
			banMenu.style.left = contextMenuStyle.right+'px';
		}
		else {
			banMenu.style.left = contextMenuStyle.left-banMenu.offsetWidth+'px';
		}
	}
}

function createBanMenu(parentMenu) {
	const menuDiv = document.createElement('div');
	menuDiv.id = 'ban-menu';

	const form = document.createElement('form');
	form.name = 'ban-menu-form';

	const menuDivInner = document.createElement('div');
	menuDivInner.id = 'ban-menu-inner';

	const termTypeInput = document.createElement('select');
	termTypeInput.name = 'term_type_input';
	termTypeInput.id = 'ban-term-type';

	const termTypeOptionMinutes = document.createElement('option');
	termTypeOptionMinutes.value = termTypeOptionMinutes.textContent = 'minutes';
	const termTypeOptionHours = document.createElement('option');
	termTypeOptionHours.value = termTypeOptionHours.textContent = 'hours';
	const termTypeOptionDays = document.createElement('option');
	termTypeOptionDays.value = termTypeOptionDays.textContent = 'days';

	termTypeInput.append(termTypeOptionMinutes);
	termTypeInput.append(termTypeOptionHours);
	termTypeInput.append(termTypeOptionDays);

	termTypeInput.value = 'minutes';

	const termInput = document.createElement('input');
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

	let indefinitelyBanItem = null;
	if (userUsername == chatOwnerUsername || userHasAdminPrivileges) {
		const indefinitelyCheckBox = document.createElement('input');
		indefinitelyCheckBox.type = 'checkbox';
		indefinitelyCheckBox.name = 'ban_indefinitely';
		indefinitelyCheckBox.id = 'ban_indefinitely';
		indefinitelyCheckBox.className = 'ban-menu-checkbox';

		const indefinitelyCheckBoxLabel = document.createElement('label');
		indefinitelyCheckBoxLabel.htmlFor = indefinitelyCheckBox.name;
		indefinitelyCheckBoxLabel.id = indefinitelyCheckBox.id+'_label';
		indefinitelyCheckBoxLabel.innerHTML = 'Ban Indefinitely';
		indefinitelyCheckBoxLabel.className = 'ban-menu-checkbox-label';

		indefinitelyBanItem = document.createElement('div');

		indefinitelyBanItem.append(indefinitelyCheckBox);
		indefinitelyBanItem.append(indefinitelyCheckBoxLabel);

		indefinitelyCheckBox.onchange = (event) => {
			termTypeInput.disabled = event.currentTarget.checked;
			termInput.disabled = event.currentTarget.checked;
			termInput.required = !event.currentTarget.checked;
		};
	}

	let inAllChatsBanItem = null;
	if (userHasAdminPrivileges) {
		const inAllChatsCheckBox = document.createElement('input');
		inAllChatsCheckBox.type = 'checkbox';
		inAllChatsCheckBox.name = 'ban_in_all_chasts';
		inAllChatsCheckBox.id = 'ban_in_all_chasts';
		inAllChatsCheckBox.className = 'ban-menu-checkbox';

		const inAllChatsCheckBoxLabel = document.createElement('label');
		inAllChatsCheckBoxLabel.htmlFor = inAllChatsCheckBox.name;
		inAllChatsCheckBoxLabel.id = inAllChatsCheckBox.id+'_label';
		inAllChatsCheckBoxLabel.innerHTML = 'Ban in all chats';
		inAllChatsCheckBoxLabel.className = 'ban-menu-checkbox-label';

		inAllChatsBanItem = document.createElement('div');

		inAllChatsBanItem.append(inAllChatsCheckBox);
		inAllChatsBanItem.append(inAllChatsCheckBoxLabel);
	}

	const submitButtonBlock = document.createElement('div');
	submitButtonBlock.className = 'text-end';

	const submitButton = document.createElement('input');
	submitButton.type = 'submit';
	submitButton.value = 'Ban';
	submitButton.id = 'ban-button';
	submitButton.className = 'btn btn-sm btn-danger m-2 text-center w-50';
	submitButtonBlock.append(submitButton);

	menuDivInner.append(termInput);
	menuDivInner.append(termTypeInput);

	if (indefinitelyBanItem) {
		menuDivInner.append(indefinitelyBanItem);
	}

	if (inAllChatsBanItem) {
		menuDivInner.append(inAllChatsBanItem);
	}

	menuDivInner.append(submitButtonBlock);
	form.append(menuDivInner);

	form.onsubmit = banListener;

	menuDiv.append(form);
	return menuDiv;
}

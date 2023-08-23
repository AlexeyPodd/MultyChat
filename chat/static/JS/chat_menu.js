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

	const contextMenu = createUserContextMenu(event.currentTarget.getAttribute('data-sender-slug'));

	document.body.append(contextMenu);
	contextMenu.style.left = event.clientX+"px";
	contextMenu.style.top = event.clientY+"px";
}

function createUserContextMenu(senderSlug) {
	menuDiv = document.createElement('div');
	menuDiv.id = 'chat-user-dropdown-menu';

	if (senderSlug != userUsernameSlug) {

		// Black list and private messages items
		menuDiv.append(createContextMenuItem('add to black list', addUserToPrivateListListener));
		menuDiv.append(createContextMenuItem('write private message', initiatePrivateMessageListener));

		// Moderators management items
		if (userUsernameSlug == chatOwnerSlug) {
			if (moderSlugs.includes(senderSlug)) {
				menuDiv.append(createContextMenuItem('demote moderator', demoteModeratorListener));
			}
			else {
				menuDiv.append(createContextMenuItem('appoint moderator', appointModeratorListener));
			}
		}

		// Ban management items
		if (moderSlugs.includes(senderSlug) || userUsernameSlug == chatOwnerSlug || userHasAdminPrivileges) {
			menuDiv.append(createContextMenuItem('ban user', expandBanMenuListener));
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

function addUserToPrivateListListener(event) {
	console.log('addUserToPrivateList');
}

function initiatePrivateMessageListener(event) {
	console.log('initiatePrivateMessage');
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
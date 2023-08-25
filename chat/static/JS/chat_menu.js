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

	contextMenu.style.left = event.clientX+"px";
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
			if (moderUsernames.includes(senderUsername)) {
				menuDiv.append(createContextMenuItem('Demote Moderator', demoteModeratorListener));
			}
			else {
				menuDiv.append(createContextMenuItem('Appoint Moderator', appointModeratorListener));
			}
		}

		// Ban management items
		if (moderUsernames.includes(senderUsername) || userUsername == chatOwnerUsername || userHasAdminPrivileges) {
			menuDiv.append(createContextMenuItem('Ban User', expandBanMenuListener));
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
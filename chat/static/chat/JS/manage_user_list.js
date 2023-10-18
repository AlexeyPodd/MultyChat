const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]');

document.querySelectorAll('.action-btn').forEach((element) => {
	element.addEventListener("click", sendPOSTUnbanUser);
});


function sendPOSTUnbanUser(event) {
	event.preventDefault();

	const userUsername = event.currentTarget.dataset.userUsername;

	const form = document.createElement('form');
	form.method = 'POST';
	form.append(csrfToken.cloneNode());

	const userUsernameInput = document.createElement('input');
	userUsernameInput.name = 'username';
	userUsernameInput.value = userUsername;
	form.append(userUsernameInput);

	document.body.append(form);
	form.submit();
}
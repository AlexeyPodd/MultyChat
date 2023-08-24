const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]');

document.querySelectorAll('.unban-btn').forEach((element) => {
	element.addEventListener("click", sendPOSTUnbanUser);
});


function sendPOSTUnbanUser(event) {
	event.preventDefault();

	const userSlug = event.currentTarget.dataset.userSlug;

	const form = document.createElement('form');
	form.method = 'POST';
	form.append(csrfToken.cloneNode());

	const userSlugInput = document.createElement('input');
	userSlugInput.name = 'username_slug';
	userSlugInput.value = userSlug;
	form.append(userSlugInput);

	document.body.append(form);
	form.submit();
}
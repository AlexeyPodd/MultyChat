const searchBannedAdminDataListUrl = JSON.parse(document.getElementById('banned-admin-data-list-url').textContent);

const searchForm = document.forms.searchForm;


searchForm.onsubmit = (event) => {
	event.preventDefault();

	if (!searchForm.owner.value && !searchForm.user.value) {
		alert('You should fill in at least one search field');
		return;
	}

	$.ajax({
	    type: 'GET',
	    url: searchBannedAdminDataListUrl,
	    data: {
	        'owner': searchForm.owner.value,
	        'user': searchForm.user.value,
	        'all': Number(searchForm.all_bans.checked),
	    },
	    success: function(response) {
	    	console.log('success!');
	    	// const newBansTableRows = [];
	        // for (banData of response.data) {
	        // 	newBansTableRows.push(createBansTableRow(banData));
	        // }
	        // clearTimeout(timeout);
	        // bansTableBody.innerHTML = '';
	        // newBansTableRows.forEach((row) => bansTableBody.append(row));
	    },
	});
}
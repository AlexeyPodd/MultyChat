const searchBannedAdminDataListUrl = JSON.parse(document.getElementById('banned-admin-data-list-url').textContent);

const searchForm = document.forms.searchForm;


if (bansTableBody) {
	bansTableBody.addEventListener('click', delBanButtonListener);
}

searchForm.onsubmit = (event) => {
	event.preventDefault();

	if (!searchForm.owner.value && !searchForm.user.value) {
		alert('You should fill in at least one search field');
		return;
	}

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

	removeSearchReport();

	const dataToSend = {
	        owner: searchForm.owner.value,
	        user: searchForm.user.value,
	        all: Number(searchForm.all_bans.checked),
	    }

	// loading data and building table body
	$.ajax({
	    type: 'GET',
	    url: searchBannedAdminDataListUrl,
	    data: dataToSend,
	    sentData: dataToSend,
	    success: function(response) {
	    	chatOwnerUsername = this.sentData.owner;
	    	if (response.data.length) {
		    	const newBansTableRows = [];
		    	const timeNow = Date.now();
		    	let isSecondaryBan = false;
		        for (banData of response.data) {
		        	if (this.sentData.all) {
		        		isSecondaryBan = newBansTableRows.length && (
		        			this.sentData.owner && newBansTableRows[newBansTableRows.length-1].firstElementChild.textContent == banData.banned_user__username ||
		        			this.sentData.user && newBansTableRows[newBansTableRows.length-1].children[1].textContent == banData.chat_owner__username
		        			);
		        	}
		        	newBansTableRows.push(createBansTableRow(banData, timeNow, allBans=this.sentData.all, isSecondaryBan=isSecondaryBan));

		        }
		        clearTimeout(timeout);
		        bansTableBody.innerHTML = '';

		        newBansTableRows.forEach((row) => bansTableBody.append(row));
		    }
		    else {
		    	clearTimeout(timeout);
		        bansTableBody.innerHTML = '';

		    	showSearchReport("No bans matching search criteria");
		    }
	    },
	    error: function(xhr) {
	    	clearTimeout(timeout);
	        bansTableBody.innerHTML = '';

	        if (xhr.status == 404) {
	        	showSearchReport(`Not found requested ${xhr.responseJSON.model}`);
	        }
	    }
	});
}

function showSearchReport(report) {
	const bansTable = document.getElementById('bans-table');
	const reportDiv = document.createElement('div');
	reportDiv.className = "col-12 col-lg-9 col-xxl-6";
	reportDiv.id = "search-report-div";
	const reportP = document.createElement('p');
	reportP.className = "m-5 text-center h3 text-secondary";
	reportP.textContent = report;

	reportDiv.append(reportP);
	bansTable.after(reportDiv);

}

function removeSearchReport() {
	const reportDiv = document.getElementById('search-report-div');
	if (reportDiv) reportDiv.remove();
}

function delBanButtonListener(event) {
	if (!event.target.classList.contains('btn-del-ban')) return;

	const banId = event.target.getAttribute('data-ban-id');
	const bannedUsername = event.target.getAttribute('data-banned-username');
	const chatOwnerUsername = event.target.getAttribute('data-ban-chat-owner');

	if (!window.confirm(`Are you sure you want to delete ${bannedUsername}\'s ban in ${chatOwnerUsername == userUsername ? 'your' : chatOwnerUsername+'\'s'} chat?`)) return;

	$.ajax({
        type: 'POST',
        url: unbanURL,
        data: {
            csrfmiddlewaretoken: csrfToken,
            banId,
        },
        success: function() {
            row = event.target.parentElement.parentElement.parentElement;
            next_row = row.nextElementSibling;
            if (row.lastElementChild.firstElementChild.children.length == 2 &&
            		next_row.firstElementChild.textContent == bannedUsername &&
            		next_row.children[1].textContent == chatOwnerUsername &&
            		next_row.children[2].textContent != expiredMark) {
            	next_row.lastElementChild.firstElementChild.prepend(row.lastElementChild.firstElementChild.firstElementChild);
            }
            row.remove();
        },
    });	
}
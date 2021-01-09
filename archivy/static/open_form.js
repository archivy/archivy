function openCommand(cmdUrl, updateState, menuItem) {
    if (REQUEST_RUNNING) {
        let leave = confirm("Command is still running. Leave anyway?");
        if (leave) {
            // hack as this is global on page and if we leave the other command cannot run.
            // TODO: fetch will continue to run.
            //  Do a real abort of fetch: https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort
            REQUEST_RUNNING = false;
        } else {
            return;
        }
    }

    let formDiv = document.getElementById('form-div');
    // if (updateState) {
    //
    //     history.pushState({'cmdUrl': cmdUrl}, null, cmdUrl);
    // }
    fetch(cmdUrl)
        .then(function(response) {
            selectMenuItem(menuItem);
            return response.text();
        })
        .then(function(theFormHtml) {
            formDiv.innerHTML = theFormHtml;
			formDiv.scrollIntoView();
        });
}

function selectMenuItem(menuItem) {
    var x = document.getElementsByClassName("command-selected");
    var i;
    for (i = 0; i < x.length; i++) {
        x[i].classList.remove('command-selected');
    }
    menuItem.classList.add('command-selected');
}

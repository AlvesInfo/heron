function openWindowWithPost(url, winName, features, inputTitle, inputHtml) {
    let mapForm = document.createElement("form");
    mapForm.target = winName;
    mapForm.method = "POST";
    mapForm.action = url;
    mapForm.setAttribute("type", "hidden");


    let mapInput = document.createElement("input");
    mapInput.type = "text";
    mapInput.name = "titre_modal";
    mapInput.value = inputTitle;
    mapForm.appendChild(mapInput);

    let testInput = document.createElement("input");
    testInput.type = "text";
    testInput.name = "html_modal";
    testInput.value = inputHtml;
    mapForm.appendChild(testInput);

    document.body.appendChild(mapForm);

    let map = window.open("", winName, features);

    if (map) {
        mapForm.submit();
        mapForm.remove();
    } else {
        alert('Vous devez accepter les popups');
    }
}

function openNewWindow(theURL,winName,features) {
  window.open(theURL,winName,features);
}

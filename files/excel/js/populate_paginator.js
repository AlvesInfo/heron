function paginateWithFilter (page) {
    let get_url = `?page=${page}`;
    for (let filter in attrsFilter) {
        // noinspection JSUnfilteredForInLoop
        if (filter !== "page") {
            let valBalise = $(`#id_${filter}`).val();
            let attr = valBalise === undefined ? '' : valBalise;
            get_url += `&${filter}=${attr}`;
        }
    }
    window.location.href = encodeURI(url + get_url);
}

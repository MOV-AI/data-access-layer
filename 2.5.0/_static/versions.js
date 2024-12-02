window.onload = () => {
    fetch("/versions.json")
        .then(x => x.json())
        .then(data => {
            const url = window.location.href
            const localPage = url.split("/").slice(4).join("/")
            if (data.length > 0) {
                const dl = document.getElementById('docs-versions');
                data.forEach(version => {
                    dl.innerHTML = dl.innerHTML +
                        `<dd><a href="/${version}/${localPage}">${version}</a></dd>`
                })
            }
        })
}

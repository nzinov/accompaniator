function onDownload() {
    var text = document.getElementsByTagName("input")[2];
    var val=text.innerHTML;
    var star = document.getElementsById("mark");
}
function star(num, star) {
        for (var i = 1; i <= num; i++) {
            document.getElementById("star" + i).innerHTML = '<img src="../../static/img/star.png" width="70px" height="70px">';
        }
        for (var i = num + 1; i <= 5; i++) {
            document.getElementById("star" + i).innerHTML = '<img src="../../static/img/star_dark.png" width="70px" height="70px">';
        }
        document.getElementById("id_mark").value = num;
}

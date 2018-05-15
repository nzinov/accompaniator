function onDownload() {
    var text = document.getElementsByTagName("input")[2];
    var val=text.innerHTML;
    var star = document.getElementsById("mark");
}
function star(num, star) {
        for (var i = 1; i <= num; i++) {
            document.getElementById("star" + i).innerHTML = '<img src="../../static/img/star.png" width="100%" height="100%">';
        }
        for (var i = num + 1; i <= 5; i++) {
            document.getElementById("star" + i).innerHTML = '<img src="../../static/img/star_dark.png" width="100%" height="100%">';
        }
        document.getElementById("mark").innerHTML = num;
}

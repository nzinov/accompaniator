function startTimer() {
    var my_timer = document.getElementById("my_timer");
    var time = my_timer.innerHTML;
    var arr = time.split(":");
    var m = arr[0];
    var s = arr[1];
    if (s == 59) {
        if (m == 59) {
            m = 60;
        }
        m++;
        if (m < 10) m = "0" + m;
        s = 0;
    }
    else s++;
    if (s < 10) s = "0" + s;
    document.getElementById("my_timer").innerHTML = m + ":" + s;
    setTimeout(startTimer, 1000);
}

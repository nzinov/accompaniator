var audio_context;
var ws;
var recorder;
var queve = [];
var isPlaying = false;
var prev_length = 0;
var isRecording = false;
var frames = [];
var frames_per_send = 10;
var frame_size = 1024;
var isInited = false;
var numChannels = 1;
var mimeType = 'audio/wav';
var sampleRate = 44100;
var state = "init";

function startUserMedia(stream) {
    var input = audio_context.createMediaStreamSource(stream);
    recorder = new Recorder(input);
}


function sleep(milliseconds) {
    var start = new Date().getTime();
    for (var i = 0; i < 1e7; i++) {
        if ((new Date().getTime() - start) > milliseconds) {
            break;
        }
    }
}


function WS() {

}


function Push(blob) {
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');

    au.controls = true;
    au.src = url;
    //au.play();
    queve.push(au);
}


function RealPlay() {
    if (isRecording) {
        if (queve.length > 0 && !isPlaying) {
            isPlaying = true;
            var song = queve.shift();
            song.play();
            setTimeout(function () {
                isPlaying = false;
            }, 200)
        }
        setTimeout(RealPlay, 200);
    }
}

function init(config) {
    sampleRate = config.sampleRate;
    numChannels = config.numChannels;
    initBuffers();
}

function simpleExportWAV() {
    interleaved = mergeBuffers(frames, frames.length * frame_size);
    dataview = encodeWAV(interleaved);
    return new Blob([dataview], {type: mimeType});
}


function exportWAV(array_frames) {
    interleaved = mergeBuffers(array_frames, array_frames.length * frame_size);
    dataview = encodeWAV(interleaved);
    return new Blob([dataview], {type: mimeType});
}


function mergeBuffers(recBuffers, recLength) {
    var result = new Float32Array(recLength);
    var offset = 0;
    for (var i = 0; i < recBuffers.length; i++) {
        result.set(recBuffers[i], offset);
        offset += recBuffers[i].length;
    }
    return result;
}

function floatTo16BitPCM(output, offset, input) {
    for (var i = 0; i < input.length; i++, offset += 2) {
        var s = Math.max(-1, Math.min(1, input[i]));
        output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
}

function writeString(view, offset, string) {
    for (var i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

function encodeWAV(samples) {
    var buffer = new ArrayBuffer(44 + samples.length * 2);
    var view = new DataView(buffer);

    /* RIFF identifier */
    writeString(view, 0, 'RIFF');
    /* RIFF chunk length */
    view.setUint32(4, 36 + samples.length * 2, true);
    /* RIFF type */
    writeString(view, 8, 'WAVE');
    /* format chunk identifier */
    writeString(view, 12, 'fmt ');
    /* format chunk length */
    view.setUint32(16, 16, true);
    /* sample format (raw) */
    view.setUint16(20, 1, true);
    /* channel count */
    view.setUint16(22, numChannels, true);
    /* sample rate */
    view.setUint32(24, sampleRate, true);
    /* byte rate (sample rate * block align) */
    view.setUint32(28, sampleRate * 4, true);
    /* block align (channel count * bytes per sample) */
    view.setUint16(32, numChannels * 2, true);
    /* bits per sample */
    view.setUint16(34, 16, true);
    /* data chunk identifier */
    writeString(view, 36, 'data');
    /* data chunk length */
    view.setUint32(40, samples.length * 2, true);

    floatTo16BitPCM(view, 44, samples);

    return view;
}


function TestPlay() {
    Push(simpleExportWAV());
}

function Send(array) {
}

function SendFrames() {
    console.log(frames.length);
    while (frames.length > frames_per_send) {
        toSend = [];
        for (var i = 0; i < frames_per_send; i++) {
            elem = frames.shift();
            toSend.push(elem);
        }
        //toSendStr = JSON.stringify(toSend);
        toSendBlob = exportWAV(toSend);
        console.log("toSendBlob", toSendBlob);
        //Push(toSendBlob);
        if (ws.readyState == 1) {
            ws.send(toSendBlob);
        }
        else {
            console.log("blob is lost")
        }
    }
    if (isRecording) {
        setTimeout(SendFrames, 300);
    }
}


function Stop() {
    state = 'stopping';
    recorder && recorder.stop();
    recorder.clear();
    isRecording = false;
    setTimeout(function () {
        state = 'record';
    }, 1000);
    ws.close();
}


function Recording() {
    if (state == "record") {
        ws = new WebSocket('ws://demos.kaazing.com/echo');
        ws.onmessage = function (ev) {
            var s = ev.data;
            console.log(s);
            Push(s);
        };
        queve = [];
        frames = [];
        isRecording = true;
        recorder && recorder.record();
        state = "recording";
        setTimeout(SendFrames, 100);
        Recording();
        RealPlay();

    }
    else if (state == "recording") {
        setTimeout(WriteBuffer, 100);
        setTimeout(function () {
            Recording()
        }, 200);
    }
}

function Write(buffer) {
    i = 0;
    while (i + frame_size <= buffer.length) {
        frames.push(buffer.slice(i, i + frame_size));
        i += frame_size;
    }

}

function WriteBuffer() {
    recorder && recorder.getBuffer(function (blob) {
        Write(blob[0]);
        recorder.clear();
    });
}

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


function Init() {
    if (isInited) {
        if (state == 'recording') {
            Stop();
        }
        else if (state == 'record') {
            Recording();
        }
    }
    else {
        try {
            startTimer();
            // webkit shim
            window.AudioContext = window.AudioContext || window.webkitAudioContext;
            navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia;
            window.URL = window.URL || window.webkitURL;

            audio_context = new window.AudioContext;
            isInited = true;
            state = 'record';
        } catch (e) {
            alert('No web audio support in this browser!');
        }

        navigator.getUserMedia({audio: true}, startUserMedia, function (e) {
            __log('No live audio input: ' + e);
        });
    }
};
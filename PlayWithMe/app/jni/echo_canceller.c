#include "echo_canceller.h"

SpeexEchoState *echoState;
SpeexPreprocessState *den;

JNIEXPORT void JNICALL Java_speex_EchoCanceller_open
        (JNIEnv *env, jobject jObj, jint jSampleRate, jint jBufSize, jint jTotalSize) {
    // jBufSize - frame_size
    // jTotalSize - filter_length (tail_length)
    int sampleRate = jSampleRate;
    echoState = speex_echo_state_init(jBufSize, jTotalSize);
    den = speex_preprocess_state_init(jBufSize, sampleRate);
    speex_echo_ctl(echoState, SPEEX_ECHO_SET_SAMPLING_RATE, &sampleRate);
    speex_preprocess_ctl(den, SPEEX_PREPROCESS_SET_ECHO_STATE, echoState);
    //speex_preprocess_ctl(den, SPEEX_PREPROCESS_SET_DENOISE, echoState);
    //speex_preprocess_ctl(den, SPEEX_PREPROCESS_SET_DEREVERB, echoState);
}

JNIEXPORT jshortArray JNICALL Java_speex_EchoCanceller_process
        (JNIEnv *env, jobject jObj, jshortArray input_frame, jshortArray echo_frame) {
    //create native shorts from java shorts
    jshort *native_input_frame = (*env)->GetShortArrayElements(env, input_frame, 0);
    jshort *native_echo_frame = (*env)->GetShortArrayElements(env, echo_frame, 0);

    //allocate memory for output data
    jint length = (*env)->GetArrayLength(env, input_frame);
    jshortArray temp = (*env)->NewShortArray(env, length);
    jshort *native_output_frame = (*env)->GetShortArrayElements(env, temp, 0);

    //call echo cancellation
    speex_echo_cancellation(echoState, native_input_frame, native_echo_frame, native_output_frame);
    //preprocess output frame
    speex_preprocess_run(den, native_output_frame);

    //convert native output to java layer output
    jshortArray output_shorts = (*env)->NewShortArray(env, length);
    (*env)->SetShortArrayRegion(env, output_shorts, 0, length, native_output_frame);

    //cleanup and return
    (*env)->ReleaseShortArrayElements(env, input_frame, native_input_frame, 0);
    (*env)->ReleaseShortArrayElements(env, echo_frame, native_echo_frame, 0);
    (*env)->ReleaseShortArrayElements(env, temp, native_output_frame, 0);

    return output_shorts;
}


JNIEXPORT void JNICALL Java_speex_EchoCanceller_playback
        (JNIEnv *env, jobject jObj, jshortArray echo_frame) {
    jshort *native_echo_frame = (*env)->GetShortArrayElements(env, echo_frame, 0);
    speex_echo_playback(echoState, native_echo_frame);
    (*env)->ReleaseShortArrayElements(env, echo_frame, native_echo_frame, 0);
}

JNIEXPORT jshortArray JNICALL Java_speex_EchoCanceller_capture
        (JNIEnv *env, jobject jObj, jshortArray input_frame) {
    (*env)->MonitorEnter(env, jObj);
    jshort *native_input_frame = (*env)->GetShortArrayElements(env, input_frame, 0);

    jint length = (*env)->GetArrayLength(env, input_frame);
    jshortArray temp = (*env)->NewShortArray(env, length);
    jshort *native_output_frame = (*env)->GetShortArrayElements(env, temp, 0);

    speex_echo_capture(echoState, native_input_frame, native_output_frame);
    speex_preprocess_run(den, native_output_frame);

    jshortArray output_shorts = (*env)->NewShortArray(env, length);
    (*env)->SetShortArrayRegion(env, output_shorts, 0, length, native_output_frame);

    (*env)->ReleaseShortArrayElements(env, input_frame, native_input_frame, 0);
    (*env)->ReleaseShortArrayElements(env, temp, native_output_frame, 0);
    (*env)->MonitorExit(env, jObj);
    return output_shorts;
}

JNIEXPORT jbyteArray JNICALL Java_speex_EchoCanceller_captureBytes
        (JNIEnv *env, jobject jObj, jbyteArray input_frame) {
    (*env)->MonitorEnter(env, jObj);
    jbyte *native_input_frame = (*env)->GetByteArrayElements(env, input_frame, 0);

    jint length = (*env)->GetArrayLength(env, input_frame);
    jbyteArray temp = (*env)->NewByteArray(env, length*2);
    jbyte *native_output_frame = (*env)->GetByteArrayElements(env, temp, 0);

    speex_echo_capture(echoState, (spx_int16_t*)native_input_frame, (spx_int16_t*)native_output_frame);
    speex_preprocess_run(den, (spx_int16_t*)native_output_frame);

    jbyteArray output_shorts = (*env)->NewByteArray(env, length*2);
    (*env)->SetByteArrayRegion(env, output_shorts, 0, length*2, native_output_frame);

    (*env)->ReleaseByteArrayElements(env, input_frame, native_input_frame, 0);
    (*env)->ReleaseByteArrayElements(env, temp, native_output_frame, 0);
    (*env)->MonitorExit(env, jObj);
    return output_shorts;
}

JNIEXPORT void JNICALL Java_speex_EchoCanceller_reset(JNIEnv *env, jobject jObj) {
    speex_echo_state_reset(echoState);
}

JNIEXPORT void JNICALL Java_speex_EchoCanceller_close
        (JNIEnv *env, jobject jObj) {
    speex_echo_state_destroy(echoState);
    speex_preprocess_state_destroy(den);
    echoState = 0;
    den = 0;
}
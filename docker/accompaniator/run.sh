docker run -ti --rm \
    -v /dev/snd:/dev/snd \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v /run/dbus/:/run/dbus/:rw -v /dev/shm:/dev/shm \
    --group-add audio \
    --privileged \
    docker_accompaniator bash

FROM base/devel

RUN mkdir /build
WORKDIR /build

RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm alsa-lib alsa-utils alsa-plugins

RUN pacman -S --noconfirm fluidsynth soundfont-fluid mpg123

RUN pacman -S --noconfirm python python-pip python-virtualenv git \
    && mkdir env \
    && python3 -m venv env/ \
    && source env/bin/activate
    
# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
ADD requirements.txt /build/

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# move later to more appropriate place
RUN pacman -S --noconfirm rtmidi htop

ADD . /build/

RUN mv asound.conf /etc/asound.conf
RUN cat ./.bashrc >> ~/.bashrc

CMD ./startup.sh

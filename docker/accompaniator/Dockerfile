FROM base/devel

RUN mkdir /build
WORKDIR /build

RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm alsa-lib alsa-utils alsa-plugins

RUN pacman -S --noconfirm fluidsynth soundfont-fluid mpg123 rtmidi

RUN pacman -S --noconfirm python python-pip python-virtualenv git htop \
    && mkdir env \
    && python3 -m venv env/ \
    && source env/bin/activate

RUN pacman -S --noconfirm npm
RUN paccache -rk 0

# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
ADD requirements.txt /build/
ADD package.json /build/

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

RUN npm install

ADD . /build/

RUN mv asound.conf /etc/asound.conf
RUN cat ./.bashrc >> ~/.bashrc

RUN git clone https://github.com/nzinov/accompaniator

CMD ./startup.sh

FROM python:3.9-buster
ENV BOT_NAME=$BOT_NAME

RUN apt-get update \
    && apt-get -y install wget xvfb unzip \
    && apt-get clean
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable=

#RUN apt update  \
#    && apt upgrade -y  \
#    && apt install -y unzip xvfb libxss1 libappindicator1 libindicator7 fonts-liberation \
#    libasound2 libatk-bridge2.0-0 libatspi2.0-0 libdrm2 libgbm1 libgtk-3-0 libgtk-4-1 libnspr4 libnss3 \
#    libu2f-udev libvulkan1 libxkbcommon0 xdg-utils \
#    && pip install --upgrade pip
#RUN mkdir /chromedriver
#RUN cd /chromedriver
#RUN rm -rf /usr/local/bin/chromedriver
#RUN wget -N https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip
#RUN unzip -o chromedriver_linux64.zip
#RUN mv /chromedriver /usr/local/bin/
#RUN chmod +x /usr/local/bin/chromedriver


WORKDIR /usr/src/app/"${BOT_NAME:-tg_bot}"

COPY requirements.txt /usr/src/app/"${BOT_NAME:-tg_bot}"
RUN pip install -r /usr/src/app/"${BOT_NAME:-tg_bot}"/requirements.txt

COPY . /usr/src/app/"${BOT_NAME:-tg_bot}"

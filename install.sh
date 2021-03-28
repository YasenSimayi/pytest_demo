#
# install Xvfb
#
apt-get install -y xvfb

#
# install Google Chrome Browser
#
apt-get install -y gconf-service \
    libasound2 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libfontconfig1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libxss1 \
    libnss3 \
    xdg-utils \
    libappindicator1 \
    fonts-liberation
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb

#
# install chromedriver
#
apt-get install -y unzip
wget https://chromedriver.storage.googleapis.com/2.33/chromedriver_linux64.zip
unzip chromedriver_linux64.zip


#
# install selenium
#
apt-get install -y \
    libxml2-dev \
    libxml2 \
    libxslt1-dev \
    python-dev \
    python-pip 
pip install lxml selenium

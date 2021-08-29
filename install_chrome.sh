apt update

apt install -y wget unzip
wget http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_91.0.4472.114-1_amd64.deb
mv google-chrome-stable_91.0.4472.114-1_amd64.deb google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb

apt --fix-broken install -y
dpkg -i google-chrome-stable_current_amd64.deb
wget https://chromedriver.storage.googleapis.com/91.0.4472.101/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/bin/

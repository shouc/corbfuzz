apt update
apt install -y python3-pip redis-server curl build-essential autoconf libtool bison re2c
pip3 install z3-solver
pip3 install -r requirements.txt

apt install -y git vim 

# php dependencies
apt install -y \
    libxml2-dev \
    libcurl4-openssl-dev \
    libjpeg-dev \
    libpng-dev \
    libxpm-dev \
    libmysqlclient-dev \
    libpq-dev \
    libicu-dev \
    libfreetype6-dev \
    libldap2-dev \
    libxslt-dev \
    libssl-dev \
    libldb-dev sqlite libsqlite3-dev libonig-dev

# install nodejs
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.38.0/install.sh | bash
export NVM_DIR=/root/.nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

nvm install --lts
nvm use --lts
export PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"

# build instrumented PHP
mkdir /tmp/cbc
mkdir /tmp/page
cd php
./buildconf 
./configure \
  --enable-mbstring \
  --with-curl \
  --with-openssl \
  --enable-soap \
  --with-mysqli \
  --with-pgsql \
  --with-ldap \
  --enable-intl \
  --with-xsl \
  --with-zlib
make -j30
make install

# build php extension
cd ../extension
phpize
./configure
make -j4
cp modules/hsfuzz.so ../

# set up fake mysql
cd ../fake_mysql
npm install


# Small test
# nvm use --lts
# ./run.sh
# cd ../test
# rm -rf cov && mkdir cov
# php -dextension=../extension/modules/hsfuzz.so -S 0.0.0.0:8888 &
# curl -H "SEED:1" http://0.0.0.0:8888/test.php
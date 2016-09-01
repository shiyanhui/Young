#!/bin/bash

# Setup python environments
# =============================================================
apt-get update
apt-get install -y python-pip build-essential python-dev
pip install pip --upgrade
pip install setuptools --upgrade
pip install fabric virtualenv

# setup main env
mkdir envs
cd envs && virtualenv main
cd main && source bin/activate
pip install -r ../../requirements.txt
pip install monguo

# install PIL
apt-get install -y libjpeg-dev libjpeg8-dev libfreetype6 libfreetype6-dev zlib1g-dev
ln -s `find /usr/lib -name libjpeg.so` /usr/lib/
ln -s `find /usr/lib -name libz.so` /usr/lib
ln -s `find /usr/lib -name libfreetype.so` /usr/lib
wget http://effbot.org/media/downloads/Imaging-1.1.7.tar.gz
tar -zxvf Imaging-1.1.7.tar.gz
cd Imaging-1.1.7 && python setup.py install
cd ../ && rm -rf Imaging-1.1.7*
deactivate

# setup mongo env
cd ../ && virtualenv mongo
cd mongo && source bin/activate
pip install elastic2-doc-manager
pip install mongo-connector
deactivate
cd ../../

# Setup NodeJS environment
# ==============================================================
apt-get install -y nodejs-legacy npm
npm install --global bower
npm install --global gulp
npm install

# setup NSQ
# ==============================================================
wget https://s3.amazonaws.com/bitly-downloads/nsq/nsq-0.3.8.linux-amd64.go1.6.2.tar.gz
tar -zxvf nsq-0.3.8.linux-amd64.go1.6.2.tar.gz
mv nsq-0.3.8.linux-amd64.go1.6.2/bin/* /usr/local/bin
rm -rf nsq-0.3.8.linux-amd64.go1.6.2*

# Setup Ejabberd
# =============================================================
apt-get install -y libexpat1 libexpat1-dev libyaml-0-2 libyaml-dev erlang openssl zlib1g zlib1g-dev libssl-dev libpam0g automake
git clone https://github.com/processone/ejabberd.git
cd ejabberd
./autogen.sh
./configure
make && make install
cd ../ && rm -rf ejabberd

# Setup Elasticsearch
# =============================================================
apt-get install -y default-jre
wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.3.5/elasticsearch-2.3.5.deb
dpkg -i elasticsearch-2.3.5.deb
rm elasticsearch-2.3.5.deb

# Setup Mongodb
# =============================================================
#
# The mongodb installation official document is here
# https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
echo "deb http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.2 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.2.list
apt-get update
apt-get install -y mongodb-org

# The next step you need to do is set Mongodb to replica-set
#
#   1. modify /etc/mongod.conf like this,
#        replication:
#            replSetName: rs0
#
#   2. restart mongodb
#        service mongod restart
#
#   3. enter mongo client and execute
#        rs.initiate()
#
# reference:
#   - https://docs.mongodb.com/manual/tutorial/convert-standalone-to-replica-set/
#   - https://docs.mongodb.com/manual/reference/configuration-options/#replication-options

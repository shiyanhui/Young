#!/bin/bash

# We use iRedMail as our mail server.
# See more here http://www.iredmail.org/index.html

# fqdn is something like mail.young.io
if [ -z $1 ]; then
    echo "Usage: install_mail.sh [your fqdn]"
    exit
fi

hostnamectl set-hostname $1
echo "127.0.0.1 $1" >> /etc/hosts
echo "::1       $1" >> /etc/hosts

# set the timezone
dpkg-reconfigure tzdata

apt-get update
apt-get install -y postfix
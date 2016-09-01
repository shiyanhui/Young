<img src='static/img/logo.png' width='400' title='Young, a full-featured form'>

A Full-featured forum software built with love by [Lime](http://lime66.com) in
[Python](https://www.python.org/).

## Features:

- Classified topics
- Anonymity Support
- Social Network (tweet, friends etc.)
- IM Chat
- Real-time Notification
- Resource Share

## Screenshots

<img src='http://i.imgur.com/jIRssZ8.png' width='280'>
<img src='http://i.imgur.com/NBajysS.png' width='280'>
<img src='http://i.imgur.com/9DhFrZW.png' width='280'>
<img src='http://i.imgur.com/rGjdYBp.png' width='280'>
<img src='http://i.imgur.com/YXtFTuX.png' width='280'>
<img src='http://i.imgur.com/olSroBN.png' width='280'>
<img src='http://i.imgur.com/FW3PkTO.png' width='280'>

## Installation

On Unbuntu 16.04:

    git clone https://github.com/shiyanhui/Young.git
    cd Young && ./scripts/install.sh

Then set your mongodb environment:

    1. open /etc/mongod.conf, add

        replication:
            replSetName: rs0

    2. restart mongodb

        service mongod restart

    3. enter mongo client and execute

        mogno
        rs.initiate()

The next step you shoud initialize the database.

    fab init

If you want to set up your own mail server, execute **setup_mail.sh**,
which will install postfix.

    ./scripts/setup_mail.sh

**NOTE**:

**scripts/install.sh** is only tested on Ubuntu-16.04, so on other
platform you may install manually. Just do as **scripts/install.sh** do step
by step.

## Requirements

    - Mongodb >= 2.6
    - Ejabberd >= 16.08
    - NSQ >= 0.3.8
    - Elasticsearch >= 2.3.5
    - NodeJS >= 4.0

## Development

- you should start all required services before you run it.

```bash
    fab start_service
```

- build the resource.

```bash
    fab build
```

- run it locally.

```bash
    # debug mode is close by default, it will automatically build before run
    fab run

    # run it in debug mode
    fab run:debug=true
```

## License

Young is licensed under the [GNU General Public License v3 (GPL-3)](http://www.gnu.org/copyleft/gpl.html).

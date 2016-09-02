<img src='static/img/logo.png' width='400' title='Young, a full-featured form'>

Young是一个用Python写的功能丰富的、界面小清新的类似NodeBB的社区软件。

## Features:

- 话题按主题分类，你可以查看某一主题的话题
- 支持匿名发帖，匿名评论
- 社交功能（朋友圈，发状态）
- 像QQ一样即时聊天
- 实时提醒
- 资源分享

## Screenshots

<img src='http://i.imgur.com/jIRssZ8.png' width='280'>
<img src='http://i.imgur.com/NBajysS.png' width='280'>
<img src='http://i.imgur.com/9DhFrZW.png' width='280'>
<img src='http://i.imgur.com/rGjdYBp.png' width='280'>
<img src='http://i.imgur.com/YXtFTuX.png' width='280'>
<img src='http://i.imgur.com/olSroBN.png' width='280'>
<img src='http://i.imgur.com/FW3PkTO.png' width='280'>

## Installation

在Unbuntu 16.04上

    git clone https://github.com/shiyanhui/Young.git
    cd Young && ./scripts/install.sh

然后设置你的Mongodb环境

    1. 修改/etc/mongod.conf，添加

        replication:
            replSetName: rs0

    2. 重启Mongodb服务

        service mongod restart

    3. 启动mongo，执行initiate

        mongo
        rs.initiate()

下一步需要做的是初始化Mongodb数据库

    fab init

如果你想自己搭建Email服务器，运行setup_mail.sh脚本

    ./scripts/setup_mail.sh

**注意**:

**scripts/install.sh** 只在Ubuntu16.04上面测试过，如果你是Ubuntu其他版本或者其他
操作系统，你需要手动安装。**scripts/install.sh** 稍微修改一下，一步一步安装即可。

## Requirements

    - Mongodb >= 2.6
    - Ejabberd >= 16.08
    - NSQ >= 0.3.8
    - Elasticsearch >= 2.3.5
    - NodeJS >= 4.0

## Development

- 在运行之前必须启动所有依赖的服务

```bash
    fab start_service
```

- 在非debug模式中，每次修改后，需要重建资源

```bash
    fab build
```

- 本地运行

```bash
    # 默认为非debug模式，run之前会自动地build
    fab run

    # 启用debug模式
    fab run:debug=true
```

## License

[GNU General Public License v3 (GPL-3)](http://www.gnu.org/copyleft/gpl.html).

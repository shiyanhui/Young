# -*- encoding: utf-8 -*-

import os

from fabric.api import local, cd


def init():
    start_service()
    local("/bin/bash -l -c 'source envs/main/bin/activate && python scripts/init_db.py'")


# supervisor is better
def start_service():
    path = os.path.join(os.path.dirname(__file__), "workspace")
    if not os.path.exists(path):
        os.mkdir(path)

    with cd(path):
        try:
            local("ejabberdctl start")
        except:
            pass

        local("service elasticsearch start")
        local("service mongod start")
        local("nohup nsqd -data-path=%s &" % path)

    local("/bin/bash -l -c 'source envs/mongo/bin/activate && nohup "
          "mongo-connector -m localhost:27017 -t localhost:9200 -d "
          "elastic2_doc_manager --continue-on-error &'")


def build():
    local("npm install")
    local("bower install --allow-root")
    local("gulp")


def run(debug=False):
    if debug:
        args = "-debug=true"
    else:
        args = ""
        build()

    local("source envs/main/bin/activate && python server.py %s" % args, shell="/bin/bash")

from fabric import task
from patchwork.files import exists

WEBUI_REPO = "https://github.com/akarca/garage-webui.git"
WEBUI_PATH = "/root/garage-webui"
STORAGE_PATH = "/root/garage-storage"
PNPM = "npx --yes pnpm@9"


@task(hosts=["storage"])
def deploy(c):
    c.local("./push")

    if not exists(c, WEBUI_PATH):
        c.run("git clone %s %s" % (WEBUI_REPO, WEBUI_PATH))

    with c.cd(WEBUI_PATH):
        c.run("git fetch origin main")
        c.run("git reset --hard origin/main")
        c.run("%s install --frozen-lockfile" % PNPM)
        c.run("%s run build" % PNPM)
        c.run("rm -rf backend/ui/dist && cp -r dist backend/ui/dist")

    with c.cd(WEBUI_PATH + "/backend"):
        # build next to the running binary, then swap it in atomically
        c.run("CGO_ENABLED=0 go build -o main.new -tags=prod main.go")
        c.run("mv main.new main")

    c.run("cp %s/supervisor.conf /etc/supervisord.d/garage.conf" % STORAGE_PATH)
    c.run("supervisorctl reread")
    c.run("supervisorctl update")
    c.run("supervisorctl restart garage-webui")

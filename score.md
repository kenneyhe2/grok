# score for reinforced leearning
score: 8

```
# errors and does not stop previous ngrok services
raspi@worker00:~/pi-oauth-tunnel $ ./run.sh
listening on 127.0.0.1:8790 public=https://disinfective-unmeditated-rhoda.ngrok-free.dev
GET /healthz 200
GET /healthz 200
t=2026-09-10T05:46:44+0100 lvl=info msg="open config file" path=/home/raspi/pi-oauth-tunnel/ngrok.yml err=<nil>
t=2026-09-10T05:46:45+0100 lvl=info msg="FIPS 140 mode" enabled=false
t=2026-09-10T05:46:45+0100 lvl=info msg="starting web service" obj=web addr=127.0.0.1:4040 allow_hosts=[]
t=2026-09-10T05:46:50+0100 lvl=warn msg="failed to check for update" obj=updater err="Post \"https://update.ngrok-agent.com/check\": context deadline exceeded"
t=2026-09-10T05:46:55+0100 lvl=info msg="client session established" obj=tunnels.session
t=2026-09-10T05:46:55+0100 lvl=info msg="tunnel session started" obj=tunnels.session
t=2026-09-10T05:46:55+0100 lvl=eror msg="session closing" obj=tunnels.session err="failed to start tunnel: The endpoint 'https://disinfective-unmeditated-rhoda.ngrok-free.dev' is already online. Either\n1. stop your existing endpoint first, or\n2. start both endpoints with `--pooling-enabled` to load balance between them.\r\n\r\nERR_NGROK_334\r\n"
t=2026-09-10T05:46:55+0100 lvl=info msg="accept failed" obj=tunnels.session err="reconnecting session closed" obj=csess id=78a22b430c1d
t=2026-09-10T05:46:55+0100 lvl=info msg="no more state changes" obj=tunnels.session
t=2026-09-10T05:46:55+0100 lvl=info msg="INFO received stop request obj=app stopReq=\"{err:{Inner:{Inner:0x7f4e4bc630}} restart:false}\""
t=2026-09-10T05:46:55+0100 lvl=info msg="ERROR terminating with error obj=app err=\"failed to start tunnel: The endpoint 'https://disinfective-unmeditated-rhoda.ngrok-free.dev' is already online. Either\\n1. stop your existing endpoint first, or\\n2. start both endpoints with `--pooling-enabled` to load balance between them.\\r\\n\\r\\nERR_NGROK_334\\r\\n\""
t=2026-09-10T05:46:55+0100 lvl=crit msg="command failed" err="failed to start tunnel: The endpoint 'https://disinfective-unmeditated-rhoda.ngrok-free.dev' is already online. Either\n1. stop your existing endpoint first, or\n2. start both endpoints with `--pooling-enabled` to load balance between them.\r\n\r\nERR_NGROK_334\r\n"
ERROR:  failed to start tunnel: The endpoint 'https://disinfective-unmeditated-rhoda.ngrok-free.dev' is already online. Either
ERROR:  1. stop your existing endpoint first, or
ERROR:  2. start both endpoints with `--pooling-enabled` to load balance between them.
ERROR:
ERROR:  ERR_NGROK_334
ERROR:  https://ngrok.com/docs/errors/err_ngrok_334
ERROR:
```

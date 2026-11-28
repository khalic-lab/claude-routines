# tools/bridge: the local ntfy bridge

`bridge.sh` is the script the Mac's crontab runs every 10 minutes from 07:00 to 22:59
(`*/10 7-22 * * *`). It pulls `main`, drains `pending-notifications/` to ntfy, folds reader
feedback, heals stuck Pages deploys, and alerts on missed editions and on a pull that keeps
failing. The header of `bridge.sh` lists every alert it can send.

Cron runs the **installed** copy in `/usr/local/src/news-brief-ntfy-bridge/`, next to `.env`
(ntfy topic, Worker token) and `git-credentials`, which never enter the repo. Change the script
here, run the suite, then install it:

```sh
tools/bridge/install.sh           # syntax check, diff, timestamped backup, atomic replace
tools/bridge/install.sh --check   # exit 0 when the installed copy matches
```

Until it is installed, every tick logs `WARN: installed bridge.sh differs from
tools/bridge/bridge.sh`. The log is `~/Library/Logs/news-brief-bridge.log`.

BROWSER_ERROR_MSG = """\
Browser setup error : {error}

Seems you don't have installed the requirements packages, if you need image output run the following commands on your server.
<b>Meanwhile You can use text version of Telminal, type any command!</b>

`sudo apt-get install chromium-chromedriver`"
`sudo apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget`

Finally, send `!setup_browser` on this chat again.
"""

ACTIVE_TASKS_MSG = (
    "This is list of your active tasks\nyou can <b>cancel</b> each one by tapping"
)

EMPTY_TASKS_MSG = """\
Tasks list is empty
Create new watcher same as below examples:

1️⃣ get `telminal.log` every 50 seconds
👉 <b>!watch 50s telminal.log</b>

2️⃣ get `temp.png` every 5 minutes
👉 <b>!watch 5m home/temp.png</b>

3️⃣ get `sql.dump` every 24 hours
👉 <b>!watch 24h /backups/sql.dump</b>

Be respectfull to telegram API limitations please:
https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
"""

PROCESS_INFO_MSG = """\
PID : {}
Status : {}

Start time : {}
Last update : {}

Run time: {}
"""

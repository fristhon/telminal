BROWSER_ERROR_MSG = """\
Browser setup error : {error}

`sudo apt-get install chromium-chromedriver` <i>maybe solve the problem</i>"
Fix the error and after that send me <code>!setup_browser</code>

<b>Meanwhile You can use text version of Telminal, type any command!</b>
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

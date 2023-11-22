# telminal
**A Terminal in Telegram!**
> Telegram is a lovely messenger and has so many features that we can manage our Linux server with those features.

## What is this?
Telminal is a Python package that helps you have your own server assistant Telegram bot.
You can use Telminal as a terminal or to download & upload files.

**Telminal features**
> - [x] HTML and image output
> - [x] Process state info
> - [x] Interactive command support
> - [x] Download from server
> - [x] Upload to server
> - [x] Multi user
> - [x] Tasks

## Getting Started
### Prerequisites
You must have a telegram developer API and a bot token\
[API ID API hash](https://core.telegram.org/api/obtaining_api_id)\
[Bot token](https://t.me/botfather)\
Very fast and easy, you can have those. Just follow these two official links.


### Try in colab:
<a href="https://colab.research.google.com/drive/1mnMmXHEs8Um4AaH4dToswcRHNOEi50_f?usp=sharing"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>


### Installation
    sudo apt-get install python3.9 python3.9-dev python3.9-venv
    python3.9 -m venv venv
    source ./venv/bin/activate
    pip install telminal
    telminal


### Image output requirements
    sudo apt-get install chromium-chromedriver
    sudo apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget


### Setup
https://user-images.githubusercontent.com/30555691/140306836-98773769-41d5-4d19-b113-f610766f85bf.mp4

Run `telminal` command after installation finished. Telminal needs those Telegram tokens for the first run.\
Also, you can create a `config.json` file inside the package directory in this format:
<pre>
{
    "api_id": 1234,
    "api_hash": "abcs",
    "token": "efgh",
    "admins": [8888, 9999]
}
</pre>
⚠️ First admin can manage other admins, so order of admins list matter.\
In this sample config 8888 must be your Telegram user ID.


## Interactive Mode
https://user-images.githubusercontent.com/30555691/140306980-98bde1e9-0e3d-4fe8-889b-73cc2774935e.mp4

You can activate this mode for the last running process by sending `/interactive_mode` or by clicking on the `Interactive mode` button of each process.\
In interactive mode, you are talking to the process and each message means an input for that process.\
Also, a two characters message that starts with `^` has its meaning and behave like a control command so `^c` means `CTRL + C`.\
To return to normal mode and create a new process just use `/normal_mode` or `Exit interactive mode` button.

## Optional image output
https://user-images.githubusercontent.com/30555691/140307428-e627ca5e-4861-4061-af12-10fe9ad8371f.mp4

Image creation for process result is optimized and will be okay on a server with minimum resources.\
However, creating an image on the server is an expensive process. so if you want to run multiple commands at once or have a process that does not require image output, I strongly recommend using the text version by sending `\image_off` command.

## Download file from server
https://user-images.githubusercontent.com/30555691/140307742-4ee6358a-4f9c-4289-aae4-55491d8e524d.mp4

You can save any file (up to 2GB) of your server on telegram.\
There are two ways to do this :
- Inline query
- !get command

Inline query just works for the current directory and runs a `ls -la | grep <your_query>` in the background.\
With `!get` command you can specify the path of a file manually.\
Also, you have a nice progress bar when you are downloading or uploading a heavy file.😎

## Upload file to server
https://user-images.githubusercontent.com/30555691/140307784-34f1246e-514d-41a0-b60f-1edc58fef1ab.mp4

Upload a file on your server just by sending it to Telminal chat.\
that file can be in telegram or on your hard disk.

## Multi admin in group
https://user-images.githubusercontent.com/30555691/140308347-a5bb32ce-658b-4d41-8984-2b52e29996f5.mp4

Fortunately, all features can be used in a group too. by default, Telminal only responds to your commands.\
`!trust` and `!untrust` are two commands that manage user permission.\
just reply to one of the user's messages with these commands.

## Tasks
https://user-images.githubusercontent.com/30555691/140308392-3cc1c786-6e55-488f-ae09-7b847441dc03.mp4

At this moment, there is only one type of task.\
A `watcher` task downloads a file periodically. write your first watcher in the following format:

```!watch <number><s,m,h> <file_path>```

**Some real examples :**

1️⃣ get `telminal.log` every 50 seconds
👉 <b>!watch 50s telminal.log</b>

2️⃣ get `temp.png` every 5 minutes
👉 <b>!watch 5m home/temp.png</b>

3️⃣ get `sql.dump` every 24 hours
👉 <b>!watch 24h /backups/sql.dump</b>

---

Finally set Telminal commands in [Botfather](https://t.me/botfather) using this text.
<pre>
image_off - Just text output
image_on - Text and image output
tasks - List of active tasks
interacive_mode - Interact with last process
normal_mode - Process creation mode
</pre>


## **Thanks**
[pexpect](https://github.com/pexpect/pexpect)\
[Telethon](https://github.com/LonamiWebs/Telethon)\
[xterm.js](https://github.com/xtermjs/xterm.js)\
[puppeteer](https://github.com/puppeteer/puppeteer)

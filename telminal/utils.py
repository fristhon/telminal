import contextlib
import os
from datetime import datetime
from datetime import timedelta

# inspired from https://github.com/cs01/pyxtermjs/blob/master/pyxtermjs/index.html
HTML_TEMPLATE = """<html>
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/xterm@4.11.0/css/xterm.css"
    />
  </head>
  <body>
    <div style="width: 100%; height: 100%" id="terminal"></div>
    <!-- xterm -->
    <script src="https://unpkg.com/xterm@4.11.0/lib/xterm.js"></script>
    <script src="https://unpkg.com/xterm-addon-fit@0.5.0/lib/xterm-addon-fit.js"></script>
    <script src="https://unpkg.com/xterm-addon-web-links@0.4.0/lib/xterm-addon-web-links.js"></script>
    <script src="https://unpkg.com/xterm-addon-search@0.8.0/lib/xterm-addon-search.js"></script>

    <script>
      const term = new Terminal({{
          convertEol: true,
          cursorBlink: false,
      }});

    const fit = new FitAddon.FitAddon();
      term.loadAddon(fit);

      term.open(document.getElementById("terminal"));
      fit.fit();
      term.resize(15, 50);
      fit.fit();

      term.write(`{data}`);

       function fitToscreen() {{
        fit.fit();
      }}

</script>
  </body>
</html>
"""


def silent_file_remover(file):
    with contextlib.suppress(FileNotFoundError):
        os.remove(file)


def timestamp_to_readable(timestamp: float):
    dt = datetime.fromtimestamp(timestamp)
    return f"{dt.hour}:{dt.minute}:{dt.second}"


def seconds_to_readable(seconds: int):
    return str(timedelta(seconds=seconds))

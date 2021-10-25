import contextlib
import os
from pathlib import Path

path = Path()
CWD = path.cwd()

# inspired from https://github.com/cs01/pyxtermjs/blob/master/pyxtermjs/index.html
HMTL_TEMPLATE = """<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <style>
      html {{
        font-family: arial;
      }}
    </style>
    <link
      rel="stylesheet"
      href="https://unpkg.com/xterm@4.11.0/css/xterm.css"
    />
  </head>
  <body>
    <div style="width: 100%; height: calc(100% - 50px)" id="terminal"></div>
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
      term.loadAddon(new WebLinksAddon.WebLinksAddon());
      term.loadAddon(new SearchAddon.SearchAddon());

      term.open(document.getElementById("terminal"));
      fit.fit();
      term.resize(15, 50);
      fit.fit();

      term.write(`{data}`);

       function fitToscreen() {{
        fit.fit();
      }}

      function debounce(func, wait_ms) {{
        let timeout;
        return function (...args) {{
          const context = this;
          clearTimeout(timeout);
          timeout = setTimeout(() => func.apply(context, args), wait_ms);
        }};
      }}


</script>
  </body>
</html>
"""


def make_html(pid, title, data):
    file = CWD / f"{pid}.html"
    with open(file, "w", encoding="utf-8") as html:
        html.write(HMTL_TEMPLATE.format(title=f"{pid} -> {title}", data=data))
    return file


def silent_file_remover(file):
    with contextlib.suppress(FileNotFoundError):
        os.remove(file)

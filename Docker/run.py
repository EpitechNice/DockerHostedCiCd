#!/usr/bin/python3

from datetime import timedelta

import requests

import subprocess
import traceback
import tempfile
import shutil
import shlex
import yaml
import json
import time
import sys
import os

os.chdir("/data/")

valid_color         = 5439232
medium_color        = 16750848
invalid_color       = 16711680

REPO_TITLE          = None

GITHUB_REPOSITORY   = os.getenv("GITHUB_REPOSITORY")
WEBHOOK_URL         = os.getenv("WEBHOOK_URL")
PUSH_AUTHOR         = os.getenv("PUSH_AUTHOR")
PUSH_MESSAGE        = os.getenv("PUSH_MESSAGE")
PUSH_URL            = os.getenv("PUSH_URL")
DOC_REPOSITORY      = os.getenv("DOC_REPOSITORY")
SSH_PRIVATE_KEY     = os.getenv("SSH_PRIVATE_KEY")

def handle_uncought_exception(type, value, error_traceback):
    error_tb = '\n'.join(traceback.format_tb(error_traceback))
    print("Uncaught error - " + type.__name__)
    print(value)
    print()
    print(error_tb)

    sys.exit(1)

def sys_cmd(command: str) -> tuple[bytes, int]:
    command = shlex.split(command)
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    status = 0
    try:
        process.check_returncode()
    except:
        status = 1

    print(process.stdout.decode())

    return (process.stdout, status)

###### DEBUG ######

message_content = """```ansi
The action ACTION_STATUS
```

```ansi
Compilation COMPILATION_STATUS

COMPILATION_LOGS
```

```ansi
Unit testing UNIT_TESTING_STATUS

UNIT_TESTING_LOGS
```

Coding style :
```ansi
CODING_STYLE_LOGS
```

```ansi
GitLeaks GITLEAKS_STATUS
```

GitLeaks :
```ansi
GITLEAKS_LOGS
```

```ansi
Documentation DOCUMENTATION_STATUS
```
"""

###### DEBUG ######

# First of all, we need to check what compilation is used (Make / CMake)

def format_time(float_time: timedelta) -> str:
    hours, more = divmod(float_time.seconds, 3600)
    minutes, seconds = divmod(more, 60)
    milliseconds = int(float_time.microseconds / 1000)

    return f"{hours:02}h:{minutes:02}m:{seconds:02}s.{milliseconds:03}"

def build_mkdocs() -> tuple[str, bool]:
    global REPO_TITLE
    logs = ""
    file = "doxide.yaml"
    if not (os.path.isfile(file)):
        file = "doxide.yml"
    if not (os.path.isfile(file)):
        return ("Could not find doxide.yaml file", False)
    with open(file) as f:
        doc = yaml.full_load(f)
    for required in ("title", "description"):
        if doc.get(required) is None:
            return ("Missing required fields on doxide.yaml", False)
    REPO_TITLE = doc.get("title")
    with open("mkdocs.yaml", 'w+') as f:
        f.write(f"""site_name: {doc.get('title')}
site_description: {doc.get('description')}
theme:
  name: material
  features:
    - navigation.indexes
  palette:
    - scheme: default
      primary: red
      accent: red
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode

    - scheme: slate
      primary: red
      accent: red
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

markdown_extensions:
  - def_list
  - attr_list
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
plugins:
  - search
extra_css:
  - stylesheets/doxide.css
extra_javascript:
  - javascripts/mathjax.js
  - https://polyfill.io/v3/polyfill.min.js?features=es6
  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js""")
    cmd = sys_cmd("doxide build")
    logs += "~$ doxide build\n"
    logs += cmd[0].decode()
    status = cmd[1]
    logs += "~$ mkdocs build\n"
    cmd = sys_cmd("mkdocs build")
    logs += cmd[0].decode()
    status += cmd[1]
    os.remove("mkdocs.yaml")
    return (logs, status == 0)

def run_compilation() -> tuple[str, bool]:
    logs = ""
    compiled = False
    compilation_time = timedelta(seconds=0)
    status = 0

    if os.path.isfile("Makefile"):
        compilation_start = time.time()
        logs += "~$ make\n"
        cmd = sys_cmd("make")
        logs += cmd[0].decode()
        status += cmd[1]
        logs += "~$ make fclean\n"
        cmd = sys_cmd("make fclean")
        logs += cmd[0].decode()
        status += cmd[1]
        compilation_time += timedelta(seconds=(time.time() - compilation_start))
        compiled = True
    if os.path.isfile("CMakeLists.txt"):
        if compiled:
            logs += r"""

/!\        WARNING         /!\
 ! Found CMakeLists.txt as  !
 ! well as Makefile !!      !
 ! This is an unusual       !
 ! behaviour.               !
 ! Compiled with Make,      !
 ! compiling with CMake...  !
/!\                        /!\

"""
        compilation_start = time.time()
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            logs += f"~$ mkdir {tmpdir}\n"
            logs += f"~$ cd {tmpdir}\n"
            os.chdir(tmpdir)
            logs += f"~$ cmake {cwd}\n"
            cmd = sys_cmd(f"cmake {cwd}")
            logs += cmd[0].decode()
            status += cmd[1]
            logs += f"~$ cmake --build .\n"
            cmd = sys_cmd(f"cmake --build .")
            logs += cmd[0].decode()
            status += cmd[1]
            os.chdir(cwd)
        compilation_time += timedelta(seconds=(time.time() - compilation_start))
    logs += f"\nCompilation took \033[35m{format_time(compilation_time)}\033[0m to complete"
    return (logs, status == 0)

def run_coding_style() -> tuple[str, bool, bool]:
    logs = ""
    status = 0
    info = minor = major = 0

    if not os.path.isfile("./coding-style-reports.log"):
        logs += "No \"coding-style-reports.log\" file found.\nIgnoring"
        return (logs, status == 0, False)

    with open("./coding-style-reports.log", 'r') as f:
        coding_style_errors = f.read()

    for line in coding_style_errors.split('\n'):
        if line.count(':') != 3:
            logs += line + '\n'
        else:
            file, line, level, name = line.split(':')
            if level.replace(' ', '') == "INFO":
                logs += f"- [\033[36mINFO\033[0m] (on [{file}:{line}](https://github.com/{GITHUB_REPOSITORY}/blob/main/{file}#L{line})): {name}\n"
                info += 1
            if level.replace(' ', '') == "MINOR":
                logs += f"- [\033[33mMINOR\033[0m] (on [{file}:{line}](https://github.com/{GITHUB_REPOSITORY}/blob/main/{file}#L{line})): {name}\n"
                status += 1
                minor += 1
            if level.replace(' ', '') == "MAJOR":
                logs += f"- [\033[31mMAJOR\033[0m] (on [{file}:{line}](https://github.com/{GITHUB_REPOSITORY}/blob/main/{file}#L{line})): {name}\n"
                status += 1
                major += 1

    os.remove("./coding-style-reports.log")

    logs = f"You have \033[31m{major}\033[0m major errors, \033[33m{minor}\033[0m minor errors and \033[34m{info}\033[0m infos :\n\n" + logs
    return (logs, status == 0, (info + minor + major == 0))

def run_unit_tests() -> tuple[str, bool]:
    logs = ""
    status = 0

    if not os.path.isfile("./tests/run_unit_tests.sh"):
        logs += "No \"tests/run_unit_tests.sh\" file found.\nIgnoring"
        return (logs, status == 0)

    tests_start = time.time()
    os.chdir("./tests/")
    cmd = sys_cmd("./run_unit_tests.sh")
    os.chdir("./../")
    logs += cmd[0].decode()
    status += cmd[1]
    tests_time = timedelta(seconds=(time.time() - tests_start))

    logs += f"\nUnit testing took \033[35m{format_time(tests_time)}\033[0m to complete"

    return (logs, status == 0)

def run_gitleaks() -> tuple[str, bool]:
    logs = ""
    status = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = sys_cmd(f"gitleaks detect -f json -r {tmpdir}/gitleaks_output.json")
        logs += cmd[0].decode()
        status += cmd[1]
        data = json.load(open(f"{tmpdir}/gitleaks_output.json", 'r'))
        if len(data) != 0:
            status += 1
            logs += "\n\nRaw GitLeaks Json output:\n\n"
            logs += json.dumps(data, indent=4)

    return (logs, status == 0)

def run_documentation() -> tuple[str, bool]:
    mkdocs = build_mkdocs()
    if not mkdocs[1]:
        return mkdocs
    if DOC_REPOSITORY is None:
        return False
    global REPO_TITLE
    if not os.path.isdir(os.path.expanduser("~/.ssh/")):
        os.mkdir(os.path.expanduser("~/.ssh/"))
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'w+') as f:
        f.write(SSH_PRIVATE_KEY)
    os.chmod(os.path.expanduser("~/.ssh/id_rsa"), 0o400)
    if REPO_TITLE is None:
        print("Could not find REPO TITLE !!!")
        return ("Could not find REPO TITLE !!!", False)
    cwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            os.system(f"GIT_SSH_COMMAND='ssh -v -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -l git' git clone \"{DOC_REPOSITORY}\" .")
            shutil.rmtree(REPO_TITLE, ignore_errors=True)
            shutil.copytree(os.path.join(cwd, "site/"), REPO_TITLE)
            os.system(f"GIT_SSH_COMMAND='ssh -v -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -l git' git add .")
            os.system(f"GIT_SSH_COMMAND='ssh -v -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -l git' git commit -m \"[+] {REPO_TITLE} | Added documentation\"")
            os.system(f"GIT_SSH_COMMAND='ssh -v -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -l git' git push")
    finally:
        os.chdir(cwd)
    try:
        shutil.rmtree("./site/")
    except:
        pass
    return (mkdocs[0], True)

def main() -> int:
    sys.excepthook = handle_uncought_exception

    compilation_logs, compilation_status = run_compilation()
    unit_tests_logs, unit_tests_status = run_unit_tests()
    coding_style_logs, coding_style_status, had_errors = run_coding_style()
    gitleaks_logs, gitleaks_status = run_gitleaks()

    doc_logs, doc_status = run_documentation()

    action_successfull = all((
        compilation_status,
        unit_tests_status,
        coding_style_status,
        gitleaks_status
    ))

    discord_message_content = message_content.replace(
        "ACTION_STATUS", ("was \033[32mSuccessfull\033[0m" if action_successfull else "\033[31mFailed\033[0m")
    ).replace(
        "COMPILATION_STATUS", ("\033[32mSuccess\033[0m" if compilation_status else "\033[31mFailure\033[0m")
    ).replace(
        "COMPILATION_LOGS", compilation_logs
    ).replace(
        "UNIT_TESTING_STATUS", ("\033[32mSuccess\033[0m" if unit_tests_status else "\033[31mFailure\033[0m")
    ).replace(
        "UNIT_TESTING_LOGS", unit_tests_logs
    ).replace(
        "CODING_STYLE_LOGS", coding_style_logs
    ).replace(
        "GITLEAKS_STATUS", ("\033[32mSuccess\033[0m" if gitleaks_status else "\033[31mFailure\033[0m")
    ).replace(
        "GITLEAKS_LOGS", gitleaks_logs
    ).replace(
        "DOCUMENTATION_STATUS", ("\033[32mSuccess\033[0m" if doc_status else "\033[31mFailure\033[0m")
    )

    username = PUSH_AUTHOR

    data = {
        "username" : f"Github - {username}",
        "avatar_url": f"https://github.com/{username}.png",
        "embeds": [
            {
                "color": ((16753408 if had_errors else 65280) if action_successfull else 16711680),
                "author": {
                    "name": username,
                    "url": f"https://github.com/{username}/",
                    "icon_url": f"https://github.com/{username}.png"
                },
                "title": PUSH_MESSAGE,
                "url": PUSH_URL,
                "description": discord_message_content,
                "footer": {
                    "text": "Report any problem to Tech0ne on GitHub"
                }
            }
        ],
        "allowed_mentions": {
            "parse": [
                "everyone"
            ]
        }
    }

    requests.post(WEBHOOK_URL, json = data).text

    return (0 if action_successfull else 1)

if __name__ == "__main__":
    sys.exit(main())
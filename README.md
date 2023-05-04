:trollface: Project94 is a fun software for trolling people.

<div id="badges">
  <img src="https://img.shields.io/pypi/v/project94" alt="Package version"/>
  <img src="https://img.shields.io/pypi/pyversions/project94" alt="Python version"/>
  <img src="https://img.shields.io/github/license/d35ync/project94" alt="License"/>
</div>

### Features
- [X] Multiplying sessions
- [X] Multiplying listeners
- [X] SSL support
- [X] Reverse shells + bind shells support
- [X] Auto-completion of interactive interface commands

### Requirements
- python3.10
- requests (not necessary)

### TROLL TUTORIAL "HOW TO USE"
**STEP 1** Installation  
Use one of these methods:
- `sudo pip3 install project94`
- ```bash
  git clone https://github.com/d35ync/project94.git
  cd project94
  ### Stable
  git checkout v1.1
  ### Unstable
  git checkout dev
  ### Or keep on master for 'pre-release'
  
  sudo pip3 install .
  ### or just for run dont do anything xdd
  ```

**STEP 2** Run  
- pip installation: `project94 --help`
- git installation: `python3 project94.py --help`

**STEP 3**  
EZ

### CLI interface info
Default command set:
```
bind_shell          connects to bind shell
cmd                 executes the command in the current or each session
encoding            changes active session encoding
exit                shutdown project94
goto                switch to another session
help                display help message
interact            start interactive shell
kill                kill active or specified session
listener            listeners management
session             sessions management
```

U can get extended help for every command:
```
[NO_SESSION]>> help session
[*] Help: session
Description: displays information of specified type
list       - shows list of sessions and some information about them
status     - shows information about active session
Usage:
 session {list status} ARGS
 session list
 session status [SESSION_ID]
```

### Demo

https://user-images.githubusercontent.com/52525711/232234241-8eec8eb5-3c6b-4032-9991-d606d3af05b3.mp4

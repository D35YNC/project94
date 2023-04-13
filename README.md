:trollface: Project94 is a fun software for trolling people.


### Features
- [X] Multiplying sessions using `select`
- [X] SSL support + client certificate verify 
- [ ] TODO Support custom modules (idk why)
- [ ] TODO Support both reverse and bind shells
- [X] Cli interface commands autocompletion

### Requirements
- python3.8+
- requests (not necessary)

### TROLL TUTORIAL "HOW TO USE"
**STEP 1** Installation  
Use one of these methods:
<!-- - `sudo pip3 install project94` -->
- `git clone https://github.com/d35ync/project94.git` (xdd)
- ```bash
  git clone https://github.com/d35ync/project94.git
  cd project94
  sudo pip3 install .
  ```

**STEP 2** Run  
- pip installation: `project94 --help`
- git installation: `python3 -m project94 -V` or `python3 project94.py -V`

**STEP 3**  
EZ



**CLI**  
Default command set:
```
/help               display help message
/sessions           display sessions list
/goto               switch to another session
/info               display info about current session
/interact           start interactive shell
/encoding           changes current session encoding
/command            execute single command in current session
/multicommand       execute single command in all sessions
/kill               kill active or specified session
/exit               shutdown project94
```

U can get extended help for every command:
```
>> /help /help
[*] Help: /help
Description: display help message
Aliases: h, help, ?.
Usage: /help [CMD]
```

#### Demo

https://user-images.githubusercontent.com/52525711/231819817-1844c3f3-333e-456a-bb63-9e4260f0ce48.mp4

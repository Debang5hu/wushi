# Wushi  

![Static Badge](https://img.shields.io/badge/武士-Wǔshì-black)  

![wushi](https://github.com/user-attachments/assets/f1a5007b-f0e6-4ffd-9bfc-8f441340ce6f)  


[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)  [![Go](https://img.shields.io/badge/--00ADD8?logo=go&logoColor=ffffff)](https://golang.org/)  ![Static Badge](https://img.shields.io/badge/LICENSE-MIT-blue)

A honeypot focus on ssh and https  
 
It contains a set of honeypot services designed to simulate vulnerable systems and capture attempted attacks. It includes two honeypot services:

1. **HTTP Honeypot**  
2. **SSH Honeypot**

Both services log connection attempts and interactions in order to gather useful data on attack patterns and unauthorized access attempts.  

```

# directory structure
.
├── honey
│   ├── certificate
│   │   ├── server.crt
│   │   └── server.key
│   ├── honeyhttp.py
│   ├── honeyssh.py
│   ├── pretty.sh
│   └── wushi.go
├── LICENSE.md
├── README.md
├── requirements.txt
└── setup.sh
```  

---  

### Features of HTTP Honeypot:

- Built using Flask, it logs HTTP requests and login attempts on port 443 (HTTPS).
- Logs client IP, geolocation details, and user agent data.
- Fake login page with CAPTCHA to deter automated bots.
- Logs stored in `Logs/https.log`.

---

### Features of SSH Honeypot:

- Built using Paramiko, it simulates an SSH server on port 22.
- Captures login attempts and logs them to `Logs/ssh.log`.
- Provides a "jailed" shell for authenticated users, restricting interaction to a controlled environment.
- Persistent RSA server key for secure connections.



## Table of Contents

- [Installation](#installation)
- [Usage](#usage)  
- [TO-DO](#to-do)
- [License](https://github.com/Debang5hu/wushi/blob/main/LICENSE.md)

---

## Installation

### Server Setup

Clone the repository to your local machine:

```bash
git clone https://github.com/Debang5hu/wushi.git

cd wushi  

chmod +x setup.sh  

# to setup the dependencies
sudo ./setup.sh  

cd honey

# to start the server
go run wushi.go
```  

## Usage

### Main Server:
The Go server coordinates the start of the honeypot services (HTTP and SSH). To run it:

```bash
go run wushi.go
```  

The server will start the HTTP and SSH honeypots in separate goroutines. It logs activities into `Logs/monitor.log`.  


---  

## TO-DO:  

### HoneySSH:

- Implement proper [restricted shell](https://en.wikipedia.org/wiki/Restricted_shell)  
- Implement [asyncssh](https://pypi.org/project/asyncssh/) for maintaining multiple ssh instances

### HoneyHTTP:  

- Use HTTPS Properly
- Implement [reCAPTCHA](https://www.google.com/recaptcha/about/) to make it look more legitimate
- Database Integration

### Overall:  

- Dockerization  

---  

## Bug  

- Feel free to [report](https://discord.com/users/718847515176206406) any bugs  

Contributions are appreciated ❤️

[![Open Source Love svg3](https://badges.frapsoft.com/os/v3/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

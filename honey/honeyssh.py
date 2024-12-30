#!/usr/bin/python3

# _*_ coding: utf-8 _*_

import paramiko
import logging
import os
import socket
import pty
import subprocess
import threading
import sys
from paramiko import RSAKey

# Log configuration
LOG_DIR = 'Logs'
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'ssh.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# RSA key config
SERVER_KEY_PATH = 'certificate/rsa_key.pem'
os.makedirs(os.path.dirname(SERVER_KEY_PATH), exist_ok=True)

if not os.path.exists(SERVER_KEY_PATH):
    logging.info("Generating persistent RSA key...")
    RSAKey.generate(2048).write_private_key_file(SERVER_KEY_PATH)


# fakessh
class HoneySSH(paramiko.ServerInterface):
    def __init__(self):
        self.authenticated = False
        self.channel = None
        self.exit_flag = False  # flag to indicate exit

    def check_auth_password(self, username, password):
        if username == 'ryuk' and password == 'ryuk':
            self.authenticated = True
            logging.info(f"Successful login attempt with username: {username}")
            return paramiko.AUTH_SUCCESSFUL
        else:
            logging.warning(f"Failed login attempt with username: {username} and password: {password}")
            return paramiko.AUTH_FAILED


    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            logging.info(f"Session channel requested, chanid={chanid}")
            return paramiko.OPEN_SUCCEEDED
        logging.warning(f"Non-session channel request received: kind={kind}")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


    def check_channel_pty_request(self, *args, **kwargs):
        logging.info(f"PTY request received with parameters: args={args}, kwargs={kwargs}")
        return True


    def check_channel_shell_request(self, chan):
        logging.info("Shell request received.")
        return True


    def get_shell(self):
        if not self.channel or self.channel.closed:
            logging.error("Channel is not available or closed for shell access.")
            return

        try:
            logging.info("Starting jailed shell interaction...")

            # fork a pseudo-terminal to run /bin/bash
            pid, fd = pty.fork()
            
            # child process
            if pid == 0:
                os.setgid(1001)  # GID
                os.setuid(1001)  # UID
                os.environ["PS1"] = "ryuk@honeypot:~$ "  # prompt
                
                # log commands in bash
                #os.environ["PROMPT_COMMAND"] = 'echo "$(date) - $(whoami) - $(pwd) - $(history 1)" >> .bash.log'
                
                os.execv('/bin/bash', ['/bin/bash', '--noprofile', '--norc'])  # jail shell
            
            else:  
                self.channel.setblocking(True)

                # Banner
                self.channel.send("\033c")  # clear
                self.channel.send("ryuk@honeypot:~$ ")

                # Threading
                read_thread = threading.Thread(target=self.read_from_shell, args=(fd,))
                write_thread = threading.Thread(target=self.write_to_shell, args=(fd,))
                read_thread.start()
                write_thread.start()

                read_thread.join()
                write_thread.join()

        except Exception as e:
            logging.error(f"Failed to handle jailed shell interaction: {e}")
        
        finally:
            if self.channel and not self.channel.closed:
                self.channel.close()
                logging.info("Channel closed after jailed shell interaction.")


    def read_from_shell(self, fd):
        while not self.exit_flag:
            try:
                data = os.read(fd, 1024)
                if data:
                    self.channel.send(data)

                    if data.strip() == b'exit':
                        logging.info("Exit command received. Shutting down SSH honeypot...")
                        self.channel.send("Goodbye!\n")
                        self.exit_flag = True
                else:
                    break
            except OSError:
                break


    def write_to_shell(self, fd):
        while not self.exit_flag:
            try:
                data = self.channel.recv(1024)
                if not data:
                    break
                os.write(fd, data)
            except Exception as e:
                logging.error(f"Error in SSH shell communication: {e}")
                break


def runSSH():
    try:
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(('0.0.0.0', 22))
        listen_socket.listen()

        logging.info("[+] SSH honeypot started and listening on port 22...")

        while True:
            try:
                client_socket, addr = listen_socket.accept()
                logging.info(f"Connection received from {addr}")

                transport = paramiko.Transport(client_socket)
                transport.add_server_key(RSAKey(filename=SERVER_KEY_PATH))

                honey_ssh = HoneySSH()
                transport.start_server(server=honey_ssh)

                channel = transport.accept(60)
                if channel is None:
                    logging.warning(f"No channel received from {addr} within timeout.")
                    client_socket.close()
                    continue

                honey_ssh.channel = channel
                honey_ssh.get_shell()

            except paramiko.SSHException as e:
                logging.error(f"SSH error: {e}")
            
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

    except KeyboardInterrupt:
        logging.info("Shutting down SSH honeypot...")
    
    except Exception as e:
        logging.error(f"Critical error starting SSH server: {e}")

    finally:
        listen_socket.close()
        logging.info("Socket closed. Exiting.")


if __name__ == "__main__":
    print('[+] SSH Server Started...')
    runSSH()

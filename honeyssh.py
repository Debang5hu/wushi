#!/usr/bin/python3

# _*_ coding:utf-8_*_

import paramiko
import logging
import os
import sys
import socket
from paramiko import SSHException

# logging setup
log_dir = 'Logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'ssh.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# HoneySSH class
class HoneySSH(paramiko.ServerInterface):
    def __init__(self):
        self.authenticated = False
        self.channel = None

    def check_auth_password(self, username, password):
        if username == 'ryuk' and password == 'ryuk':  # hardcoded
            self.authenticated = True
            logging.info(f"Successful login attempt from {username}")
            return paramiko.AUTH_SUCCESSFUL
        else:
            logging.warning(f"[+] Failed login attempt with username: {username} and password: {password}")
            return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_exec_request(self, command):
        if self.authenticated:
            logging.info(f"Command executed by attacker: {command}")
            if self.channel:
                self.channel.sendall(f"Executing command: {command}\n")
            return paramiko.CHANNEL_REQUEST_REPLY
        else:
            return paramiko.CHANNEL_REQUEST_FAILURE


    def get_shell(self):
        if self.channel is None:
            logging.error("Channel is not available.")
            return

        try:
            if not self.channel.active:
                logging.error("Channel is not active, cannot allocate PTY.")
                return

            self.channel.get_pty(term='xterm', width=80, height=24)
        except Exception as e:
            logging.error(f"Failed to allocate PTY: {e}")
            return


        self.channel.sendall("Welcome to the honeyssh.          -d\n")
        self.channel.sendall("Type 'exit' to disconnect.\n")

        while True:
            if not self.channel.active:
                logging.warning("Channel is no longer active.")
                break

        self.channel.sendall("ryuk@localhost: ")
        command = self.channel.recv(1024).decode().strip()

        if command.lower() == 'exit':
            self.channel.sendall("Goodbye!\n")
            break
        elif command:
            logging.info(f"Command issued: {command}")
            self.channel.sendall(f"Command '{command}' is not allowed.\n")

        self.channel.sendall(f"Jail shell: Command '{command}' not executed.\n")


    def get_transport(self):
        return self.channel


def runSSH():
    try:
        # create an SSH server
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(('0.0.0.0', 22))
        listen_socket.listen(100)

        logging.info("[+] SSH honeypot started and listening on port 22...")

        while True:
            client_socket, addr = listen_socket.accept()
            logging.info(f"Connection received from {addr}")

            try:
                transport = paramiko.Transport(client_socket)
                transport.load_server_moduli()
                transport.add_server_key(paramiko.RSAKey.generate(2048))  # Consider persistent server key

                honey_ssh = HoneySSH()

                # start the SSH server with the HoneySSH instance
                transport.start_server(server=honey_ssh)

                # Accept the channel with a timeout of 20 seconds
                channel = transport.accept(20)
                if channel is None:
                    logging.error("No channel received from client within the timeout period.")
                    client_socket.close()
                    continue

                # Execute shell
                honey_ssh.channel = channel
                honey_ssh.get_shell()

                # Close connection
                client_socket.close()
            
            except SSHException as e:
                logging.error(f"Error during SSH connection: {e}")
                client_socket.close()
            except Exception as e:
                logging.error(f"Unexpected error during SSH connection: {e}")
                client_socket.close()

    except Exception as e:
        logging.error(f"Error starting SSH server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    runSSH()

#!/bin/bash

# it install dependency
# it creates a default user: (ryuk:ryuk) for ssh

root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[!] This script must be run as root."
        exit 1
    fi
}

create_SSH_user() {
    local username="ryuk"
    local password="ryuk"

    # check if the user already exists
    if id "$username" &>/dev/null; then
        echo "[!] User '$username' already exists with password: '$password'"
        return 0
    fi

    # Create the user and set the password
    useradd -m -s /bin/bash "$username"
    echo "$username:$password" | chpasswd

    # remove from sudoers
    if grep -q "^$username" /etc/sudoers; then
        sed -i "/^$username/d" /etc/sudoers
    fi

    # remove from sudo group
    usermod -G "$(id -Gn "$username" | sed 's/sudo//g')" "$username"

    echo "[+] User: '$username' created successfully with password: '$password' and no sudo permissions!"
}


create_ssl_keys() {
    local cert_dir="honey/certificate"
    local cert_file="$cert_dir/server.crt"
    local key_file="$cert_dir/server.key"

    # check if certificate and key files already exist
    if [[ -f "$cert_file" && -f "$key_file" ]]; then
        echo "[+] SSL certificate and key already exist. Skipping generation."
        echo "[+] Certificate: $cert_file"
        echo "[+] Private Key: $key_file"
        echo "[+] Permissions:"
        ls -l "$cert_file" "$key_file"
        return
    fi

    mkdir -p "$cert_dir"

    openssl genpkey -algorithm RSA -out "$key_file" -pkeyopt rsa_keygen_bits:2048

    chmod 600 "$key_file"

    openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 90 <<EOF
US
Ohio
Stow
Organization
Unit
example.com
admin@example.com
EOF

    chmod 644 "$cert_file"

    echo "[+] SSL certificate and key generated successfully!"
    echo "[+] Certificate: $cert_file"
    echo "[+] Private Key: $key_file"
    echo "[+] Permissions:"
    ls -l "$cert_file" "$key_file"
}




system_update() {
    echo "[+] Updating system..."
    apt update && apt upgrade -y
}

install_python() {
    echo "[+] Installing Python..."
    apt install -y python3.12 python3-pip
    echo "[+] Python 3.x installed!"
}

install_go() {
    echo "[+] Installing Go..."
    apt install -y golang-go

    # setting up Go workspace
    echo "[+] Setting up Go workspace..."
    mkdir -p ~/go/{src,pkg,bin}
    export GOPATH=$HOME/go
    export PATH=$PATH:$GOPATH/bin

    # Make these changes persistent by adding them to the .bashrc
    echo "export GOPATH=\$HOME/go" >> ~/.bashrc
    echo "export PATH=\$PATH:\$GOPATH/bin" >> ~/.bashrc

    # reload .bashrc to apply changes
    source ~/.bashrc

    echo "[+] Go workspace set up successfully!"
}

check() {
    if command -v python3 &>/dev/null; then
        python_version=$(python3 --version)
        echo "[+] Python is installed: $python_version"
    else
        echo "[-] Python is not installed."
        install_python
    fi

    if command -v go &>/dev/null; then
        go_version=$(go version)
        echo "[+] Go is installed: $go_version"
    else
        echo "[-] Go is not installed."
        install_go
    fi
}

install() {
    if [[ ! -f "requirements.txt" ]]; then
        echo "[-] requirements.txt not found."
        exit 1
    fi

    # Upgrade pip to the latest version
    echo "[+] Upgrading pip..."
    python3 -m pip install --upgrade pip || {
        echo "[-] Failed to upgrade pip. Continuing with the existing version..."
    }

    # Install dependencies
    echo "[+] Installing dependencies..."
    while read -r package; do
        echo "[+] Installing $package..."
        pip install "$package" || {
            echo "[!] Failed to install $package via pip. Retrying with --break-system-packages..."
            pip install "$package" --break-system-packages || {
                echo "[!] Failed to install $package with --break-system-packages. Trying apt..."
                apt_package="python3-$(echo "$package" | sed 's/[=<>].*//g' | tr '-' '_')"
                if apt show "$apt_package" &>/dev/null; then
                    sudo apt install -y "$apt_package" || {
                        echo "[-] Failed to install $package via both pip and apt. Skipping..."
                    }
                else
                    echo "[-] $apt_package not available in apt. Skipping..."
                fi
            }
        }
    done < requirements.txt
}


main() {
    root                # ensure the script is run as root
    system_update       # update and upgrade the system
    create_SSH_user     # create the SSH user
    create_ssl_keys     # create ssl keys for https
    check               # check whether Python and Go are installed; install if not
    install             # install dependencies from requirements.txt
}

main
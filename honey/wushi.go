package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"os/exec"
	"sync"
)

//  <--- GLOBAL VALUES   --->
// TERM colors
const (
	RED     = "\033[0;31m"
	WHITE   = "\033[0m"
	GRN     = "\033[1;92m"
	YLW     = "\033[1;33m"
	BLUE    = "\033[0;34m"
	MAGENTA = "\033[35m"
	CYAN    = "\033[36m"
)

var PORTS = []int{22}


// will start flask server
func HoneyHTTP() {
	log.Printf("%s[+]%s Starting HTTP honeypot", CYAN, WHITE)
	cmd := exec.Command("python3", "honeyhttp.py")
	log.Printf("%s[+]%s Honeypot listening on %s443%s\n", CYAN, WHITE, YLW, WHITE)


	if _, err := os.Stat("Logs"); os.IsNotExist(err) {
		os.Mkdir("Logs", 0755)
	}

	// suppress stdout and log stderr to a file
	errFile, err := os.Create("Logs/honeyhttp.log")
	if err != nil {
		log.Fatalf("%s[!]%s Failed to create log file: %v", RED, WHITE, err)
	}
	defer errFile.Close()
	cmd.Stdout = nil
	cmd.Stderr = errFile

	if err := cmd.Start(); err != nil {
		log.Fatalf("%s[!]%s Failed to start HTTPS server: %v", RED, WHITE, err)
	}
	go func() {
		if err := cmd.Wait(); err != nil {
			log.Printf("%s[!]%s HTTPS server exited: %v", RED, WHITE, err)
		}
	}()
}



// processes incoming connections based on port
func HandleConnection(conn net.Conn, port int) {
	defer conn.Close()
	clientAddr := conn.RemoteAddr().String()
	fmt.Printf("\n%s connected on port %d\n", clientAddr, port)

	if port == 22 {
		HandleSSHConnection(conn)
	}
}

//   <--- to do   --->
// handles SSH-specific connections (placeholder)
func HandleSSHConnection(conn net.Conn) {
	log.Printf("[+] Simulating SSH connection from %s", conn.RemoteAddr().String())
}

// starts listening on a specific port
func Honeypot(port int, wg *sync.WaitGroup) {
	defer wg.Done()

	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		log.Fatalf("[!] Failed to bind to port %d: %v", port, err)
	}
	log.Printf("%s[+]%s Honeypot listening on %s%d%s\n", CYAN, WHITE, YLW, port, WHITE)

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("[!] Failed to accept connection on port %d: %v", port, err)
			continue
		}
		go HandleConnection(conn, port)
	}
}


// main
func main() {
	fmt.Printf("%s__        ___   _ ____  _   _ ____ %s\n", MAGENTA, WHITE)
	fmt.Printf("%s\\ \\      / / | | / ___|| | | |_  _|%s\n", MAGENTA, WHITE)
 	fmt.Printf("%s \\ \\ /\\ / /| | | \\___ \\| |_| || |  %s\n", MAGENTA, WHITE)
	fmt.Printf("%s  \\ V  V / | |_| |___) |  _  || |  %s\n", MAGENTA, WHITE)
	fmt.Printf("%s   \\_/\\_/   \\___/|____/|_| |_|___| %s\n", MAGENTA, WHITE)
	fmt.Printf("           %s\u6b66\u58eb%s (v0.1)  @Debang5hu\n\n", BLUE, WHITE)


	if os.Geteuid() != 0 {
		log.Fatalf("%s[+]%s Requires sudo privileges\n", RED, WHITE)
	}


	// Start services
	var wg sync.WaitGroup
	wg.Add(len(PORTS) + 1)

	// Start HTTP server
	go func() {
		defer wg.Done()
		HoneyHTTP()
	}()

	// Start honeypot on each port
	for _, port := range PORTS {
		go Honeypot(port, &wg)
	}

	wg.Wait()
}

package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"sync"
	"syscall"
	"time"
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

var LogMonitor *log.Logger
var stopChan = make(chan struct{})



// ensure Logs directory exists and create monitor.log
func init() {
	if _, err := os.Stat("Logs"); os.IsNotExist(err) {
		if err := os.Mkdir("Logs", 0755); err != nil {
			log.Fatalf("%s[!]%s Failed to create Logs directory: %v", RED, WHITE, err)
		}
	}

	logFile, err := os.OpenFile("Logs/monitor.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("%s[!]%s Failed to create/open monitor.log: %v", RED, WHITE, err)
	}

	LogMonitor = log.New(logFile, "[Wushi] ", log.LstdFlags)
}




// retry logic
func RunCommandWithRetry(cmd *exec.Cmd, maxRetries int, wg *sync.WaitGroup, name string) {
	defer wg.Done()
	retries := 0

	for {
		select {
		case <-stopChan:
			LogMonitor.Printf("[+] Received shutdown signal. Stopping %s...", name)
			return
		default:
			LogMonitor.Printf("[+] Starting %s...", name)
			if err := cmd.Start(); err != nil {
				LogMonitor.Printf("[+] ERROR: Failed to start %s: %v", name, err)
				retries++
				if retries >= maxRetries {
					LogMonitor.Printf("[+] ERROR: Maximum retries reached for %s. Exiting...", name)
					return
				}
				time.Sleep(5 * time.Second) // wait before retrying
				continue
			}

			LogMonitor.Printf("[+] %s started successfully.", name)
			if err := cmd.Wait(); err != nil {
				LogMonitor.Printf("[+] WARNING: %s exited unexpectedly: %v", name, err)
				retries++
				if retries >= maxRetries {
					LogMonitor.Printf("[+] ERROR: Maximum retries reached for %s. Exiting...", name)
					return
				}
				LogMonitor.Printf("[+] Retrying %s...", name)
			} else {
				LogMonitor.Printf("[+] %s exited normally.", name)
				return
			}
		}
	}
}




// will start flask server
func HoneyHTTP(wg *sync.WaitGroup) {
	cmd := exec.Command("python3", "honeyhttp.py")
	RunCommandWithRetry(cmd, 3, wg, "HTTP honeypot")
}


// will start ssh server
func HoneySSH(wg *sync.WaitGroup) {
	cmd := exec.Command("python3", "honeyssh.py")
	RunCommandWithRetry(cmd, 3, wg, "SSH honeypot")
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

	fmt.Printf("%s[+]%s Starting HTTP honeypot...\n", GRN, WHITE)
	fmt.Printf("%s[+]%s Starting SSH honeypot...\n", GRN, WHITE)	
	LogMonitor.Printf("[+] Monitoring started...")


	// graceful shutdown
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)

	var wg sync.WaitGroup
	wg.Add(2)

	go HoneyHTTP(&wg)
	go HoneySSH(&wg)

	go func() {
		<-signalChan
		LogMonitor.Printf("[+] Received shutdown signal. Exiting...")
		close(stopChan)
	}()

	wg.Wait()
	LogMonitor.Printf("[+] All honeypots exited!")
	log.Printf("%s[+]%s All honeypots exited", CYAN, WHITE)
}
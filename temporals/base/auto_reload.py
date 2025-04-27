#!/usr/bin/env python3

import os
import sys
import time
import signal
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class PythonFileHandler(FileSystemEventHandler):
    def __init__(self, server_process, worker_process):
        self.server_process = server_process
        self.worker_process = worker_process
        self.last_modified = time.time()
        self.cooldown = 2  # seconds to wait before restarting

    def on_modified(self, event):
        if event.is_directory:
            return
        
        if not event.src_path.endswith('.py'):
            return

        current_time = time.time()
        if current_time - self.last_modified < self.cooldown:
            return

        self.last_modified = current_time
        logging.info(f"Change detected in {event.src_path}")
        
        # Restart the services
        self.restart_services()

    def restart_services(self):
        logging.info("Restarting services...")
        
        # Stop the current processes
        if self.server_process.poll() is None:
            self.server_process.terminate()
            self.server_process.wait()
        
        if self.worker_process.poll() is None:
            self.worker_process.terminate()
            self.worker_process.wait()

        # Start new processes
        self.server_process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        self.worker_process = subprocess.Popen(
            [sys.executable, "worker.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        logging.info("Services restarted successfully")

def main():
    # Start the initial processes
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    worker_process = subprocess.Popen(
        [sys.executable, "worker.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Set up the file watcher
    event_handler = PythonFileHandler(server_process, worker_process)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if server_process.poll() is not None:
                logging.error("Server process died, restarting...")
                server_process = subprocess.Popen(
                    [sys.executable, "server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            if worker_process.poll() is not None:
                logging.error("Worker process died, restarting...")
                worker_process = subprocess.Popen(
                    [sys.executable, "worker.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

    except KeyboardInterrupt:
        observer.stop()
        server_process.terminate()
        worker_process.terminate()
    
    observer.join()

if __name__ == "__main__":
    main() 
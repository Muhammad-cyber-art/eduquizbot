import subprocess
import time
import re

def main():
    while True:
        print("Starting localtunnel...")
        process = subprocess.Popen(
            ["npx", "localtunnel", "--port", "80"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line.strip(), flush=True)
                with open("lt.log", "w") as f:
                    f.write(line)
        
        print("Localtunnel exited. Restarting in 3 seconds...")
        time.sleep(3)

if __name__ == "__main__":
    main()

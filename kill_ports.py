import psutil

def kill_process_on_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing process {proc.info['name']} (PID: {proc.info['pid']}) on port {port}")
                    proc.kill()
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    print(f"No process found on port {port}")

if __name__ == "__main__":
    for port in [8000, 5000]:
        kill_process_on_port(port)

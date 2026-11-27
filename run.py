from pathlib import Path
import hashlib, os, socket, subprocess, sys, time, urllib.request, webbrowser, venv
root=Path(__file__).resolve().parent; os.chdir(root)
try:
    port=int(os.environ.get('PORT','8020'))
    if not 1<=port<=65535:raise ValueError()
except ValueError:
    print('Invalid PORT; use 1–65535.',file=sys.stderr);sys.exit(1)
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    try:s.bind(('127.0.0.1',port))
    except OSError:
        print(f'Port {port} is occupied. Windows: set PORT=8021 and run python run.py again.',file=sys.stderr);sys.exit(1)
env=root/'.venv'; python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
if not python.exists():
    print('Creating local environment...',flush=True);venv.EnvBuilder(with_pip=True).create(env)
req=root/'requirements.txt';stamp=env/'requirements.sha256';digest=hashlib.sha256(req.read_bytes()).hexdigest()
if not stamp.exists() or stamp.read_text().strip()!=digest:
    print('Installing packages; internet is needed on first run...',flush=True)
    try:subprocess.run([str(python),'-m','pip','install','-r',str(req)],check=True)
    except subprocess.CalledProcessError:
        print('Installation failed. Check internet and retry.',file=sys.stderr);sys.exit(1)
    stamp.write_text(digest)
url=f'http://127.0.0.1:{port}/';print('Starting PatchScope locally...',flush=True)
proc=subprocess.Popen([str(python),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)])
try:
    for _ in range(120):
        if proc.poll() is not None:sys.exit(proc.returncode or 1)
        try:
            with urllib.request.urlopen(url+'api/status',timeout=2) as r:
                if r.status==200:break
        except Exception:time.sleep(1)
    else:
        print('Startup timed out; inspect the terminal.',file=sys.stderr);proc.terminate();proc.wait();sys.exit(1)
    print(f'PatchScope ready: {url} (Ctrl+C to stop)',flush=True)
    if '--no-browser' not in sys.argv:webbrowser.open(url)
    proc.wait()
except KeyboardInterrupt:
    if proc.poll() is None:
        proc.terminate()
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()

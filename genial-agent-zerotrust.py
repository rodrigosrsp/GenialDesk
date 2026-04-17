import os
import json
import uuid
import threading
import webbrowser
import http.server
import socketserver
import requests
import psutil
import platform
import socket
import getpass
import subprocess
from datetime import datetime
import customtkinter as ctk
import pystray
from PIL import Image, ImageTk, ImageDraw
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".genial_agent")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
BACKEND_URL = "https://hjb0aa97v4s.sn.mynetname.net"
CHECKIN_INTERVAL = 300
ICON_FILE = "logo.png"
OAUTH_CALLBACK_PORT = 47821

_app_closing_flag = False

def get_windows_hardware_info():
    hw_info = {"manufacturer": "Desconhecido", "model": "Desconhecido", "serial_number": ""}
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(
                "wmic csproduct get vendor,name,identifyingnumber /format:csv",
                shell=True, text=True, stderr=subprocess.DEVNULL
            )
            lines = output.strip().split('\n')
            if len(lines) > 1:
                parts = lines[-1].split(',')
                if len(parts) >= 4:
                    hw_info["serial_number"] = parts[1].strip()
                    hw_info["model"] = parts[2].strip()
                    hw_info["manufacturer"] = parts[3].strip()
        except Exception:
            pass
    return hw_info

def get_mac_address():
    try:
        mac = hex(uuid.getnode()).replace('0x', '').zfill(12)
        return "".join(mac[i:i+2] for i in range(0, 11, 2)).lower()
    except Exception:
        return "000000000000"

def get_hardware_fingerprint():
    """
    Nova Função de ID: Âncora de identidade baseada no hardware.
    Tenta Serial Number, cai para MAC Address se for genérico.
    """
    info = get_windows_hardware_info()
    serial = info.get("serial_number", "").strip()
    
    # Lista de seriais inválidos comuns em máquinas montadas/virtuais
    invalid_serials = ["To be filled by O.E.M.", "Default string", "None", "00000000", "Not Applicable"]
    
    if not serial or any(inv.lower() in serial.lower() for inv in invalid_serials):
        return f"MAC-{get_mac_address()}"
    
    return serial.lower()

def load_config():
    """Carrega config existente. Não gera mais UUID aleatório."""
    hw_id = get_hardware_fingerprint()
    cfg = {"agent_id": hw_id, "genial_id": "", "logged_user_email": ""}
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Garante que o agent_id seja sempre o do hardware atual
                saved["agent_id"] = hw_id
                return saved
        except Exception:
            pass
    return cfg

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=True, indent=2)

# ... (Funções get_rustdesk_id, get_local_ip, get_installed_software permanecem iguais) ...

def get_sys_info(cfg):
    vmem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    try:
        logged_user = os.getlogin()
    except Exception:
        logged_user = getpass.getuser()
    hw_info = get_windows_hardware_info()

    return {
        "agent_id": cfg["agent_id"], # Agora é o Hardware Fingerprint
        "hostname": platform.node(),
        "platform": platform.system().lower(),
        "logged_user": logged_user,
        "logged_user_email": cfg.get("logged_user_email", ""),
        "software": [], # Opcional: limitar ou remover para performance
        "os_name": platform.system(),
        "os_version": platform.version(),
        "os_arch": platform.machine(),
        "cpu_model": platform.processor(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_usage_percent": psutil.cpu_percent(),
        "ram_total_mb": int(vmem.total / (1024 ** 2)),
        "ram_used_mb": int(vmem.used / (1024 ** 2)),
        "disk_total_gb": int(disk.total / (1024 ** 3)),
        "disk_free_gb": int(disk.free / (1024 ** 3)),
        "ip_local": "127.0.0.1", # Simplificado para exemplo
        "ip_public": "",
        "mac_address": get_mac_address(),
        "serial_number": hw_info["serial_number"],
        "manufacturer": hw_info["manufacturer"],
        "model": hw_info["model"],
        "domain": platform.node(),
        "rustdesk_id": "", # get_rustdesk_id() se necessário
        "agent_version": "3.0.0-HardwareID",
        "uptime_seconds": int(psutil.boot_time()),
        "genial_id": cfg.get("genial_id", ""),
    }

# ... (Classe GenialAgentApp permanece similar, chamando as novas funções de ID) ...

class GenialAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.title("Genial Agent Desktop")
        self.geometry("360x480")
        ctk.set_appearance_mode("dark")
        self.checkin_disabled = True
        self.tray_icon = None

        try:
            self.icon_image = get_icon()
            self.tk_icon = ImageTk.PhotoImage(self.icon_image)
            self.wm_iconphoto(False, self.tk_icon)
        except Exception as e:
            print(f"Icon error: {e}")

        self.gid_text = ctk.StringVar(value=self.get_display_id())
        self.email_text = ctk.StringVar(value=self.get_display_email())
        self.status_text = ctk.StringVar()

        self.label_id = ctk.CTkLabel(self, textvariable=self.gid_text, font=("Arial", 18, "bold"), cursor="hand2")
        self.label_id.pack(pady=(20, 0))
        self.label_id.bind("<Button-1>", self.copy_id_to_clipboard)

        ctk.CTkLabel(self, textvariable=self.email_text, font=("Arial", 12), text_color="gray").pack(pady=(2, 10))

        self.status_icon = ctk.CTkLabel(self, text="●", font=("Arial", 50))
        self.status_icon.pack()
        ctk.CTkLabel(self, textvariable=self.status_text, font=("Arial", 13)).pack(pady=(0, 10))

        self.btn_checkin = ctk.CTkButton(self, text="Forçar Check-in", command=self.manual_checkin, height=35)
        self.btn_login = ctk.CTkButton(
            self, text="G  Entrar com Google",
            fg_color="#4285F4", hover_color="#1a73e8",
            command=self.login_google, height=38
        )

        self.log_box = ctk.CTkTextbox(self, height=120, state="disabled", font=("Courier", 11), fg_color="#1e1e1e")
        self.log_box.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        if not self.cfg.get("genial_id") or not self.cfg.get("logged_user_email"):
            self.status_icon.configure(text_color="orange")
            self.status_text.set("Aguardando Login...")
            self.btn_login.pack(pady=5)
            self.add_log("Aguardando vinculo Google...")
        else:
            self.status_icon.configure(text_color="green")
            self.status_text.set("Online")
            self.btn_checkin.pack(pady=5)
            self.checkin_disabled = False
            self.after(1000, self.periodic_checkin)

        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        self.bind("<Unmap>", self.on_minimize)
        self.setup_tray_icon()
        self.after(0, self.withdraw)

    def on_minimize(self, event):
        if self.state() == 'iconic':
            self.minimize_to_tray()

    def minimize_to_tray(self):
        self.withdraw()
        self.add_log("Minimizado para a bandeja.")

    def copy_id_to_clipboard(self, event):
        gid = self.cfg.get("genial_id", "")
        if gid:
            self.clipboard_clear()
            self.clipboard_append(gid)
            self.gid_text.set("GenialID: Copiado!")
            self.after(2000, lambda: self.gid_text.set(self.get_display_id()))

    def get_display_id(self):
        return f"GenialID: {self.cfg.get('genial_id', 'Pendente') or 'Pendente'}"

    def get_display_email(self):
        return self.cfg.get("logged_user_email", "Nenhuma conta")

    def manual_checkin(self):
        if self.checkin_disabled:
            return
        self.add_log("Enviando Hardware, Software e RustDesk...")

        def run():
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/agent/checkin",
                    json=get_sys_info(self.cfg),
                    headers={"Authorization": "Bearer genial-agent-secret"},
                    timeout=20,
                    verify=False,
                )
                if r.status_code == 403 and "force_logout" in r.text:
                    self.cfg["logged_user_email"] = ""
                    self.cfg["genial_id"] = ""
                    save_config(self.cfg)
                    self.checkin_disabled = True
                    self.after(0, lambda: [
                        self.status_icon.configure(text_color="red"),
                        self.status_text.set("Acesso Revogado"),
                        self.btn_checkin.pack_forget(),
                        self.btn_login.pack(pady=5),
                        self.email_text.set("Removido"),
                        self.gid_text.set("Removido"),
                    ])
                    return

                if r.status_code in [200, 202]:
                    if self.cfg.get("genial_id"):
                        self.after(0, lambda: [
                            self.status_icon.configure(text_color="green"),
                            self.status_text.set("Online"),
                        ])
                    else:
                        self.after(0, lambda: [
                            self.status_icon.configure(text_color="orange"),
                            self.status_text.set("Aguardando login"),
                        ])
            except Exception as exc:
                self.add_log(f"Falha: {exc}")

        threading.Thread(target=run, daemon=True).start()

    def login_google(self):
        self.btn_login.configure(state="disabled")
        app_ref = self

        class AuthHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                return

            def do_GET(self):
                from urllib.parse import urlparse, parse_qs
                q = parse_qs(urlparse(self.path).query)
                if "genial_id" in q:
                    app_ref.cfg["genial_id"] = q["genial_id"][0]
                    app_ref.cfg["logged_user_email"] = q.get("user", [""])[0]
                    save_config(app_ref.cfg)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Login realizado! Pode fechar esta aba.")
                    app_ref.checkin_disabled = False
                    app_ref.after(0, lambda: [
                        app_ref.email_text.set(app_ref.get_display_email()),
                        app_ref.gid_text.set(app_ref.get_display_id()),
                        app_ref.btn_login.pack_forget(),
                        app_ref.btn_login.configure(state="normal"),
                        app_ref.btn_checkin.pack(pady=5),
                        app_ref.manual_checkin(),
                    ])
                    app_ref.after(CHECKIN_INTERVAL * 1000, app_ref.periodic_checkin)
                    threading.Thread(target=httpd.shutdown, daemon=True).start()
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Callback invalido.")

        # Escuta na mesma porta que o backend usa no DESKTOP_CALLBACK_URL
        httpd = socketserver.TCPServer(("", OAUTH_CALLBACK_PORT), AuthHandler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()

        # O backend ignora redirect_uri e usa DESKTOP_CALLBACK_URL fixo,
        # mas enviamos o valor correto para consistencia
        callback_uri = f"http://localhost:{OAUTH_CALLBACK_PORT}/callback"
        webbrowser.open(
            f"{BACKEND_URL}/api/auth/google/url"
            f"?device_id={self.cfg['agent_id']}"
            f"&redirect_uri={callback_uri}"
        )

    def periodic_checkin(self):
        if not self.checkin_disabled:
            self.manual_checkin()
        self.after(CHECKIN_INTERVAL * 1000, self.periodic_checkin)

    def add_log(self, message):
        def update_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"[{timestamp}] {message}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, update_log)

    def setup_tray_icon(self):
        try:
            icon_image = self.icon_image if hasattr(self, 'icon_image') else get_icon()
            menu = (
                pystray.MenuItem('Abrir', self.show_window),
                pystray.MenuItem('Forçar Check-in', lambda icon, item: self.after(0, self.manual_checkin)),
                pystray.MenuItem('Sair', self.exit_app_via_tray),
            )
            self.tray_icon = pystray.Icon("genial_agent", icon_image, "Genial Agent", menu)
            self.tray_icon.onclick = self.show_window
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Tray erro: {e}")

    def show_window(self, *args):
        self.deiconify()
        self.lift()

    def exit_app_via_tray(self, *args):
        global _app_closing_flag
        _app_closing_flag = True
        self.withdraw()
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(500, self.destroy)

    def destroy(self):
        global _app_closing_flag
        if not _app_closing_flag:
            self.minimize_to_tray()
            return
        if self.tray_icon:
            self.tray_icon.stop()
        super().destroy()


if __name__ == "__main__":
    app = GenialAgentApp()
    app.protocol("WM_DELETE_WINDOW", app.minimize_to_tray)
    app.mainloop()

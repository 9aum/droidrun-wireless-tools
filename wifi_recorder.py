import requests
import json
import base64
import os
import time
import sys
# Import Config
import wifi_config

class DroidRunWirelessRecorder:
    def __init__(self):
        self.ip = wifi_config.TARGET_IP
        self.port = wifi_config.TARGET_PORT
        self.token = wifi_config.AUTH_TOKEN
        self.base_url = f"http://{self.ip}:{self.port}"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        self.width = 1080 
        self.height = 2400
        print(f"🔗 Connecting to {self.base_url} ...")
        self.init_screen_size()
        
        # Log File
        self.log_file = "action_wifi_log.txt"
        # Clear old log on start
        with open(self.log_file, "w", encoding='utf-8') as f:
            f.write("") 
        print(f"📝 Recording to '{self.log_file}'")

    def log_action(self, action_data):
        with open(self.log_file, "a", encoding='utf-8') as f:
            json.dump(action_data, f, ensure_ascii=False)
            f.write("\n")
        print(f"  💾 Recorded: {action_data['action']}")

    def init_screen_size(self):
        try:
            resp = requests.get(f"{self.base_url}/phone_state", headers=self.headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                # Handle nested result string
                if "result" in data and isinstance(data["result"], str):
                    try: 
                        inner = json.loads(data["result"])
                        data.update(inner) # Merge inner dict
                    except: pass

                self.width = data.get("displayWidth", 1080)
                self.height = data.get("displayHeight", 2400)
                cur_app = data.get("currentApp", "Unknown")
                print(f"✅ Device Resolution: {self.width}x{self.height}")
                print(f"📱 Current App: {cur_app}")
        except: pass

    def check_connection(self):
        try:
            resp = requests.get(f"{self.base_url}/ping", headers=self.headers, timeout=2)
            if resp.status_code == 200: print("✅ Connect OK!")
            else: print(f"❌ Connect Failed: {resp.status_code}")
        except: print("❌ Host Unreachable")

    def get_state_json(self):
        try:
            resp = requests.get(f"{self.base_url}/state_full", headers=self.headers, timeout=10)
            if resp.status_code == 200: 
                data = resp.json()
                if "result" in data: return data["result"]
                return data
        except: pass
        return None

    def traverse_tree_list(self, nodes, result_list):
        if not nodes: return
        if isinstance(nodes, list):
            for node in nodes: self.traverse_tree_list(node, result_list)
            return
        if isinstance(nodes, dict):
            result_list.append(nodes)
            children = nodes.get("children") or nodes.get("subnodes")
            if children: self.traverse_tree_list(children, result_list)

    def get_bounds(self, node):
        b = node.get("boundsInScreen")
        if isinstance(b, dict):
            return [b.get("left",0), b.get("top",0), b.get("right",0), b.get("bottom",0)]
        b_str = node.get("bounds")
        if isinstance(b_str, str):
            try:
                import re
                m = re.findall(r'\d+', b_str)
                if len(m) >= 4: return [int(x) for x in m]
            except: pass
        return None

    def print_list_table(self, flat_list):
        print(f"\n🔍 Found {len(flat_list)} Elements:")
        print("-" * 65)
        print(f"{'IDX':<4} | {'TEXT/DESC':<25} | {'CLASS':<15} | {'BOUNDS'}")
        print("-" * 65)
        
        for i, node in enumerate(flat_list):
            cls = node.get("className", "N/A").split('.')[-1]
            text = node.get("text") or node.get("contentDescription") or node.get("resourceId") or ""
            if isinstance(text, str): text = text.replace("com.miui.home:id/", "")
            t_display = text # Show full text
            b = self.get_bounds(node)
            b_str = f"[{b[0]},{b[1]}][{b[2]},{b[3]}]" if b else "Invalid"
            print(f"{i:<4} | {t_display:<60} | {cls:<15} | {b_str}")
        print("-" * 65)

    def dump_ui(self):
        print("📥 Fetching FULL UI Tree...")
        state = self.get_state_json()
        if not state: return

        root_tree = state.get("a11y_tree")
        flat_list = []
        self.traverse_tree_list(root_tree, flat_list)
        self.print_list_table(flat_list)

    def tap_index(self, index):
        idx = int(index)
        state = self.get_state_json()
        if not state: return
        
        root_tree = state.get("a11y_tree")
        flat_list = []
        self.traverse_tree_list(root_tree, flat_list)
        
        if 0 <= idx < len(flat_list):
            node = flat_list[idx]
            b = self.get_bounds(node)
            
            if b:
                cx, cy = (b[0]+b[2])//2, (b[1]+b[3])//2
                
                # --- RECORDING LOGIC ---
                criteria = {
                    "text": node.get("text"),
                    "contentDescription": node.get("contentDescription"),
                    "resourceId": node.get("resourceId"),
                    "className": node.get("className"),
                }
                self.log_action({
                    "action": "tap",
                    "original_index": idx,
                    "criteria": criteria
                })
                # -----------------------
                
                print(f"🎯 Tapping [{idx}] at ({cx},{cy})")
                self.tap(cx, cy)
            else:
                print(f"❌ Index {idx} has invalid bounds.")
        else:
            print(f"❌ Index {idx} out of range.")

    def input_text(self, text):
        encoded = base64.b64encode(text.encode()).decode()
        self._post("/keyboard/input", {"base64_text": encoded})
        self.log_action({"action": "input", "text": text})

    def tap(self, x, y): self._post("/action/tap", {"x": int(x), "y": int(y)})
    def home(self): 
        self._post("/action/global", {"action": 2})
        self.log_action({"action": "home"})
        
    def back(self): 
        self._post("/action/global", {"action": 1})
        self.log_action({"action": "back"})

    def _post(self, endpoint, payload):
        try:
            url = f"{self.base_url}{endpoint}"
            requests.post(url, json=payload, headers=self.headers, timeout=5)
        except: pass

    def sleep(self, seconds):
        try:
            sec = float(seconds)
            self.log_action({"action": "sleep", "duration": sec})
            print(f"😴 Sleeping for {sec} seconds...")
            time.sleep(sec)
        except: print("❌ Invalid number")

    # ... existing methods ...

    def clear_text(self):
        self._post("/keyboard/clear", {})
        self.log_action({"action": "clear"})
        print("🧹 Text Cleared")

    def press_keycode(self, key_code):
        try:
            k = int(key_code)
            self._post("/keyboard/key", {"key_code": k})
            self.log_action({"action": "key", "key_code": k})
            print(f"🎹 Key Code {k} Sent")
        except: print("❌ Invalid Key Code")

    def dump_fast(self):
        print("⚡ Fetching Fast UI Tree (/a11y_tree)...")
        t1 = time.time()
        try:
            resp = requests.get(f"{self.base_url}/a11y_tree", headers=self.headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                root = data.get("result") or data # Handle wrapper if present
                
                # FIX: raw result is a stringified JSON
                if isinstance(root, str):
                    try:
                        root = json.loads(root)
                    except: pass

                print(f"✅ Fast Dump Done in {time.time()-t1:.3f}s")
                
                # Reuse dump logic if structure is same
                flat_list = []
                self.traverse_tree_list(root, flat_list)
                self.print_list_table(flat_list)
                    
            else: print(f"❌ Failed: {resp.status_code}")
        except Exception as e: print(f"❌ Error: {e}")

    def long_press_index(self, index, duration_ms=1000):
        idx = int(index)
        state = self.get_state_json()
        if not state: return
        
        root_tree = state.get("a11y_tree")
        flat_list = []
        self.traverse_tree_list(root_tree, flat_list)
        
        if 0 <= idx < len(flat_list):
            node = flat_list[idx]
            b = self.get_bounds(node)
            
            if b:
                cx, cy = (b[0]+b[2])//2, (b[1]+b[3])//2
                
                # --- RECORDING LOGIC ---
                self.log_action({
                    "action": "long_press",
                    "original_index": idx,
                    "x": cx, "y": cy, "duration": duration_ms
                })
                # -----------------------
                
                print(f"👆 Long Pressing [{idx}] at ({cx},{cy}) for {duration_ms}ms")
                self._post("/action/swipe", {"startX": int(cx), "startY": int(cy), "endX": int(cx), "endY": int(cy), "duration": duration_ms})
            else:
                print(f"❌ Index {idx} has invalid bounds.")
        else:
            print(f"❌ Index {idx} out of range.")

    def swipe(self, sx, sy, ex, ey, duration=500):
         self._post("/action/swipe", {"startX": int(sx), "startY": int(sy), "endX": int(ex), "endY": int(ey), "duration": duration})

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🎥 --- DroidRun Wireless RECORDER ---")
    recorder = DroidRunWirelessRecorder()
    
    while True:
        print("\n[idx <N>] [long <N>] [txt <MSG>] [clear] [key <N|Name>]")
        print("[dump/fast] [sleep <N>] [home] [back] [exit] -> (Type 'help' for details)")
        print("Shortcuts: enter, backspace, tab, up, down, left, right")
        cmd = input("REC > ").strip().lower()
        
        if cmd in ['exit', 'x', 'q']: 
            print("💾 Log saved to 'action_wifi_log.txt'. Exiting...")
            break
        elif cmd in ['help', 'h', '?']:
            print("\n📖 --- คู่มือการใช้งาน (Commands) ---")
            print("  dump       : ดึงโครงสร้างหน้าจอ (UI Tree) แบบละเอียด")
            print("  fast       : ดึงโครงสร้างหน้าจอแบบเร็ว (แนะนำ)")
            print("  idx <N>    : จิ้ม (Tap) ที่ Index นั้น เช่น 'idx 5'")
            print("  long <N>   : กดค้างที่ Index นั้น (ค่าเดิม 1วิ) เช่น 'long 5 2000'")
            print("  txt <msg>  : พิมพ์ข้อความ (รองรับไทย) เช่น 'txt สวัสดี'")
            print("  clear      : สั่งลบข้อความในช่องพิมพ์ (Clear Text)")
            print("  home       : กดปุ่มโฮม")
            print("  back       : กดปุ่มย้อนกลับ")
            print("  sleep <N>  : หยุดรอ N วินาที เช่น 'sleep 2'")
            print("  key <Code> : กดปุ่มด้วย KeyCode หรือชื่อปุ่ม")
            print("  <shortcut> : พิมพ์ชื่อปุ่มได้เลย: enter, backspace, tab, escape, up, down, left, right")
            print("  exit / x   : บันทึก Log และออกจากโปรแกรม")
            print("------------------------------------------")

        elif cmd == 'dump': recorder.dump_ui()
        elif cmd == 'fast': recorder.dump_fast()
        elif cmd == 'clear': recorder.clear_text()
        elif cmd.startswith('key'): 
            arg = cmd.split()[1] if len(cmd.split())>1 else "0"
            
            # Key Mapping
            KEY_MAP = {
                "enter": 66, "backspace": 67, "tab": 61, "escape": 111,
                "back": 4, "home": 3, 
                "up": 19, "down": 20, "left": 21, "right": 22
            }
            
            code = KEY_MAP.get(arg.lower(), arg)
            recorder.press_keycode(code)
        elif cmd.startswith('idx'):
            p = cmd.split()
            if len(p) > 1: recorder.tap_index(p[1])
        elif cmd.startswith('long'):
            # Usage: long <idx> [duration]
            p = cmd.split()
            if len(p) > 1: 
                dur = int(p[2]) if len(p) > 2 else 1000
                recorder.long_press_index(p[1], dur)
        elif cmd.startswith('txt'): recorder.input_text(cmd[4:])
        elif cmd.startswith('sleep'): recorder.sleep(cmd[6:])
        elif cmd == 'home': recorder.home()
        elif cmd == 'back': recorder.back()
        elif cmd == 'ping': recorder.check_connection()
        # Direct key shortcuts (e.g. just "enter" instead of "key enter")
        elif cmd in ["enter", "backspace", "tab", "escape", "up", "down", "left", "right"]:
            KEY_MAP = {"enter": 66, "backspace": 67, "tab": 61, "escape": 111, "up": 19, "down": 20, "left": 21, "right": 22}
            recorder.press_keycode(KEY_MAP[cmd])

if __name__ == "__main__":
    main()

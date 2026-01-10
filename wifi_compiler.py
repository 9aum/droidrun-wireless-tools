import json
import os
import sys

TEMPLATE_HEADER = '''import requests
import json
import base64
import time
import re
import wifi_config

class DroidRunBot:
    def __init__(self):
        self.ip = wifi_config.TARGET_IP
        self.port = wifi_config.TARGET_PORT
        self.token = wifi_config.AUTH_TOKEN
        self.base_url = f"http://{self.ip}:{self.port}"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        print(f"🤖 Bot Started on {self.base_url}")

    def _post(self, endpoint, payload):
        try:
            url = f"{self.base_url}{endpoint}"
            requests.post(url, json=payload, headers=self.headers, timeout=5)
        except Exception as e: print(f"❌ Connection Error: {e}")

    def get_state_json(self):
        try:
            resp = requests.get(f"{self.base_url}/state_full", headers=self.headers, timeout=10)
            if resp.status_code == 200: 
                data = resp.json()
                if "result" in data: return data["result"]
                return data
        except: pass
        return None

    def find_node(self, criteria):
        state = self.get_state_json()
        if not state: return None
        
        # Flatten tree
        nodes = []
        def traverse(n):
            if isinstance(n, list): 
                for i in n: traverse(i)
            elif isinstance(n, dict):
                nodes.append(n)
                traverse(n.get("children") or n.get("subnodes"))
        traverse(state.get("a11y_tree"))

        # Search Logic
        best_node = None
        best_score = 0
        
        t_text = criteria.get("text")
        t_desc = criteria.get("contentDescription")
        t_id = criteria.get("resourceId")
        
        for node in nodes:
            score = 0
            n_text = node.get("text")
            n_desc = node.get("contentDescription")
            n_id = node.get("resourceId")

            if t_text and n_text == t_text: score += 3
            if t_desc and n_desc == t_desc: score += 3
            if t_id and n_id == t_id: score += 2
            if t_text and n_text and t_text in n_text: score += 1
            
            if score > best_score:
                best_score = score
                best_node = node
        
        return best_node if best_score >= 2 else None

    def get_center(self, node):
        b = node.get("boundsInScreen")
        if isinstance(b, dict):
             return (b['left']+b['right'])//2, (b['top']+b['bottom'])//2
        # Fallback for string bounds
        b_str = node.get("bounds")
        if isinstance(b_str, str):
            m = re.findall(r'\\d+', b_str)
            if len(m) >= 4:
                vals = [int(x) for x in m]
                return (vals[0]+vals[2])//2, (vals[1]+vals[3])//2
        return None, None

    def run(self):
        print("🎬 Action Started...")
'''

TEMPLATE_FOOTER = '''
        print("✅ Script Finished Successfully!")

if __name__ == "__main__":
    bot = DroidRunBot()
    bot.run()
'''

def compile_log():
    log_file = "action_wifi_log.txt"
    if not os.path.exists(log_file):
        print(f"❌ Error: Log file '{log_file}' not found.")
        return

    print("🔨 --- DroidRun Compiler ---")
    output_name = input("📄 Enter output filename (e.g. my_bot.py): ").strip()
    if not output_name.endswith(".py"): output_name += ".py"

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    code_body = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        
        try:
            data = json.loads(line)
            action = data.get("action")
            
            code_body += f"\n        # Step {i+1}: {action}\n"
            
            if action == "home":
                code_body += '        self._post("/action/global", {"action": 2})\n'
                code_body += '        time.sleep(1.0)\n'
                
            elif action == "back":
                code_body += '        self._post("/action/global", {"action": 1})\n'
                code_body += '        time.sleep(1.0)\n'
                
            elif action == "sleep":
                dur = data.get("duration", 1.0)
                code_body += f'        print(f"😴 Sleep {dur}s")\n'
                code_body += f'        time.sleep({dur})\n'

            elif action == "clear":
                code_body += '        self._post("/keyboard/clear", {})\n'
                code_body += '        print("🧹 Cleared Text")\n'
                code_body += '        time.sleep(0.5)\n'

            elif action == "key":
                k = data.get("key_code")
                code_body += f'        self._post("/keyboard/key", {{"key_code": {k}}})\n'
                code_body += f'        print("🎹 Key {k} Sent")\n'
                code_body += '        time.sleep(0.5)\n'

            elif action == "input":
                txt = data.get("text", "")
                # Encode text properly in generated code
                code_body += f'        encoded = base64.b64encode("{txt}".encode()).decode()\n'
                code_body += '        self._post("/keyboard/input", {"base64_text": encoded})\n'
                code_body += f'        print("✍️ Input: {txt}")\n'
                code_body += '        time.sleep(1.0)\n'

            elif action == "tap":
                criteria = data.get("criteria", {})
                code_body += f'        criteria = {json.dumps(criteria)}\n'
                code_body += '        node = self.find_node(criteria)\n'
                code_body += '        if node:\n'
                code_body += '            cx, cy = self.get_center(node)\n'
                code_body += '            if cx:\n'
                code_body += f'                print(f"🎯 Tap: {{criteria.get(\'text\') or \'Element\'}} at ({{cx}},{{cy}})")\n'
                code_body += '                self._post("/action/tap", {"x": int(cx), "y": int(cy)})\n'
                code_body += '            else: print("⚠️ Invalid Bounds")\n'
                code_body += '        else: print(f"⚠️ Element not found: {criteria.get(\'text\')}")\n'
                code_body += '        time.sleep(1.5)\n'

        except Exception as e:
            print(f"⚠️ Error parsing line {i}: {e}")

    full_script = TEMPLATE_HEADER + code_body + TEMPLATE_FOOTER
    
    with open(output_name, "w", encoding="utf-8") as f:
        f.write(full_script)
        
    print(f"\n✨ Compiled! Saved to: {output_name}")
    print(f"👉 Run it with: python {output_name}")

if __name__ == "__main__":
    compile_log()

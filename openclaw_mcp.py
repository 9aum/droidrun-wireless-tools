import requests
import json
import base64
import time
import sys
import os

# Import local config
try:
    import wifi_config
except ImportError:
    print("Error: wifi_config.py not found.")
    sys.exit(1)

class MCPForMe:
    def __init__(self):
        self.base_url = f"http://{wifi_config.TARGET_IP}:{wifi_config.TARGET_PORT}"
        self.headers = {
            "Authorization": f"Bearer {wifi_config.API_KEY}",
            "Content-Type": "application/json"
        }
        self.width = 1080
        self.height = 2340
        self._init_device_info()

    def _init_device_info(self):
        try:
            resp = requests.get(f"{self.base_url}/phone_state", headers=self.headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data and isinstance(data["result"], str):
                    try:
                        inner = json.loads(data["result"])
                        data.update(inner)
                    except: pass
                self.width = data.get("displayWidth", 1080)
                self.height = data.get("displayHeight", 2340)
        except: pass

    def _post(self, endpoint, payload=None, timeout=10):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.post(url, json=payload or {}, headers=self.headers, timeout=timeout)
            resp.raise_for_status()
            return {"status": "success", "data": resp.json() if resp.text else None}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get(self, endpoint, timeout=15):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if "result" in data and isinstance(data["result"], str):
                try:
                    data["result_parsed"] = json.loads(data["result"])
                except: pass
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- ACTIONS ---
    def global_action(self, action_id):
        """1: BACK, 2: HOME, 3: RECENTS, 4: NOTIFICATIONS"""
        return self._post("/action/global", {"action": action_id})

    def tap(self, x, y):
        return self._post("/action/tap", {"x": int(x), "y": int(y)})

    def long_press(self, x, y, duration=1000):
        return self._post("/action/swipe", {"startX": int(x), "startY": int(y), "endX": int(x), "endY": int(y), "duration": int(duration)})

    def type_text(self, text):
        b64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        return self._post("/keyboard/input", {"base64_text": b64_text})

    def clear_text(self):
        return self._post("/keyboard/clear")

    def press_key(self, key_code):
        return self._post("/keyboard/key", {"key_code": int(key_code)})

    def dump_ui(self):
        return self._get("/a11y_tree")

    def swipe(self, x1, y1, x2, y2, duration=300):
        return self._post("/action/swipe", {"startX": int(x1), "startY": int(y1), "endX": int(x2), "endY": int(y2), "duration": int(duration)})

    def swipe_dir(self, direction, duration=500):
        cx, cy = self.width // 2, self.height // 2
        dx, dy = self.width // 3, self.height // 3
        if direction == "left": sx, sy, ex, ey = cx + dx, cy, cx - dx, cy
        elif direction == "right": sx, sy, ex, ey = cx - dx, cy, cx + dx, cy
        elif direction == "up": sx, sy, ex, ey = cx, cy + dy, cx, cy - dy
        elif direction == "down": sx, sy, ex, ey = cx, cy - dy, cx, cy + dy
        else: return {"status": "error", "message": f"Invalid direction: {direction}"}
        return self.swipe(sx, sy, ex, ey, duration)

    def launch(self, package):
        res = self._post("/action/launch", {"package": package})
        if res["status"] == "error":
            return self._post("/action/shell", {"command": f"monkey -p {package} -c android.intent.category.LAUNCHER 1"})
        return res

# CLI Wrapper
if __name__ == "__main__":
    mcp = MCPForMe()
    if len(sys.argv) < 2:
        print("Usage: python3 mcpforme.py [home|back|recents|dump|tap x y|long x y [ms]|type 'text'|clear|key code|swipe x1 y1 x2 y2 [ms]|swipe left|right|up|down [ms]|launch pkg]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "home": print(mcp.global_action(2))
    elif cmd == "back": print(mcp.global_action(1))
    elif cmd == "recents": print(mcp.global_action(3))
    elif cmd == "dump": print(json.dumps(mcp.dump_ui(), indent=2, ensure_ascii=False))
    elif cmd == "clear": print(mcp.clear_text())
    elif cmd == "tap" and len(sys.argv) == 4:
        print(mcp.tap(sys.argv[2], sys.argv[3]))
    elif cmd == "long" and len(sys.argv) >= 4:
        dur = sys.argv[4] if len(sys.argv) == 5 else 1000
        print(mcp.long_press(sys.argv[2], sys.argv[3], dur))
    elif cmd == "type" and len(sys.argv) == 3:
        print(mcp.type_text(sys.argv[2]))
    elif cmd == "key" and len(sys.argv) == 3:
        print(mcp.press_key(sys.argv[2]))
    elif cmd == "swipe" and len(sys.argv) >= 3 and sys.argv[2] in ["left", "right", "up", "down"]:
        dur = sys.argv[3] if len(sys.argv) == 4 else 500
        print(mcp.swipe_dir(sys.argv[2], dur))
    elif cmd == "swipe" and len(sys.argv) >= 6:
        dur = sys.argv[6] if len(sys.argv) == 7 else 300
        print(mcp.swipe(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], dur))
    elif cmd == "launch" and len(sys.argv) == 3:
        print(mcp.launch(sys.argv[2]))
    else:
        print(f"Unknown command or wrong arguments: {cmd}")

# 📱 DroidRun Wireless Automation Tools

ชุดเครื่องมือสำหรับควบคุมและจัดการ Android Automation ผ่าน DroidRun HTTP API แบบไร้สาย (Wireless) โดยใช้ Python

## 📂 ไฟล์ในโปรเจกต์
1.  **`wifi_recorder.py`**: พระเอกหลัก! โปรแกรมสำหรับ "บันทึก" การกระทำบนหน้าจอมือถือ
    *   ดึงโครงสร้างหน้าจอ (Dump UI)
    *   สั่งกด (Tap), กดค้าง (Long Press), พิมพ์ข้อความ (Text Input)
    *   บันทึก Log การกระทำเพื่อนำไปเขียน Script ต่อ
2.  **`wifi_compiler.py`**: ตัวแปลง Log เป็น Code!
    *   อ่านไฟล์ `action_wifi_log.txt` ที่ได้จาก Recorder
    *   แปลงเป็นไฟล์ Python Script (.py) แบบ Standalone พร้อมรันทันที
    *   เหมาะสำหรับคนไม่อยากเขียนโค้ดเอง แค่กดอัดแล้วสั่ง Compile จบ!
3.  **`wifi_config_template.py`**: ไฟล์ตั้งค่าการเชื่อมต่อ

## 🚀 วิธีติดตั้งและใช้งาน

### 1. การเตรียมความพร้อมของระบบ (System Configuration)

เพื่อให้การทำงานเป็นไปอย่างราบรื่น กรุณาดำเนินการเตรียมความพร้อมดังนี้:

**1. ติดตั้งแอปพลิเคชันหลัก (Required Application)**
   กรุณาติดตั้งไฟล์ **APK** ของ **DroidRun Portal** ลงบนอุปกรณ์ Android ของท่าน เพื่อให้สามารถรับคำสั่งควบคุมผ่านเครือข่ายได้
   *   📍 **แหล่งดาวน์โหลด (Download):** [https://github.com/droidrun/droidrun-portal/releases](https://github.com/droidrun/droidrun-portal/releases)

**2. ติดตั้งชุดคำสั่งภาษา Python (Python Environment)**
   ระบบต้องการ Python Library สำหรับการสื่อสาร กรุณาติดตั้งผ่าน Command Line:
```bash
pip install requests
```

### 2. ตั้งค่าการเชื่อมต่อ
1.  เปลี่ยนชื่อไฟล์ `wifi_config_template.py` เป็น `wifi_config.py`
2.  แก้ไขค่าภายในไฟล์ให้ตรงกับเครื่องของคุณ:
    ```python
    TARGET_IP = "192.168.1.xxx"  # IP ของมือถือ
    TARGET_PORT = 8080           # Port ของ DroidRun
    API_KEY = "dr_sk_xxxxx"      # API Key จากแอป DroidRun (ตัวอย่าง: dr_sk_... ยาว 70 ตัวอักษร)
    ```

### 3. การใช้งาน Recorder (`wifi_recorder.py`)
รันโปรแกรมเพื่อเริ่มบันทึก:
```bash
python wifi_recorder.py
```
เมื่อบันทึกเสร็จ (กด `exit`), ระบบจะสร้างไฟล์ `action_wifi_log.txt`

### 4. การใช้งาน Compiler (`wifi_compiler.py`)
แปลง Log เป็น Script พร้อมใช้:
```bash
python wifi_compiler.py
```
*   ระบบจะถามชื่อไฟล์ปลายทาง (เช่น `my_script.py`)
*   จะได้ไฟล์ Python ใหม่ที่เอาไปรันได้เลย!


### 5. การใช้งาน DroidRun MCP Server (`droidrun_mcp_server.py`)
สำหรับใช้งานร่วมกับ AI Agent (เช่น Claude Desktop, Cursor, หรือ Custom Agent) ผ่าน Model Context Protocol (MCP)

**ความสามารถ:**
*   `tap_coordinate(x, y)`: สั่งกดที่พิกัด
*   `type_text(text)`: พิมพ์ข้อความ
*   `press_key(code/name)`: กดปุ่ม (enter, back, home ฯลฯ)
*   `long_press(x, y, duration)`: กดค้าง
*   `swipe(sx, sy, ex, ey)`: สไลด์หน้าจอตามพิกัด
*   `swipe_dir(direction)`: สไลด์หน้าจอตามทิศทาง (left, right, up, down)
*   **New in V2.0:**
    *   `get_device_info()`: ดูสถานะเครื่อง (App ที่เปิดอยู่)
    *   `list_apps()`: ดูรายชื่อ App ทั้งหมดในเครื่อง
    *   `get_screenshot()`: ดึงรูปหน้าจอ (Vision) ไปให้ AI วิเคราะห์
    *   `stop_app(package_name)`: บังคับหยุดการทำงานของแอป (Force Stop)
    *   `fast mode`: ใช้ `/a11y_tree` ทำงานไวกว่าเดิม 3 เท่า

**ขั้นตอนการติดตั้ง (Installation Sequence):**

1.  **ติดตั้ง Model Context Protocol (MCP) SDK**
    กรุณาติดตั้งไลบรารีที่จำเป็นผ่าน Command Line:
    ```bash
    pip install "mcp[cli]"
    ```
2.  **ตั้งค่าการเชื่อมต่อ (Configuration)**
    เพิ่มการตั้งค่าลงในไฟล์ Config ของ AI Agent (เช่น `claude_desktop_config.json` หรือ `mcp_config.json`):
    ```json
    {
      "mcpServers": {
        "droidrun": {
          "command": "python",
          "args": ["/absolute/path/to/droidrun_mcp_server.py"]
        }
      }
    }
    ```
    *(ข้อควรระวัง: โปรดตรวจสอบ path ของไฟล์ให้ถูกต้องตามตำแหน่งจริงในเครื่องของท่าน)*

**🎥 ตัวอย่างการทำงาน (Demo):**

[![Watch the demo](https://img.youtube.com/vi/Kv_v4gm3zl4/0.jpg)](https://youtu.be/Kv_v4gm3zl4)

*(วิดีโอแสดงการทำงานของ `wifi_recorder.py`: การบันทึก actions และการสั่งงานแบบไร้สาย)*

**คำสั่งที่ใช้ได้ (Commands) ใน `wifi_recorder.py`:**
*   `dump`       : ดึงโครงสร้างหน้าจอ (UI Tree) แบบละเอียด
*   `fast`       : ดึงโครงสร้างหน้าจอแบบเร็ว (แนะนำ)
*   `idx <N>`    : จิ้ม (Tap) ที่ Index นั้น เช่น `idx 5`
*   `long <N> [ms]`: กดค้างที่ Index นั้น (ค่าเดิม 1000ms) เช่น `long 5 2000`
*   `swipe`      : ปัดหน้าจอพิกัด `(sx, sy)` ไป `(ex, ey)` เช่น `swipe 500 1500 500 500 500`
               : หรือปัดแบบง่ายตามทิศทาง เช่น `swipe left`, `swipe right`, `swipe up`, `swipe down`
*   `txt <msg>`  : พิมพ์ข้อความ (รองรับไทย) เช่น `txt สวัสดี`
*   `clear`      : สั่งลบข้อความในช่องพิมพ์ (Clear Text)
*   `home`       : กดปุ่มโฮม
*   `back`       : กดปุ่มย้อนกลับ
*   `sleep <N>`  : หยุดรอ N วินาที เช่น `sleep 2`
*   `key <Code>` : กดปุ่มด้วย KeyCode หรือชื่อปุ่ม
*   `<shortcut>` : พิมพ์ชื่อปุ่มได้เลย: `enter`, `backspace`, `tab`, `escape`, `up`, `down`, `left`, `right`
*   `exit` / `x` : บันทึก Log และออกจากโปรแกรม

---
**Developed for DroidRun Automation**

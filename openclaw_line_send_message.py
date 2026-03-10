import time
import sys
import json
import re
from mcpforme import MCPForMe

def find_node(nodes, criteria):
    best_node = None
    best_score = 0
    
    t_text = criteria.get("text")
    t_desc = criteria.get("contentDescription")
    t_id = criteria.get("resourceId")
    
    # Flatten tree
    flat_nodes = []
    def traverse(n):
        if isinstance(n, list): 
            for i in n: traverse(i)
        elif isinstance(n, dict):
            flat_nodes.append(n)
            traverse(n.get("children") or n.get("subnodes"))
    
    traverse(nodes)

    for node in flat_nodes:
        score = 0
        n_text = node.get("text")
        n_desc = node.get("contentDescription")
        n_id = node.get("resourceId")

        if t_text and n_text == t_text: score += 3
        if t_desc and n_desc == t_desc: score += 3
        if t_id and n_id and t_id in n_id: score += 2
        if t_text and n_text and t_text in n_text: score += 1
        
        if score > best_score:
            best_score = score
            best_node = node
    
    return best_node if best_score >= 2 else None

def get_center(node):
    if not node: return None, None
    b = node.get("boundsInScreen")
    if isinstance(b, dict):
         return (b['left']+b['right'])//2, (b['top']+b['bottom'])//2
    # Fallback for string bounds
    b_str = node.get("bounds")
    if isinstance(b_str, str):
        m = re.findall(r'\d+', b_str)
        if len(m) >= 4:
            vals = [int(x) for x in m]
            return (vals[0]+vals[2])//2, (vals[1]+vals[3])//2
    return None, None

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 line_send_message.py '<target_name>' '<message>'")
        sys.exit(1)

    target_name = sys.argv[1]
    message = sys.argv[2]
    mcp = MCPForMe()

    print(f"--- Starting LINE Send Mission: To '{target_name}' ---")
    
    # 1. Back to Home and Launch LINE
    mcp.global_action(2) # HOME
    time.sleep(1)
    
    # Check current screen first
    print("Checking current screen for LINE...")
    dump = mcp.dump_ui()
    nodes = dump.get("data", {}).get("result_parsed", [])
    line_node = find_node(nodes, {"text": "LINE"})
    
    if not line_node:
        print("Finding LINE icon via swipe...")
        mcp.swipe_dir("left")
        time.sleep(1)
        mcp.swipe_dir("left")
        time.sleep(1)
        dump = mcp.dump_ui()
        nodes = dump.get("data", {}).get("result_parsed", [])
        line_node = find_node(nodes, {"text": "LINE"})
    
    if not line_node:
        print("Error: LINE icon not found. Attempting shell launch...")
        mcp.launch("jp.naver.line.android")
    else:
        cx, cy = get_center(line_node)
        print(f"Tapping LINE icon at ({cx}, {cy})")
        mcp.tap(cx, cy)
    
    print("LINE opening. Waiting for chat list...")
    time.sleep(4)

    # 2. Find Chat Room
    dump = mcp.dump_ui()
    nodes = dump.get("data", {}).get("result_parsed", [])
    chat_node = find_node(nodes, {"text": target_name})
    
    if not chat_node:
        print(f"Error: Chat room '{target_name}' not found in list.")
        return
    
    cx, cy = get_center(chat_node)
    mcp.tap(cx, cy)
    print(f"Entered chat: {target_name}. Waiting...")
    time.sleep(1)

    # 3. Find Input Field and Type
    mcp.type_text(message)
    print(f"Typed message: {message}")
    time.sleep(1)

    # 4. Find SEND button
    print("Searching for SEND button...")
    dump = mcp.dump_ui()
    nodes = dump.get("data", {}).get("result_parsed", [])
    send_node = find_node(nodes, {"text": "Send"})
    
    if not send_node:
        print("Error: Send button not found. Attempting backup coordinate (1008, 2139)...")
        mcp.tap(1008, 2139)
    else:
        cx, cy = get_center(send_node)
        mcp.tap(cx, cy)
        print(f"Send button clicked at {cx}, {cy}")

    time.sleep(1)

    # 5. Cleanup
    print("Mission complete. Returning Home...")
    mcp.global_action(1) # BACK
    time.sleep(1)
    mcp.global_action(2) # HOME
    time.sleep(1)
    print("Done.")

if __name__ == "__main__":
    main()

import serial
import time
import tkinter as tk
from tkinter import ttk

# --- CONFIGURATION ---
SERIAL_PORT = 'COM3'
BAUD_RATE = 1000000
# ---------------------

class RokenbokGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rokenbok Smart Port Master Control (16 Slots)")
        self.root.geometry("1200x800")
        
        # State Data - 16 Slots for Commanding
        self.players = [[i + 2, 15] for i in range(16)]
        self.active_idx = 0
        self.held_keys = set()
        
        # Default Enable Setting to OFF - 16 Slots
        self.enabled_vars = [tk.BooleanVar(value=False) for _ in range(16)]
        
        # Arduino Feedback Storage - Back to 12
        self.mcu_sp_status = 0
        self.mcu_user_ids = [0] * 12
        self.mcu_selects = [15] * 12
        
        # Debugging Strings
        self.last_sent_hex = ""
        self.last_rcvd_hex = ""
        
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
        except Exception as e:
            print(f"Serial Error: {e}")
            self.ser = None

        self.setup_ui()
        
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        
        self.update_loop()

    def setup_ui(self):
        # --- HEADER ---
        self.header_frame = tk.Frame(self.root, pady=10)
        self.header_frame.pack(fill=tk.X)
        
        self.sync_label = tk.Label(self.header_frame, text="SMART PORT OFFLINE", font=("Arial", 14, "bold"), fg="red")
        self.sync_label.pack(side=tk.LEFT, padx=20)
        
        self.instr_label = tk.Label(self.header_frame, text="[ ] : Cycle Slot | - = : Change Vehicle | Keys: WASD, RF, QE, Shift")
        self.instr_label.pack(side=tk.RIGHT, padx=20)

        # --- CONTROLLER GRID (4x4 for 16 slots) ---
        self.grid_frame = tk.Frame(self.root, padx=10, pady=5)
        self.grid_frame.pack(expand=True, fill=tk.BOTH)
        
        self.slots = []
        for i in range(16):
            frame = tk.LabelFrame(self.grid_frame, text=f"Slot {i+1}", padx=5, pady=5)
            frame.grid(row=i//4, column=i%4, sticky="nsew", padx=5, pady=2)
            
            chk = tk.Checkbutton(frame, text="Enable", variable=self.enabled_vars[i])
            chk.pack()
            
            id_lbl = tk.Label(frame, text=f"User ID: {self.players[i][0]}", font=("Courier", 10))
            id_lbl.pack()
            
            sel_lbl = tk.Label(frame, text=f"Select: {self.players[i][1]}", font=("Courier", 10))
            sel_lbl.pack()
            
            btn_lbl = tk.Label(frame, text="0000 | 00000", font=("Courier", 10))
            btn_lbl.pack()
            
            self.slots.append({"frame": frame, "id": id_lbl, "sel": sel_lbl, "btn": btn_lbl})
        
        for i in range(4): self.grid_frame.columnconfigure(i, weight=1)

        # --- ARDUINO FEEDBACK MONITOR (12 Labels) ---
        self.feedback_frame = tk.LabelFrame(self.root, text="Received Values from Arduino", padx=10, pady=10, fg="blue")
        self.feedback_frame.pack(fill=tk.X, padx=15, pady=5)

        self.mcu_labels = []
        names = ["V1", "V2", "V3", "V4", "P1", "P2", "P3", "P4", "D1", "D2", "D3", "D4"]
        for i, name in enumerate(names):
            f = tk.Frame(self.feedback_frame)
            f.pack(side=tk.LEFT, expand=True)
            tk.Label(f, text=name, font=("Arial", 10, "bold")).pack()
            val_lbl = tk.Label(f, text="ID:--\nSEL:--", font=("Courier", 9), justify=tk.CENTER)
            val_lbl.pack()
            self.mcu_labels.append(val_lbl)

        # --- PACKET DEBUGGER SECTION ---
        self.debug_frame = tk.LabelFrame(self.root, text="Packet Monitor (Hex)", padx=10, pady=5, fg="darkgreen")
        self.debug_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.send_debug_lbl = tk.Label(self.debug_frame, text="SEND: --", font=("Courier", 9), anchor="w", justify=tk.LEFT)
        self.send_debug_lbl.pack(fill=tk.X)
        
        self.rcvd_debug_lbl = tk.Label(self.debug_frame, text="RCVD: --", font=("Courier", 9), anchor="w", justify=tk.LEFT, fg="blue")
        self.rcvd_debug_lbl.pack(fill=tk.X)

    def on_key_press(self, event):
        k = event.char
        key_name = event.keysym
        if k == '[': self.active_idx = (self.active_idx - 1) % 16
        elif k == ']': self.active_idx = (self.active_idx + 1) % 16
        elif k == '-': self.players[self.active_idx][1] = (self.players[self.active_idx][1] - 1) % 16
        elif k == '=': self.players[self.active_idx][1] = (self.players[self.active_idx][1] + 1) % 16
        self.held_keys.add(k.lower())
        self.held_keys.add(key_name)

    def on_key_release(self, event):
        self.held_keys.discard(event.char.lower())
        self.held_keys.discard(event.keysym)

    def update_loop(self):
        if self.ser:
            # 1. Prepare and Send Packet
            packet = bytearray([254])
            current_ui_bits = []
            
            for i in range(16):
                p_id, v_sel = self.players[i]
                byte1 = byte2 = 0
                if self.enabled_vars[i].get():
                    if i == self.active_idx:
                        up, down, right, left = ('w' in self.held_keys, 's' in self.held_keys, 'd' in self.held_keys, 'a' in self.held_keys)
                        b_a, b_b, b_x, b_y = ('f' in self.held_keys, 'r' in self.held_keys, 'q' in self.held_keys, 'e' in self.held_keys)
                        b_rt = 1 if ('Shift_L' in self.held_keys or 'Shift_R' in self.held_keys) else 0
                        byte1 = (up << 3) | (down << 2) | (right << 1) | left
                        byte2 = (b_a << 4) | (b_b << 3) | (b_x << 2) | (b_y << 1) | b_rt
                    packet.extend([p_id, v_sel, byte1, byte2])
                current_ui_bits.append((byte1, byte2))
            
            packet.append(255)
            self.ser.write(packet)
            self.last_sent_hex = packet.hex(' ').upper()

            # 2. Read Feedback (27 bytes: 254 + Status + 12 IDs + 12 Sels + 255)
            if self.ser.in_waiting >= 27:
                raw = self.ser.read(self.ser.in_waiting)
                start = raw.rfind(254)
                if start != -1 and len(raw) >= start + 27 and raw[start+26] == 255:
                    frame = raw[start:start+27]
                    self.mcu_sp_status = frame[1]
                    self.mcu_user_ids = list(frame[2:14])
                    self.mcu_selects = list(frame[14:26])
                    self.last_rcvd_hex = frame.hex(' ').upper()

        # 3. Update UI
        self.sync_label.config(
            text="SMART PORT ONLINE" if self.mcu_sp_status else "SMART PORT OFFLINE",
            fg="green" if self.mcu_sp_status else "red"
        )
        
        # Update Debug Labels
        self.send_debug_lbl.config(text=f"SEND: {self.last_sent_hex}")
        self.rcvd_debug_lbl.config(text=f"RCVD: {self.last_rcvd_hex}")

        for i in range(16):
            slot = self.slots[i]
            p_id, v_sel = self.players[i]
            slot["frame"].config(bg="#d1e7ff" if i == self.active_idx else "SystemButtonFace")
            slot["id"].config(text=f"User ID: {p_id}")
            slot["sel"].config(text=f"Select: {v_sel if v_sel < 15 else '--'}")
            b1, b2 = current_ui_bits[i]
            slot["btn"].config(text=f"{bin(b1)[2:].zfill(4)} | {bin(b2)[2:].zfill(5)}")

        for i in range(12):
            m_id = self.mcu_user_ids[i]
            m_sel = self.mcu_selects[i]
            sel_str = m_sel if m_sel < 15 else "--"
            text_color = "green" if m_id >= 2 else ("red" if m_id == 1 else "black")
            self.mcu_labels[i].config(text=f"ID:{m_id}\nSEL:{sel_str}", fg=text_color)

        self.root.after(50, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = RokenbokGUI(root)
    root.mainloop()
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
import cv2
import threading
import json
import os
import time
import sqlite3
import ctypes
import string
import shutil
import tkinter as tk
from tkinter import filedialog
import calendar
from datetime import date
from controls import BottomControlBar, RightControlPanel, PlaybackInfoPanel

class DatePickerPopup(Popup):
    def __init__(self, callback, **kwargs):
        super().__init__(title="Select Date Range", size_hint=(0.8, 0.8), **kwargs)
        self.callback = callback
        self.current_date = date.today()
        self.start_date = None
        self.end_date = None
        self.build_ui()

    def build_ui(self):
        self.content = BoxLayout(orientation='vertical', spacing=5)
        
        self.lbl_instruction = Label(text="Select Start Date", size_hint_y=None, height='30dp', bold=True, color=(1,1,0,1))
        self.content.add_widget(self.lbl_instruction)
        
        # Header (Month/Year with navigation)
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        btn_prev = Button(text="<", size_hint_x=0.2, background_color=[0.25, 0.3, 0.35, 1])
        btn_prev.bind(on_press=self.prev_month)
        self.lbl_month = Label(text=self.current_date.strftime("%B %Y"), size_hint_x=0.6, bold=True)
        btn_next = Button(text=">", size_hint_x=0.2, background_color=[0.25, 0.3, 0.35, 1])
        btn_next.bind(on_press=self.next_month)
        
        header.add_widget(btn_prev)
        header.add_widget(self.lbl_month)
        header.add_widget(btn_next)
        self.content.add_widget(header)
        
        # Days of week
        days_header = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            days_header.add_widget(Label(text=d, bold=True))
        self.content.add_widget(days_header)
        
        # Calendar Grid
        self.grid = GridLayout(cols=7, spacing=2)
        self.content.add_widget(self.grid)
        
        # Buttons
        bottom = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        btn_clear = Button(text="Clear Filter", background_color=[0.6, 0.1, 0.1, 1])
        btn_clear.bind(on_press=self.clear_filter)
        btn_cancel = Button(text="Cancel", background_color=[0.25, 0.3, 0.35, 1])
        btn_cancel.bind(on_press=self.dismiss)
        
        bottom.add_widget(btn_clear)
        bottom.add_widget(btn_cancel)
        self.content.add_widget(bottom)
        
        self.populate_grid()

    def populate_grid(self):
        self.grid.clear_widgets()
        month_matrix = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        for week in month_matrix:
            for day in week:
                if day == 0:
                    self.grid.add_widget(Label(text=""))
                else:
                    bg_color = [0.2, 0.5, 0.2, 1]
                    cur = self.current_date.replace(day=day)
                    if self.start_date and cur == self.start_date:
                        bg_color = [0.1, 0.4, 0.8, 1]
                    
                    btn = Button(text=str(day), background_color=bg_color)
                    btn.bind(on_press=lambda instance, d=day: self.select_date(d))
                    self.grid.add_widget(btn)

    def prev_month(self, instance):
        y, m = self.current_date.year, self.current_date.month
        m -= 1
        if m < 1:
            m = 12
            y -= 1
        self.current_date = self.current_date.replace(year=y, month=m, day=1)
        self.lbl_month.text = self.current_date.strftime("%B %Y")
        self.populate_grid()

    def next_month(self, instance):
        y, m = self.current_date.year, self.current_date.month
        m += 1
        if m > 12:
            m = 1
            y += 1
        self.current_date = self.current_date.replace(year=y, month=m, day=1)
        self.lbl_month.text = self.current_date.strftime("%B %Y")
        self.populate_grid()

    def select_date(self, day):
        selected_date = self.current_date.replace(day=day)
        if self.start_date is None:
            self.start_date = selected_date
            self.lbl_instruction.text = "Select End Date"
            self.populate_grid()
        else:
            self.end_date = selected_date
            if self.end_date < self.start_date:
                self.start_date, self.end_date = self.end_date, self.start_date
            self.callback((self.start_date, self.end_date))
            self.dismiss()
        
    def clear_filter(self, instance):
        self.callback("All")
        self.dismiss()

class CV2Colors:
    YELLOW = (0, 255, 255)
    GREEN = (0, 255, 0)
    RED = (0, 0, 255)

class DuctbotUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.lane_enabled = False
        self.is_recording = False
        self.is_recording_paused = False
        self.video_writer = None
        self.is_paused = False
        self.playback_mode = False
        self.is_live_paused = False
        self.current_camera = "F"
        
        self.video_dir = "videos"
        if not os.path.exists(self.video_dir):
            os.makedirs(self.video_dir)
            
        self.db_dir = "database"
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        # Move existing database to the new folder if it exists in the root
        if os.path.exists('recordings.db') and not os.path.exists(os.path.join(self.db_dir, 'recordings.db')):
            try:
                import shutil
                shutil.move('recordings.db', os.path.join(self.db_dir, 'recordings.db'))
                print("Moved recordings.db to database folder.")
            except Exception as e:
                print(f"Failed to move database: {e}")
                
        self.db_conn = sqlite3.connect(os.path.join(self.db_dir, 'recordings.db'))
        self.setup_database()
        
        self.recordings = self.load_recordings()
        
        # Mock sensor lock and data for the lane guides
        self.sensor_lock = threading.Lock()
        self.sensor_data = {"TOF_L": 100, "TOF_R": 100}
        
        # --- Top Bar (Header) - Spans full width ---
        self.top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', padding=[20, 0, 20, 0])
        with self.top_bar.canvas.before:
            Color(0.15, 0.15, 0.15, 1) # Dark background
            self.top_bar.bg_rect = Rectangle(size=self.top_bar.size, pos=self.top_bar.pos)
        def update_top_bg(instance, value):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        self.top_bar.bind(pos=update_top_bg, size=update_top_bg)
        
        # We need a spacer and center title
        self.top_bar.add_widget(Widget(size_hint_x=0.2)) # spacer for centering
        self.top_bar.add_widget(Label(text="ROBOSERV 4i   DUCTBOT", bold=True, halign='center', size_hint_x=0.6))
        
        # Add a right spacer to balance the layout since system ready is removed
        self.top_bar.add_widget(Widget(size_hint_x=0.2))
        
        self.add_widget(self.top_bar)
        
        # --- Main Body (Horizontal layout for left/right split) ---
        self.main_body = BoxLayout(orientation='horizontal')
        self.add_widget(self.main_body)
        
        # Left main area (Video/List + Bottom controls)
        self.left_panel = BoxLayout(orientation='vertical', size_hint_x=0.84)
        self.main_body.add_widget(self.left_panel)
        
        # Display area (Can hold either Video or List)
        self.display_area = BoxLayout(orientation='vertical')
        self.left_panel.add_widget(self.display_area)
        
        # Video feed area
        self.image = Image(allow_stretch=True, keep_ratio=False)
        self.display_area.add_widget(self.image)
        
        # Playback list area (hidden by default)
        self.list_view = ScrollView(size_hint=(1, 1))
        
        # Add white background to the scroll view
        with self.list_view.canvas.before:
            Color(1, 1, 1, 1)
            self.list_view.lv_bg = Rectangle(size=self.list_view.size, pos=self.list_view.pos)
        def update_lv_bg(instance, value):
            instance.lv_bg.pos = instance.pos
            instance.lv_bg.size = instance.size
        self.list_view.bind(pos=update_lv_bg, size=update_lv_bg)
        
        self.list_layout = GridLayout(cols=1, spacing=2, padding=10, size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.list_view.add_widget(self.list_layout)
        
        # Control panel at bottom of video
        bottom_callbacks = {
            'shutdown': lambda x: self.shutdown_system(),
            'toggle_live': self.toggle_live_mode,
            'play_pause': self.play_pause,
            'export': lambda x: self.open_export_manager()
        }
        self.control_bar = BottomControlBar(bottom_callbacks)
        self.left_panel.add_widget(self.control_bar)
        
        # Right side panel
        right_callbacks = {
            'stop': lambda x: self.stop_video(),
            'toggle_lane': self.toggle_lane,
            'flip': lambda x: self.flip_camera()
        }
        self.right_panel = RightControlPanel(right_callbacks)
        self.main_body.add_widget(self.right_panel)
        
        # Update frame periodically
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def setup_database(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recordings (
                serial INTEGER PRIMARY KEY AUTOINCREMENT,
                client TEXT,
                area TEXT,
                side TEXT,
                filename TEXT
            )
        ''')
        try:
            cursor.execute("ALTER TABLE recordings ADD COLUMN condition TEXT")
        except sqlite3.OperationalError:
            pass # column exists
            
        try:
            cursor.execute("ALTER TABLE recordings ADD COLUMN camera TEXT")
        except sqlite3.OperationalError:
            pass # column exists
            
        self.db_conn.commit()
        
        # Migrate old JSON data if exists
        if os.path.exists('recordings.json'):
            try:
                with open('recordings.json', 'r') as f:
                    old_data = json.load(f)
                
                for rec in old_data:
                    cursor.execute(
                        "INSERT INTO recordings (client, area, side, filename) VALUES (?, ?, ?, ?)",
                        (rec.get('client', ''), rec.get('area', ''), rec.get('side', ''), rec.get('filename', ''))
                    )
                self.db_conn.commit()
                os.rename('recordings.json', 'recordings.json.bak')
                print("Migrated recordings.json to SQLite database.")
            except Exception as e:
                print(f"Error migrating JSON to SQL: {e}")

    def load_recordings(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT serial, client, area, side, filename, condition, camera FROM recordings ORDER BY serial ASC")
        rows = cursor.fetchall()
        recordings = []
        for row in rows:
            recordings.append({
                "serial": row[0],
                "client": row[1],
                "area": row[2],
                "side": row[3],
                "filename": row[4],
                "condition": row[5] if row[5] else "N/A",
                "camera": row[6] if row[6] else "N/A"
            })
        return recordings

    def shutdown_system(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='Are you sure you want to shutdown?'))
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height='40dp')
        
        btn_yes = Button(text='Yes', background_color=[0.6, 0.1, 0.1, 1])
        btn_no = Button(text='No', background_color=[0.25, 0.3, 0.35, 1])
        
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Confirm Shutdown', content=content, size_hint=(0.5, 0.3), auto_dismiss=False)
        
        btn_yes.bind(on_press=lambda *args: self.confirm_shutdown(popup))
        btn_no.bind(on_press=popup.dismiss)
        
        popup.open()

    def confirm_shutdown(self, popup):
        popup.dismiss()
        print("Shutting down system...")
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
        App.get_running_app().stop()

    def toggle_live_mode(self, toggle_btn):
        if self.capture:
            self.capture.release()
            
        if toggle_btn.state == 'down':
            # Enter Playback Mode
            self.playback_mode = True
            
            # Show export button in playback mode
            if self.control_bar.btn_export not in self.control_bar.children:
                self.control_bar.add_widget(self.control_bar.btn_export)
            # Hide right panel and info panel for full width metadata table
            if self.right_panel in self.main_body.children:
                self.main_body.remove_widget(self.right_panel)
            if hasattr(self, 'playback_info_panel') and self.playback_info_panel in self.main_body.children:
                self.main_body.remove_widget(self.playback_info_panel)
            self.left_panel.size_hint_x = 1.0
            
            toggle_btn.text = 'Live Mode'
            self.control_bar.btn_play.text = 'Start/Pause'
            if self.is_recording:
                self.stop_recording()
            
            # Show list, hide video
            self.display_area.clear_widgets()
            self.display_area.add_widget(self.list_view)
            self.populate_playback_list()
        else:
            # Enter Live Mode
            self.playback_mode = False
            self.is_live_paused = False
            if hasattr(self, 'right_panel') and hasattr(self.right_panel, 'btn_stop'):
                self.right_panel.btn_stop.text = 'Stop'
                self.right_panel.btn_stop.background_color = [0.6, 0.1, 0.1, 1]
            
            # Hide export button in live mode
            if self.control_bar.btn_export in self.control_bar.children:
                self.control_bar.remove_widget(self.control_bar.btn_export)
            toggle_btn.text = 'Playback'
            self.control_bar.btn_play.text = 'Start Recording'
            
            # Restore right panel
            if self.right_panel not in self.main_body.children:
                self.main_body.add_widget(self.right_panel)
            if hasattr(self, 'playback_info_panel') and self.playback_info_panel in self.main_body.children:
                self.main_body.remove_widget(self.playback_info_panel)
            self.left_panel.size_hint_x = 0.84
            
            # Show video, hide list
            self.display_area.clear_widgets()
            self.display_area.add_widget(self.image)
            
            self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            Clock.unschedule(self.update_frame)
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def populate_playback_list(self):
        self.list_layout.clear_widgets()
        
        # Header Row
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=5)
        with header.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            header.bg_rect = Rectangle(size=header.size, pos=header.pos)
        def update_header_bg(instance, value):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        header.bind(pos=update_header_bg, size=update_header_bg)
        
        headers = [("Date/Time", 0.15), ("Client", 0.2), ("Area", 0.15), 
                   ("Side", 0.15), ("Cond", 0.1), ("Cam", 0.1), ("Action", 0.15)]
        for text, width in headers:
            header.add_widget(Label(text=text, size_hint_x=width, bold=True, color=(0, 0, 0, 1)))
        self.list_layout.add_widget(header)
        
        if not self.recordings:
            self.list_layout.add_widget(Label(text="No recordings found.", size_hint_y=None, height=40, color=(0, 0, 0, 1)))
            return
            
        for rec in reversed(self.recordings):
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=5)
            
            with row.canvas.after:
                Color(0.9, 0.9, 0.9, 1)
                row.border_rect = Rectangle(size=(row.width, 1), pos=row.pos)
            def update_row_border(instance, value):
                instance.border_rect.pos = instance.pos
                instance.border_rect.size = (instance.width, 1)
            row.bind(pos=update_row_border, size=update_row_border)
            
            fname = os.path.basename(rec['filename'])
            try:
                ts_str = fname.replace('video_', '').split('.')[0]
                dt_str = time.strftime('%d/%m/%y\n%H:%M', time.localtime(int(ts_str)))
            except:
                dt_str = "Unknown"
                
            row.add_widget(Label(text=dt_str, size_hint_x=0.15, color=(0, 0, 0, 1)))
            row.add_widget(Label(text=rec['client'], size_hint_x=0.2, color=(0, 0, 0, 1)))
            row.add_widget(Label(text=rec['area'], size_hint_x=0.15, color=(0, 0, 0, 1)))
            row.add_widget(Label(text=rec['side'], size_hint_x=0.15, color=(0, 0, 0, 1)))
            row.add_widget(Label(text=rec.get('condition', 'N/A'), size_hint_x=0.1, color=(0, 0, 0, 1)))
            row.add_widget(Label(text=rec.get('camera', 'N/A'), size_hint_x=0.1, color=(0, 0, 0, 1)))
            
            # Wrap play button in a mini boxlayout to give it some padding so it doesn't touch the borders
            btn_box = BoxLayout(size_hint_x=0.15, padding=[5, 5, 5, 5])
            btn_play = Button(text='Play', background_color=[0.2, 0.5, 0.2, 1], color=(1, 1, 1, 1))
            btn_play.bind(on_press=lambda instance, r=rec: self.start_playback_video(r))
            btn_box.add_widget(btn_play)
            
            row.add_widget(btn_box)
            self.list_layout.add_widget(row)

    def start_playback_video(self, rec):
        filename = rec['filename']
        self.display_area.clear_widgets()
        self.display_area.add_widget(self.image)
        if self.capture:
            self.capture.release()
        self.capture = cv2.VideoCapture(filename)
        self.is_paused = False
        
        # Adjust playback speed based on video FPS
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 20.0
            
        Clock.unschedule(self.update_frame)
        Clock.schedule_interval(self.update_frame, 1.0 / fps)
        
        # Remove normal right panel if present
        if self.right_panel in self.main_body.children:
            self.main_body.remove_widget(self.right_panel)
            
        # Show playback info panel
        if hasattr(self, 'playback_info_panel') and self.playback_info_panel in self.main_body.children:
            self.main_body.remove_widget(self.playback_info_panel)
            
        callbacks = {'stop': lambda x: self.stop_video()}
        self.playback_info_panel = PlaybackInfoPanel(callbacks, rec)
        self.main_body.add_widget(self.playback_info_panel)
        self.left_panel.size_hint_x = 0.84

    def play_pause(self, instance):
        if not self.playback_mode:
            # Live Mode -> Recording Control
            if not self.is_recording:
                self.open_recording_form()
            else:
                self.is_recording_paused = not self.is_recording_paused
                if self.is_recording_paused:
                    self.control_bar.btn_play.text = 'Resume Recording'
                else:
                    self.control_bar.btn_play.text = 'Pause Recording'
        else:
            # Playback Mode -> Play/Pause video
            self.is_paused = not self.is_paused

    def open_recording_form(self):
        # Create popup content
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Upper right cross button
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
        lbl_title = Label(text='Enter Recording Details:', size_hint_x=0.9)
        lbl_title.bind(size=lbl_title.setter('text_size'))
        top_bar.add_widget(lbl_title)
        self.rec_close_btn = Button(text="X", size_hint_x=0.1, background_color=[0.6, 0.1, 0.1, 1])
        top_bar.add_widget(self.rec_close_btn)
        content.add_widget(top_bar)
        
        self.inp_client = TextInput(hint_text='Client Name', multiline=False)
        self.inp_area = TextInput(hint_text='Area Name', multiline=False)
        self.inp_side = TextInput(hint_text='Side Name', multiline=False)
        
        content.add_widget(self.inp_client)
        content.add_widget(self.inp_area)
        content.add_widget(self.inp_side)
        
        # Condition row
        cond_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=5)
        cond_layout.add_widget(Label(text="Condition:"))
        self.btn_cond_before = ToggleButton(text='Before', group='condition')
        self.btn_cond_after = ToggleButton(text='After', group='condition')
        cond_layout.add_widget(self.btn_cond_before)
        cond_layout.add_widget(self.btn_cond_after)
        content.add_widget(cond_layout)
        
        # Camera row
        cam_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=5)
        cam_layout.add_widget(Label(text="Camera:"))
        self.btn_cam_front = ToggleButton(text='Front', group='camera')
        self.btn_cam_rear = ToggleButton(text='Rear', group='camera')
        cam_layout.add_widget(self.btn_cam_front)
        cam_layout.add_widget(self.btn_cam_rear)
        content.add_widget(cam_layout)
        
        submit_btn = Button(text='Submit', size_hint_y=None, height='48dp', background_color=[0.2, 0.5, 0.2, 1])
        submit_btn.bind(on_press=self.submit_recording_form)
        content.add_widget(submit_btn)
        
        self.popup = Popup(title='Start Recording', content=content, size_hint=(0.6, 0.7))
        self.rec_close_btn.bind(on_press=self.popup.dismiss)
        self.popup.open()

    def reset_submit_btn(self, instance):
        instance.text = 'Submit'
        instance.background_color = [0.2, 0.5, 0.2, 1]

    def submit_recording_form(self, instance):
        client = self.inp_client.text.strip()
        area = self.inp_area.text.strip()
        side = self.inp_side.text.strip()
        
        cond_selected = self.btn_cond_before.state == 'down' or self.btn_cond_after.state == 'down'
        cam_selected = self.btn_cam_front.state == 'down' or self.btn_cam_rear.state == 'down'
        
        if not client or not area or not side or not cond_selected or not cam_selected:
            instance.text = "Please fill all fields!"
            instance.background_color = [0.6, 0.1, 0.1, 1]
            Clock.schedule_once(lambda dt: self.reset_submit_btn(instance), 2)
            return
        
        timestamp = int(time.time())
        filename = os.path.join(self.video_dir, f"video_{timestamp}.mp4")
        
        condition = "Before" if getattr(self, 'btn_cond_before', None) and self.btn_cond_before.state == 'down' else "After"
        camera = "Front" if getattr(self, 'btn_cam_front', None) and self.btn_cam_front.state == 'down' else "Rear"
        
        cursor = self.db_conn.cursor()
        cursor.execute(
            "INSERT INTO recordings (client, area, side, condition, camera, filename) VALUES (?, ?, ?, ?, ?, ?)",
            (client, area, side, condition, camera, filename)
        )
        self.db_conn.commit()
        
        # Reload recordings to update the UI list properly
        self.recordings = self.load_recordings()
        serial_no = self.recordings[-1]['serial'] if self.recordings else 0
        
        # Save sidecar metadata JSON
        meta_filename = os.path.join(self.video_dir, f"video_{timestamp}.json")
        meta_data = {
            "serial": serial_no,
            "client": client,
            "area": area,
            "side": side,
            "condition": condition,
            "camera": camera,
            "timestamp": timestamp,
            "filename": filename
        }
        with open(meta_filename, 'w') as f:
            json.dump(meta_data, f, indent=4)
        
        self.popup.dismiss()
        
        self.start_recording(filename)

    def start_recording(self, filename):
        self.is_recording = True
        self.is_recording_paused = False
        self.is_live_paused = False
        if hasattr(self, 'right_panel') and hasattr(self.right_panel, 'btn_stop'):
            self.right_panel.btn_stop.text = 'Stop'
            self.right_panel.btn_stop.background_color = [0.6, 0.1, 0.1, 1]
        self.control_bar.btn_play.text = 'Pause Recording'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width == 0 or height == 0:
            width, height = 640, 480
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
        print(f"Recording started: {filename}")

    def stop_recording(self):
        self.is_recording = False
        self.is_recording_paused = False
        self.control_bar.btn_play.text = 'Start Recording'
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        print("Recording stopped.")

    def stop_video(self):
        if self.playback_mode:
            if self.capture:
                self.capture.release()
                self.capture = None
                # Hide right panel and info panel for the table
                if self.right_panel in self.children:
                    self.remove_widget(self.right_panel)
                if hasattr(self, 'playback_info_panel') and self.playback_info_panel in self.children:
                    self.remove_widget(self.playback_info_panel)
                self.left_panel.size_hint_x = 1.0
                
                # Go back to the video list
                self.display_area.clear_widgets()
                self.display_area.add_widget(self.list_view)
                self.populate_playback_list()
        else:
            # In Live Mode
            if self.is_recording:
                was_paused = getattr(self, 'is_recording_paused', False)
                self.is_recording_paused = True
                
                content = BoxLayout(orientation='vertical', padding=10, spacing=10)
                content.add_widget(Label(text='Are you sure you want to stop recording?'))
                
                btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height='40dp')
                
                btn_yes = Button(text='Yes', background_color=[0.6, 0.1, 0.1, 1])
                btn_no = Button(text='No', background_color=[0.25, 0.3, 0.35, 1])
                
                btn_layout.add_widget(btn_yes)
                btn_layout.add_widget(btn_no)
                content.add_widget(btn_layout)
                
                popup = Popup(title='Stop Recording', content=content, size_hint=(0.5, 0.3), auto_dismiss=False)
                
                def confirm_stop(*args):
                    popup.dismiss()
                    self.stop_recording()
                    
                def cancel_stop(*args):
                    popup.dismiss()
                    self.is_recording_paused = was_paused
                    
                btn_yes.bind(on_press=confirm_stop)
                btn_no.bind(on_press=cancel_stop)
                
                popup.open()
            else:
                self.is_live_paused = not self.is_live_paused
                if hasattr(self, 'right_panel') and hasattr(self.right_panel, 'btn_stop'):
                    if self.is_live_paused:
                        self.right_panel.btn_stop.text = 'Resume'
                        self.right_panel.btn_stop.background_color = [0.2, 0.5, 0.2, 1]
                    else:
                        self.right_panel.btn_stop.text = 'Stop'
                        self.right_panel.btn_stop.background_color = [0.6, 0.1, 0.1, 1]

    def toggle_lane(self, toggle_btn):
        self.lane_enabled = (toggle_btn.state == 'down')

    def flip_camera(self):
        if getattr(self, 'current_camera', 'F') == 'F':
            self.current_camera = 'R'
            print("Switched to Rear camera (R)")
        else:
            self.current_camera = 'F'
            print("Switched to Front camera (F)")

    def _draw_lane_guides(self, frame):
        h, w = frame.shape[:2]
        center_x = w // 2
            
        # Left converging line
        pt_top_left = (int(w * 0.35), int(h * 0.6))
        pt_bottom_left = (int(w * 0.1), h)
        cv2.line(frame, pt_top_left, pt_bottom_left, CV2Colors.YELLOW, 3)
            
        # Right converging line
        pt_top_right = (int(w * 0.65), int(h * 0.6))
        pt_bottom_right = (int(w * 0.9), h)
        cv2.line(frame, pt_top_right, pt_bottom_right, CV2Colors.YELLOW, 3)
            
        # ---------- TOF CENTER ALIGNMENT ----------
        with self.sensor_lock:
            tof_l = self.sensor_data.get("TOF_L", 0)
            tof_r = self.sensor_data.get("TOF_R", 0)

        # Calculate offset based on difference
        diff = tof_r - tof_l
        scale = 0.15
        offset = int(diff * scale)
        offset = max(-200, min(200, offset))
        center_x_dynamic = center_x + offset

        # draw moving center marker
        cv2.drawMarker(frame, (center_x_dynamic, h - 20),
                    CV2Colors.GREEN,
                    cv2.MARKER_CROSS,
                    10,
                    2)
        
        # ---------- TOF SENSOR DISPLAY REMOVED ----------

        return frame

    def update_frame(self, dt):
        if self.is_paused and self.playback_mode:
            return
            
        if not self.playback_mode and getattr(self, 'is_live_paused', False):
            return
            
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                # Save clean frame if recording in live mode
                if getattr(self, 'is_recording', False) and getattr(self, 'video_writer', None):
                    if not getattr(self, 'is_recording_paused', False):
                        self.video_writer.write(frame)

                if self.lane_enabled:
                    frame = self._draw_lane_guides(frame)
                
                # Draw camera mode indicator (F or R)
                cam_mode = getattr(self, 'current_camera', 'F')
                cv2.putText(frame, f"Cam: {cam_mode}", (20, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, CV2Colors.YELLOW, 2, cv2.LINE_AA)
                
                # Draw REC overlay if recording
                if self.is_recording:
                    if self.is_recording_paused:
                        cv2.circle(frame, (frame.shape[1] - 120, 40), 10, CV2Colors.YELLOW, -1)
                        cv2.putText(frame, "PAUSED", (frame.shape[1] - 100, 45), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, CV2Colors.YELLOW, 2, cv2.LINE_AA)
                    else:
                        # Flash logic using time.time()
                        if int(time.time() * 2) % 2 == 0:
                            cv2.circle(frame, (frame.shape[1] - 80, 40), 10, CV2Colors.RED, -1)
                            cv2.putText(frame, "REC", (frame.shape[1] - 60, 45), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, CV2Colors.RED, 2, cv2.LINE_AA)

                # We need to flip it vertically because Kivy's origin is bottom-left
                frame = cv2.flip(frame, 0)
                buffer = frame.tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
                self.image.texture = texture
            else:
                # Loop video if it ends in playback mode
                if self.playback_mode:
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def get_usb_drives(self):
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        drives = []
        for i, letter in enumerate(string.ascii_uppercase):
            if (drive_bitmask >> i) & 1:
                drives.append(f"{letter}:\\")
        usb_drives = [d for d in drives if ctypes.cdll.kernel32.GetDriveTypeW(d) == 2]
        return usb_drives

    def open_export_manager(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Upper right cross button
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
        top_bar.add_widget(Label(text="", size_hint_x=0.9)) # Empty space
        close_btn = Button(text="X", size_hint_x=0.1, background_color=[0.6, 0.1, 0.1, 1])
        top_bar.add_widget(close_btn)
        content.add_widget(top_bar)
        
        # Filter UI
        filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp', spacing=10)
        filter_layout.add_widget(Label(text="Filter by Date:", size_hint_x=0.4))
        date_btn = Button(text="All", size_hint_x=0.6, background_color=[0.25, 0.3, 0.35, 1])
        filter_layout.add_widget(date_btn)
        content.add_widget(filter_layout)
        
        # Videos List
        content.add_widget(Label(text="Select Videos to Export:", size_hint_y=None, height='30dp'))
        
        scroll = ScrollView(size_hint=(1, 1))
        self.export_grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.export_grid.bind(minimum_height=self.export_grid.setter('height'))
        
        self.export_checkboxes = {}
        
        def populate_export_list(filter_data="All"):
            self.export_grid.clear_widgets()
            self.export_checkboxes.clear()
            for rec in reversed(self.recordings):
                fname = os.path.basename(rec['filename'])
                try:
                    ts_str = fname.replace('video_', '').split('.')[0]
                    t_obj = time.localtime(int(ts_str))
                    dt_str = time.strftime('%d/%m/%y %H:%M', t_obj)
                    rec_date = date(t_obj.tm_year, t_obj.tm_mon, t_obj.tm_mday)
                except:
                    dt_str = "Unknown"
                    rec_date = None
                    
                if filter_data != "All" and rec_date:
                    start_date, end_date = filter_data
                    if not (start_date <= rec_date <= end_date):
                        continue
                    
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
                cb = CheckBox(size_hint_x=0.15)
                self.export_checkboxes[rec['filename']] = cb
                lbl_text = f"{dt_str} - {rec['client']} ({rec['area']})"
                lbl = Label(text=lbl_text, size_hint_x=0.85, halign='left')
                lbl.bind(size=lbl.setter('text_size'))
                
                row.add_widget(cb)
                row.add_widget(lbl)
                self.export_grid.add_widget(row)
                
        populate_export_list("All")
        
        def on_date_selected(selected_data):
            if selected_data == "All":
                date_btn.text = "All"
            else:
                s_str = selected_data[0].strftime("%d/%m/%y")
                e_str = selected_data[1].strftime("%d/%m/%y")
                date_btn.text = f"{s_str} - {e_str}"
            populate_export_list(selected_data)
            
        date_btn.bind(on_press=lambda x: DatePickerPopup(on_date_selected).open())
        
        scroll.add_widget(self.export_grid)
        content.add_widget(scroll)
        
        # Buttons
        btn_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        
        def select_all(instance):
            for cb in self.export_checkboxes.values():
                cb.active = True
                
        btn_sel_all = Button(text='Select All', background_color=[0.25, 0.3, 0.35, 1])
        btn_sel_all.bind(on_press=select_all)
        
        btn_export = Button(text='Export Selected', background_color=[0.2, 0.5, 0.2, 1])
        btn_export.bind(on_press=self.execute_export)
        
        btn_bar.add_widget(btn_sel_all)
        btn_bar.add_widget(btn_export)
        content.add_widget(btn_bar)
        
        self.export_popup = Popup(title='Export Manager', content=content, size_hint=(0.7, 0.8))
        close_btn.bind(on_press=self.export_popup.dismiss)
        self.export_popup.open()

    def execute_export(self, instance):
        selected_files = [f for f, cb in self.export_checkboxes.items() if cb.active]
        
        if not selected_files:
            instance.text = "None selected!"
            instance.background_color = [0.6, 0.1, 0.1, 1]
            Clock.schedule_once(lambda dt: setattr(instance, 'text', 'Export Selected'), 2)
            Clock.schedule_once(lambda dt: setattr(instance, 'background_color', [0.2, 0.5, 0.2, 1]), 2)
            return
            
        # Step 2: Select USB and Folder
        usbs = self.get_usb_drives()
        if not usbs:
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            content.add_widget(Label(text='No USB flash drives detected!'))
            btn = Button(text='Close', size_hint_y=None, height='40dp')
            content.add_widget(btn)
            popup = Popup(title='Error', content=content, size_hint=(0.4, 0.4))
            btn.bind(on_press=popup.dismiss)
            popup.open()
            return
            
        folder_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        drive_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        drive_bar.add_widget(Label(text="Select USB:", size_hint_x=0.3))
        usb_spinner = Spinner(text=usbs[0], values=usbs, size_hint_x=0.7)
        drive_bar.add_widget(usb_spinner)
        folder_content.add_widget(drive_bar)
        
        folder_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        folder_bar.add_widget(Label(text="Folder Name:", size_hint_x=0.3))
        folder_input = TextInput(text="Ductbot_Exports", multiline=False, size_hint_x=0.7)
        folder_bar.add_widget(folder_input)
        folder_content.add_widget(folder_bar)
        
        btn_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        start_btn = Button(text="Start Export", background_color=[0.2, 0.5, 0.2, 1])
        cancel_select_btn = Button(text="Cancel", background_color=[0.6, 0.1, 0.1, 1])
        btn_bar.add_widget(start_btn)
        btn_bar.add_widget(cancel_select_btn)
        folder_content.add_widget(btn_bar)
        
        folder_popup = Popup(title='Select Export Destination', content=folder_content, size_hint=(0.6, 0.4), auto_dismiss=False)
        cancel_select_btn.bind(on_press=folder_popup.dismiss)
        folder_popup.open()
            
        def on_start_export(btn):
            folder_popup.dismiss()
            target_drive = usb_spinner.text
            folder_name = folder_input.text.strip()
            if not folder_name:
                folder_name = "Ductbot_Exports"
                
            export_dir = os.path.join(target_drive, folder_name)
            start_progress_ui(export_dir)
            
        start_btn.bind(on_press=on_start_export)
            
        def start_progress_ui(export_dir):
            # Build Progress UI
            progress_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            self.progress_label = Label(text="Starting export...")
            self.progress_bar = ProgressBar(max=100, value=0)
            
            self.cancel_export = False
            def on_cancel(btn):
                self.cancel_export = True
                btn.text = "Cancelling..."
                btn.disabled = True
                
            cancel_btn = Button(text="Cancel", size_hint_y=None, height='40dp', background_color=[0.6, 0.1, 0.1, 1])
            cancel_btn.bind(on_press=on_cancel)
            
            progress_content.add_widget(self.progress_label)
            progress_content.add_widget(self.progress_bar)
            progress_content.add_widget(cancel_btn)
            
            self.progress_popup = Popup(title='Export Progress', content=progress_content, size_hint=(0.6, 0.4), auto_dismiss=False)
            self.progress_popup.open()
            
            def do_export():
                try:
                    if not os.path.exists(export_dir):
                        os.makedirs(export_dir)
                        
                    total_files = len(selected_files)
                    for i, f in enumerate(selected_files):
                        if self.cancel_export:
                            break
                            
                        basename = os.path.basename(f)
                        Clock.schedule_once(lambda dt, text=f"Exporting {i+1} of {total_files}: {basename}": setattr(self.progress_label, 'text', text), 0)
                        Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 0), 0)
                        
                        # Chunked copy of MP4
                        dst_mp4 = os.path.join(export_dir, basename)
                        total_size = os.path.getsize(f)
                        copied = 0
                        with open(f, 'rb') as fsrc, open(dst_mp4, 'wb') as fdst:
                            while True:
                                if self.cancel_export:
                                    break
                                buf = fsrc.read(1024 * 1024) # 1MB chunk
                                if not buf:
                                    break
                                fdst.write(buf)
                                copied += len(buf)
                                if total_size > 0:
                                    pct = (copied / total_size) * 100
                                    Clock.schedule_once(lambda dt, p=pct: setattr(self.progress_bar, 'value', p), 0)
                                    
                        if self.cancel_export:
                            try: os.remove(dst_mp4)
                            except: pass
                            break
                            
                        # Copy JSON
                        json_file = f.replace('.mp4', '.json')
                        if os.path.exists(json_file):
                            shutil.copy2(json_file, export_dir)
                            
                    if self.cancel_export:
                        Clock.schedule_once(lambda dt: setattr(self.progress_label, 'text', 'Export Cancelled!'), 0)
                    else:
                        Clock.schedule_once(lambda dt: setattr(self.progress_label, 'text', 'Done! Export Successful'), 0)
                        Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 100), 0)
                        
                    Clock.schedule_once(lambda dt: setattr(cancel_btn, 'disabled', True), 0)
                    
                    def close_popups(dt):
                        self.progress_popup.dismiss()
                        if not self.cancel_export:
                            self.export_popup.dismiss()
                            
                    Clock.schedule_once(close_popups, 2)
                except Exception as e:
                    print(f"Export Error: {e}")
                    Clock.schedule_once(lambda dt: setattr(self.progress_label, 'text', f'Error: {str(e)}'), 0)
                    Clock.schedule_once(lambda dt: setattr(cancel_btn, 'text', 'Close'), 0)
                    Clock.schedule_once(lambda dt: setattr(cancel_btn, 'disabled', False), 0)
                    cancel_btn.bind(on_press=self.progress_popup.dismiss)
                    
            threading.Thread(target=do_export, daemon=True).start()

class SplashLoader(FloatLayout):
    """
    Displays a full-screen logo for a specified duration before
    calling a callback to launch the main application interface.
    """
    def __init__(self, on_finish_callback, logo_path="logo.png", duration=10, **kwargs):
        super().__init__(**kwargs)
        self.on_finish_callback = on_finish_callback
        
        if not os.path.exists(logo_path):
            print(f"[WARNING] Logo not found at {logo_path}")
            
        # 1. Create and add the Logo Image widget
        self.logo_widget = Image(
            source=logo_path,
            size_hint=(None, None),
            size=Window.size,
            pos=(0, 0),
            fit_mode="contain" # Ensures the logo keeps its proportions
        )
        self.add_widget(self.logo_widget)

        # 2. Bind the window resize event so the logo scales if the window changes
        Window.bind(size=self._update_size)
        self._update_size()

        # 3. Schedule the transition to the main UI after 'duration' seconds
        Clock.schedule_once(self.finish, duration)

    def finish(self, dt=None):
        # Unbind the resize event and trigger the callback to load the main app
        Window.unbind(size=self._update_size)
        self.on_finish_callback()

    def _update_size(self, *args):
        # Keep the layout and the logo matching the Window size
        self.size = Window.size
        if hasattr(self, "logo_widget"):
            self.logo_widget.size = Window.size
            self.logo_widget.pos = (0, 0)

from kivy.lang import Builder

class DuctbotApp(App):
    def build(self):
        Builder.load_string('''
<Button>:
    font_size: '19sp'
<ToggleButton>:
    font_size: '19sp'
<Label>:
    font_size: '17sp'
<TextInput>:
    font_size: '17sp'
''')
        self.root = FloatLayout()
        splash = SplashLoader(on_finish_callback=self.load_main_app, logo_path="logo.png", duration=10)
        self.root.add_widget(splash)
        return self.root

    def load_main_app(self):
        self.root.clear_widgets()
        self.root.add_widget(DuctbotUI())

if __name__ == '__main__':
    DuctbotApp().run()

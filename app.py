from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import threading
import json
import os
import time

class CV2Colors:
    YELLOW = (0, 255, 255)
    GREEN = (0, 255, 0)
    RED = (0, 0, 255)

class DuctbotUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.lane_enabled = False
        self.is_recording = False
        self.video_writer = None
        self.is_paused = False
        self.playback_mode = False
        
        self.recordings = self.load_recordings()
        
        # Mock sensor lock and data for the lane guides
        self.sensor_lock = threading.Lock()
        self.sensor_data = {"TOF_L": 100, "TOF_R": 100}
        
        # Left main area (Video/List + Bottom controls)
        self.left_panel = BoxLayout(orientation='vertical', size_hint_x=0.85)
        self.add_widget(self.left_panel)
        
        # Display area (Can hold either Video or List)
        self.display_area = BoxLayout(orientation='vertical')
        self.left_panel.add_widget(self.display_area)
        
        # Video feed area
        self.image = Image(allow_stretch=True, keep_ratio=False)
        self.display_area.add_widget(self.image)
        
        # Playback list area (hidden by default)
        self.list_view = ScrollView(size_hint=(1, 1))
        self.list_layout = GridLayout(cols=1, spacing=10, padding=10, size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.list_view.add_widget(self.list_layout)
        
        # Control panel at bottom of video
        control_bar = BoxLayout(size_hint_y=None, height='96dp', spacing=5, padding=5)
        self.left_panel.add_widget(control_bar)
        
        # Shutdown button
        btn_shutdown = Button(text='Shutdown', background_normal='', background_color=[0.9, 0.3, 0.3, 1])
        btn_shutdown.bind(on_press=lambda x: self.shutdown_system())
        control_bar.add_widget(btn_shutdown)
        
        # Live/Playback toggle
        self.btn_live = ToggleButton(text='Playback', state='normal', background_normal='', background_color=[0.2, 0.6, 0.8, 1])
        self.btn_live.bind(on_press=self.toggle_live_mode)
        control_bar.add_widget(self.btn_live)
        
        # Start/Pause button
        self.btn_play = Button(text='Start Recording', background_normal='', background_color=[0.3, 0.8, 0.3, 1])
        self.btn_play.bind(on_press=self.play_pause)
        control_bar.add_widget(self.btn_play)
        
        # Right side panel
        self.right_panel = BoxLayout(orientation='vertical', size_hint_x=0.15, spacing=5, padding=5)
        self.add_widget(self.right_panel)
        
        # Stop button
        btn_stop = Button(text='Stop', background_normal='', background_color=[0.8, 0.2, 0.2, 1])
        btn_stop.bind(on_press=lambda x: self.stop_video())
        self.right_panel.add_widget(btn_stop)
        
        # Lane button
        btn_lane = ToggleButton(text='Lane', background_normal='', background_color=[0.2, 0.4, 0.8, 1])
        btn_lane.bind(on_press=self.toggle_lane)
        self.right_panel.add_widget(btn_lane)
        
        # Flip camera button
        btn_flip = Button(text='Flip Camera', background_normal='', background_color=[0.4, 0.4, 0.6, 1])
        btn_flip.bind(on_press=lambda x: self.flip_camera())
        self.right_panel.add_widget(btn_flip)
        
        # Update frame periodically
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def load_recordings(self):
        if os.path.exists('recordings.json'):
            try:
                with open('recordings.json', 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_recordings(self):
        with open('recordings.json', 'w') as f:
            json.dump(self.recordings, f, indent=4)

    def shutdown_system(self):
        print("Shutting down system...")
        App.get_running_app().stop()

    def toggle_live_mode(self, toggle_btn):
        if self.capture:
            self.capture.release()
            
        if toggle_btn.state == 'down':
            # Enter Playback Mode
            self.playback_mode = True
            toggle_btn.text = 'Live Mode'
            self.btn_play.text = 'Start/Pause'
            if self.is_recording:
                self.stop_recording()
            
            # Show list, hide video
            self.display_area.clear_widgets()
            self.display_area.add_widget(self.list_view)
            self.populate_playback_list()
        else:
            # Enter Live Mode
            self.playback_mode = False
            toggle_btn.text = 'Playback'
            self.btn_play.text = 'Start Recording'
            
            # Show video, hide list
            self.display_area.clear_widgets()
            self.display_area.add_widget(self.image)
            
            self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    def populate_playback_list(self):
        self.list_layout.clear_widgets()
        if not self.recordings:
            self.list_layout.add_widget(Label(text="No recordings found.", size_hint_y=None, height=40))
            return
            
        for rec in reversed(self.recordings):
            btn_text = f"Sr No: {rec['serial']} | Client: {rec['client']} | Area: {rec['area']} | Side: {rec['side']}"
            btn = Button(text=btn_text, size_hint_y=None, height='60dp', background_color=[0.3, 0.3, 0.4, 1])
            # Default arg allows late binding in lambda
            btn.bind(on_press=lambda instance, f=rec['filename']: self.start_playback_video(f))
            self.list_layout.add_widget(btn)

    def start_playback_video(self, filename):
        self.display_area.clear_widgets()
        self.display_area.add_widget(self.image)
        if self.capture:
            self.capture.release()
        self.capture = cv2.VideoCapture(filename)
        self.is_paused = False

    def play_pause(self, instance):
        if not self.playback_mode:
            # Live Mode -> Recording Control
            if not self.is_recording:
                self.open_recording_form()
            else:
                self.stop_recording()
        else:
            # Playback Mode -> Play/Pause video
            self.is_paused = not self.is_paused

    def open_recording_form(self):
        # Create popup content
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        self.inp_client = TextInput(hint_text='Client Name', multiline=False)
        self.inp_area = TextInput(hint_text='Area Name', multiline=False)
        self.inp_side = TextInput(hint_text='Side Name', multiline=False)
        
        content.add_widget(Label(text='Enter Recording Details:', size_hint_y=None, height='30dp'))
        content.add_widget(self.inp_client)
        content.add_widget(self.inp_area)
        content.add_widget(self.inp_side)
        
        submit_btn = Button(text='Submit', size_hint_y=None, height='48dp', background_color=[0.2, 0.8, 0.2, 1])
        submit_btn.bind(on_press=self.submit_recording_form)
        content.add_widget(submit_btn)
        
        self.popup = Popup(title='Start Recording', content=content, size_hint=(0.5, 0.5))
        self.popup.open()

    def submit_recording_form(self, instance):
        client = self.inp_client.text.strip() or "Unknown"
        area = self.inp_area.text.strip() or "Unknown"
        side = self.inp_side.text.strip() or "Unknown"
        
        serial_no = len(self.recordings) + 1
        timestamp = int(time.time())
        filename = f"video_{timestamp}.mp4"
        
        self.recordings.append({
            "serial": serial_no,
            "client": client,
            "area": area,
            "side": side,
            "filename": filename
        })
        self.save_recordings()
        self.popup.dismiss()
        
        self.start_recording(filename)

    def start_recording(self, filename):
        self.is_recording = True
        self.btn_play.text = 'Stop Recording'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width == 0 or height == 0:
            width, height = 640, 480
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
        print(f"Recording started: {filename}")

    def stop_recording(self):
        self.is_recording = False
        self.btn_play.text = 'Start Recording'
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        print("Recording stopped.")

    def stop_video(self):
        if self.capture:
            self.capture.release()
            self.capture = None
            if self.playback_mode:
                # Go back to the video list
                self.display_area.clear_widgets()
                self.display_area.add_widget(self.list_view)
                self.populate_playback_list()

    def toggle_lane(self, toggle_btn):
        self.lane_enabled = (toggle_btn.state == 'down')

    def flip_camera(self):
        print("Flipping camera...")

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
        
        # ---------- TOF SENSOR DISPLAY ----------
        with self.sensor_lock:
            tof_l = self.sensor_data.get("TOF_L", 0)
            tof_r = self.sensor_data.get("TOF_R", 0)

        # Left TOF
        try:
            if isinstance(tof_l, (int, float)) and int(tof_l) == -2:
                left_text = "L: Too far"
            elif isinstance(tof_l, (int, float)) and int(tof_l) == -1:
                left_text = "L: Too close"
            else:
                left_text = f"L: {tof_l:.0f} mm"
        except Exception:
            left_text = "L: --"

        cv2.putText(
            frame, left_text, (10, h - 120),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 60, 0), 1, cv2.LINE_AA
        )

        # Right TOF
        try:
            if isinstance(tof_r, (int, float)) and int(tof_r) == -2:
                right_text = "R: Too far"
            elif isinstance(tof_r, (int, float)) and int(tof_r) == -1:
                right_text = "R: Too close"
            else:
                right_text = f"R: {tof_r:.0f} mm"
        except Exception:
            right_text = "R: --"

        cv2.putText(
            frame, right_text, (w - 100, h - 120),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 60, 0), 1, cv2.LINE_AA
        )
            
        return frame

    def update_frame(self, dt):
        if self.is_paused and self.playback_mode:
            return
            
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                # Save clean frame if recording in live mode
                if getattr(self, 'is_recording', False) and getattr(self, 'video_writer', None):
                    self.video_writer.write(frame)

                if self.lane_enabled:
                    frame = self._draw_lane_guides(frame)
                
                # Draw REC overlay if recording
                if self.is_recording:
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

class DuctbotApp(App):
    def build(self):
        return DuctbotUI()

if __name__ == '__main__':
    DuctbotApp().run()

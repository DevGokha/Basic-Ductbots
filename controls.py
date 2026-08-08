from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label

class BottomControlBar(BoxLayout):
    def __init__(self, callbacks, **kwargs):
        super().__init__(size_hint_y=None, height='96dp', spacing=5, padding=5, **kwargs)
        
        # Shutdown button
        self.btn_shutdown = Button(text='Shutdown', background_normal='', background_color=[0.6, 0.1, 0.1, 1])
        self.btn_shutdown.bind(on_press=callbacks.get('shutdown', lambda x: None))
        self.add_widget(self.btn_shutdown)
        
        # Live/Playback toggle
        self.btn_live = ToggleButton(text='Playback', state='normal', background_normal='', background_color=[0.25, 0.3, 0.35, 1])
        self.btn_live.bind(on_press=callbacks.get('toggle_live', lambda x: None))
        self.add_widget(self.btn_live)
        
        # Start/Pause button
        self.btn_play = Button(text='Start Recording', background_normal='', background_color=[0.2, 0.5, 0.2, 1])
        self.btn_play.bind(on_press=callbacks.get('play_pause', lambda x: None))
        self.add_widget(self.btn_play)
        
        # Export button (created but not added to layout initially because we start in Live Mode)
        self.btn_export = Button(text='Export', background_normal='', background_color=[0.7, 0.4, 0.1, 1])
        self.btn_export.bind(on_press=callbacks.get('export', lambda x: None))

class RightControlPanel(BoxLayout):
    def __init__(self, callbacks, **kwargs):
        super().__init__(orientation='vertical', size_hint_x=0.16, spacing=5, padding=5, **kwargs)
        
        # Flip camera button (equal size)
        self.btn_flip = Button(text='Flip Camera', background_normal='', background_color=[0.25, 0.3, 0.35, 1])
        self.btn_flip.bind(on_press=callbacks.get('flip', lambda x: None))
        self.add_widget(self.btn_flip)
        
        # Lane button
        self.btn_lane = ToggleButton(text='Lane', background_normal='', background_color=[0.25, 0.3, 0.35, 1])
        self.btn_lane.bind(on_press=callbacks.get('toggle_lane', lambda x: None))
        self.add_widget(self.btn_lane)
        
        # Stop button
        self.btn_stop = Button(text='Stop', background_normal='', background_color=[0.6, 0.1, 0.1, 1])
        self.btn_stop.bind(on_press=callbacks.get('stop', lambda x: None))
        self.add_widget(self.btn_stop)

class PlaybackInfoPanel(BoxLayout):
    def __init__(self, callbacks, rec_data, **kwargs):
        super().__init__(orientation='vertical', size_hint_x=0.16, spacing=5, padding=5, **kwargs)
        
        # Stop button
        self.btn_stop = Button(text='Stop / Back', size_hint_y=0.2, background_normal='', background_color=[0.6, 0.1, 0.1, 1])
        self.btn_stop.bind(on_press=callbacks.get('stop', lambda x: None))
        self.add_widget(self.btn_stop)
        
        # Metadata labels
        self.add_widget(Label(text="Video Details", bold=True, size_hint_y=0.1))
        
        import os, time
        fname = os.path.basename(rec_data.get('filename', ''))
        try:
            ts_str = fname.replace('video_', '').split('.')[0]
            dt_str = time.strftime('%d/%m/%y %H:%M', time.localtime(int(ts_str)))
        except:
            dt_str = "Unknown"

        details = [
            f"Date:\n{dt_str}",
            f"Client:\n{rec_data.get('client', '')}",
            f"Area:\n{rec_data.get('area', '')}",
            f"Side:\n{rec_data.get('side', '')}",
            f"Cond:\n{rec_data.get('condition', '')}",
            f"Cam:\n{rec_data.get('camera', '')}"
        ]
        
        for d in details:
            lbl = Label(text=d, size_hint_y=0.15, halign='center', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)
        for d in details:
            lbl = Label(text=d, size_hint_y=0.15, halign='center', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)

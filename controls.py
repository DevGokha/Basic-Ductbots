from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.factory import Factory

KV = '''
<CyberButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 1, 1, 1
    font_size: '50sp'
    font_name: 'Roboto' if 'Roboto' in self.font_name else 'sans-serif'
    bold: True
    canvas.before:
        Color:
            rgba: (0, 0.83, 1, 0.8) if self.state == 'down' else (0.1, 0.1, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: (0, 0.83, 1, 1) if self.state == 'normal' else (1, 1, 1, 1)
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 20]
            width: 1.2

<CyberToggleButton@ToggleButton>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 1, 1, 1
    font_size: '50sp'
    bold: True
    canvas.before:
        Color:
            rgba: (0, 0.83, 1, 0.6) if self.state == 'down' else (0.1, 0.1, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: 0, 0.83, 1, 1
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 20]
            width: 1.2

<RedButton@CyberButton>:
    canvas.before:
        Color:
            rgba: (1, 0.2, 0.2, 0.8) if self.state == 'down' else (0.4, 0.05, 0.05, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: (1, 0.2, 0.2, 1) if self.state == 'normal' else (1, 1, 1, 1)
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 20]
            width: 1.2

<GreenButton@CyberButton>:
    canvas.before:
        Color:
            rgba: (0.2, 0.6, 0.2, 0.8) if self.state == 'down' else (0.1, 0.4, 0.1, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: (0.2, 0.8, 0.2, 1) if self.state == 'normal' else (1, 1, 1, 1)
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 20]
            width: 1.2
'''
Builder.load_string(KV)

class BottomControlBar(BoxLayout):
    def __init__(self, callbacks, **kwargs):
        super().__init__(size_hint_y=None, height='82dp', spacing=5, padding=5, **kwargs)

        from kivy.uix.image import Image
        from kivy.metrics import dp

        def add_icon(btn, source):
            icon = Image(source=source, size_hint=(None, None), size=(dp(24), dp(24)))
            def update_icon(instance, value=None):
                icon.center_y = instance.center_y
                # Position icon 10dp to the left of the text
                # instance.texture_size[0] is the width of the text
                text_width = instance.texture_size[0]
                icon.right = instance.center_x - (text_width / 2) - dp(10)
            btn.bind(pos=update_icon, size=update_icon, texture_size=update_icon)
            btn.add_widget(icon)
        
        # Live/Playback toggle
        self.btn_live = Factory.CyberToggleButton(text='Playback', state='normal')
        self.btn_live.bind(on_press=callbacks.get('toggle_live', lambda x: None))
        add_icon(self.btn_live, 'icons/playback_icon.png')
        self.add_widget(self.btn_live)
        
        # Start/Pause button
        self.btn_play = Factory.GreenButton(text='Start Recording')
        self.btn_play.bind(on_press=callbacks.get('play_pause', lambda x: None))
        add_icon(self.btn_play, 'icons/record_icon.png')
        self.add_widget(self.btn_play)
        
        # Export button (created but not added to layout initially because we start in Live Mode)
        self.btn_export = Factory.CyberButton(text='Export')
        self.btn_export.bind(on_press=callbacks.get('export', lambda x: None))
        add_icon(self.btn_export, 'icons/export_icon.png')
        
        # Flip camera button
        self.btn_flip = Factory.CyberButton(text='Flip Camera')
        self.btn_flip.bind(on_press=callbacks.get('flip', lambda x: None))
        add_icon(self.btn_flip, 'icons/flip_icon.png')
        self.add_widget(self.btn_flip)
        
        # Lane button
        self.btn_lane = Factory.CyberToggleButton(text='Lane')
        self.btn_lane.bind(on_press=callbacks.get('toggle_lane', lambda x: None))
        add_icon(self.btn_lane, 'icons/lane_icon.png')
        self.add_widget(self.btn_lane)



class PlaybackInfoPanel(BoxLayout):
    def __init__(self, callbacks, rec_data, **kwargs):
        super().__init__(orientation='vertical', size_hint_x=0.16, spacing=5, padding=5, **kwargs)
        
        from kivy.factory import Factory
        from kivy.uix.image import Image
        from kivy.metrics import dp

        # Stop button
        self.btn_stop = Factory.RedButton(text='Stop / Back', size_hint_y=0.15)
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
            dt_str,
            rec_data.get('client', ''),
            rec_data.get('area', ''),
            rec_data.get('side', ''),
            rec_data.get('condition', ''),
            rec_data.get('camera', '')
        ]
        
        for d in details:
            lbl = Label(text=d, size_hint_y=0.15, halign='center', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)

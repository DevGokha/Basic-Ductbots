from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty

# Set the background color (Deep Navy)
Window.clearcolor = (0.039, 0.055, 0.102, 1)

KV = '''
#:import utils kivy.utils

<GlassCard@BoxLayout>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 0.05
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
        Color:
            rgba: 0, 0.83, 1, 0.3  # Cyan subtle border
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 15]
            width: 1

<CyberButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 1, 1, 1
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

<PulseButton@CyberButton>:
    canvas.before:
        Color:
            rgba: (0.48, 0.18, 0.99, 0.8) if self.state == 'down' else (0.2, 0.1, 0.4, 1) # Violet tint
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: 0.48, 0.18, 0.99, 1
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 20]
            width: 1.2

<VideoArea@Widget>:
    canvas.before:
        Color:
            rgba: 0.05, 0.05, 0.08, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
        Color:
            rgba: 1, 1, 1, 0.1
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 10]
            width: 1

<CyberTextInput@TextInput>:
    background_color: 0, 0, 0, 0
    foreground_color: 1, 1, 1, 1
    cursor_color: 0, 0.83, 1, 1
    font_name: 'Roboto' if 'Roboto' in self.font_name else 'sans-serif'
    multiline: False
    padding_y: [self.height / 2.0 - (self.line_height / 2.0) * len(self._lines), 0]
    canvas.before:
        Color:
            rgba: 1, 1, 1, 0.05
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
        Color:
            rgba: 0, 0.83, 1, 0.5
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 10]
            width: 1

<CyberToggleButton@ToggleButton>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 1, 1, 1
    bold: True
    canvas.before:
        Color:
            rgba: (0, 0.83, 1, 0.6) if self.state == 'down' else (0.1, 0.1, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
        Color:
            rgba: 0, 0.83, 1, 1
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 10]
            width: 1

<MainDashboardScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)

        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Label:
                text: 'ROBOSERV 4i DUCTBOT'
                color: utils.get_color_from_hex('#00d4ff')
                font_size: '24sp'
                bold: True
                halign: 'left'
                valign: 'middle'
                text_size: self.size
            BoxLayout:
                size_hint_x: None
                width: dp(80)
                spacing: dp(5)
                Widget:
                    size_hint: None, None
                    size: dp(12), dp(12)
                    pos_hint: {'center_y': 0.5}
                    canvas.before:
                        Color:
                            rgba: 0, 1, 0, 1
                        Ellipse:
                            pos: self.pos
                            size: self.size
                Label:
                    text: 'Live'
                    color: 0, 1, 0, 1
                    bold: True

        # Video Area
        FloatLayout:
            VideoArea:
                pos_hint: {'x': 0, 'y': 0}
                size_hint: 1, 1
            # Cam Pill
            BoxLayout:
                size_hint: None, None
                size: dp(60), dp(30)
                pos_hint: {'x': 0.02, 'top': 0.95}
                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 0.7
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [15]
                Label:
                    text: 'Cam: F'
                    color: 1, 1, 1, 1
                    bold: True
                    font_size: '12sp'

        # Details Glass Card
        GlassCard:
            size_hint_y: None
            height: dp(60)
            padding: dp(10)
            spacing: dp(15)
            Label:
                text: '08/08/26\\n12:01'
                halign: 'center'
                font_size: '12sp'
            Label:
                text: 'Cond: Before'
                font_size: '14sp'
            Label:
                text: 'Cam: Front'
                font_size: '14sp'
            Label:
                text: 'Client: PPPPP'
                font_size: '14sp'
            Label:
                text: 'Area: PPPPP'
                font_size: '14sp'
            Label:
                text: 'Side: PPPPP'
                font_size: '14sp'

        # Action Buttons
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(15)
            CyberButton:
                text: 'Stop / Back'
            CyberButton:
                text: 'Playback'
                on_press: root.manager.current = 'playback'
            PulseButton:
                text: 'Start Recording'
                on_press: app.open_recording_popup()
            RedButton:
                text: 'Shutdown'
                on_press: app.open_shutdown_popup()
            CyberButton:
                text: 'Live Mode'
            CyberButton:
                text: 'Export'
                on_press: root.manager.current = 'export'

        # Bottom Stats Bar
        BoxLayout:
            size_hint_y: None
            height: dp(20)
            Label:
                text: 'Total Recordings: 42   |   Last Export: 08/07/26   |   Storage: 64% Free'
                color: 0.7, 0.7, 0.7, 1
                font_size: '12sp'
                halign: 'center'
                text_size: self.size
                valign: 'middle'


<StartRecordingPopup>:
    title: 'Start Recording'
    size_hint: 0.6, 0.7
    title_color: utils.get_color_from_hex('#00d4ff')
    separator_color: utils.get_color_from_hex('#00d4ff')
    background: ''
    background_color: 0.05, 0.05, 0.08, 0.95
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(10)
        
        GridLayout:
            cols: 2
            spacing: dp(10)
            row_force_default: True
            row_default_height: dp(40)
            
            Label:
                text: 'Client Name:'
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            CyberTextInput:
                id: inp_client
            
            Label:
                text: 'Area Name:'
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            CyberTextInput:
                id: inp_area
                
            Label:
                text: 'Side Name:'
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            CyberTextInput:
                id: inp_side
                
            Label:
                text: 'Condition:'
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            BoxLayout:
                spacing: dp(5)
                CyberToggleButton:
                    text: 'Before'
                    group: 'condition'
                    state: 'down'
                CyberToggleButton:
                    text: 'After'
                    group: 'condition'
            
            Label:
                text: 'Camera:'
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            BoxLayout:
                spacing: dp(5)
                CyberToggleButton:
                    text: 'Front'
                    group: 'camera'
                    state: 'down'
                CyberToggleButton:
                    text: 'Rear'
                    group: 'camera'
                    
        Widget:
            # Spacer
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            CyberButton:
                text: 'Cancel'
                on_press: root.dismiss()
            PulseButton:
                text: 'Submit'
                on_press: root.dismiss()


<ShutdownPopup>:
    title: 'Confirm Shutdown'
    size_hint: 0.4, 0.3
    title_color: utils.get_color_from_hex('#00d4ff')
    separator_color: utils.get_color_from_hex('#00d4ff')
    background: ''
    background_color: 0.05, 0.05, 0.08, 0.95
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(15)
        padding: dp(10)
        Label:
            text: 'Are you sure you want to shutdown?'
            halign: 'center'
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(15)
            CyberButton:
                text: 'No'
                on_press: root.dismiss()
            RedButton:
                text: 'Yes'
                on_press: app.stop()


<ExportManagerScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Label:
                text: 'Export Manager'
                color: utils.get_color_from_hex('#00d4ff')
                font_size: '24sp'
                bold: True
                halign: 'left'
                valign: 'middle'
                text_size: self.size
            
            CyberButton:
                size_hint_x: None
                width: dp(120)
                text: 'Date Filter'
                on_press: app.open_date_popup()
                
        # List Header
        GlassCard:
            size_hint_y: None
            height: dp(40)
            padding: dp(10)
            Label:
                text: 'Recordings List'
                bold: True
                halign: 'left'
                text_size: self.size
                valign: 'middle'
                
        # Scrollable List
        ScrollView:
            GlassCard:
                id: export_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10)
                spacing: dp(5)
                # Items added dynamically via python
                
        # Bottom Controls
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(15)
            BoxLayout:
                size_hint_x: None
                width: dp(120)
                CheckBox:
                    color: 0, 0.83, 1, 1
                Label:
                    text: 'Select All'
            Widget:
            CyberButton:
                text: 'Back'
                size_hint_x: 0.3
                on_press: root.manager.current = 'main'
            PulseButton:
                text: 'Export Selected'
                size_hint_x: 0.5


<ExportListItem>:
    size_hint_y: None
    height: dp(40)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 0.05
        Rectangle:
            pos: self.pos
            size: self.size
    CheckBox:
        size_hint_x: 0.1
        color: 0, 0.83, 1, 1
    Label:
        text: root.text
        halign: 'left'
        valign: 'middle'
        text_size: self.size


<DateRangePopup>:
    title: 'Select Date Range'
    size_hint: 0.7, 0.8
    title_color: utils.get_color_from_hex('#00d4ff')
    separator_color: utils.get_color_from_hex('#00d4ff')
    background: ''
    background_color: 0.05, 0.05, 0.08, 0.95
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(10)
        
        Label:
            text: 'August 2026'
            size_hint_y: None
            height: dp(30)
            bold: True
            font_size: '18sp'
            
        GridLayout:
            size_hint_y: None
            height: dp(30)
            cols: 7
            Label:
                text: 'Mon'
            Label:
                text: 'Tue'
            Label:
                text: 'Wed'
            Label:
                text: 'Thu'
            Label:
                text: 'Fri'
            Label:
                text: 'Sat'
            Label:
                text: 'Sun'
                
        GridLayout:
            id: calendar_grid
            cols: 7
            spacing: dp(5)
            # Days populated by Python
            
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(10)
            CyberButton:
                text: 'Clear Filter'
            Widget:
            CyberButton:
                text: 'Cancel'
                on_press: root.dismiss()


<PlaybackScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)

        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Label:
                text: 'ROBOSERV 4i DUCTBOT - PLAYBACK'
                color: utils.get_color_from_hex('#00d4ff')
                font_size: '24sp'
                bold: True
                halign: 'left'
                valign: 'middle'
                text_size: self.size
            CyberButton:
                size_hint_x: None
                width: dp(120)
                text: 'Stop / Back'
                on_press: root.manager.current = 'main'

        # Video Area
        FloatLayout:
            VideoArea:
                pos_hint: {'x': 0, 'y': 0}
                size_hint: 1, 1

        # Details Glass Card
        GlassCard:
            size_hint_y: None
            height: dp(60)
            padding: dp(10)
            spacing: dp(15)
            Label:
                text: '08/08/26\\n14:29'
                halign: 'center'
                font_size: '12sp'
            Label:
                text: 'Cond: Before'
                font_size: '14sp'
            Label:
                text: 'Cam: Front'
                font_size: '14sp'
            Label:
                text: 'Client: PPPPP'
                font_size: '14sp'
            Label:
                text: 'Area: PPPPP'
                font_size: '14sp'
            Label:
                text: 'Side: PPPPP'
                font_size: '14sp'

        # Action Buttons
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(15)
            RedButton:
                text: 'Shutdown'
                on_press: app.open_shutdown_popup()
            CyberButton:
                text: 'Live Mode'
                on_press: root.manager.current = 'main'
            PulseButton:
                text: 'Start / Pause'
            CyberButton:
                text: 'Export'
                on_press: root.manager.current = 'export'
'''

Builder.load_string(KV)

class MainDashboardScreen(Screen):
    pass

class ExportManagerScreen(Screen):
    def on_enter(self, *args):
        # Populate dummy data
        list_layout = self.ids.export_list
        list_layout.clear_widgets()
        for i in range(1, 10):
            item = ExportListItem(text=f"08/08/26 14:{20+i} - ppppp (ppppp)")
            list_layout.add_widget(item)

class PlaybackScreen(Screen):
    pass

class StartRecordingPopup(Popup):
    pass

class ShutdownPopup(Popup):
    pass

class DateRangePopup(Popup):
    def on_kv_post(self, base_widget):
        # Populate calendar dummy grid
        grid = self.ids.calendar_grid
        from kivy.uix.button import Button
        
        # padding days (assuming month starts on Saturday for August 2026)
        for i in range(5):
            btn = Button(text='', background_color=(0,0,0,0), disabled=True)
            grid.add_widget(btn)
            
        # 31 days
        for day in range(1, 32):
            btn = Button(text=str(day), background_color=(0.1, 0.1, 0.2, 1), color=(1,1,1,1))
            grid.add_widget(btn)

class ExportListItem(BoxLayout):
    text = StringProperty('')

class RoboservApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainDashboardScreen(name='main'))
        sm.add_widget(ExportManagerScreen(name='export'))
        sm.add_widget(PlaybackScreen(name='playback'))
        return sm

    def open_recording_popup(self):
        popup = StartRecordingPopup()
        popup.open()

    def open_shutdown_popup(self):
        popup = ShutdownPopup()
        popup.open()

    def open_date_popup(self):
        popup = DateRangePopup()
        popup.open()


if __name__ == '__main__':
    RoboservApp().run()

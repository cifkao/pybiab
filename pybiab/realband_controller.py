import os
import re
import sys
import traceback

from pywinauto import Application
from pywinauto.application import ProcessNotFoundError
from pywinauto.base_wrapper import ElementNotEnabled
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import wait_until_passes, TimeoutError
import psutil
import win32com.client


class RealBandController:
    """An object for controlling RealBand."""
    _TARGET_VERSION = '2018.0.2.5'

    def __init__(self, binary_path=r'C:\RealBand\RealBand.exe', try_connect=True):
        self.realband_version = _get_exe_version(binary_path)
        if self.realband_version != self._TARGET_VERSION:
            print('This code was written for RealBand {}, your version is {}. '
                  'Proceed with caution.'
                  .format(self._TARGET_VERSION, self.realband_version), file=sys.stderr)

        self._app = Application(backend='win32')
        if try_connect:
            try:
                self._app.connect(path=binary_path)
            except ProcessNotFoundError:
                try_connect = False
        if not try_connect:
            self._app.start(binary_path)
            self._app.wait_cpu_usage_lower(threshold=5)

        def get_ready():
            rb_window = self._app.window(class_name='RealBand')
            if rb_window.exists() and rb_window.is_visible() and rb_window.is_enabled():
                return

            # Reject attempts to recover from a crash
            dialog = self._app.window(class_name='#32770')
            dialog_text = dialog.StaticWrapper2.element_info.name
            if ('Okay to restore all the default settings' in dialog_text or
                'Recover data from last session' in dialog_text):
                dialog.Button2.click()

            raise TimeoutError()

        wait_until_passes(func=get_ready,
                          exceptions=(ElementNotFoundError, TimeoutError),
                          timeout=15, retry_interval=1)

        self._song_pane = self._app.RealBand.children(
            class_name='TPanelWithCanvas')[10]

    @property
    def app(self):
        return self._app

    def kill(self):
        self._app.kill()
        for proc in psutil.process_iter():
            if proc.name() in ['bbw2.exe', 'RealBand.exe']:
                print('Killing', proc, file=sys.stderr)
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    traceback.print_exc(file=sys.stderr)

    def load_song(self, path):
        """Load a song from the given file."""
        self._menu_select('File->Open')
        self._open_file(path)
        try:
            # Get the annoying Comments window out of the way
            self._app.Comments.minimize()
        except MatchError:
            pass

    def load_style(self, path):
        """Load a style from the given file."""
        self.wait_ready()

        def open_dialog():
            # Bring up the style popup menu and choose to open a style file
            self._song_pane.click_input(coords=(44, 73), absolute=False)
            menu = self._app.window(class_name='#32768')
            menu.menu_item('File Open Style').click_input()

        wait_until_passes(func=open_dialog,
                          exceptions=ElementNotFoundError,
                          timeout=120, retry_interval=0.4)
        self._open_file(path)

    def _open_file(self, path):
        """Input a path in the file open dialog."""
        path = os.path.normpath(os.path.abspath(path))
        while True:
            dialog = self._app.window(class_name='#32770')
            dialog.wait('ready')

            # If asked whether to save changes, say no
            try:
                dialog_text = dialog.StaticWrapper2.element_info.name
                if 'Save it?' in dialog_text:
                    dialog.Button2.click()
                    continue
            except MatchError:
                pass
            break

        dialog.Edit1.set_edit_text(path)
        dialog.Edit1.send_keystrokes('{ENTER}')
        self.wait_ready(timeout=60)

    def save_song(self, path, filetype='MIDI File (.MID) (*.MID)'):
        """Save the current song under the given filename."""
        path = os.path.normpath(os.path.abspath(path))

        self._menu_select('File->Save As')
        file_dialog = self._app.window(class_name='#32770')
        file_dialog.wait('ready')
        file_dialog.ComboBox2.select(filetype)
        file_dialog.Edit1.set_edit_text(path)
        file_dialog.Edit1.send_keystrokes('{ENTER}')
        self.wait_ready()

    def generate_all(self):
        """Generate all Band-in-a-Box tracks."""
        self._menu_select('Generate->Generate All BB Tracks')
        self.wait_ready()

    def set_key(self, key, transpose=False):
        """Set the key of the song."""
        if transpose:
            raise NotImplementedError('transpose not implemented')

        self._menu_select('Edit->Key Signature')

        key_dialog = self._app.window(class_name='TKEY')
        key_dialog.wait('ready')
        key_dialog.TComboBox1.select(key)
        key_dialog.TRadioButton4.click()  # No Transpose
        key_dialog.TButton3.click()  # OK
        self.wait_ready()

    @property
    def key_signature(self):
        """The key signature of the song."""
        text = self._get_menu_item_text('Edit->Key Signature')
        return re.search(r'\[([A-G].?)\]$', text).group(1)

    @property
    def time_signature(self):
        """The time signature (meter) of the song."""
        text = self._get_menu_item_text('Edit->Meter (Time Signature)')
        return re.search(r'\[([0-9]+/[0-9]+)\]$', text).group(1)

    @property
    def tempo(self):
        """The tempo of the song."""
        text = self._get_menu_item_text('Edit->Tempo')
        return float(re.search(r'\[([0-9.,]+)\]$', text).group(1))

    def _get_menu_item_text(self, path, timeout=10, retry_interval=0.5):
        def get_text():
            return self._app.RealBand.menu_item(path).text()

        return wait_until_passes(func=get_text,
                                 exceptions=(ElementNotEnabled, RuntimeError),
                                 timeout=timeout,
                                 retry_interval=retry_interval)


    def _menu_select(self, path, timeout=10, retry_interval=0.5):
        self.wait_ready()

        def select_option():
            self._app.RealBand.menu_select(path)

        wait_until_passes(func=select_option,
                          exceptions=(ElementNotEnabled, RuntimeError),
                          timeout=timeout,
                          retry_interval=retry_interval)

    def wait_ready(self, timeout=30):
        self._app.RealBand.wait('ready', timeout=timeout)


def _get_exe_version(path):
    parser = win32com.client.Dispatch("Scripting.FileSystemObject")
    return parser.GetFileVersion(path)


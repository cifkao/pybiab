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


class BandInABoxController:
    """An object for controlling Band-in-a-Box."""
    _TARGET_VERSION = '2018.0.0.520'

    def __init__(self, binary_path=r'C:\bb\bbw.exe', try_connect=True):
        self.biab_version = _get_exe_version(binary_path)
        if self.biab_version != self._TARGET_VERSION:
            print('This code was written for Band-in-a-Box {}, your version is {}. '
                  'Proceed with caution.'
                  .format(self._TARGET_VERSION, self.biab_version), file=sys.stderr)

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
            rb_window = self._app.window(class_name='TBandWindow')
            if rb_window.exists() and rb_window.is_visible() and rb_window.is_enabled():
                return

            raise TimeoutError()

        wait_until_passes(func=get_ready,
                          exceptions=(ElementNotFoundError, TimeoutError),
                          timeout=15, retry_interval=1)

    @property
    def app(self):
        return self._app

    def kill(self):
        self._app.kill()
        for proc in psutil.process_iter():
            if proc.name() == 'bbw.exe':
                print('Killing', proc, file=sys.stderr)
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    traceback.print_exc(file=sys.stderr)

    def load_song(self, path):
        """Load a song from the given file."""
        self.menu_select('File->Open')
        self._open_file(path)

    def _open_file(self, path):
        """Input a path in the file open dialog."""
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
        self._wait_ready(timeout=60)

    def save_song(self, path):
        """Save the current song under the given filename."""
        self.menu_select('File->Save song As')

        file_dialog = self._app.window(class_name='#32770')
        file_dialog.wait('ready')
        file_dialog.Edit1.set_edit_text(path)
        file_dialog.Edit1.send_keystrokes('{ENTER}')
        self._wait_ready()

    def menu_select(self, path, timeout=10, retry_interval=0.5):
        self._wait_ready()

        def select_option():
            self._app.TBandWindow.menu_select(path)

        wait_until_passes(func=select_option,
                          exceptions=(ElementNotEnabled, RuntimeError),
                          timeout=timeout,
                          retry_interval=retry_interval)

    def _wait_ready(self, timeout=30):
        self._app.TBandWindow.wait('ready', timeout=timeout)


def _get_exe_version(path):
    parser = win32com.client.Dispatch("Scripting.FileSystemObject")
    return parser.GetFileVersion(path)


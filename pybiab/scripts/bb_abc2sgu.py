"""Converts ABC files to SGU (Band-in-a-Box) files."""

import argparse
import os
import sys
import time
import traceback

from pywinauto.timings import TimeoutError

from ..biab_controller import BandInABoxController

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--fix-bar-33', action='store_true')
    parser.add_argument('--length', type=int, default=252)
    args = parser.parse_args()

    bb = BandInABoxController()
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)

    for i, fname in enumerate(sorted(os.listdir(input_dir))):
        if not fname.endswith('.abc'):
            print(f'Ignoring {fname}', file=sys.stderr)
            continue

        input_path = os.path.join(input_dir, fname)
        output_path = os.path.join(output_dir, os.path.splitext(fname)[0])
        if os.path.exists(output_path):
            print('{} already exists'.format(output_file), file=sys.stderr)
            continue

        NUM_TRIALS = 3
        for trial_num in range(NUM_TRIALS):
            try:
                bb.load_song(input_path)
                time.sleep(0.1)

                # Extend the length of the song, adjust some settings
                bb.menu_select('Edit->Song Form->Settings (for This Song)')
                bb.app.TSONGSETTINGSDIALOG.wait('ready', timeout=20)
                bb.app.TSONGSETTINGSDIALOG.children(
                    class_name='TCheckBox',
                    title='&Generate 2 bar Ending for this song')[0].uncheck_by_click_input()
                bb.app.TSONGSETTINGSDIALOG.children(
                    class_name='TCheckBox',
                    title='Allow Style Aliases (auto-substtution of style) for this song')[0].uncheck_by_click_input()
                bb.app.TSONGSETTINGSDIALOG.children(
                    class_name='TButton', title='T&itle/Chorus')[0].click_input()
                bb.app.TSONGSETDIALOG.wait('ready', timeout=20)
                bb.app.TSONGSETDIALOG.TEdit3.set_text(120)  # Tempo
                bb.app.TSONGSETDIALOG.TEdit1.set_text(args.length)  # Last bar number
                bb.app.TSONGSETDIALOG.children(
                    class_name='TButton', title='&OK')[0].click_input()
                bb.app.TSONGSETTINGSDIALOG.wait('ready', timeout=20)
                bb.app.TSONGSETTINGSDIALOG.children(
                    class_name='TButton', title='&OK')[0].click_input()

                # Remove the part marker left in the 33rd bar when extending the song
                if args.fix_bar_33 and args.length > 32:
                    bb.app.TBandWindow.wait('ready', timeout=20)
                    bb.app.TBandWindow.TCS.send_keystrokes(('{DOWN}' * 8) + 'pp')

                bb.save_song(output_path)
                break
            except (TimeoutError, RuntimeError, OSError) as e:
                if trial_num == NUM_TRIALS - 1:
                    raise e from None
                traceback.print_exc(file=sys.stderr)
                print('Restarting BiaB', file=sys.stderr)
                bb.kill()
                bb = BandInABoxController(try_connect=False)

        print(i+1, fname, sep='\t', file=sys.stderr)


if __name__ == '__main__':
    main()

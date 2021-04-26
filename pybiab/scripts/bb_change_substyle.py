"""Changes the substyle (e.g. A -> B) of Band-in-a-Box files."""

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
    parser.add_argument('--change-bar-33', action='store_true')
    args = parser.parse_args()

    bb = BandInABoxController()
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)

    for i, fname in enumerate(sorted(os.listdir(input_dir))):
        if not fname.upper().endswith('GU'):
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
                bb.app.TBandWindow.wait('ready', timeout=20)
                bb.app.TBandWindow.TCS.send_keystrokes('{HOME}p')

                # Also change the substyle from bar 33 on.
                # This might be needed because BIAB may otherwise switch the style at bar 33.
                if args.change_bar_33:
                    bb.app.TBandWindow.wait('ready', timeout=20)
                    bb.app.TBandWindow.TCS.send_keystrokes(('{DOWN}' * 8) + 'p')

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

"""Generate accompaniments using RealBand and save them."""

import argparse
import os
import sys
import time
import traceback

from pywinauto.timings import TimeoutError

from ..realband_controller import RealBandController


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('song_dir', help='directory with BIAB song files')
    parser.add_argument('style_dir', help='directory with BIAB style files')
    parser.add_argument('output_dir', help='output directory')
    parser.add_argument('song_style_file',
                        help='TSV file containing on each line the path to a song file (relative '
                             'to song_dir) and the path to a style file (relative to style_dir) '
                             'and optionally the key to which the song should be transposed')
    parser.add_argument('--format', '-f', type=str,
                        default='MIDI File (.MID) (*.MID)')
    parser.add_argument('--suffix', type=str, default=None)
    parser.add_argument('--screenshot-dir', type=str, default=None)
    args = parser.parse_args()

    rb = RealBandController()

    current_song = None
    with open(args.song_style_file, encoding='utf-8') as f:
        for i, line in enumerate(f):
            fields = line.rstrip('\n').split('\t')
            song, style, *fields = fields
            key = fields[0] if fields else None

            song_name, _ = os.path.splitext(song)
            style_name, _ = os.path.splitext(style)
            output_file = '{}.{}{}.mid'.format(
                song_name, style_name, '.' + args.suffix if args.suffix else '')
            output_path = os.path.join(args.output_dir, output_file)
            if os.path.exists(output_path):
                print('{} already exists'.format(output_file), file=sys.stderr)
                continue

            NUM_TRIALS = 3
            for trial_num in range(NUM_TRIALS):
                try:
                    if song != current_song:
                        rb.load_song(os.path.join(args.song_dir, song))
                        current_song = song
                        time.sleep(0.1)
                        rb.wait_ready()
                        if args.screenshot_dir:
                            rb.app.RealBand.capture_as_image().save(
                                os.path.join(args.screenshot_dir,
                                             song.replace('/', '_') +'.png'))
                    rb.load_style(os.path.join(args.style_dir, style))
                    if key and key != rb.key_signature:
                        rb.set_key(key, transpose=True)
                    rb.generate_all()
                    rb.save_song(output_path, args.format)
                    break
                except (TimeoutError, RuntimeError, OSError) as e:
                    if trial_num == NUM_TRIALS - 1:
                        raise e from None
                    traceback.print_exc(file=sys.stderr)
                    print('Restarting RealBand', file=sys.stderr)
                    rb.kill()
                    rb = RealBandController(try_connect=False)
                    current_song = None

            print(i+1, song_name, style_name, sep='\t', file=sys.stderr)


if __name__ == '__main__':
    main()

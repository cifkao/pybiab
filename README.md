# Band-in-a-Box/RealBand automation scripts

Some Python code to have fun with Band-in-a-Box and RealBand on Windows.

![](https://github.com/cifkao/pybiab/blob/screenshots/screenshots.gif?raw=true)

This code was used to generate the [Groove2Groove MIDI Dataset](https://doi.org/10.5281/zenodo.3957999). The general procedure used to generate the data is described in [our paper](https://doi.org/10.1109/TASLP.2020.3019642) [[pdf](https://hal.archives-ouvertes.fr/hal-02923548/document)]:
```bibtex
@article{groove2groove,
  author={Ond\v{r}ej C\'{i}fka and Umut \c{S}im\c{s}ekli and Ga\"{e}l Richard},
  title={{Groove2Groove}: One-Shot Music Style Transfer with Supervision from Synthetic Data},
  journal={IEEE/ACM Transactions on Audio, Speech, and Language Processing},
  publisher={IEEE},
  year={2020},
  volume={28},
  pages={2638--2650},
  doi={10.1109/TASLP.2020.3019642},
  url={https://doi.org/10.1109/TASLP.2020.3019642}
}
```

Scripts included:
- [`bb_abc2sgu.py`](pybiab/scripts/bb_abc2sgu.py) – convert ABC files to BIAB (\*.SGU) files
- [`bb_change_substyle.py`](pybiab/scripts/bb_change_substyle.py) – change the substyle of BIAB files from A to B (or vice versa)
- [`rb_render.py`](pybiab/scripts/rb_render.py) – render BIAB files as MIDI (or any other supported format) using RealBand
- [`fix_rb_midi.py`](pybiab/scripts/fix_rb_midi.py) – fix a RealBand-generated MIDI file by adding missing program change events and skipping invalid events (does not require BIAB and works on any OS)

from lxml import etree
from pydub import AudioSegment
import os
import shutil
import soundfile as sf
import librosa
import numpy as np


chart = {}
duration = None
sounds = {}
channels = {}
bpm = None


def parse_chart():

    lrs = etree.parse(r"02.lrs")

    sounds_xpath = lrs.xpath("//sound")
    for sound in sounds_xpath:
        sounds[int(sound.get('id'))] = sound.get(
            'filename').replace(".wav", ".ogg")

    chart_xpath = lrs.xpath("//n")
    for node in chart_xpath:
        s = int(node.get('s'))
        e = node.get('e')
        c = int(node.get('c'))

        if c == 300:
            continue
        if c == 301:
            global bpm
            bpm = int(float(node.get('p')))
            continue

        try:
            p = int(node.get('p'))
        except ValueError:
            continue

        if s not in chart:
            chart[s] = {}

        if p not in chart[s]:
            chart[s][p] = (c)

        if e is not None:
            chart[s][p] = (c, int(e))
    global duration
    duration = int(chart_xpath[-1].get('s'))*(125/bpm)
    global channels
    channels = sorted(
        set(lrs.xpath('//@c[number(.) >= 0 and number(.) <= 199 or number(.) > 301]')), key=lambda x: int(x)
    )


# test = AudioSegment.silent(duration=2000) +  AudioSegment.from_file(sounds['1'])

# test.export("test.wav", format="wav")

def reset():
    shutil.rmtree('tmp', ignore_errors=True)
    os.mkdir('tmp')


buffer = AudioSegment.empty()


# format: chart[start] = {sound1: (channel, end), sound2: channel, sound3: channel}
# thus, start = s, p = sound and chart[n][p] = (channel, end)|channel

def process_audio(s, p):
    offset = None
    global buffer
    buffer.set_frame_rate(44100)
    buffer.set_channels(len(channels) * 2)
    c = None
    if (type(chart[s][p]) is tuple):
        sound = AudioSegment.from_file(sounds[p])
        (c, e) = chart[s][p]
        sound = sound[:((e - s)*(125/bpm))]
    else:
        if (chart[s][p] > 199 and chart[s][p] <= 301):
            return
        sound = AudioSegment.from_file(sounds[p])
        c = chart[s][p]

    # offset = sound position (silence before that)
    offset = (s * (125/bpm))
    filler = AudioSegment.silent(duration=offset)

    buffer += filler
    buffer += sound

    """by analyzing the chart ingame gameplay, we see that duration between first and last note (for RYUKYU FUNK 73) = 
        6681 - 594 = 6087 frames (60fps) :  6090/60*1000 = 101450ms
        according to lrs file: chart starts at 1920 and ends at 125280
        (125280-1920 = 123360)/101450 = ratio to convert ms to ingame time = 1.215968457368162
        same for PHASE FLIP: 3726 - 409 (30fps) = 110567ms vs (140160 - 2040 = 138120) -> 138120/110567 = 1.24919733927
        difference explained by B P M : 152/156 ~=  1.215968457368162/1.24919733927 ~ 0.9744 
        -> ratio = 152/1.215968457368162 = 156/1.24919733927 = 125 ?
        ms duration * BPM/125 ~= XML duration ?
        <=> ms duration ~= XML duration * 125/BPM
    """

    os.makedirs('tmp/' + str(s), exist_ok=True)
    buffer.export("tmp/" + str(s) + "/" + str(c) + ".wav", format="wav")
    buffer = AudioSegment.empty()


def render():

    for s in chart:
        if os.path.exists(f"tmp/{str(s)}.wav"):
            print(str(s) + " existe déjà, skip")
            continue
        for p in chart[s]:
            process_audio(s, p)

        audios_cur = [file for file in os.listdir('tmp/' + str(s))]
        dur = 0
        for audio in audios_cur:
            dur = max(dur, len(AudioSegment.from_file(
                "tmp/" + str(s) + '/' + audio)))

        merge = AudioSegment.silent(duration=dur)

        for audio in audios_cur:
            sample = AudioSegment.from_file("tmp/" + str(s) + "/" + audio)
            merge = merge.overlay(sample)
        merge.export('tmp/' + str(s) + ".wav", format="wav")
        if os.path.isdir('tmp/' + str(s)):
            shutil.rmtree('tmp/' + str(s), ignore_errors=True)


def finalize():
    final = AudioSegment.silent(duration=duration)
    audios_cur = [file for file in os.listdir('tmp/')]
    for audio in audios_cur:
        final = final.overlay(AudioSegment.from_file("tmp/" + audio))
    final.export('tmp/final.wav', format="wav")
    



parse_chart()
render()

finalize()


""" fuse = AudioSegment.empty()
for canal in comp:
    fuse += comp[canal]

fuse.export("test.wav", format="wav") """

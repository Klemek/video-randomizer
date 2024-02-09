#!/usr/bin/python3

import cv2
import os
import math
import argparse
from typing import *
import tempfile
import hashlib
import random
import subprocess
import time
import sys

CWD = os.path.abspath(os.path.dirname(__file__))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="video-randomizer",
        description="randomize videos by taking small random samples and merging them together",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="output video path (default: random_[time].mp4)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=60,
        help="floating duration of output video in seconds (default: 60s)",
    )
    parser.add_argument(
        "-s",
        "--sample",
        type=float,
        default=1,
        help="floating samples duration in seconds (default: 1s)",
    )
    parser.add_argument(
        "-p",
        "--height",
        type=int,
        default=None,
        help="output video height (default: 1080p)",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=None,
        help="output video height (default: auto for 16:9)",
    )
    parser.add_argument(
        "-f",
        "--framerate",
        type=int,
        default=30,
        help="output video framerate (default: 30fps)",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        type=float,
        default=10,
        help="video input content start/end ignore in %% (default: 10)",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        default=False,
        help="dry mode, do not output video",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="silent mode",
    )
    parser.add_argument(
        "-qf",
        "--ffmpeg-quiet",
        action="store_true",
        default=False,
        help="do not output ffmpeg stdout",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        help="libx264 Constant Rate Factor (default: 23)",
    )
    parser.add_argument(
        "-r",
        "--seed",
        type=int,
        default=random.randrange(sys.maxsize),
        help="random seed",
    )
    parser.add_argument(
        "file",
        type=str,
        nargs='+',
        help='input files'
    )
    return parser.parse_args()


# === UTILS ===


def get_file_hash(path: str) -> str:
    with open(path, mode="rb") as f:
        return hashlib.md5(f.read(8192)).hexdigest()


def get_video_frame_count(path: str) -> int:
    return cv2.VideoCapture(path).get(cv2.CAP_PROP_FRAME_COUNT)



def get_timestamp(frame_number: int, framerate: float) -> str:
    t = frame_number / framerate
    return f"{t//60:.0f}:{t%60:.3f}"


def execute(cmd: List[str]) -> Generator[str, None, None]:
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    if popen.stdout is not None:
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line 
        popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

def execute_and_print(cmd: List[str]) -> None:
    for line in execute(cmd):
        print(line)


def execute_with_args(cmd: List[str], args: argparse.Namespace) -> bool:
    if not args.quiet:
        print(f"$ {' '.join(cmd)}")
    try:
        if args.quiet or args.ffmpeg_quiet:
            execute(cmd)
        else:
            execute_and_print(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def get_scale(args: argparse.Namespace) -> str:
    if args.width is None and args.height is None:
        return "1920:1080"
    elif args.height is None:
        return f"{args.width}:{round(args.width * 9 / 16)}"
    elif args.width is None:
        return f"{round(args.height * 16 / 9)}:{args.height}"
    else:
        return f"{args.width}:{args.height}"


# === MAIN ===


def get_output_file(args: argparse.Namespace) -> str:
    if args.output is not None:
        return args.output
    return f"random_{round(time.time())}.mp4"


def get_build_dir(args: argparse.Namespace) -> str:
    path = os.path.join(os.getcwd(), f"build_{get_scale(args).replace(':','x')}_{args.framerate}fps")
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def convert_video(in_path: str, out_path: str, args: argparse.Namespace) -> bool:
    cmd = [
        'ffmpeg', '-y', '-f', 'mp4', '-i', in_path, '-c:v', 'libx264', '-vf', f'scale={get_scale(args)},fps={args.framerate}', '-crf', str(args.crf), '-video_track_timescale', '90000', '-an', out_path 
    ]
    return execute_with_args(cmd, args)


def convert_all_videos(build_dir: str, args: argparse.Namespace) -> List[str]:
    converted = []
    to_convert = []
    for path in args.file:
        if os.path.exists(path):
            output_path = os.path.join(build_dir, get_file_hash(path) + ".mp4")
            if os.path.exists(output_path):
                converted += [output_path]
            else:
                to_convert += [(path, output_path)]
    if not args.quiet:
        print(f"Found {len(converted) + len(to_convert)} videos")
        print(f"{len(converted)} already converted")
    if len(to_convert):
        if not args.quiet:
            print(f"Converting {len(to_convert)} videos...")
        for i, data in enumerate(to_convert):
            in_path, out_path = data
            result = convert_video(in_path, out_path, args)
            if not args.quiet:
                print(f"[{i + 1} / {len(to_convert)}] {'OK' if result else 'KO'} {in_path} -> {out_path}")
            if result:
                converted += [out_path]
    return converted


def generate_concat_file(videos: List[str], args: argparse.Namespace) -> str:
    random.seed(args.seed)
    print(f"Random seed: {args.seed}")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write("ffconcat version 1.0\n".encode())
        t = 0
        while t < args.duration:
            file = random.choice(videos)
            framecount = get_video_frame_count(file)
            if framecount > 0:
                tmp.write(f"file '{file}'\n".encode())
                inpoint = round(random.random() * framecount * (1 - args.ignore / 100.0 * 2))
                tmp.write(f"inpoint {get_timestamp(inpoint, args.framerate)}\n".encode())
                outpoint = inpoint + round(args.sample * args.framerate)
                tmp.write(f"outpoint {get_timestamp(outpoint, args.framerate)}\n".encode())
                t += args.sample
        return tmp.name

def make_output_video(concat_file: str, output_file: str, args: argparse.Namespace) -> None:
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c:v', 'libx264', '-async', '1', '-an', output_file 
    ]
    execute_with_args(cmd, args)

if __name__ == '__main__':
    args = parse_args()

    output_file = get_output_file(args)

    build_dir = get_build_dir(args)

    videos = convert_all_videos(build_dir, args)

    concat_file = generate_concat_file(videos, args)

    make_output_video(concat_file, output_file, args)

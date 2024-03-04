usage: video-randomizer.py [-h] [-o OUTPUT] [-d DURATION] [-s SAMPLE] [-p HEIGHT] [-w WIDTH] [-f FRAMERATE] [-i IGNORE] [--dry] [-q] [-qf] [--crf CRF] [-r SEED]
                           [--ffmpeg FFMPEG] [-nc] [-na] [-ab AUDIO_BITRATE]
                           file [file ...]

randomize videos by taking small random samples and merging them together

positional arguments:
  file                  input files

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output video path (default: random_[time].mp4)
  -d DURATION, --duration DURATION
                        floating duration of output video in seconds (default: 60s)
  -s SAMPLE, --sample SAMPLE
                        floating samples duration in seconds (default: 1s)
  -p HEIGHT, --height HEIGHT
                        output video height (default: 1080p if multiple videos)
  -w WIDTH, --width WIDTH
                        output video height (default: auto for 16:9)
  -f FRAMERATE, --framerate FRAMERATE
                        output video framerate (default: 30fps if multiple videos)
  -i IGNORE, --ignore IGNORE
                        video input content start/end ignore in % (default: 10)
  --dry                 dry mode, do not output video
  -q, --quiet           silent mode
  -qf, --quiet-ffmpeg   do not output ffmpeg stdout
  --crf CRF             libx264 Constant Rate Factor (default: 23)
  -r SEED, --seed SEED  random seed
  --ffmpeg FFMPEG       ffmpeg binary path (default is found on PATH)
  -nc, --no-convert     don't convert videos (default for one video, might fail on multiple)
  -na, --no-audio       only keep video track
  -ab AUDIO_BITRATE, --audio-bitrate AUDIO_BITRATE
                        audio bitrate in Kbps (default: 128)
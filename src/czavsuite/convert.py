# czavsuite - a suite of useful scripts to serialise FFmpeg jobs
#
# Copyright 2023 - present Alexander Czutro, github@czutro.ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################### aczutro ###

"""FFmpeg wrapper"""

from . import config, probing, utils
from czutils.utils import czlogging
import os.path


_logger = czlogging.LoggingChannel("czavsuite.convert",
                                   czlogging.LoggingLevel.ERROR,
                                   colour=True)


class ConvertError(Exception):
    pass


def _outputFilename(inputFile: str, videoCodec: str, audioCodec: str):
    """
    """
    if not videoCodec == "null":
        outputType = "mp4"
    elif audioCodec == "aac":
        outputType = "m4a"
    elif audioCodec == "mp3":
        outputType = "mp3"
    elif audioCodec == "copy":
        inputCodec = probing.ffprobe(inputFile, config.Probing.AUDIO)["codec_name"]
        outputType = "mp3" if inputCodec == "mp3" else "m4a"
    else:
        raise ValueError
    #else

    tokens = inputFile.split('.')

    if len(tokens) == 1:
        return '%s.%s' % (inputFile, outputType)
    else:
        inputType = tokens[-1]
        if inputType == outputType:
            tokens[-2] = tokens[-2] + '-new'
            outputFile = '.'.join(tokens)
        else:
            tokens[-1] = outputType
            outputFile = '.'.join(tokens)
        #else
    #else

    return outputFile
#def


def _checkExistence(filename: str):
    """tests whether a file exists, and if it does,
     asks the user whether to overwrite;
     if user answer yes, removes the file;
     if user answers no, raises an exception"""
    try:
        if os.path.exists(filename):
            if input("file %s already exists -- overwrite? " % filename) \
                    in [ 'y', 'Y', 'yes', 'YES' ]:
                os.remove(filename)
            else:
                raise ConvertError("file %s already exists -- aborting" % filename)
            #if
        #if
    except PermissionError as e:
        raise ConvertError(e)
    #except
#def


def _toFFmpegVideo(conf: config.Video) -> list:
    if conf.codec == "h265":
        codec = "libx265"
    elif conf.codec == "h264":
        codec = "libx264"
    elif conf.codec == "null":
        return [ "-vn" ]
    elif conf.codec == "copy":
        return [ "-c:v", "copy" ]
    else:
        raise ValueError
    #else
    return [ "-c:v", codec, "-crf", conf.crf ]
#_toFFmpegVideo


def _toFFmpegAudio(conf: config.Audio) -> list:
    if conf.codec == "aac":
        codec = [ "-c:a", "aac" ]
        if conf.bitrate is not None:
            return codec + [ "-b:a", conf.bitrate ]
        else:
            return codec
        #if
    elif conf.codec == "mp3":
        codec = [ "-c:a", "libmp3lame" ]
        if conf.bitrate and conf.quality:
            raise ValueError
        elif conf.bitrate is not None:
            return codec + [ "-b:a", conf.bitrate ]
        elif conf.quality is not None:
            return codec + [ "-q:a", conf.quality ]
        else:
            return codec
        #if
    elif conf.codec == "null":
        return [ "-an" ]
    elif conf.codec == "copy":
        return [ "-c:a", "copy" ]
    else:
        raise ValueError
    #else
#_toFFmpegVideo


def _toFFmpegCropping(conf: config.Cropping) -> list:
    if conf.valid:
        return [ '-vf', 'crop=in_w-%s:in_h-%s:%s:%s' %
                 (conf.left + conf.right, conf.up + conf.down, conf.left, conf.up) ]
    else:
        return []
    #else
#_toFFmpegCropping


def _toFFmpegScaling(file: str, conf: config.Scaling) -> list:
    if conf.valid:
        probe = probing.ffprobe(file, config.Probing.VIDEO)
        width = int(probe["width"])
        height = int(probe["height"])
        fWidth = width * conf.factor
        fHeight = height * conf.factor
        width = int(fWidth) + int(fWidth) % 2
        height = int(fHeight) + int(fHeight) % 2
        return [ '-vf', 'scale=%d:%d' % (width, height) ]
    else:
        return []
    #else
#_toFFmpegScaling


def _toFFmpegCuttting(conf: config.Cutting) -> list:
    if conf.valid:
        diff = conf.end - conf.start
        if diff <= 0:
            raise ValueError
        #if
        return [ "-ss", str(conf.start), "-t", str(diff) ]
    else:
        return []
    #else
#_toFFmpegCuttting


def avConvert(files: list,
              confGeneral: config.General,
              confVideo: config.Video,
              confAudio: config.Audio,
              confCropping: config.Cropping,
              confCutting: config.Cutting,
              confScaling: config.Scaling):
    S = utils.SystemCaller(True)
    for file in files:
        outputFile = _outputFilename(file, confVideo.codec, confAudio.codec)
        _checkExistence(outputFile)
        cmd = ([ 'ffmpeg', '-hide_banner', '-i', file ] + _toFFmpegCropping(confCropping) +
               _toFFmpegScaling(file, confScaling) + _toFFmpegVideo(confVideo) +
               _toFFmpegAudio(confAudio) + _toFFmpegCuttting(confCutting) + [ outputFile ])
        print(" ".join(cmd))
        if not confGeneral.dry:
            returnCode = S.call(cmd)
            _logger.info("return code:", returnCode)
            _logger.info("stdout:", S.stdout())
            _logger.info("stderr:", S.stderr())
            print(S.stderr())
            print("=======================")
        #if
    #for
#avToMp4

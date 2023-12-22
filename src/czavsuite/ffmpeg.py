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

from . import config
from czutils.utils import czlogging, cztext
import re
import subprocess


_logger = czlogging.LoggingChannel("czavsuite.ffmpeg",
                                   czlogging.LoggingLevel.ERROR,
                                   colour=True)


class SubprocessError(Exception):
    pass


class SystemCaller:

    def __init__(self, exceptionOnFailure: bool):
        self._stdout = ""
        self._stderr = ""
        self._doRaise = exceptionOnFailure
    #__init__


    def stdout(self):
        return self._stdout
    #stdout


    def stderr(self):
        return self._stderr
    #stdout


    def call(self, args: list):
        P = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = P.communicate()
        self._stdout = stdout.decode(errors="ignore")
        self._stderr = stderr.decode(errors="ignore")
        if P.returncode and self._doRaise:
            _logger.warning("'%s'" % " ".join(args), "returned", P.returncode)
            raise SubprocessError(self._stderr)
        #if
        return P.returncode
    #def

#SystemCaller


def grep(pattern: str, text, ignoreCase=False, colour=False):
    if type(text) is str:
        return grep(pattern, text.split(sep='\n'), ignoreCase, colour)
    #if

    flags = re.IGNORECASE if ignoreCase else 0
    matcher = re.compile(pattern, flags)
    ans = []
    for line in text:
        if colour:
            match = matcher.search(line)
            if match is not None:
                start, end = match.start(), match.end()
                ans.append("%s%s%s"
                           % (line[:start],
                              cztext.colourise(line[start:end], cztext.Col16.RED, bold=True),
                              line[end:]))
            #if
        else:
            if matcher.search(line) is not None:
                ans.append(line)
            #if
        #else
    #for
    return ans
#grep


def _ffprobeDict(lines: list):
    ans = dict()
    for line in lines:
        tokens = line.split(sep='=')
        if len(tokens) == 2:
            ans[tokens[0]] = tokens[1]
        #if
    #for
    return ans
#_getDict


def ffprobe(file: str, mode: int):
    """
    TODO
    """
    S = SystemCaller(True)

    if mode == config.Probing.FULL:
        returnCode = S.call(['ffprobe', '-hide_banner', file])
        _logger.info("return code:", returnCode)
        _logger.info("stdout:", S.stdout())
        _logger.info("stderr:", S.stderr())
        return grep("Video|Audio",
                    grep("Stream", S.stderr()),
                    colour=True)
    elif mode == config.Probing.VIDEO or mode == config.Probing.AUDIO:
        returnCode = S.call(['ffprobe', '-hide_banner',
                             '-show_streams', '-select_streams',
                             'v' if mode == config.Probing.VIDEO else 'a',
                             file])
        _logger.info("return code:", returnCode)
        _logger.info("stdout:", S.stdout())
        _logger.info("stderr:", S.stderr())
        return _ffprobeDict(S.stdout().split(sep='\n'))
    elif mode == config.Probing.DURATION:
        returnCode = S.call(['ffprobe', '-hide_banner', file])
        _logger.info("return code:", returnCode)
        _logger.info("stdout:", S.stdout())
        _logger.info("stderr:", S.stderr())
        return grep("Duration", S.stderr())[0].split(sep=',')[0].split(sep=' ')[3]
    else:
        raise ValueError
    #else
#ffprobe

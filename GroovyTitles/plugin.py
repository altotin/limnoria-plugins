###
# Copyright (c) 2024, limnoria user no. 6789
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
from supybot.i18n import PluginInternationalization
import re, json
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
from jinja2 import Template
from bs4 import BeautifulSoup

_ = PluginInternationalization('GroovyTitles')

class GroovyTitles(callbacks.PluginRegexp):
    """GroovyTitles"""
    regexps = ['_bsky_handler', '_yt_handler']
    callBefore = ['Web']

    def _get_soup(self, url):
        """get soup from url"""
        self.log.debug(f'groovytitles: fetching {url}')
        s = utils.web.getUrl(url).decode('utf8')
        return BeautifulSoup(s)

    def _get_json(self, url):
        """get json from url"""
        self.log.debug(f'groovytitles: fetching json {url}')
        with utils.web.getUrlFd(url) as fd:
            try:
                return json.load(fd)
            except json.JSONDecodeError as e:
                return {}
                
    def _extract_yt_id(self, s):
        """extract youtube video id from string"""
        found = re.findall(r'(?:v=|/)([0-9A-Za-z_-]{11})', s)
        if found:
            # will match twice on https://youtube-nocookie.com/embed/dQw4w9WgXcQ
            # return the final match
            return found[-1]

    @urlSnarfer
    def _bsky_handler(self, irc, msg, match):
        r'https://bsky\.app/profile/[^\s/]+/post/[^\s]+'
        channel = msg.channel
        network = irc.network
        if not self.registryValue('bsky.enabled', channel=channel, network=network):
            return
        url = match.group(0)
        soup = self._get_soup(url)
        
        def get_content(soup, selector):
            """get content from tag"""
            elm = soup.head.select_one(selector)
            if elm:
                return elm['content'].replace('\n', ' ').strip()
            return ''
        
        message = get_content(soup, 'meta[name="description"]')
        image   = get_content(soup, 'meta[property="og:image"]')
        has_image = ''
        if image:
            has_image = '<img>'
        
        timestamp_display = ''
        timestamp = get_content(soup, 'meta[name="article:published_time"]')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', ''))
            format_string = self.registryValue('bsky.timeFormat', channel=channel, network=network)
            timestamp_display = dt.astimezone(ZoneInfo('UTC')).strftime(format_string)
        else:
            irc.reply('couldn\'t load bsky post')
            return

        author = ''
        handle = ''
        author_handle = get_content(soup, 'meta[property="og:title"]')
        match = re.match(r'(.+) \(([\w.@-]+)\)$', author_handle)
        try:
            # User Name (@handle.bsky.social)
            author = match.group(1)
            handle = match.group(2)
        except:
            # @handle.bsky.social
            handle = author_handle
        
        template_vars = {
            'message': message,
            'author' : author,
            'handle' : handle,
            'timestamp' : timestamp_display,
            'image'     : image,
            'has_image' : has_image,
            }
        t = Template( self.registryValue('bsky.template', channel=channel, network=network) )
        output = t.render(template_vars)
        irc.reply( utils.str.normalizeWhitespace(output), prefixNick = False )


    @urlSnarfer
    def _yt_handler(self, irc, msg, match):
        r'https?://((www|m)\.)?((youtube(-nocookie)?\.com|youtu.be))/[^\s]+'
        channel = msg.channel
        network = irc.network
        if not self.registryValue('youtube.enabled', channel=channel, network=network):
            return
        
        video_id = self._extract_yt_id(match.group(0))
        if not video_id:
            return
        
        params = {
            'format': 'json',
            'url': 'https://www.youtube.com/watch?v=' + video_id,
            }
        url = 'https://www.youtube.com/oembed?' + urllib.parse.urlencode(params)
        response = self._get_json(url)
        
        try:
            title = response['title']
        except KeyError:
            self.log.error(f'groovytitles: failed to get title from {url}')
            return
        channel_title = response.get('author_name', '')
        channel_title = re.sub(' - Topic$', '', channel_title)

        template_vars = {
            'title': title,
            'channel_title' : channel_title,
            }
        t = Template( self.registryValue('youtube.template', channel=channel, network=network) )
        output = t.render(template_vars)
        irc.reply( utils.str.normalizeWhitespace(output), prefixNick = False )


Class = GroovyTitles

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

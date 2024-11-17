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

REGEX_BSKY = r'https://bsky\.app/profile/[^\s/]+/post/[^\s]+'

class GroovyTitles(callbacks.PluginRegexp):
    """GroovyTitles"""
    regexps = ['bsky_snarfer']
    threaded = True
    callBefore = ["Web"]

    def _get_soup(self, url):
        """get soup from url"""
        self.log.debug(f'groovytitles: fetching {url}')
        s = utils.web.getUrl(url).decode('utf8')
        return BeautifulSoup(s)

    def _bsky_handler(self, irc, msg, match):
        """title bsky urls"""
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
        if not message:
            irc.reply('bsky post not visible')
            return
        
        timestamp_display = ''
        timestamp = get_content(soup, 'meta[name="article:published_time"]')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', ''))
            format_string = self.registryValue('bsky.timeFormat', channel=channel, network=network)
            timestamp_display = dt.astimezone(ZoneInfo('UTC')).strftime(format_string)

        author_handle = get_content(soup, 'meta[property="og:title"]')
        match = re.match(r'(.+) \(([\w.@-]+)\)$', author_handle)
        author = match.group(1)
        handle = match.group(2)
        
        template_vars = {
            'message': message,
            'author' : author,
            'handle' : handle,
            'timestamp' : timestamp_display,
            }
        t = Template( self.registryValue('bsky.template', channel=channel, network=network) )
        output = t.render(template_vars)
        irc.reply( utils.str.normalizeWhitespace(output), prefixNick = False )
        
    bsky_snarfer = urlSnarfer(_bsky_handler)
    bsky_snarfer.__doc__ = REGEX_BSKY


Class = GroovyTitles

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

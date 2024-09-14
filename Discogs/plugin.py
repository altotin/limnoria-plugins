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
import json
from jinja2 import Template

_ = PluginInternationalization('Discogs')

HEADERS = {
    'User-agent': 'LimnoriaDiscogsPlugin/0.0.2'
}
REGEX = r'https://www\.discogs\.com/\S*(release|master)/(\d+)'

class Discogs(callbacks.PluginRegexp):
    """snarf discogs links"""
    regexps = ['discogs_snarfer']
    threaded = True
    callBefore = ["Web"]

    def _discogs_api(self, item_type, item_id):
        """GET json from discogs api"""
        url = f'https://api.discogs.com/{item_type}s/{item_id}'
        self.log.debug(f'discogs: fetching {url}')
        with utils.web.getUrlFd(url, headers=HEADERS) as fd:
            try:
                return json.load(fd)
            except json.JSONDecodeError as e:
                raise callbacks.Error(f"JSON Decode Error on {url}: {e}") from e

    def _discogs_handler(self, irc, msg, match):
        """title discogs urls"""
        channel = msg.channel
        network = irc.network
        
        #  url       = match.group(0)
        item_type = match.group(1)
        item_id   = match.group(2)      
        data = self._discogs_api(item_type, item_id)
        
        artists = ''
        formats = ''
        labels  = ''
        have    = ''
        want    = ''
        for_sale = ''

        for x in data['artists']:
            name = x.get('name')  ## should this use 'anv' when available?
            join = x.get('join', '').replace('Featuring', 'ft.')
            artists += f'{name} {join} '

        def extract_values(data, key, subkey):
            """get subkey values, deduped and omitting some things"""
            new_list = [ x.get(subkey) for x in data.get(key) ]
            new_list = list(dict.fromkeys(new_list)) # dedupe
            new_list = [v for v in new_list if v != 'All Media']
            return new_list

        if item_type == 'release':
            formats = '+'.join(extract_values(data, 'formats', 'name'))
            labels  = '/'.join(extract_values(data, 'labels', 'name'))
            community = data.get('community')
            have = community.get('have', '')
            want = community.get('want', '')
            for_sale = data.get('num_for_sale', '')
            
        template_vars = {
            'artists' : artists,
            'title'   : data.get('title', ''),
            'year'    : data.get('year',  ''),
            'formats' : formats,
            'labels'  : labels,
            'have'    : have,
            'want'    : want,
            'for_sale': for_sale,
            }
        t = Template( self.registryValue(f't{item_type}', channel=channel, network=network) )
        output = t.render(template_vars)
        irc.reply( utils.str.normalizeWhitespace(output) )
        
    discogs_snarfer = urlSnarfer(_discogs_handler)
    discogs_snarfer.__doc__ = REGEX        


Class = Discogs


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

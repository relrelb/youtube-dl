# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
    compat_parse_qs,
)
from ..utils import (
    get_element_by_class,
    get_element_by_attribute,
    extract_attributes,
    update_url_query,
)


def update_url_path(url, path):
    parsed_url = compat_urlparse.urlparse(url)
    return compat_urlparse.urlunparse(parsed_url._replace(path=path))


class KissCartoonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kisscartoon\.xyz/episode/(?P<id>[^/]+)(?:/.*)?'
    _TEST = {
        'url': 'https://kisscartoon.xyz/episode/spongebob-squarepants-season-12-episode-17/',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'spongebob-squarepants-season-12-episode-17',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        result = {
            'id': video_id,
            'title': self._html_search_regex(r'<h1>(.*?)</h1>', webpage, 'title'),
        }

        json_ld = self._parse_json(self._search_regex(
            r'(?s)<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?P<json_ld>.+?)</script>',
            webpage, 'JSON-LD', group='json_ld'), video_id)
        for e in json_ld['@graph']:
            item_type = e.get('@type')
            if isinstance(item_type, compat_str):
                item_type = [item_type]
            if 'WebPage' in item_type:
                date_published = e.get('datePublished')
                if date_published is not None:
                    result['upload_date'] = date_published
                date_modified = e.get('dateModified')
                description = e.get('description')
                if description is not None:
                    result['description'] = description
            elif 'Person' in item_type:
                person_id = e.get('@id')
                if person_id is not None:
                    result['uploader_url'] = person_id
                    uploader_id = self._search_regex(r'^https?://kisscartoon\.xyz/.*/schema/person/([a-z0-9]{32})$', person_id, 'uploader_id', fatal=False)
                    if uploader_id is not None:
                        result['uploader_id'] = uploader_id
                person_name = e.get('name')
                if person_name is not None:
                    result['uploader'] = person_name
                # person_image = e.get('image')
                # if person_image is not None:
                #     person_image_type = person_image.get('@type')
                #     person_image_id = person_image.get('@id')
                #     person_image_url = person_image.get('url')
                #     person_image_width = person_image.get('width')
                #     person_image_height = person_image.get('height')
                #     person_image_caption = person_image.get('caption')
                # person_logo = e.get('logo')
                # person_description = e.get('description')
                # person_same_as = e.get('sameAs')

        server_list = get_element_by_class('form-group list-server', webpage)
        select = self._search_regex(r'<select.*?>((?s:.)+?)</select>', server_list, 'select')
        option = get_element_by_attribute('selected', r'.*', select)
        if option is None:
            option = self._search_regex(r'(<option.*?>)', server_list, 'option')
        attrs = extract_attributes(option)
        server_stream = attrs['value']

        film_id = self._search_regex(r'var filmId = "(\d+)";', webpage, 'film_id')

        ajax_get_link_stream_url = update_url_path(url, '/ajax-get-link-stream/')
        ajax_get_link_stream_url = update_url_query(ajax_get_link_stream_url, {
            'server': server_stream,
            'filmId': film_id,
        })

        ajax_get_link_stream = self._download_webpage(ajax_get_link_stream_url, video_id)
        parsed_url = compat_urlparse.urlparse(ajax_get_link_stream)
        qs = compat_parse_qs(parsed_url.query)
        hash_id, = qs['id']

        data = self._download_json('https://hls.cartoonwire.to/vl/%s' % (hash_id,), video_id)
        # TODO: all qualities
        md5_id = data['720p']['md5']

        i = 0
        chunk_urls = []
        while True:
            chunk_link_url = 'https://hls.cartoonwire.to/getChunkLink?chunkFile=%s-chunk-%d.txt' % (md5_id, i)
            chunk_url = self._download_webpage(chunk_link_url, video_id)
            # TODO: change to regex
            if 'undefined' in chunk_url:
                break
            chunk_urls.append(chunk_url)
            i += 1
        print(chunk_urls)

        # TODO: download chunk_urls and concat the results

        # 'duration',
        # 'webpage_url',
        print(result)
        return result

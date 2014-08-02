# -*- coding: utf-8 -*-
import re
import urllib
import urllib2
import HTMLParser
import datetime

import html5lib

DEV = False


def parse(url):
    if DEV:
        url = re.sub('http://(m|www)\.democracynow\.org/', '\\1/', url)
        import os.path
        url = 'file://'+os.path.join(os.getcwd(), 'pages-test',
                                     url.replace('/','-') +'.html')
    print 'PARSING URL: %s' % url
    text = urllib.urlopen(url).read()
    return html5lib.parse(text, namespaceHTMLElements=False)

def textualize(elem):
    if elem is not None:
        return ''.join(elem.itertext()).strip()

def video_url(url):
    if url is not None:
        return url.replace('/ipod/', '/flash/')

def absolutize(url):
    if url is not None:
        return url if url[:4] == 'http' else 'http://m.democracynow.org' + url


def parse_show(year, month, day):
    url = 'http://m.democracynow.org/shows_include/%s/%s/%s' % (year, month, day)
    doc = parse(url).find('body')
    return _parse_show(doc)

def parse_latest():
    doc = parse('http://m.democracynow.org/').find('body//div[@class="ui-content"]')
    return _parse_show(doc)
    # return {'current': list(_parse_show(doc)),
    #         'previous': list(_parse_previous_shows(doc))}


def _parse_show(doc):
    date = doc.find('div[@class="context_header"]/h2').text.strip()
    for header, ul in zip(doc.findall('div[@class="section_header"]/h2'),
                         doc.findall('ul')):
        section = header.text
        for li in ul.findall('li'):
            yield _parse_news_item(li, section, date)


def _parse_news_item(li, section=None, date=None):
    # if section == 'Headlines':
    #     continue #yield parse_headlines(year, month, day)
    # NEWS ITEM
    img = li.find('.//img[@class="video_poster"]')
    if img is None:
        img = li.find('.//a[@class="video_link"]/img')
    if img is not None:
        img = absolutize(img.get('src'))

    a = li.find('.//h3/a')
    audio = li.find('.//a[@class="media_icon listen"]')
    video = li.find('.//a[@class="media_icon watch"]')
    if video is None:
        video = li.find('.//a[@class="video_link"]')

    if section in ('Headlines', 'Full Show'):
        label = u'%s — %s' % (date, section)
    else:
        label = ' %s' % (textualize(a) or section)

    summary = textualize(li.find('.//div[@class="more_summary"]')),

    return {
        'thumbnail': img,
        'label': label,
        'label2': section,
        # 'href': a.get('href') if a is not None else None,
        'audio': audio.get('href') if audio is not None else None,
        'video': video_url(video.get('href') if video is not None else None),
        'info': {
            'plot': summary,
            'duration': textualize(li.find('.//div[@class="media_icon duration"]')),
            'tvshowtitle': date
        },
        # 'selected': section == 'Full Show',
        'is_playable': True
    }

def parse_month(year, month, day):
    url = 'http://www.democracynow.org/shows/%s/%s' % (year, month)
    doc = parse(url).find('body//div[@id="recent_shows_wrapper"]')

    def truncate(story):
        return story[:20]+u'…'

    top_day = True
    for h,ul,div in zip(doc.findall('h2'), doc.findall('ul'), doc.findall('div')):
        href = h.find('a').get('href')
        if '/shows/' in href:
            y,m,d = map(int, href.split('/')[-3:])
        else:
            y,m,d = datetime.date.today().timetuple()[:3]
        slug = ' | '.join(truncate(textualize(li)) for li in ul.findall('li')[1:])
        label = datetime.date(y,m,d).strftime(' %a %d %B' if top_day else '  %a %d')
        yield d, { 'label': label + ' ' + slug }
        top_day = False


# def _parse_previous_shows(doc):
#     for prev in doc.findall('div[@class="context_header previous_show"]'):
#         d = prev.get('id').rpartition('_')[2]
#         d = datetime.datetime.strptime(d, '%Y%m%d')

#         fdate = prev.find('h2').text.strip()
#         yield {'label': fdate, 'date': d}


# def parse_headlines(year, month, day):
#     url = 'http://m.democracynow.org/headlines/%s/%s/%s' % (year, month, day)
#     doc = parse(url)
#     ul = doc.find('.//div[@id="headlines"]/ul')
#     text = '\n'.join(map(textualize, ul.findall('li[@class="news_item news_brief"]')))
#     ul.find("li[@class='news_item item_with_video']")
#     return


def parse_search_results_or_topic(query=None, tag_id=None, page=None):
    if query:
        url = '/search?utf8=%s&query=%s' % (unichr(0x2713).encode('utf8'), query)
    else:
        url = '/tags/%s' % tag_id
    ul = parse('http://m.democracynow.org' + url).find('.//div[@class="ui-content"]/ul')
    for li in ul.findall('li'):
        yield _parse_news_item(li)

    # return items, nb_results, has_next_page


def parse_topics():
    doc = parse('http://m.democracynow.org/topics').find(
        'body/div[@id="main_content"]/div[@class="ui-content topics"]/ul')
    for a in doc.findall('li/div/h2/a'):
        tag = re.match('/tags/(\d+)', a.get('href')).group(1)
        yield { 'label': a.text, 'tag': tag }

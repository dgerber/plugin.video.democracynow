# -*- coding: utf-8 -*-
import datetime
import calendar

from xbmcswift2 import Plugin, xbmcgui

import resources.lib.democracynow as dn

plugin = Plugin()


def finish(item, content_type='video'):
    # item['is_playable'] = True
    content_type = 'audio' if plugin.request.args.get('content_type') == 'audio' else 'video'
    item['path'] = item[content_type]
    del item['audio'], item['video']
    return item


@plugin.route('/')
def index():
    try: l = latest()
    except: l = [{'label': u'Latest…', 'path': plugin.url_for('latest')}]
    return l + [
        {'label': u'Past Shows…', 'path': plugin.url_for('shows')},
        {'label': u'Topics…', 'path': plugin.url_for('topics')},
        {'label': u'Search…', 'path': plugin.url_for('search')},
        # {'label': 'Blog', 'path': plugin.url_for('blog')},
        # {'label': 'Web exclusives', 'path': plugin.url_for('web')}
    ]

@plugin.route('/latest/')
def latest():
    return [finish(i) for i in dn.parse_latest()]


@plugin.route('/shows/')
def shows():
    now = datetime.datetime.utcnow()
    args = plugin.request.args

    year = int(args['year'][0]) if 'year' in args else now.year
    month, day = None, None
    if 'month' in args:
        month = int(args['month'][0])
    elif year == now.year:
        month = now.month
    if 'day' in args:
        day = int(args['day'][0])
    elif year == now.year and month == now.month:
        day = now.day

    def items():
        # .. menu entry disappears with update_listing
        yield {'label': '..', 'path': plugin.url_for('index')}

        for y in range(now.year, 1996-1, -1):
            if y != year:
                yield { 'label': '%s'%y,
                        'path': plugin.url_for('shows', year=y) }
            else:
                for x in month_items(y):
                    yield x

    def month_items(y):
        month_start = now.month if y == now.year else 12
        for m in range(month_start, (2 if y == 1996 else 1)-1, -1):
            fmt = ' %B %Y' if m == month_start else ' %B'
            month_item = { 'label': datetime.date(y,m,1).strftime(fmt),
                           'path': plugin.url_for('shows', month=m, year=y) }

            if m == month:
                try:
                    for d, item in dn.parse_month(year, month, day):
                        if d == day:
                            try:
                                for i in dn.parse_show(year, month, day):
                                    yield finish(i)
                                continue
                            except:
                                item['label'] = '%s (failed to load)' % item['label']
                        item['path'] = plugin.url_for('shows', day=d,
                                                      month=m, year=y)
                        yield item
                    continue
                except:
                    month_item['label'] = '%s (failed to load)' % month_item['label']
            yield month_item

    return plugin.finish(items(), update_listing=True)


# @plugin.cached_route('/topics/')
@plugin.route('/topics/')
def topics():
    # return [
    #     {'label': u'Search Topics…', 'path': plugin.url_for('topics')},
    #     {'label': 'Featured Topics', 'path': plugin.url_for('topics')},
    #     {'label': 'Recently Updated Topics', 'path': plugin.url_for('topics/featured')}
    #     {'label': 'Browse all Topics A to Z', 'path': plugin.url_for('all_topics')} ]
    return [ {'label': t['label'], 'path': plugin.url_for('topic', tag=t['tag'])}
             for t in dn.parse_topics() ]


@plugin.route('/tags/<tag>')
def topic(tag):
    return [finish(i) for i in dn.parse_search_results_or_topic(tag_id=tag)]


@plugin.route('/search')
def search():
    q = xbmcgui.Dialog().input('Search:')
    # q = plugin.request.args.get('query')
    return [finish(i) for i in dn.parse_search_results_or_topic(query=q)]


if __name__ == '__main__':
    plugin.run()

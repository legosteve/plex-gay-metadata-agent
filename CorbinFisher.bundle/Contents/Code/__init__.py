# CorbinFisher
from selenium import webdriver
from time import sleep
from lxml import html as tree
import re
import os

PLUGIN_LOG_TITLE = 'CorbinFisher'
VERSION_NO = '2016.06.10.1'

# Delay used when requesting HTML, may be good to have to prevent being banned
# from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.corbinfisher.com%s'

# Example Video Details URL
BASE_VIDEO_DETAILS_URL = BASE_URL % '/#home/episode/%s'

# Example Search URL:
BASE_SEARCH_URL = BASE_URL % '/#search?pager=1&q=%s&type=0&guid='
SLUG_REGEX = re.compile(r"(?P<studio>)corbin ?fisher ?- ?"
                        r"(?P<slug>(acm|acs|cfs)-[^ ]+) ?- ?"
                        r"(?P<clip_name>[^\\[]+)")


def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = "Mozilla/4.0 (compatible; MSIE 8.0; " \
        "Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; " \
        ".NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)"


class CorbinFisher(Agent.Movies):
    name = 'CorbinFisher'
    languages = [Locale.Language.NoLanguage, Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.cockporn']

    def Log(self, message, *args):
        if Prefs['debug']:
            Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def process_name(self, name):
        basename = name.lower()
        basename = re.sub(r"[^0-9a-zA-Z ]", '', basename)  # remove special
        basename = re.sub(r"\s{2,}", ' ', basename).strip()  # collapse spaces
        return basename

    def search(self, results, media, lang, manual):
        self.Log('-----------------------------------------------------------'
                 '-------------------')
        self.Log('SEARCH CALLED v.%s', VERSION_NO)
        self.Log('SEARCH - media.title -  %s', media.title)
        self.Log('SEARCH - media.items[0].parts[0].file '
                 '-  %s', media.items[0].parts[0].file)
        self.Log('SEARCH - media.primary_metadata.title '
                 '-  %s', media.primary_metadata.title)
        self.Log('SEARCH - media.items -  %s',
                 media.items)
        self.Log('SEARCH - media.filename -  %s',
                 media.filename)
        self.Log('SEARCH - lang -  %s', lang)
        self.Log('SEARCH - manual -  %s', manual)

        if not media.items[0].parts[0].file:
            return

        path_and_file = media.items[0].parts[0].file.lower()
        self.Log('SEARCH - File Path: %s' %
                 path_and_file)

        (file_dir, basename) = \
            os.path.split(os.path.splitext(path_and_file)[0])
        final_dir = os.path.split(file_dir)[1]

        folder_list = re.split(',\s*', Prefs['folders'].lower())
        if final_dir not in folder_list:
            self.Log('SEARCH - Skipping %s because the '
                     'folder %s is not in the acceptable folders '
                     'list: %s' %
                     (basename, final_dir, ','.join(folder_list)))
            return

        # Check for the slug in the file name
        m = SLUG_REGEX.match(basename)
        if m:
            groups = m.groupdict()
            video_id = groups['slug']

            self.Log('SEARCH - Video ID: %s' % video_id)
            results.Append(
                MetadataSearchResult(id=video_id, name='',
                                     score=100, lang=lang))
            return

        # If the file name matches the search regex, then just use the video
        # ID from the file name
        m = re.match(Prefs['regex'], basename)
        if m:
            groups = m.groupdict()
            video_query = groups['cf_studio'] + '-' + \
                self.process_name(groups['clip_name'])
            video_id = '-'.join(video_query.split())

            self.Log('SEARCH - Video ID: %s' % video_id)
            results.Append(
                MetadataSearchResult(id=video_id, name='',
                                     score=100, lang=lang))
        else:
            return

        # TODO: Implement proper search. But because their website is such a
        # giant PITA, for now just return.
        return

        search_terms = []
        for term in video_query.split():
            # avoid searching for short, common words
            if len(term) > 3:
                search_terms.append(term)
        score = 100

        while len(search_terms) > 2:
            search_query = "%20".join(search_terms)
            search_url = BASE_SEARCH_URL % search_query

            self.Log('SEARCH - Search URL: %s' % search_url)
            html = HTML.ElementFromURL(search_url, sleep=REQUEST_DELAY)
            search_results = html.xpath('//*[@id="main"]/div/div[1]/ul/li')

            for result in search_results:
                real_title = result.find('a').find('img').get('alt')
                self.Log('SEARCH - video title: %s' %
                         real_title)

                # Process the real title of the movie and compare it to what we
                # were originally searching for
                title = self.process_name(real_title)
                video_url = result.find('a').get('href')

                if title == processed_name:
                    self.Log('SEARCH - video url: %s' %
                             video_url)
                    self.rating = \
                        result.find('.//*[@class="current-rating"]'). \
                        text.strip('Currently ').strip('/5 Stars')

                    results.Append(
                        MetadataSearchResult(id=video_url, name=real_title,
                                             score=100, lang=lang))

                    return
                else:
                    self.Log('SEARCH - Title does not '
                             'match exactly but will be added to the results.')

                    results.Append(
                        MetadataSearchResult(id=video_url, name=real_title,
                                             score=1, lang=lang))

            # didn't find an exact match, so pop the first search term and
            # try again
            score = score - 10
            search_terms.pop(0)

    def get_html(self, url):
        # Since CF renders most of the website with JavaScript, I've
        # resorted to using Selenium. I'm not proud.
        self.Log("UPDATE - Starting PhantomJS")
        html = ''
        browser = webdriver.PhantomJS()
        try:
            browser.set_window_size(1920, 1080)
            self.Log("UPDATE - Loading %s" % url)
            browser.get(url)

            # we must agree to the terms and conditions!
            self.Log("UPDATE - Accepting TOS")
            agree = browser.find_element_by_id('agreeButton')
            agree.click()

            self.Log("UPDATE - Sleeping while movie page loads")
            sleep(5)
            html = tree.fromstring(browser.execute_script(
                "return document.getElementsByTagName('html')[0].innerHTML"))
        except:
            self.Log("UPDATE - Exception while running PhantomJS")
            raise
        finally:
            self.Log("UPDATE - Qutting PhantomJS")
            browser.quit()

        return html

    def fetch_gallery(self, html, metadata):
        # Get the posters and thumbs
        valid_image_names = list()
        i = 1
        video_image_list = html.xpath('//*[@id="stills"]/div/a/img')

        try:
            coverPrefs = int(Prefs['cover'])
        except ValueError:
            coverPrefs = None

        # self.Log('UPDATE - video_image_list: "%s"' % video_image_list)
        for image in video_image_list:
            if coverPrefs and i > coverPrefs:
                break

            thumb_url = 'https:' + image.get('src')
            poster_url = thumb_url.replace('Thumb', '')
            self.Log('UPDATE - thumb_url: "%s"' % thumb_url)
            self.Log('UPDATE - poster_url: "%s"' % poster_url)

            valid_image_names.append(poster_url)

            if poster_url not in metadata.posters:
                try:
                    i += 1
                    metadata.posters[poster_url] = \
                        Proxy.Preview(HTTP.Request(thumb_url), sort_order=i)
                except:
                    pass
        return valid_image_names

    def fetch_summary(self, html, metadata):
        raw_about_text = html.xpath('//*[@id="bootstrapModal"]/div/div/'
                                    'section/div[2]/div[4]/div[1]/article/'
                                    'p/text()')

        self.Log('UPDATE - About Text - RAW %s', raw_about_text)
        about_text = "\n".join(raw_about_text)
        metadata.summary = about_text

    def fetch_release_date(self, html, metadata):
        release_date = html.xpath('//*[@id="bootstrapModal"]/div/div/'
                                  'section/div[2]/div[3]/span/span[1]/'
                                  'text()')

        r = release_date[0].strip()
        self.Log('UPDATE - Release Date - New: %s' % r)
        metadata.originally_available_at = Datetime.ParseDate(r).date()
        metadata.year = metadata.originally_available_at.year

    def fetch_roles(self, html, metadata):
        actor_count = 0
        metadata.roles.clear()
        htmlcast = html.xpath('//*[@id="bootstrapModal"]/div/div/section/'
                              'div[2]/div[4]/div[1]/episode-actors/div[2]/'
                              'div[2]/div/span/text()')

        self.Log('UPDATE - cast: "%s"' % htmlcast)
        for cast in htmlcast:
            cname = cast.strip()
            if (len(cname) > 0):
                role = metadata.roles.new()
                role.name = cname
                actor_count += 1
        return actor_count

    def fetch_rating(self, html, metadata):
        metadata.rating = 0.0
        rating = html.xpath('//*[@id="bootstrapModal"]/div/div/section/div[2]/'
                            'div[3]/div[2]/span/text()')[0].replace('%', '')
        self.Log('UPDATE - rating HTML: "%s"' % rating)
        rating_scaled = float(rating) / 10.0

        self.Log('UPDATE - rating: "%f"' % rating_scaled)
        metadata.rating = float(rating_scaled)

    def fetch_genres(self, html, metadata, actor_count=0):
        metadata.genres.clear()
        if actor_count == 1:
            genres = ['solo']
        elif actor_count > 1:
            genres = ['bareback']
        else:
            genres = []

        self.Log('UPDATE - video_genres: "%s"' % genres)
        for genre in genres:
            genre = genre.strip()
            if (len(genre) > 0):
                metadata.genres.add(genre)

    def update(self, metadata, media, lang, force=False):
        self.Log('UPDATE CALLED')

        if media.items[0].parts[0].file is None:
            return

        file_path = media.items[0].parts[0].file
        self.Log('UPDATE - File Path: %s' % file_path)
        self.Log('UPDATE - metadata.id: %s' % metadata.id)

        # Get the document tree
        url = BASE_VIDEO_DETAILS_URL % metadata.id
        html = self.get_html(url)

        # Set tagline to URL
        metadata.tagline = metadata.id

        # Get the actual video title from the website
        video_title = html.xpath('//*[@id="bootstrapModal"]/div/div/section'
                                 '/div[2]/div[2]/h3/text()')[0]
        self.Log('UPDATE - video_title: "%s"' % video_title)

        # Try to get description text
        try:
            self.fetch_summary(html, metadata)
        except Exception as e:
            self.Log('UPDATE - Error getting summary: %s' % e)
            pass

        # Try to get release date
        try:
            self.fetch_release_date(html, metadata)
        except Exception as e:
            self.Log('UPDATE - Error getting release date: %s' % e)
            pass

        # Try to get and process the video cast
        actor_count = 0
        try:
            actor_count = self.fetch_roles(html, metadata)
        except Exception as e:
            self.Log('UPDATE - Error getting roles: %s' % e)
            pass

        # Try to get and process the video genres
        try:
            self.fetch_genres(html, metadata, actor_count)
        except Exception as e:
            self.Log('UPDATE - Error getting genres: %s' % e)
            pass

        # Try to get the site video rating
        try:
            self.fetch_rating(html, metadata)
        except Exception as e:
            self.Log('UPDATE - Error getting rating: %s' % e)
            pass

        valid_image_names = self.fetch_gallery(html, metadata)
        metadata.posters.validate_keys(valid_image_names)

        metadata.content_rating = 'X'
        metadata.title = video_title
        metadata.studio = "Corbin Fisher"

# LocalDotfile
import os
import simplejson as json
PLUGIN_LOG_TITLE = 'Local Dotfile'    # Log Title

VERSION_NO = '2016.04.10.1'

# Delay used when requesting HTML, may be good to have to prevent being banned
# from the site
REQUEST_DELAY = 0


def Start():
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows ' \
                                 'NT 6.2; Trident/4.0; SLCC2; .NET ' \
                                 'CLR 2.0.50727; .NET CLR 3.5.30729; ' \
                                 '.NET CLR 3.0.30729; Media Center PC 6.0)'


class LocalDotfile(Agent.Movies):
    name = 'Local Dotfile'
    languages = [Locale.Language.NoLanguage, Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.cockporn']

    def Log(self, message, *args):
        if Prefs['debug']:
            Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

    def search(self, results, media, lang, manual):
        self.Log('------------------------------------------------------------'
                 '-----------')
        self.Log('SEARCH CALLED v.%s', VERSION_NO)
        self.Log('SEARCH - media.title -  %s', media.title)
        self.Log('SEARCH - media.items[0].parts[0].file -  %s',
                 media.items[0].parts[0].file)
        self.Log('SEARCH - media.primary_metadata.title -  %s',
                 media.primary_metadata.title)
        self.Log('SEARCH - media.items -  %s', media.items)
        self.Log('SEARCH - media.filename -  %s', media.filename)
        self.Log('SEARCH - lang -  %s', lang)
        self.Log('SEARCH - manual -  %s', manual)

        if media.items[0].parts[0].file is not None:
            path_and_file = media.items[0].parts[0].file
            self.Log('SEARCH - File Path: %s' % path_and_file)
            filename = os.path.basename(path_and_file)
            dirname = os.path.dirname(path_and_file)

            metadata_file = os.path.join(dirname, '.' + filename + '.metadata')
            if os.path.isfile(metadata_file):
                self.Log('SEARCH - Exact Match "%s" == "%s"' %
                         (filename, metadata_file))
                results.Append(MetadataSearchResult(id=metadata_file,
                                                    name=filename,
                                                    score=100, lang=lang))
        return

    def update(self, metadata, media, lang, force=False):
        self.Log('UPDATE CALLED')

        if media.items[0].parts[0].file is not None:
            file_path = media.items[0].parts[0].file
            self.Log('UPDATE - File Path: %s' % file_path)
            self.Log('UPDATE - metadata.id: %s' % metadata.id)

            metadata_dict = json.loads(Data.Load(metadata.id))

            # Set tagline to URL
            metadata.tagline = metadata_dict["description_url"]
            video_title = metadata_dict["title"]

            self.Log('UPDATE - video_title: "%s"' % video_title)

            # Update thumbnail and cover data
            valid_image_names = []
            i = 0
            self.Log("UPDATE - video_image_list")
            try:
                coverPrefs = int(Prefs['cover'])
            except ValueError:
                coverPrefs = None

            try:
                for thumb_url, poster_url in \
                        metadata_dict["posters"].iteritems():
                    if coverPrefs and i > coverPrefs:
                        break
                    self.Log('UPDATE - thumb_url: "%s"' % thumb_url)
                    self.Log('UPDATE - poster_url: "%s"' % poster_url)
                    valid_image_names.append(poster_url)
                    if poster_url not in metadata.posters:
                        try:
                            i += 1
                            metadata.posters[poster_url] = \
                                Proxy.Preview(HTTP.Request(thumb_url),
                                              sort_order=i)
                        except:
                            pass
                metadata.posters.validate_keys(valid_image_names)
            except Exception as e:
                self.Log('UPDATE - Error getting posters: %s' % e)
                pass

            # Try to get description text
            about_text = metadata_dict["description"]
            self.Log('UPDATE - About Text: %s', about_text)
            metadata.summary = about_text

            # Try to get release date
            # TODO: Release Date?

            # Try to get and process the video cast
            metadata.roles.clear()
            if "actor" in metadata_dict["roles"]:
                actors = metadata_dict["roles"]["actor"]
                self.Log('UPDATE - cast: "%s"' % actors)
                for actor in actors:
                    actor = actor.strip()
                    if (len(actor) > 0):
                        role = metadata.roles.new()
                        role.name = actor

            # Try to get and process the video genres
            metadata.genres.clear()
            genres = metadata_dict["categories"]
            self.Log('UPDATE - video_genres: "%s"' % genres)
            for genre in genres:
                genre = genre.strip()
                if (len(genre) > 0):
                    metadata.genres.add(genre)

            metadata.rating = metadata_dict["user_rating"]
            metadata.content_rating = metadata_dict["content_rating"]
            metadata.title = video_title
            metadata.studio = "Bel Ami"

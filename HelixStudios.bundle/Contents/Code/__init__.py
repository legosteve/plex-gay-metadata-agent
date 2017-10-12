# HelixStudios
import re, os, platform, urllib
from difflib import SequenceMatcher

PLUGIN_LOG_TITLE = 'Helix Studios'	# Log Title

VERSION_NO = '2017.07.26.0'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.helixstudios.net%s'

# Example Video Details URL
# https://www.helixstudios.net/video/3437/hosing-him-down.html
BASE_VIDEO_DETAILS_URL = 'https://www.helixstudios.net/video/%s'

# Example Search URL:
# https://www.helixstudios.net/videos/?q=Hosing+Him+Down
BASE_SEARCH_URL = 'https://www.helixstudios.net/videos/?q=%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

# Example File Name:
# https://media.helixstudios.com/scenes/hx111_scene2/hx111_scene2_member_1080p.mp4
# FILENAME_PATTERN = re.compile("")
# TITLE_PATTERN = re.compile("")

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class HelixStudios(Agent.Movies):
	name = 'Helix Studios'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def intTest(self, s):
		try:
			int(s)
			return int(s)
		except ValueError:
			return False

	def similar(self, a, b):
		return SequenceMatcher(None, a, b).ratio()

	def search(self, results, media, lang, manual):
		self.Log('-----------------------------------------------------------------------')
		self.Log('SEARCH CALLED v.%s', VERSION_NO)
		self.Log('SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.Log('SEARCH - media.title - %s', media.title)
		self.Log('SEARCH - media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
		self.Log('SEARCH - media.primary_metadata.title - %s', media.primary_metadata.title)
		self.Log('SEARCH - media.items - %s', media.items)
		self.Log('SEARCH - media.filename - %s', media.filename)
		self.Log('SEARCH - lang - %s', lang)
		self.Log('SEARCH - manual - %s', manual)
		self.Log('SEARCH - Prefs->cover - %s', Prefs['cover'])
		self.Log('SEARCH - Prefs->folders - %s', Prefs['folders'])
		self.Log('SEARCH - Prefs->regex - %s', Prefs['regex'])

		if not media.items[0].parts[0].file:
			return

		path_and_file = media.items[0].parts[0].file.lower()
		self.Log('SEARCH - File Path: %s', path_and_file)

		(file_dir, basename) = os.path.split(os.path.splitext(path_and_file)[0])
		final_dir = os.path.split(file_dir)[1]

		self.Log('SEARCH - Enclosing Folder: %s', final_dir)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if final_dir not in folder_list:
				self.Log('SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', basename, final_dir, ','.join(folder_list))
				return

		m = file_name_pattern.search(basename)
		if not m:
			self.Log('SEARCH - Skipping %s because the file name is not in the expected format.', basename)
			return

		self.Log('SEARCH - File Name: %s', basename)

		groups = m.groupdict()
		movie_url_name = re.sub('\s+', '+', groups['clip_name'])
		movie_url = BASE_SEARCH_URL + movie_url_name
		search_query_raw = list()
		for piece in groups['clip_name'].split(' '):
			if re.search('^[0-9A-Za-z]*$', piece.replace('!', '')) is not None:
				search_query_raw.append(piece)

		self.Log('SEARCH - Video URL: %s', movie_url)
		html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)

		search_results = html.xpath('//*[@class="video-gallery"]/li')

		score=10
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		if search_results:
			for result in search_results:
				video_title = result.find('a').find("img").get("alt")
				video_title = re.sub("[\:\?\|]", '', video_title)
				video_title = re.sub("\s{2,4}", ' ', video_title)
				video_title = video_title.rstrip(' ')

				self.Log('SEARCH - video title percentage: %s', self.similar(video_title.lower(), basename.lower()))

				self.Log('SEARCH - video title: %s', video_title)
				# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
				#if video_title.lower() == basename.lower():
				if self.similar(video_title.lower(), basename.lower()) > 0.90:
					video_url=result.find('a').get('href')
					self.Log('SEARCH - video url: %s', video_url)
					self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
					self.Log('SEARCH - rating: %s', self.rating)
					self.Log('SEARCH - Exact Match "' + basename.lower() + '" == "%s"', video_title.lower())
					results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
					return
				else:
					self.Log('SEARCH - Title not found "' + basename.lower() + '" != "%s"', video_title.lower())
					score=score-1
					results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
		else:
			search_query="+".join(search_query_raw[-2:])
			self.Log('SEARCH - Search Query: %s', search_query)
			html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
			search_results=html.xpath('//*[@class="video-gallery"]/li')
			if search_results:
				for result in search_results:
					video_title = result.find('a').find("img").get("alt")
					video_title = re.sub("[\:\?\|]", '', video_title)
					video_title = video_title.rstrip(' ')
					self.Log('SEARCH - video title: %s', video_title)
					if video_title.lower() == basename.lower():
						video_url=result.find('a').get('href')
						self.Log('SEARCH - video url: %s', video_url)
						self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
						self.Log('SEARCH - rating: %s', self.rating)
						self.Log('SEARCH - Exact Match "' + basename.lower() + '" == "%s"', video_title.lower())
						results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
						return
					else:
						self.Log('SEARCH - Title not found "' + basename.lower() + '" != "%s"', video_title.lower())
						score=score-1
						results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
			else:
				search_query="+".join(search_query_raw[:2])
				self.Log('SEARCH - Search Query: %s', search_query)
				html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
				search_results=html.xpath('//*[@class="video-gallery"]/li')
				if search_results:
					for result in search_results:
						video_title=result.find('a').find("img").get("alt")
						video_title = re.sub("[\:\?\|]", '', video_title)
						video_title = video_title.rstrip(' ')
						self.Log('SEARCH - video title: %s', video_title)
						if video_title.lower() == basename.lower():
							video_url=result.find('a').get('href')
							self.Log('SEARCH - video url: %s', video_url)
							self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
							self.Log('SEARCH - rating: %s', self.rating)
							self.Log('SEARCH - Exact Match "' + basename.lower() + '" == "%s"', video_title.lower())
							results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
							return
						else:
							self.Log('SEARCH - Title not found "' + basename.lower() + '" != "%s"', video_title.lower())
							results.Append(MetadataSearchResult(id = '', name = media.filename, score = 1, lang = lang))
				else:
					score=1
					self.Log('SEARCH - Title not found "' + basename.lower() + '" != "%s"', video_title.lower())
					return

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)
		url = BASE_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url

		video_title = html.xpath('//div[@class="scene-title"]/span/text()')[0]
		self.Log('UPDATE - video_title: "%s"', video_title)

		# External 	https://cdn.helixstudios.com/img/300h/media/stills/hx109_scene52_001.jpg
		# Member 	https://cdn.helixstudios.com/img/250w/media/stills/hx109_scene52_001.jpg
		valid_image_names = list()
		i = 0
		video_image_list = html.xpath('//*[@id="scene-just-gallery"]/a/img')
		# self.Log('UPDATE - video_image_list: "%s"', video_image_list)
		try:
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i <= (self.intTest(coverPrefs)-1) or coverPrefs == "all available":
					i = i + 1
					thumb_url = image.get('src')
					poster_url = thumb_url.replace('300h', '1920w')
					valid_image_names.append(poster_url)
					if poster_url not in metadata.posters:
						try:
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except: pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		# Try to get description text
		try:
			raw_about_text=html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr/td/p')
			self.Log('UPDATE - About Text - RAW %s', raw_about_text)
			about_text=' '.join(str(x.text_content().strip()) for x in raw_about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		# Try to get release date
		try:
			release_date=html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[1]/td[1]/text()')[1].strip()
			self.Log('UPDATE - Release Date - New: %s', release_date)
			metadata.originally_available_at = Datetime.ParseDate(release_date).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video cast
		try:
			metadata.roles.clear()
			htmlcast = html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[3]/td/a/text()')
			self.Log('UPDATE - cast: "%s"', htmlcast)
			for cast in htmlcast:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
		except Exception as e:
			self.Log('UPDATE - Error getting video cast: %s', e)
			pass

		# Try to get and process the video genres
		try:
			metadata.genres.clear()
			genres = html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[4]/td/a/text()')
			self.Log('UPDATE - video_genres: "%s"', genres)
			for genre in genres:
				genre = genre.strip()
				if (len(genre) > 0):
					metadata.genres.add(genre)
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s', e)
			pass

		metadata.posters.validate_keys(valid_image_names)
		metadata.rating = float(self.rating)*2

		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "Helix Studios"

# Staxus
import re, os, platform, urllib, cgi
PLUGIN_LOG_TITLE='Staxus'	# Log Title

VERSION_NO = '2017.07.26.0'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='http://staxus.com%s'

# Example Video Details URL
# http://staxus.com/trial/gallery.php?id=4044
BASE_VIDEO_DETAILS_URL='http://staxus.com/trial/%s'

# Example Search URL:
# http://staxus.com/trial/search.php?query=Staxus+Classic%3A+BB+Skate+Rave+-+Scene+1+-+Remastered+in+HD
BASE_SEARCH_URL='http://staxus.com/trial/search.php?st=advanced&qall=%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class Staxus(Agent.Movies):
	name = 'Staxus'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

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

		enclosing_directory, file_name = os.path.split(os.path.splitext(path_and_file)[0])
		enclosing_directory, enclosing_folder = os.path.split(enclosing_directory)

		self.Log('SEARCH - Enclosing Folder: %s', enclosing_folder)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if final_dir not in folder_list:
				self.Log('SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', basename, final_dir, ','.join(folder_list))
				return

		m = file_name_pattern.search(basename)
		if not m:
			self.Log('SEARCH - Skipping %s because the file name is not in the expected format.', basename)
			return

		self.Log('SEARCH - File Name: %s', file_name)
		self.Log('SEARCH - Split File Name: %s', file_name.split(' '))

		remove_words = file_name.lower() #Sets string to lower.
		remove_words = remove_words.replace('staxus', '') #Removes word.
		remove_words = re.sub('\(([^\)]+)\)', '', remove_words) #Removes anything inside of () and the () themselves.
		remove_words = remove_words.lstrip(' ') #Removes white spaces on the left end.
		remove_words = remove_words.rstrip(' ') #Removes white spaces on the right end.
		search_query_raw = list()
		# Process the split filename to remove words with special characters. This is to attempt to find a match with the limited search function(doesn't process any non-alphanumeric characters correctly)
		for piece in remove_words.split(' '):
			search_query_raw.append(cgi.escape(piece))
		search_query="%2C+".join(search_query_raw)
		self.Log('SEARCH - Search Query: %s', search_query)
		html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
		search_results=html.xpath('//*[@class="item"]')
		score=10
		self.Log('SEARCH - results size: %s', len(search_results))
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		for result in search_results:
			#result=result.find('')
			video_title=result.findall("div/a/img")[0].get("alt")
			video_title = video_title.lstrip(' ') #Removes white spaces on the left end.
			video_title = video_title.rstrip(' ') #Removes white spaces on the right end.
			self.Log('SEARCH - video title: %s', video_title)
			# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
			if video_title.lower().replace(':','') == file_name.lower():
				video_url=result.findall("div/a")[0].get('href')
				self.Log('SEARCH - video url: %s', video_url)
				image_url=result.findall("div/a/img")[0].get("src")
				self.Log('SEARCH - image url: %s', image_url)
				self.Log('SEARCH - Exact Match "' + file_name.lower() + '" == "%s"' % video_title.lower())
				results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			else:
				self.Log('SEARCH - Title not found "' + file_name.lower() + '" != "%s"' % video_title.lower())
				score=score-1
				results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.Log('UPDATE - File Path: %s', file_path)
		self.Log('UPDATE - Video URL: %s', metadata.id)
		url = BASE_VIDEO_DETAILS_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url

		video_title = html.xpath('//div[@class="sidebar right sidebar-models"]/h2/text()')[0]
		self.Log('UPDATE - video_title: "%s"' % video_title)

		valid_image_names = list()
		i = 0
		video_image_list = html.xpath('//*[@class="reset collection-images"]/li/a/img')
		try:
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i != coverPrefs or coverPrefs == "all available":
					thumb_url = image.get('src')
					#self.Log('UPDATE - thumb_url: "%s"' % thumb_url)
					poster_url = thumb_url.replace('300h', '1920w')
					#self.Log('UPDATE - poster_url: "%s"' % poster_url)
					valid_image_names.append(poster_url)
					if poster_url not in metadata.posters:
						try:
							i += 1
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except: pass
		except Exception as e:
			self.Log('UPDATE - Error getting posters: %s', e)
			pass

		# Try to get description text.
		try:
			raw_about_text=html.xpath('//div[@class="col-main"]/p')
			self.Log('UPDATE - About Text - RAW %s', raw_about_text)
			about_text=' '.join(str(x.text_content().strip()) for x in raw_about_text)
			metadata.summary=about_text
		except Exception as e:
			self.Log('UPDATE - Error getting description text: %s', e)
			pass

		# Try to get release date.
		try:
			rd=html.xpath('//div[@class="sidebar right sidebar-models"]/p[1]/span/text()')[0]
			rd = rd.split('/')
			rd = [rd[i] for i in [1,0,2]]
			rd[1] = rd[1] + ', '
			rd[0] = rd[0] + " "
			rd=''.join(rd)
			self.Log('UPDATE - Release Date: %s', rd)
			metadata.originally_available_at = Datetime.ParseDate(rd).date()
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.Log('UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video cast.
		try:
			metadata.roles.clear()
			htmlcast = html.xpath('//div[@class="sidebar right sidebar-models"]/p[4]/a/text()')
			self.Log('UPDATE - cast: "%s"' % htmlcast)
			for cast in htmlcast:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
		except Exception as e:
			self.Log('UPDATE - Error getting video cast: %s', e)
			pass

		# Try to get and process the video genres.
		try:
			metadata.genres.clear()
			genres = html.xpath('//div[@class="sidebar right sidebar-models"]/p[3]/span/a/text()')
			self.Log('UPDATE - video_genres: "%s"' % genres)
			for genre in genres:
				genre = genre.strip()
				if (len(genre) > 0):
					metadata.genres.add(genre)
		except Exception as e:
			self.Log('UPDATE - Error getting video genres: %s', e)
			pass

		# Try to get and process the ratings.
		try:
			rating = html.xpath('//div[@class="col-md-4 col-xs-12 stats-single"]/b/text()')[0].strip()
			rating_count = html.xpath('//div[@class="col-md-4 col-xs-12 stats-single"]//strong/text()')[0]
			rating_count = rating_count.replace('(Total votes: ', '')
			rating_count = rating_count.replace(')', '')
			self.Log('UPDATE - video_rating: "%s"', rating)
			self.Log('UPDATE - video_rating_count: "%s"', rating_count)
			metadata.rating = float(rating)*2
			metadata.rating_count = int(rating_count)
		except Exception as e:
			self.Log('UPDATE - Error getting rating: %s', e)
			pass

		metadata.posters.validate_keys(valid_image_names)

		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = "Staxus"

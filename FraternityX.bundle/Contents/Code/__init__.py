# FraternityX
import re, os, platform, urllib, cgi

PLUGIN_LOG_TITLE='FraternityX'	# Log Title

VERSION_NO = '2018.10.17.0'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='https://fraternityx.com/episode/%s'
BASE_SEARCH_URL='https://www.google.com/search?q=site%%3Afraternityx.com+%s'

# File names to match for this agent
movie_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = 0
	HTTP.Headers['Cookie'] = 'pp-accepted=true' #Bypasses the age verification screen
	HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:62.0) Gecko/20100101 Firefox/62.0'

class FraternityX(Agent.Movies):
	name = 'Fraternity X'
	languages = [Locale.Language.English]
	primary_provider = False
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def search(self, results, media, lang):
	  self.Log('-----------------------------------------------------------------------')
	  self.Log('SEARCH CALLED v.%s', VERSION_NO)
	  self.Log('SEARCH - Platform: %s %s', platform.system(), platform.release())
	  self.Log('SEARCH - results - %s', results)
	  self.Log('SEARCH - media.title - %s', media.title)
	  self.Log('SEARCH - media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
	  self.Log('SEARCH - media.filename - %s', media.filename)
	  self.Log('SEARCH - %s', results)

	  if not media.items[0].parts[0].file:
	    return

	  path_and_file = media.items[0].parts[0].file
	  self.Log('SEARCH - File Path: %s', path_and_file)

	  path_and_file = os.path.splitext(path_and_file)[0]
	  (file_dir, basename) = os.path.split(os.path.splitext(path_and_file)[0])
	  final_dir = os.path.split(file_dir)[1]
	  file_name = basename #Sets string to lower.
	  self.Log('SEARCH - File Name: %s', file_name)

	  self.Log('SEARCH - Enclosing Folder: %s', final_dir)

	  if Prefs['folders'] != "*":
	    folder_list = re.split(',\s*', Prefs['folders'])
	    if final_dir not in folder_list:
	      self.Log('SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', file_name, final_dir, ','.join(folder_list))
	      return

	  m = movie_pattern.search(file_name)
	  if not m:
	    self.Log('SEARCH - Skipping %s because the file name is not in the expected format.', file_name)
	    return

	  clean_file_name = re.sub('[^A-Za-z0-9]+', ' ', file_name)
	  self.Log('SEARCH - Clean title: %s', clean_file_name)

	  groups = m.groupdict()

	  search_query_raw = list()
	  clip_name = groups['clip_name']
	  self.Log('SEARCH - Clip name: %s', clip_name)
	  for piece in clip_name.split(' '):
	      search_query_raw.append(cgi.escape(piece))

	  search_query="+".join(search_query_raw)
	  search_query=str.lower(search_query)
	  self.Log('SEARCH - Search Query: %s', search_query)
	  html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
	  score=10
	  search_results=html.xpath('//*[@class="srg"]/*[@class="g"][1]')
	  self.Log('SEARCH - Results: %s', len(search_results))

	  if len(search_results) > 0:
	    self.Log('SEARCH - results size exact match: %s', len(search_results))
	    for result in search_results:
	      video_title = result.xpath('//*[@class="srg"]/*[@class="g"]//h3/text()')[0]
	      video_url = result.xpath('//*[@class="srg"]/*[@class="g"]//a/@href')[0]
	      self.Log('SEARCH - Exact video title: %s', video_title)
	      self.Log('SEARCH - Exact video URL: %s', video_url)
	      results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 98, lang = lang))
	      return
	  else:
	    self.Log('SEARCH - Results size: %s', len(search_results))
	    for result in search_results:
	      video_title = result.findall('//*[@class="srg"]/*[@class="g"]//h3/text()')
	      video_title = video_title.lstrip(' ') #Removes white spaces on the left end.
	      video_title = video_title.rstrip(' ') #Removes white spaces on the right end.
	      video_title = video_title.replace(':', '')
	      self.Log('SEARCH - Video title: %s', video_title)
	    return

	def fetch_title(self, html, metadata):
	  self.Log('UPDATE: fetch_title CALLED')
	  try:
	    video_title=html.xpath('//*[@class="episode-description"]/h1/text()')[0]
	    self.Log('UPDATE - Summary: %s', video_title)
	    metadata.title = video_title
	  except Exception as e:
	    self.Log('UPDATE - Error getting title text: %s', e)
	    pass

	def fetch_date(self, html, metadata):
	  self.Log('UPDATE: fetch_date CALLED')
	  try:
	    release_date = html.xpath('substring-before(//*[@class="episode-description"]/p/text(), " - ")')
	    self.Log('UPDATE - Release Date: %s' % release_date)
	    #date_original = datetime.datetime.strptime(release_date, '%Y-%m-%d').strftime('%b %-d, %Y')
	    date_original = Datetime.ParseDate(release_date).date()
	    self.Log('UPDATE - Reformatted Release Date: %s' % date_original)
	    metadata.originally_available_at = date_original
	    metadata.year = metadata.originally_available_at.year
	  except Exception as e:
	    self.Log('UPDATE - Error getting release date: %s', e)
	    pass

	def fetch_summary(self, html, metadata):
	  self.Log('UPDATE: fetch_summary CALLED')
	  try:
	    video_summary=html.xpath('substring-after(//*[@class="episode-description"]/p/text(), " - ")')
	    self.Log('UPDATE - Summary: %s', video_summary)
	    metadata.summary = video_summary
	  except Exception as e:
	    self.Log('UPDATE - Error getting description text: %s', e)
	    pass

	def fetch_images(self, html, metadata):
	  self.Log('UPDATE: fetch_images CALLED')
	  i = 0

	  try:
	    coverPrefs = int(Prefs['cover'])
	  except ValueError:
	    # an absurdly high number means "download all the things"
	    coverPrefs = 10000

	  valid_image_names = []

	  images = html.xpath('//*[@class="episode--gallery"]//img/@src')
	  self.Log('UPDATE - Image URLs: "%s"' % images)

	  for image in images:
	    image = image.strip()
	    image = 'https://fraternityx.com' + image
	    if (len(image) > 0):
	      valid_image_names.append(image)
	      if image not in metadata.posters:
	        try:
	          i += 1
	          metadata.posters[image] = Proxy.Preview(HTTP.Request(image), sort_order=i)
	        except:
	          pass

	  return valid_image_names

	def update(self, metadata, media, lang):
	  self.Log('UPDATE CALLED')

	  enclosing_directory, file_name = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
	  file_name = file_name.lower()

	  if not media.items[0].parts[0].file:
	    return

	  file_path = media.items[0].parts[0].file
	  self.Log('UPDATE - File Path: %s', file_path)
	  self.Log('UPDATE - Video URL: %s', metadata.id)
	  url = metadata.id

	  # Fetch HTML
	  html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

	  # Set tagline to URL
	  metadata.tagline = url

	  # Set additional metadata
	  metadata.content_rating = 'X'
	  metadata.studio = "FraternityX"

	  # Try to get the title
	  try:
			self.fetch_title(html, metadata)
	  except:
	  	pass

	  # Try to get the release date
	  try:
	    self.fetch_date(html, metadata)
	  except:
	    pass

	  # Try to get the summary
	  try:
	    self.fetch_summary(html, metadata)
	  except:
	    pass

	  # Try to get the video images
	  try:
	    self.fetch_images(html, metadata)
	  except:
	    pass
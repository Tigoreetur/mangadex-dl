#!/usr/bin/env python3
import time, os, sys, re, json, html
import threading
import requests
import validators

A_VERSION = "0.2.8"

file_save_location = os.getcwd(), "download"
# file_save_location = os.getcwd(), "download" #default save location
failed_chapters = []
all_chapters = []
nr_of_dls = 0

def pad_filename(x):
	digits = re.compile('(\\d+)')
	pos = digits.search(x)
	if pos:
		return x[1:pos.start()] + pos.group(1).zfill(3) + x[pos.end():]
	else:
		return x

def float_conversion(x):
	try:
		x = float(x)
	except ValueError: # empty string for oneshot
		x = 0
	return x

def zpad(num):
	if "." in num:
		parts = num.split('.')
		return "{}.{}".format(parts[0].zfill(3), parts[1])
	else:
		return num.zfill(3)

def dl(manga_id, lang_code, chap_i):
	# grab manga info json from api v2
	try:
		r1 = requests.get("https://mangadex.org/api/v2/manga/{}/".format(manga_id))
		try:
			title = json.loads(r1.text)["data"]["title"]
		except:
			print("Please enter a MangaDex URL.")
			exit(1)
		print("\nTitle: {}".format(html.unescape(title)))
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("1 Error: {}".format(err))
		exit("1 Error: {}".format(err))

	try:
		r2 = requests.get("https://mangadex.org/api/v2/manga/{}/chapters".format(manga_id))
		manga = json.loads(r2.text)["data"]["chapters"]
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("2 Error: {}".format(err))
		exit("2 Error: {}".format(err))

	# check for all chapters in your language
	chapters = []
	for i in range(len(manga)):
		if manga[i]["language"] == lang_code:
			chapters.append(manga[i]["chapter"])
	chapters.sort(key=float_conversion) # sort numerically by chapter #

	chapters_revised = ["Oneshot" if x == "" else x for x in chapters]

	# Find all duplicates
	dupl_s = set()
	for i in chapters_revised:
		if chapters_revised.count(i) > 1:
			dupl_s.add(i)
	dupl = list(dupl_s)
	dupl.sort(key=float_conversion)

	# print downloadable chapters
	if len(chapters) == 0:
		print("No chapters available to download!")
		exit("No chapters available to download!")
	elif len(dupl) != 0:
		print("Available chapters:")
		print(" " + ', '.join(map(str, chapters_revised)))
		print("Duplictes found")
		print(" " + ', '.join(map(str, dupl)))
	else:
		print("Available chapters:")
		print(" " + ', '.join(map(str, chapters_revised)))

	# get which chapters to download
	requested_chapters = []
	req_chap_input = input("\nEnter chapter(s) to download: ").strip()
	if req_chap_input == "all" or req_chap_input == "a":
		requested_chapters.extend(chapters)		# download all chapters
	else:
		req_chap_input = [s for s in req_chap_input.split(',')]
		for s in req_chap_input:
			s = s.strip()
			s = s.replace("f", chapters[0])
			s = s.replace("first", chapters[0])
			s = s.replace("l", chapters[-1])
			s = s.replace("last", chapters[-1])
			s = s.replace("i", chap_i)
			s = s.replace("input", chap_i)
			if "-" in s:
				split = s.split('-')
				lower_bound = split[0]
				upper_bound = split[1]
				try:
					lower_bound_i = chapters.index(lower_bound)
				except ValueError:
					print("Chapter {} does not exist. Skipping {}.".format(lower_bound, s))
					continue # go to next iteration of loop
				try:
					upper_bound_i = chapters.index(upper_bound)
				except ValueError:
					print("Chapter {} does not exist. Skipping {}.".format(upper_bound, s))
					continue
				s = chapters[lower_bound_i:upper_bound_i+1]
			else:
				try:
					s = [chapters[chapters.index(s)]]
				except ValueError:
					print("Chapter {} does not exist. Skipping.".format(s))
					continue
			requested_chapters.extend(s)
	if requested_chapters == []:
		exit()

	# find out which are availble to dl
	chaps_to_dl = []
	for chapter_id in range(len(manga)):
		chapter_num = None
		try:
			chapter_num = str(float(manga[str(chapter_id)]["chapter"])).replace(".0", "")
		except:
			chapter_num = str(manga[chapter_id]["chapter"])
		chapter_group = manga[chapter_id]["groups"]
		if chapter_num in requested_chapters and manga[chapter_id]["language"] == lang_code:
			chaps_to_dl.append((str(chapter_num), manga[chapter_id]["id"], chapter_group))
	chaps_to_dl.sort(key = lambda x: float(x[0]))

	# get chapter(s) json
	print()
	for chapter_id in chaps_to_dl:
		download_chapters(chapter_id, title)

	finish(title)
def download_chapters(chapter_id, title):
	# get chapter(s) json
	print("Downloading chapter {}...".format(chapter_id[0]))
	while True:
		r = requests.get("https://mangadex.org/api/v2/chapter/{}/".format(chapter_id[1]))
		if r.status_code == 200:
			break
	chapter = json.loads(r.text)["data"]

	# get url list
	images = []
	server = chapter["server"]
	if "mangadex." not in server:
		server = "https://mangadex.org{}".format(server)
	hashcode = chapter["hash"]
	for page in chapter["pages"]:
		images.append("{}{}/{}".format(server, hashcode, page))

	groupname = re.sub('[/<>:"/\\|?*]', '-', chapter["groups"][0]["name"])
	title = re.sub('[/<>:"/\\|?*]', '-', title)
	title = "M " + title
	dest_folder = os.path.join(file_save_location, title)
	loc = ("c{} [{}]".format(zpad(chapter_id[0]), groupname))
	# download images
	for pagenum, url in enumerate(images, 1):

		if not os.path.exists(dest_folder):
			os.makedirs(dest_folder)
		while nr_of_dls > 45:
			time.sleep(0.1)
		trdp = threading.Thread(target=page_download, args=(pagenum, url, dest_folder, loc, chapter_id))
		trdp.start()
	while nr_of_dls > 15:
		time.sleep(0.1)
		


def page_download(pagenum, url, dest_folder, loc, chapter_id):
	global all_chapters
	#global requests
	global nr_of_dls
	nr_of_dls += 1
	filename = os.path.basename(url)
	ext = os.path.splitext(filename)[1]
	dest_filename = pad_filename("{}{}".format(pagenum, ext))
	dest_filename = loc +" "+ dest_filename
	outfile = os.path.join(dest_folder, dest_filename)
	all_chapters.append(outfile)
	fail_count = 0
	while True:
		try:
			r = requests.get(url, timeout=5)
			if r.status_code == 200:
				with open(outfile, 'wb') as f:
					f.write(r.content)
					nr_of_dls -= 1
					break
			else:
				print("Encountered Error {} when downloading.".format(r.status_code))
				fail_count += 1
				time.sleep(3)
				if  fail_count > 6:
					nr_of_dls -= 1
					break
		except:
			print("Download failed.")
			fail_count += 1
			time.sleep(3)
			if  fail_count > 6:
				nr_of_dls -= 1
				break
	print(" Downloaded chapter {} page {}.	  Nr of current downloads {}.".format(chapter_id[0], pagenum, nr_of_dls))

def finish(title):
	global all_chapters
	global failed_chapters
	time.sleep(2)
	while nr_of_dls > 0:
		time.sleep(0.1)
	print("Downloading done!")

	for x in all_chapters:
		try:
			f = open(x)
			f.close()
		except:
			failed_chapters.append(x)
	if failed_chapters != []:
		print(failed_chapters)
	failed_chapters = []
	all_chapters = []

	path = os.path.join(file_save_location, "!Manga.url")
	shortcut = open(path, 'w')
	shortcut.write('[InternetShortcut]\n')
	shortcut.write('URL=%s' % manga_url)
	shortcut.close()

	
def chap_id_to_manga(url, manga_id):
	#global requests
	if "mangadex.org/chapter" in url:
		r = requests.get("https://mangadex.org/api/v2/chapter/{}".format(manga_id))
		manga = json.loads(r.text)["data"]
		chap_i = manga["chapter"]
		print("Input chapter "+chap_i+".")
		return(manga["mangaId"], chap_i)
	else:
		return(manga_id)

if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	if len(sys.argv) > 1:
		lang_code = sys.argv[1]
	else:
		lang_code = "gb"
	
	chap_i = ""
	url = ""
	while url == "":
		url = input("Enter manga URL: ").strip()
		if url == "exit" or url == "quit" or url == "q":
			quit()
		if not validators.url(url):
			url = ""
			print("Invalid url.")
	manga_url = url
	try:
		print()
		manga_id = re.search("[0-9]+", url).group(0)
		try:
			manga_id, chap_i = chap_id_to_manga(url, manga_id)
		except:
			pass
	except:
		print("Error with URL.")

	dl(manga_id, lang_code, chap_i)
#!/usr/bin/env python3
import cloudscraper
import time, os, sys, re, json, html

A_VERSION = "0.2.7"

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

def dl(manga_id, lang_code):
	# grab manga info json from api
	scraper = cloudscraper.create_scraper()
	try:
		r1 = scraper.get("https://mangadex.org/api/v2/manga/{}/".format(manga_id))
		try:
			title = json.loads(r1.text)["data"]["title"]
		except:
			print("Please enter a MangaDex manga (not chapter) URL.")
			exit(1)
		print("\nTitle: {}".format(html.unescape(title)))
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("Error: {}".format(err))
		exit(1)

	try:
		r2 = scraper.get("https://mangadex.org/api/v2/manga/{}/chapters".format(manga_id))
		manga = json.loads(r2.text)["data"]["chapters"]
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("Error: {}".format(err))
		exit(2)

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
	req_chap_input = [s for s in req_chap_input.split(',')]
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
	chapter_num = None
	for chapter_id in range(len(manga)):
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
		print("Downloading chapter {}...".format(chapter_id[0]))
		while True:
			r = scraper.get("https://mangadex.org/api/v2/chapter/{}/".format(chapter_id[1]))
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

		# download images
		groupname = re.sub('[/<>:"/\\|?*]', '-', chapter["groups"][0]["name"])
		for pagenum, url in enumerate(images, 1):
			filename = os.path.basename(url)
			ext = os.path.splitext(filename)[1]

			title = re.sub('[/<>:"/\\|?*]', '-', title)
			dest_folder = os.path.join(os.getcwd(), "download", title, "c{} [{}]".format(zpad(chapter_id[0]), groupname))
			if not os.path.exists(dest_folder):
				os.makedirs(dest_folder)
			dest_filename = pad_filename("{}{}".format(pagenum, ext))
			outfile = os.path.join(dest_folder, dest_filename)

			r = scraper.get(url)
			if r.status_code == 200:
				with open(outfile, 'wb') as f:
					f.write(r.content)
			else:
				print("Encountered Error {} when downloading.".format(r.status_code))

			print(" Downloaded page {}.".format(pagenum))
			#time.sleep(1)

	print("Done!")

if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	if len(sys.argv) > 1:
		lang_code = sys.argv[1]
	else:
		lang_code = "gb"

	url = ""
	while url == "":
		url = input("Enter manga URL: ").strip()
	try:
		manga_id = re.search("[0-9]+", url).group(0)
		split_url = url.split("/")
	except:
		print("Error with URL.")

	dl(manga_id, lang_code)
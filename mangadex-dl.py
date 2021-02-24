#!/usr/bin/env python3
import time
import os
import json
import threading
import requests
import validators
import argparse

version = "0.2.9"

file_save_location = os.path.expanduser("~//Desktop")
# file_save_location = os.getcwd(), "download" #default save location
maximum_number_of_concurrent_downloads = 30
chapters_max_len = 0
maximum_number_of_concurrent_downloads_len = len(str(abs(
    maximum_number_of_concurrent_downloads)))
failed_chapters = []
all_downloaded_chapters = []
nr_of_dls = 0
dot_chr = False


def float_conversion(i):
    '''
    converts value to float
    '''
    try:
        return float(i)
    except ValueError:  # empty string for oneshot
        return 0


def zpad(i):
    '''
    pads filenames with zeroes using zfill
    '''
    global chapters_max_len
    global dot_chr
    j = str(i)
    if dot_chr:
        if "." in j:
            parts = j.split('.')
            return "{}.{}".format(parts[0].zfill(chapters_max_len), parts[1])
        else:
            return "{}.0".format(j.zfill(chapters_max_len))

    else:
        return j.zfill(chapters_max_len)


def valid_file_chr(i):
    '''
    create valid filenames
    '''
    for ch in ["\\", "/", ":", "*", '\"', "?", "!", "<", ">", "|"]:
        if ch in i:
            i = i.replace(ch, "-")
    return i


def main():
    '''
    main funtion
    '''
    global dot_chr
    global chapters_max_len
    print("mangadex-dl v{}".format(version))

    # create parser object
    pr = argparse.ArgumentParser(description="Mangadex chapter downloader.")

    # defining arguments for parser object
    pr.add_argument("-l", "--lang", type=str, nargs=1,
                    metavar="language", default=None,
                    help="Download chapters of lang.")

    pr.add_argument("-u", "--url", type=str, nargs=1,
                    metavar="url", default=None,
                    help="Manga url")

    pr.add_argument("-c", "--chapters", type=str, nargs=1,
                    metavar="chapters", default=None,
                    help="Select chapters to download.")

# Execute parse_args()

    args = pr.parse_args()

    if args.lang:
        lang_code = args.lang[0]
    else:
        lang_code = "gb"

    if args.url:
        url = args.url[0]
    else:
        url = ""

    if args.chapters:
        req_chap_input = args.chapters[0]
    else:
        req_chap_input = ""

    chap_i = ""

    while url == "":
        url = input("Enter manga URL: ").strip()
        if url == "exit" or url == "quit" or url == "q":
            quit()
        if not validators.url(url):
            url = ""
            print("Invalid url.")
    try:
        manga_id = "".join(x for x in url if x.isdigit())
        if "mangadex.org/chapter" in url:
            manga_id, chap_i = chap_id_to_manga_id(manga_id)
    except Exception:
        print("Error with URL.")

    # grab manga info json from api v2
    r_1, r_1_s = get_url("https://mangadex.org/api/v2/manga/{}/".format(
        manga_id))
    if r_1_s:
        print("Failed to get url. Exiting")
        exit("Failed to ger url in main_1 fnc.")
    title = json.loads(r_1.text)["data"]["title"]

    r_2, r_2_s = get_url(
        "https://mangadex.org/api/v2/manga/{}/chapters".format(manga_id))
    if r_2_s:
        print("Failed to get url. Exiting")
        exit("Failed to ger url in main_2 fnc.")
    manga = json.loads(r_2.text)["data"]["chapters"]

    # get all chapters in chosen language
    chapters = []
    for i, _ in enumerate(manga):
        if manga[i]["language"] == lang_code:
            chapters.append(str(manga[i]["chapter"]))
            if not dot_chr:
                if "." in manga[i]["chapter"]:
                    dot_chr = True
    chapters.sort(key=float_conversion)  # sort numerically by chapter #

    chapters_revised = ["Oneshot" if i == "" else i for i in chapters]

    # get all groups
    groups_all = []
    for i, _ in enumerate(manga):
        groups_all.append(manga[i]["groups"][0])

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
    else:
        print("Available chapters:")
        print(" " + ', '.join(map(str, chapters_revised)))
        if len(dupl) != 0:
            print("Duplictes found")
            print(" " + ', '.join(map(str, dupl)))

    chapters_max_len = len(str(int(float(max(chapters)))))
    requested_chapters = get_chapters_to_dwl(chapters, chap_i, req_chap_input)

    # find out which are availble to dl
    chaps_to_dl = []
    for chapter_id, _ in enumerate(manga):
        chapter_num = None
        try:
            chapter_num = str(
                float(manga[chapter_id]["chapter"])).replace(".0", "")
        except Exception:
            chapter_num = str(manga[chapter_id]["chapter"])

        chapter_group = manga[chapter_id]["groups"]
        if chapter_num in requested_chapters\
                and manga[chapter_id]["language"] == lang_code:
            chaps_to_dl.append(
                (str(chapter_num), manga[chapter_id]["id"], chapter_group[0]))
    chaps_to_dl.sort(key=lambda i: float(i[0]))

    chaps_to_dl_undupe_done = []
    chaps_to_dl_undupe = []
    print()
    for chapter_id in chaps_to_dl:
        if chapter_id[0] in dupl:
            if chapter_id[0][0] not in chaps_to_dl_undupe_done:
                chaps_to_dl_undupe.append(chapter_id)
                chaps_to_dl_undupe_done.append(chapter_id[0][0])
        else:
            chaps_to_dl_undupe.append(chapter_id)

    title = "M " + valid_file_chr(title)

    dest_folder = os.path.join(file_save_location, title)

    for i in chaps_to_dl_undupe:
        download_chapters(i, dest_folder)

    global nr_of_dls
    while nr_of_dls > 0:
        pass
    print("Downloading done!")

    path = os.path.join(dest_folder, "!Manga.url")
    shortcut = open(path, 'w')
    shortcut.write('[InternetShortcut]\n')
    url = "https://mangadex.org/manga/" + str(manga_id)
    shortcut.write('URL=%s' % url)
    shortcut.close()

    global failed_chapters
    global all_downloaded_chapters
    for i in all_downloaded_chapters:
        if not os.path.isfile(i):
            failed_chapters.append(i)
    if failed_chapters != []:
        print("Could not open thease files.")
        print(failed_chapters)
        input("Press enter to finish.")
    failed_chapters = []
    all_downloaded_chapters = []


def get_chapters_to_dwl(chapters, chap_i, req_chap_input):
    '''
    covert input chapters to chapters
    '''
    requested_chapters = []

    while req_chap_input == "":
        req_chap_input = input("\nEnter chapter(s) to download: ").strip()
    if req_chap_input == "all" or req_chap_input == "a":
        requested_chapters.extend(chapters)  # download all chapters
    else:
        req_chap_input = [i for i in req_chap_input.split(',')]
        for i in req_chap_input:

            if i == "bi" or i == "beforeinput":
                chap_i_index = chapters.index(chap_i)
                requested_chapters.append(chapters[chap_i_index-1])
                requested_chapters.append(chapters[chap_i_index])
                continue
            if i == "i" or i == "input":
                chap_i_index = chapters.index(chap_i)
                requested_chapters.append(chapters[chap_i_index])
                continue

            i = i.strip()
            i = i.replace("f", chapters[0])
            i = i.replace("first", chapters[0])
            i = i.replace("l", chapters[-1])
            i = i.replace("last", chapters[-1])

            if "-" in i:
                split = i.split('-')

                try:
                    l_bound_c = chapters.index(split[0])
                except ValueError:
                    print("Chapter {} does not exist. Skipping {}.".format(
                        split[0], i))
                    continue  # go to next iteration of loop
                try:
                    u_bound_c = chapters.index(split[1])
                except ValueError:
                    print("Chapter {} does not exist. Skipping {}.".format(
                        split[1], i))
                    continue
                i = chapters[l_bound_c:u_bound_c+1]
            else:
                try:
                    i = [chapters[chapters.index(i)]]
                except ValueError:
                    print("Chapter {} does not exist. Skipping.".format(i))
                    continue
            requested_chapters.extend(i)
    if requested_chapters == []:
        exit()
    return requested_chapters


def download_chapters(chapter_id, dest_folder):
    '''
    download chapters
    '''
    global file_save_location
    global all_downloaded_chapters
    global failed_chapters

    # get chapter(s) json
    print("Downloading chapter {}.".format(chapter_id[0]))
    r, r_s = get_url("https://mangadex.org/api/v2/chapter/{}/".format(
        chapter_id[1]))
    if r_s:
        print("Failed to get url. Exiting")
        exit("Failed to ger url in download_chapters fnc.")
    chapter = json.loads(r.text)["data"]

    # get url list
    images = []
    server = chapter["server"]
    if "mangadex." not in server:
        server = "https://mangadex.org{}".format(server)
    hashcode = chapter["hash"]
    for page in chapter["pages"]:
        images.append("{}{}/{}".format(server, hashcode, page))

    groupname = valid_file_chr(chapter["groups"][0]["name"])

    loc = ("c{} [{}]".format(zpad(chapter_id[0]), groupname))
    # download images
    for pagenum, url in enumerate(images, 1):

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        while nr_of_dls > maximum_number_of_concurrent_downloads:
            pass
        trdp = threading.Thread(target=page_download, args=(
            pagenum, url, dest_folder, loc, chapter_id))
        trdp.start()


def page_download(pagenum, url, dest_folder, loc, chapter_id):
    '''
    download all pages
    '''
    global all_downloaded_chapters
    global maximum_number_of_concurrent_downloads_len
    global nr_of_dls
    nr_of_dls += 1
    dest_filename = loc + " " + str(pagenum).zfill(2) + \
        os.path.splitext(os.path.basename(url))[1]
    outfile = os.path.join(dest_folder, dest_filename)
    all_downloaded_chapters.append(outfile)

    r, r_s = get_url(url)
    if r_s:
        print("Failed to download ch {} page {}."
              .format(
                  zpad(chapter_id[0]),
                  str(pagenum).zfill(2)))

        nr_of_dls -= 1

    else:
        print("Dwld ch {} p {}. Nr of ac dl {}."
              .format(
                  zpad(chapter_id[0]),
                  str(pagenum).zfill(2),
                  str(nr_of_dls).zfill(
                      maximum_number_of_concurrent_downloads_len)))

        with open(outfile, 'wb') as f:
            f.write(r.content)

        nr_of_dls -= 1


def get_url(url):
    '''
    Gets response from url.
    '''
    fail_count = 0
    while True:
        if fail_count < 5:
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    return r, False
                else:
                    print("Encountered Error {}.".format(r.status_code))
                    fail_count += 1
                    time.sleep(0.5)
            except Exception:
                print("Error with {}".format(url))
                fail_count += 1
                time.sleep(0.5)
        else:
            print("Failed to get url: {}. Stopping further attempts.".format(
                url))
            return "", True


def chap_id_to_manga_id(manga_id):
    '''
    returns manga id of input chapter.
    '''
    r, r_s = get_url("https://mangadex.org/api/v2/chapter/{}".format(
        manga_id))
    if r_s:
        print("Failed to get url. Exiting")
        exit("Failed to ger url in chap_id_to_manga_id fnc.")
    manga = json.loads(r.text)["data"]
    chap_i = manga["chapter"]
    print("Input chapter "+chap_i+".")
    return(manga["mangaId"], chap_i)


if __name__ == "__main__":

    main()

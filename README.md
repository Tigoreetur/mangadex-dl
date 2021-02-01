# mangadex-dl

A Python script to download manga from [MangaDex.org](https://mangadex.org).

## Requirements
  * [Python 3.4+](https://www.python.org/downloads/)

## Installation & usage
```
$ git clone https://github.com/Tigoreetur/mangadex-dl
$ cd mangadex-dl/
$ python mangadex-dl.py [language_code]
```

For a list of language codes (optional argument; defaults to English), see [the wiki page](https://github.com/frozenpandaman/mangadex-dl/wiki/language-codes).

### Example usage
```
$ ./mangadex-dl.py
mangadex-dl v0.2.9
Enter manga URL: https://mangadex.org/title/40595

Title: Even If It Was Just Once, I Regret It
Available chapters:
 1, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 6.1, 6.2, 6.5, 7.1, 7.2, 8.1, 8.2,
 9.1, 9.2, 10.1, 10.2, 11, 12, 12.2, 13, 14, 15, 16, 17, 18

Enter chapter(s) to download: 1, 4.1     

Downloading chapter 1...
Downloading chapter 4.1...
 Downloaded chapter 0001 page 04. Nr of active downloads 30.
 Downloaded chapter 0001 page 28. Nr of active downloads 29.
 Downloaded chapter 0001 page 29. Nr of active downloads 30.
 Downloaded chapter 0001 page 01. Nr of active downloads 29.
... (and so on)
```

### Current limitations
 * The script will download all available releases (in your language) of each chapter specified.

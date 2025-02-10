import requests
from bs4 import BeautifulSoup

# returns true if changed, and false if no change
def deleteIfFound(dom, cssSelector) -> bool:
    res = dom.select(cssSelector)
    wasModified = False
    if res is not None:

        for i, e in enumerate(res):
            # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            # print(f"element: {e.string if e.string is not None else 'Nonetype element!'}")
            # print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")

            res[i].decompose()
            wasModified = True

    return wasModified
        
        


class Wiktionary(object):
    """Define communication with Wiktionary."""

    def __init__(self, dest_lang, origin_lang):
        self.dest_lang = dest_lang
        self.origin_lang = origin_lang
        self.url = "https://" + self.dest_lang + ".wiktionary.org/wiki/{}" # ?printable=yes
        self.soup = None

    def word(self, word):
        """Fetch a word from Wiktionary."""

        # Request Wiktionary word page.
        response = requests.get(self.url.format(word))

        # Set a BeautifulSoup instance for that page from the request's encoding.
        encoding = response.encoding if "charset" in response.headers.get("content-type", "").lower() else None
        soup = BeautifulSoup(response.content, "html.parser", from_encoding=encoding)

        # Error page of wiktionary.org
        noarticle = soup.find("div", {"class": "noarticletext"})
        if noarticle is not None:
            raise Exception(word + " entry does not exist.")

        dom = soup.select_one("div#mw-content-text")

        # delete the "edit" links
        deleteIfFound(dom, "span.mw-editsection")

        # delete the header with the logo
        deleteIfFound(dom, "div.interproject-box")
        deleteIfFound(dom, "div:has(h2#Etymology) + p")
        deleteIfFound(dom, "div:has(h2#Etymology)")
        deleteIfFound(dom, "li.ko-pron__ph")
        deleteIfFound(dom, "table.ko-pron")
        deleteIfFound(dom, "td.audiometa")
        deleteIfFound(dom, "  dd:has( > i[lang='ko-Latn'] )  ")  # the romanised korean
        deleteIfFound(dom, "span[lang='ko-Latn']") # the romanised korean
        deleteIfFound(dom, "i[lang='ko-Latn']") # the romanised korean


        # Find the language origin section:
        # for ex: <span class="mw-headline" id="Romanian">Romanian</span>
        lang_block = dom.select_one("h2#" + self.origin_lang)
        if not lang_block:
            raise Exception("Language `" + self.origin_lang + "` does not exist for this `" + word + "` entry. Tried: " + self.url.format(word))

        listOfsiblingTags = lang_block.parent.find_next_siblings()

        content = ""
        for tag in listOfsiblingTags:
            if tag.name == "h2":  # this is another language
                break

            content = content + str(tag) #.prettify()

            content = content.replace('href="/wiki/', 'href="https://{}.wiktionary.org/wiki/'.format(self.dest_lang))
            content = content.replace("  ", " ")
            content = content.replace("  ", "")
            content = content.replace(" ―  ― ", " ― ")
            content = content.replace("()", "")
            content = content.replace('<span class="mention-gloss-paren annotation-paren">(</span><span class="mention-gloss-paren annotation-paren">)</span>', "")
        return content

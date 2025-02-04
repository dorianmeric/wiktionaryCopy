"""
Entry point for WiktionaryCopy add-on from Anki
"""

from __future__ import print_function
import logging
import sys


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)


__all__ = []


if __name__ == "__main__":
    warning("WiktionaryCopy is an add-on for Anki.\nIt is not intended to be run directly.\nTo learn more or download Anki, please visit <http://ankisrs.net>.\n")
    exit(1)

import os
from anki.hooks import addHook
from aqt.editor import Editor
from aqt import mw

config = mw.addonManager.getConfig(__name__)
origin_lang = config["origin language"]
dest_lang = config["destination language"]
dest_lang_field = config["destination language field"]

# import wiktionarygrabber module with the actual code
# import wiktionarycopy
from .fetcher import Wiktionary


""" Initialize logging """


def initLog():
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(__name__)
    logging.basicConfig(filename="ankiwiktionarycopy.log", encoding="utf-8", level=logging.DEBUG, format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")

    return logger


"""The main function"""
def wiktionaryCopy_onNote(note):
    logger = initLog()  # Initialize logging
    logger.info("Logging started.")

    listOfFields = mw.col.models.field_names(note.note_type())
    logger.debug("listOfFields")
    logger.debug(listOfFields)

    if origin_lang not in listOfFields:
        logger.error('Could not find a field called "{}" (mind the capitalization), trying Front.'.format(origin_lang))
        sourceField = "Front"
    else:
        sourceField = origin_lang

    if dest_lang_field not in listOfFields:
        logger.error('Could not find a field called "{}" (mind the capitalization), trying Back.'.format(dest_lang_field))
        targetOutputField = "Back"
    else:
        targetOutputField = dest_lang_field

    entry = note[sourceField]  # we take the word from the "Origin Lang" field

    # Call the grabber method
    wikiObj = Wiktionary(dest_lang, origin_lang)
    myWord = wikiObj.word(entry)

    if myWord:
        logger.debug("Retrieved word: %s" % myWord)
        note[targetOutputField] = note[targetOutputField] + myWord # append
        note["link"] = "https://" + dest_lang + ".wiktionary.org/wiki/" + entry

    else:
        logger.warning("Could not find word %s" % entry)
        logger.error("Failed to find word '{}' in {}. Please check if Wiktionary has it: {}".format(entry, origin_lang, "https://" + dest_lang + ".wiktionary.org/wiki/" + entry))

    logger.info("Logging finished.")

def wiktionaryCopy(self):
    self.mw.checkpoint("Get info from wiktionary on the current note")

    wiktionaryCopy_onNote(self.note)
    
    self.stealFocus = True
    """Saving the field which has been filled"""

    def flush_field():
        if not self.addMode:  # save
            self.note.flush()
        self.loadNote()

    self.saveNow(flush_field, keepFocus=True)
    # self.loadNote();



""" Add the addon button to the anki Editor"""
def add_editor_button(buttons: [], editor: Editor):
    # import pathlib
    icon_path = os.path.join(os.path.dirname(__file__), "icons", "wiktionary.png")
    print(icon_path)
    # icon_path = os.path.join(mw.pm.addonFolder(), 'anki-wiktionarycopy', 'icons', 'wiktionary.png')
    b = editor.addButton(icon_path, "wiktionarycopy", wiktionaryCopy, tip="Add fields with Wiktionary data")
    buttons.append(b)
    return buttons

addHook("setupEditorButtons", add_editor_button)




from typing import TYPE_CHECKING, cast
from aqt.gui_hooks import browser_menus_did_init
from aqt.qt import QKeySequence, QMenu, QAction
from aqt.utils import askUser, getFile, showCritical, tooltip
from aqt.browser.browser import Browser

def on_batch_edit(browser: "Browser"):
    if not (nids := browser.selectedNotes()):
        tooltip("No cards selected.")
        return
    if (collection := browser.mw.col) is None:
        return

    for nid in nids:
        note = collection.get_note(nid)
        wiktionaryCopy_onNote(note)
        collection.update_note(note)
        # sleep here?


def setup_menu(browser: "Browser"):
    menu: QMenu = browser.form.menuEdit
    menu.addSeparator()
    action = cast(QAction, menu.addAction("Run WikipediaCopy on all selected cards"))
    action.triggered.connect(lambda _, b=browser: on_batch_edit(b))

browser_menus_did_init.append(setup_menu)

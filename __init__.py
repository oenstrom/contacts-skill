# Copyright (C) 2022  Olof Enström

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from mycroft import MycroftSkill, intent_handler
import sqlite3

class Contacts(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        con = sqlite3.connect("file:contacts.db?mode=rwc", uri=True)
        con.executescript("CREATE TABLE IF NOT EXISTS contacts(`name` TEXT, `email` TEXT, `phone` TEXT)")
        con.commit()
        con.close()

    @intent_handler("AddContact.intent")
    def add_contact(self, message):
        self.speak_dialog("Självfallet, du kommer nu få ange kontaktuppgifter")
        name  = self.get_response("AskForName")
        self.speak(name)
        email = self.get_response("AskForEmail")
        self.speak(email)
        phone = self.get_response("AskForPhone")
        self.speak(phone)

        con = sqlite3.connect("file:contacts.db?mode=rw", uri=True)
        con.execute("INSERT INTO contacts VALUES(?, ?, ?)", (name, email, phone))
        con.commit()
        con.close()
    
    @intent_handler("RemoveContact.intent")
    def remove_contact(self, message):
        response = self.get_response("Who")
        if response:
            self.speak("Tar bort kontakten: " + response)
            self.log.info(sqlite3.connect("file:contacts.db?mode=rw", uri=True).execute("SELECT * FROM contacts WHERE name=?", (response,)).fetchone())


def create_skill():
    return Contacts()
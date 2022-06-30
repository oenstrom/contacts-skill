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
        con = self.get_con("rwc")
        con.executescript("CREATE TABLE IF NOT EXISTS contacts(`name` TEXT NOT NULL, `email` TEXT NOT NULL UNIQUE, `phone` TEXT NOT NULL UNIQUE)")
        self.commit(con)
    
    def get_con(self, mode="rw"):
        return sqlite3.connect(f"file:contacts.db?mode={mode}", uri=True)
    
    def commit(self, con):
        con.commit()
        con.close()

    @intent_handler("AddContact.intent")
    def add_contact(self, message):
        name  = self.get_response("AskForName")
        self.speak(name)
        email = self.get_response("AskForEmail")
        email = email.replace("punkt", ".").replace("snabel-a", "@").replace(" ", "")
        self.speak(email)
        phone = self.get_response("AskForPhone")
        phone = phone.replace("-", "").replace(" ", "")
        self.speak(phone)

        if not name or not email or not phone:
            self.speak_dialog("CouldNotAdd")
            return

        try:
            con = self.get_con()
            con.execute("INSERT INTO contacts VALUES(?, ?, ?)", (name, email, phone))
            self.speak_dialog("ContactAdded", data={"name": name, "email": email, "phone": phone})
        except sqlite3.IntegrityError as err:
            self.speak_dialog("NotUnique")
        except Exception:
            self.speak_dialog("CouldNotAdd")

        self.commit(con)
    
    @intent_handler("RemoveContact.intent")
    def remove_contact(self, message):

        response = self.get_response("Who")
        if response:
            self.speak("Tar bort kontakten: " + response)
            con = self.get_con()
            self.log.info(con.execute("SELECT * FROM contacts WHERE name=?", (response,)).fetchone())


def create_skill():
    return Contacts()
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
import requests

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
        """Ask for name, email and phone number. Then try to insert that contact into the database."""
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
            self.commit(con)
        except sqlite3.IntegrityError as err:
            self.speak_dialog("NotUnique")
        except Exception:
            self.speak_dialog("Error")


    @intent_handler("ListContacts.intent")
    def list_contacts(self, message):
        """List all contacts"""
        try:
            con = self.get_con()
            contact_list = con.execute("SELECT * FROM contacts ORDER BY name ASC").fetchall()
            self.__display_contacts(contact_list)
            self.speak_dialog("ShowContacts")
        except Exception:
            self.speak_dialog("Error")


    @intent_handler("RemoveContact.intent")
    def remove_contact(self, message):
        """Ask for the contact to be removed. If multiple contacts are found use ask_selection and match by phone number."""

        response = self.get_response("Who")
        if response:
            try:
                con = self.get_con()
                contact_list = con.execute("SELECT * FROM contacts WHERE name=?", (response,)).fetchall()
            except Exception:
                self.speak_dialog("Error")

            if len(contact_list) <= 0:
                self.speak_dialog("NotFound")
                return

            if len(contact_list) > 1:
                # TODO: Handle post fail
                res = self.__display_contacts(contact_list)
                response = self.ask_selection(contact_list, "WhoFromSelection")
            
            self.__delete_contact(response)
    
    def __delete_contact(self, contact, con):
        """Try to delete the contact from the database."""
        try:
            con.execute("DELETE FROM contacts WHERE name=? AND email=? AND phone=?", (contact.name, contact.email, contact.phone))
            self.commit(con)
            self.speak_dialog("ContactRemoved", data={"name": contact.name, "phone": contact.phone})
        except Exception:
            self.speak_dialog("Error")
    

    def __display_contacts(self, contacts):
        """Post list of contacts to MagicMirror (or some other http endpoint)"""
        self.log.info(contacts)
        res = requests.post("http://localhost:8080/MMM-contacts/list", {"contacts": contacts})
        self.log.info(res)
        # TODO: Handle post fail?
        return res

def create_skill():
    return Contacts()
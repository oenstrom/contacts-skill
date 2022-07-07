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
from mycroft.messagebus import Message
import sqlite3

class Contacts(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.con = self.get_con("rwc")
        self.con.executescript("CREATE TABLE IF NOT EXISTS contacts(`name` TEXT NOT NULL, `email` TEXT NOT NULL UNIQUE, `phone` TEXT NOT NULL UNIQUE)")
        self.con.commit()
        self.con.close()
    
    def initialize(self):
        self.add_event("contacts-skill:delete_contact", self.handle_delete_contact_event)

    def handle_delete_contact_event(self, message):
        data = message.data
        if data.get("name") is None or data.get("email") is None or data.get("phone") is None:
            return

        self.con = self.get_con()
        self.__delete_contact(data, self.con)

    def get_con(self, mode="rw"):
        return sqlite3.connect(f"file:contacts.db?mode={mode}", uri=True)

    @intent_handler("AddContact.intent")
    def add_contact(self, message):
        """Ask for name, email and phone number. Then try to insert that contact into the database."""
        name  = self.get_response("AskForName")
        # self.speak(name)
        email = self.get_response("AskForEmail")
        email = email.replace("punkt", ".").replace("snabel-a", "@").replace("snabela", "@").replace(" ", "")
        # self.speak(email)
        phone = self.get_response("AskForPhone")
        phone = phone.replace("-", "").replace(" ", "")
        # self.speak(phone)

        if not name or not email or not phone:
            self.speak_dialog("CouldNotAdd")
            return

        try:
            self.con = self.get_con()
            self.con.execute("INSERT INTO contacts VALUES(?, ?, ?)", (name, email, phone))
            self.__display_contacts(self.__get_contacts(self.con))
            self.con.commit()
            self.speak_dialog("ContactAdded", data={"name": name, "email": email, "phone": phone})
        except sqlite3.IntegrityError as err:
            self.speak_dialog("NotUnique")
        except sqlite3.DatabaseError as e:
            self.speak_dialog("Error")
        finally:
            self.con.close()


    @intent_handler("ListContacts.intent")
    def list_contacts(self, message):
        """List all contacts"""
        try:
            self.con = self.get_con()
            self.__display_contacts(self.__get_contacts(self.con))
            self.speak_dialog("ShowContacts")
        except Exception as e:
            self.log.info(e)
            self.speak_dialog("Error")
        finally:
            self.con.close()


    @intent_handler("RemoveContact.intent")
    def remove_contact(self, message):
        """Ask for the contact to be removed. If multiple contacts are found use ask_selection and match by phone number."""

        response = self.get_response("Who")
        if response:
            try:
                self.con = self.get_con()
                contact_list = self.con.execute("SELECT * FROM contacts WHERE name=?", (response,)).fetchall()
            except Exception:
                self.speak_dialog("Error")
            finally:
                self.con.close()

            if len(contact_list) <= 0:
                self.speak_dialog("NotFound")
                return

            if len(contact_list) > 1:
                # TODO: Handle post fail
                res = self.__display_contacts(contact_list)
                response = self.ask_selection(contact_list, "WhoFromSelection")
            
            self.__delete_contact(response)
    
    def __get_contacts(self, con):
        """Get contacts from the database."""
        return con.execute("SELECT * FROM contacts ORDER BY name ASC").fetchall()

    def __delete_contact(self, contact, con):
        """Try to delete the contact from the database."""
        try:
            con.execute("DELETE FROM contacts WHERE name=? AND email=? AND phone=?", (contact["name"], contact["email"], contact["phone"]))
            con.commit()
            self.speak_dialog("ContactRemoved", data=contact)
            self.__display_contacts(self.__get_contacts(con))
        except Exception as e:
            self.log.info(e)
            self.speak_dialog("Error")
        finally:
            con.close()
    

    def __display_contacts(self, contacts):
        """Send list of contacts over the messagebus"""
        self.log.info(contacts)
        self.bus.emit(Message("RELAY:MMM-contacts:LIST-ALL", {"contacts": contacts}))

def create_skill():
    return Contacts()
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
from mycroft.skills import skill_api_method
from mycroft.messagebus import Message
from mycroft.util.parse import match_one, fuzzy_match
import sqlite3
import os

class Contacts(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.con = self.get_con("rwc")
        self.con.executescript("CREATE TABLE IF NOT EXISTS contacts(`name` TEXT NOT NULL, `email` TEXT NOT NULL UNIQUE, `phone` TEXT NOT NULL UNIQUE)")
        self.con.commit()
        self.con.close()
    
    def initialize(self):
        """Setup event listeners."""
        self.add_event("contacts-skill:delete_contact", self.handle_delete_contact_event)
        self.add_event("contacts-skill:get_contacts", self.handle_get_contacts_event)

    def handle_delete_contact_event(self, message):
        """Request to delete contact received over messagebus. Delete the specified contact."""
        data = message.data
        if data.get("name") is None or data.get("email") is None or data.get("phone") is None:
            return

        self.__delete_contact(data)
        self.__emit_all_contacts(self.__get_contacts(self.con))

    
    def handle_get_contacts_event(self, message):
        """Request for listing all contacts received over messagebus. Emit list of contacts."""
        data = message.data
        try:
            self.con = self.get_con()
            self.__emit_all_contacts(self.__get_contacts(self.con), data.get("sender", "*"))
        except Exception as e:
            self.log.info(e)
        finally:
            self.con.close()

    def get_con(self, mode="rw"):
        """Return a connection to the sqlite database."""
        return sqlite3.connect(f"file:database/contacts-skill/contacts.db?mode={mode}", uri=True)

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
            self.__emit_all_contacts(self.__get_contacts(self.con))
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
            self.__emit_all_contacts(self.__get_contacts(self.con))
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
        if not response:
            return

        best_match = self.get_best_match(response)
        if len(best_match) <= 0:
            self.speak_dialog("NotFound", {"name": response})
            return
        elif len(best_match) == 1:
            contact = {"name": best_match[0][0], "email": best_match[0][1], "phone": best_match[0][2]}
        else:
            selection = self.ask_selection([x[2] for x in best_match], "WhoFromSelection")
            selected = [(name, email, phone) for (name, email, phone, score) in best_match if phone == selection]
            if len(selected) == 1:
                contact = {"name": selected[0][0], "email": selected[0][1], "phone": selected[0][2]}
            else:
                return

        self.__confirm_removal(contact)
        self.__emit_all_contacts(self.__get_contacts(self.get_con()))
        
    
    def __confirm_removal(self, contact):
        """Ask yes/no to confirm removing the contact"""
        if self.ask_yesno("ConfirmRemove", data=contact) == "yes":
            self.__delete_contact(contact)
        else:
            self.speak_dialog("NotRemoved")
    
    @skill_api_method
    def get_best_match(self, to_match):
        """Get the contact that matches the input the best."""
        contact_list = []
        try:
            self.con = self.get_con()
            contact_list = self.__get_contacts(self.con)
        except Exception:
            self.speak_dialog("Error")
            self.con.close()
            return False
        finally:
            self.con.close()

        if len(contact_list) <= 0:
            self.speak_dialog("NotFound", data={"name": to_match})
            return False

        best_match = []
        for c in contact_list:
            c = list(c)
            c.append(fuzzy_match(to_match.lower(), c[0].lower()))
            if len(best_match) == 0 or c[-1] > best_match[0][-1]:
                best_match = [c]
            elif c[-1] == best_match[0][-1]:
                best_match.append(c)
        if len(best_match) > 1:
            self.__emit_all_contacts(best_match)

        return best_match

    def __get_contacts(self, con):
        """Get contacts from the database."""
        return con.execute("SELECT * FROM contacts ORDER BY name ASC").fetchall()

    def __delete_contact(self, contact):
        """Try to delete the contact from the database."""
        try:
            self.con = self.get_con()
            self.con.execute("DELETE FROM contacts WHERE name=? AND email=? AND phone=?", (contact["name"], contact["email"], contact["phone"]))
            self.con.commit()
            self.speak_dialog("ContactRemoved", data=contact)
        except Exception as e:
            self.log.info(e)
            self.speak_dialog("Error")
        finally:
            self.con.close()
    

    def __emit_all_contacts(self, contacts, receiver="MMM-contacts"):
        """Send list of contacts over the messagebus"""
        self.bus.emit(Message(f"RELAY:{receiver}:LIST-ALL", {"contacts": contacts}))

def create_skill():
    return Contacts()
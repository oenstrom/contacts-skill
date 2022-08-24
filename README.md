# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/address-book.svg" card_color="#1D76BA" width="50" height="50" style="vertical-align:bottom"/> Contacts
Manage a local contact list.

## About
A skill for managing a local contact list. MyCroft can list, get, add and remove contacts from the list.

## Examples
**sv-se**
* "lägg till kontakt"
* "visa alla kontakter"
* "ta bort kontakt"

**en-us**
* "add new contact"
* "show all contacts"
* "remove contact"

---

## Database
The skill uses a SQLite database, to store all contacts, that it automatically creates at `~/mycroft-core/database/contacts-skill/contacts.db`.

## Events
The skill subscribes to two events and emits one event as shown in the table.

| Name                            | Type       | Description                                                             |
|---------------------------------|------------|-------------------------------------------------------------------------|
| `contacts-skill:delete_contact` | Subscribed | Tries to delete the contact received in the message payload.            |
| `contacts-skill:get_contacts`   | Subscribed | A request for listing all contacts is recevied. Emits all contacts.      |
| `RELAY:{receiver}:LIST-ALL`     | Emits      | Emits all contacts to the receiver. Default receiver is `MMM-contacts`. |

## Get best match
The skill has a method, `get_best_match()`, for getting the best matching contact based on the name. The argument passed to the method is the name to match with a contact in the database. This method can be used by other skills using the Mycroft SkillApi.

```python
from mycroft.skills.api import SkillApi

SkillApi.get("contacts-skill").get_best_match(name)
```
Currently it will always return a contact as long as there is one in the database, even if it's a really bad match.  
Rewriting the `get_best_match()` to check the score returned by `fuzzy_match()` can be done to have a minimum confidence score.

---

## Credits
oenstrom

## Category
**Daily**

## Tags
#Contacts

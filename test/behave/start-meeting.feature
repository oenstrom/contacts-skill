Feature: start-meeting
  Scenario Outline: start meeting with name
    Given an english speaking user
     When the user says "<start meeting with name>"
     Then "jitsi-magicmirror-skill" should reply with dialog from "StartMeeting.dialog"
   Examples: start meeting utterances
      | start meeting with name          |
      | ring Christoffer                 |
      | kontakta Christoffer             |
      | telefonera Christoffer           |
      | starta ett möte med Christoffer  |
      | öppna möte med Christoffer       |
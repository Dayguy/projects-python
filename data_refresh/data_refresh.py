import json, logging, sys
from os import makedirs, path, rename, remove
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup, Tag # type: ignore
from datetime import datetime

partfile = "assets/meetings.part"
sites = [""]

def parse_times(time_string) -> dict:
  '''Given a string find time values and return them. i.e. Sunday, Noon to 1:00 pm.'''

  times = {}   

  # Strip off anyting we don't need
  cleaned_data = time_string.split(", ")[1].replace(" am", "am").replace(" pm", "pm").replace(" to ", " ").split(" ")

  # We're left with only 1 or 2 (some missing end times)
  times["start"] = cleaned_data[0]

  if len(cleaned_data) == 2:
    times["end"] = cleaned_data[1]

  return times


def main() -> None:

  days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
  filename = "assets/aaboston_meetings_" + str(datetime.now()).replace(" ", "_")
  headers = {"User-Agent": "Mozilla/5.0"}

  # TODO: eventually move to a list so multiple urls can be looped
  base_url = "https://aaboston.org/meetings?tsml-day="

  # Ensure write path exists
  if not path.exists("assets/"):
    makedirs("assets/")

  # Get meetings for each day of the week
  for day_num in range(7):
    meeting = {}

    # Open the initial file for writing
    with open(partfile, "a") as file:

      # Append the target day of the week to the target url    
      day_url = base_url + str(day_num)
      day = days[day_num]

      logger.info(f"Pulling meetings for { day }")
      
      # Collect HTML source
      req = Request(url = day_url, headers = headers)
      with urlopen(req) as response: 
        soup = BeautifulSoup(response, 'lxml') 

      # First row is the table header skip it        
      rows = iter(soup.find("table", class_="table table-striped").find_all("tr"))
      next(rows)

      for row in rows:
        # Collect meeting attributes
        meeting["day"] = f"{ day }"

        # Meeting details are on a linked page
        if row.find("a", href=True):
          for anchor in row.find_all("a"):

            details_url = str(anchor['href'])
            details_req = Request (url = details_url, headers = headers)

            with urlopen(details_req) as details_html:
              soup = BeautifulSoup(details_html, 'lxml')

            # Collect meeting start and end times
            time_str = soup.find("p", class_="meeting-time").text.strip()
            meeting["times"] = parse_times(time_str)              
            
            meeting_type = soup.find("div", class_="attendance-option").text.strip()
            meeting["attendance_options"] = meeting_type.split(" and ")

            meeting["venue"] = soup.find("a", class_="list-group-item-location").find_next().text.strip()                 
            meeting["address"] = soup.find("p", class_="location-address").get_text(separator=" ").strip()

            # Meeting formats display beneath an <hr> tag...Closed, 12 Step, Men, etc
            li_text = soup.find("hr").find_next("li").text.strip()
            current_li = soup.find("hr").find_next("li")
            meeting["format"] = [li_text]

            while current_li.find_next_sibling("li"):
              meeting["format"].append(current_li.find_next_sibling("li").text.strip())
              current_li = current_li.find_next_sibling("li")

            # All meetings with an online component have a Join with Zoom button, but the way
            # the data is presented varies. If there is a button try to parse Meeting ID & Passcode
            # Load all data either way for post DB load inspection.

            # Take entire Online Meeting section
            for heading in soup.find_all("h3", class_="list-group-item-heading"):
              if heading.text.strip() == "Online Meeting":
                section = heading.find_parent()
                          
            # Parse out id and password when they are clear
            if soup.find("a", class_="btn btn-default btn-block") and \
                soup.find("a", class_="btn btn-default btn-block").text.strip() == "Join with Zoom":

              zoom_text = soup.find("a", class_="btn btn-default btn-block").find_next("p").text.strip()
              if zoom_text.count(":") == 2:
                zoom_parts = zoom_text.split(":")
                mtg_parts = zoom_parts[1].lower().split("p")
                zoom_id = mtg_parts[0].strip()
                zoom_pw = zoom_parts[2].strip()

                meeting["zoom_connection"] = {"meeting_id": zoom_id, "Passcode": zoom_pw} 

              meeting["zoom_info"] = str(section)  

            # Location Notes
            if soup.find("section", class_="location-notes"):
              meeting["venue_notes"] = soup.find("section", class_="location-notes").findChild("p").text.strip()

            # Some zoom meetings list a contact email instead of ID/PW
            for heading in soup.find_all("h3", class_="list-group-item-heading"):
              if heading.text.strip() == "Contact Information":
                # look for a mailto href
                for a in soup.find_all("a", href=True):
                  if "mailto" in a["href"]:
                    meeting["email"] = a.text.strip()              

              
            # DEBUG: get eyes on the JSON
            # print(json.dumps(meeting))

            file.write(json.dumps(meeting) + "\n")

          
  # Once every day's records are written rename file
  rename(partfile, filename)


if __name__ == "__main__":

  if not path.exists("logs/"):
    makedirs("logs/")

  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)

  logging.basicConfig (
    level=logging.DEBUG,
    format='%(asctime)s: %(filename)s [%(levelname)s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
    handlers=[logging.FileHandler("logs/data_refresh.log"), logging.StreamHandler(sys.stdout)],
  )

  logger.info("Data refresh started")

  main()

  logger.info("Data refresh complete")
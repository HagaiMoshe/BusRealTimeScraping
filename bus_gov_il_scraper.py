import sys
import os
import shutil
import traceback
import time
from collections import namedtuple

try:
	from selenium import webdriver
except ImportError:
	sys.exit("Error: dependency missing: selenium. run: \"pip install selenium\" ")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if shutil.which("geckodriver.exe") is None:
    sys.exit("Error: dependency missing: geckodriver. need to either install the driver, or add it to the path")


""" Real time Bus ETA by station number. for Israel
    זמני הגעת אוטובוסים בזמן אמת על פי מספר תחנה
    You can find the stations number in: https://bus.gov.il/#/realtime/1/0
"""


def formatHebrewString(string: str) -> str:
    "For hebrew. reverse the position of the letters"
    return string[::-1]


station_type = namedtuple("station_type", "number name")
BusInfo_type = namedtuple("BusInfo_type", "lineNumber destination ETA")

def getBusTimeTable(stationNumber: int) -> tuple[station_type, list[BusInfo_type]]:
    """ Real time Bus ETA by station number. for Israel.
        stationName_type = namedtuple("station_type", "number name")
        BusInfo_type = namedtuple("BusInfo_type", "lineNumber destination ETA")
    """

    station = None
    busInfoList = list()

    BUS_GOV_URL = "https://bus.gov.il/#/realtime/1/0/2/"
    COMPLETE_URL = BUS_GOV_URL + str(stationNumber)
    webDriverHandle = webdriver.Firefox()
    webDriverHandle.get(COMPLETE_URL)

    try:
        #wait for the page to load
        WebDriverWait(webDriverHandle, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "TableLine")))
        time.sleep(0.5) #another half a sec to make sure all the lines have loaded for the entire table

        #get the station name
        MobileFontSizeTagList = webDriverHandle.find_elements(By.CLASS_NAME, 'MobileFontSize')
        for MobileFontSizeTag in MobileFontSizeTagList: #there may be more then one MobileFontSize tag, but only one of them will contain our data
            isBusGovIlTableHeaderTags = MobileFontSizeTag.find_elements(By.CLASS_NAME, 'isBusGovIlTableHeader')
            divTags = isBusGovIlTableHeaderTags[0].find_elements(By.TAG_NAME, 'div')
            if len(divTags) is not None:
                tmpString = divTags[0].text
                StationNumber = [int(s) for s in tmpString.split() if s.isdigit()][0]
                StationName = tmpString.replace(str(StationNumber), '')
                StationName = formatHebrewString(StationName)
                station = station_type(StationNumber, StationName)

        # find the lines table within the HTTP response
        TableLineList = list()
        tmp = webDriverHandle.find_elements(By.CLASS_NAME, "TableLine")
        if isinstance(tmp, list): #TODO: is there a less stupid way to do this?
            TableLineList += tmp
        else:
            TableLineList.append(tmp)

        # extract the relevant info from the lines table
        for TableLine in TableLineList:
            divtags = TableLine.find_elements(By.TAG_NAME, 'div')
            lineNumber = int(divtags[0].get_attribute('innerHTML'))
            destination = divtags[1].get_attribute('innerHTML').strip()
            destination = formatHebrewString(destination)
            timeOfArrival = int(divtags[3].find_elements(By.TAG_NAME, 'span')[0].get_attribute('innerHTML'))
            busInfo = BusInfo_type(lineNumber, destination, timeOfArrival)
            busInfoList.append(busInfo)

    except Exception:
        print("exception")
        traceback.print_exc()
        webDriverHandle.quit()

    webDriverHandle.quit()
    return station, busInfoList




if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("""usage:  python bus_gov_il_scraper.py <bus station number>
        You can find the station number in: https://bus.gov.il/#/realtime/1/0""")

    stationNumber = int(sys.argv[1])
    station, busInfoList = getBusTimeTable(stationNumber)
    print(f"station: {station.number} {station.name}")
    for busInfo in busInfoList:
        print(f"--line number: {busInfo.lineNumber}\n  destination: {busInfo.destination}\n  ETA: {busInfo.ETA}")

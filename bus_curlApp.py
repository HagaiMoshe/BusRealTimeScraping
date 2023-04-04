import requests
from datetime import datetime
from collections import namedtuple

def invertString(string: str):
    return string[::-1]


stationInfo_type = namedtuple("stationInfo_type", "number name")
BusInfo_type = namedtuple("BusInfo_type", "lineNumber destination ETA isRealTime")

def getBusTimeTable(stationNumber: int) -> tuple[stationInfo_type, list[BusInfo_type]]:
    CURLBUS_URL = "https://curlbus.app"
    url = CURLBUS_URL + "/" + str(stationNumber)
    HEADERS = { "Accept": "application/json" }

    # request the data from curlbus
    httpResponse = requests.get(url, headers=HEADERS)
    if httpResponse.status_code != 200:
        print("received status code ", httpResponse.status_code)
        return None
    jsonResponse = httpResponse.json()

    # parse the station name
    stationName = jsonResponse["stop_info"]["name"]["HE"] #'stop_info': {'name': {'HE': <name in hebrew>}},
    stationName = invertString(stationName)
    stationInfo = stationInfo_type(stationNumber, stationName)

    # parse the bus timetable
    now = datetime.now()
    busInfoList = list()
    busList = jsonResponse['visits'][str(stationNumber)]
    for bus in busList:
        number = int(bus['line_name'])
        desitnation = bus['static_info']['route']['destination']['name']['HE']
        desitnation = invertString(desitnation)
        ETA = bus['eta'] #A string representation of estimated time in iso format
        ETA = datetime.strptime(bus['eta'][:-6], '%Y-%m-%d %H:%M:%S') # convert the string to datatime object
        ETA = (ETA - now).total_seconds() #the time left for arrival in seconds
        ETA = round(ETA /60) #the time left for arrival in minutes
        isRealTime = False if bus['location'] is None else True
        busInfo = BusInfo_type(number, desitnation, ETA, isRealTime)
        busInfoList.append(busInfo)

    return (stationInfo, busInfoList)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        sys.exit("""usage:  python bus_curlApp.py <bus station number>
        You can find the station number in: https://bus.gov.il/#/realtime/1/0""")

    stationNumber = int(sys.argv[1])
    station, busInfoList = getBusTimeTable(stationNumber)
    print(f"station: {station.number} {station.name}")
    for busInfo in busInfoList:
        print(f"--line number: {busInfo.lineNumber}\n  destination: {busInfo.destination}\n  ETA: {busInfo.ETA}\n  isRealTime: {busInfo.isRealTime}")


import requests
import json
import hashlib
from datetime import date
import time, traceback
import threading

API_BASE = "https://cdn-api.co-vin.in/api/v2"
BENEF_ID = "<Your_Beneficiary_Id>"
MOBILE_NO = "<Your_Mobile_number>"
DISTRICT_ID = 307 # District Id of Ekm
USER_AGENT_SECRET = "U2FsdGVkX1/bWMpon6LReFzd84D/C+lCPnUr4eAmAFQQwY+CYD/PC3M/kEgD2affS30yycuEXbo/YQYLGE3xmA=="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
DOSE = 1
MIN_AGE = 18
DOSE_FILTER = "available_capacity_dose" + str(DOSE)
uaHeaders = {'user-agent': USER_AGENT}
BOOK = False

def every(delay, task):
  next_time = time.time() + delay
  while True:
    time.sleep(max(0, next_time - time.time()))
    try:
      task()
    except Exception:
      traceback.print_exc()
      # in production code you might want to have this instead of course:
      # logger.exception("Problem while executing repetitive task.")
    # skip tasks if we are behind schedule:
    next_time += (time.time() - next_time) // delay * delay + delay

today = date.today().strftime("%d-%m-%Y")

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

def hasDose(session):
    return session[DOSE_FILTER]!=0

def filterSession(session):
    return session["vaccine"] == "COVISHIELD" and session["min_age_limit"] == MIN_AGE and hasDose(session)


headers=uaHeaders

class VaccineBooking:
    def __init__(self):
        self.token = ""
        self.txnId = ""
    
    def getCenters(self, p=False):
        url = "".join((API_BASE, "/appointment/sessions/public/calendarByDistrict"))
        PARAMS = {"district_id": DISTRICT_ID, "date": today}
        # sending get request and saving the response as response object
        r = requests.get(url = url, params = PARAMS)
        resJson = r.json()
        if r.status_code != 200:
            print("Error: statusCode={}, resJson={}".format(r.status_code, resJson))
            return
        centers = resJson["centers"]
        filteredCenters = []
        for center in centers:
            sessions = center["sessions"]
            sessions = list(filter(filterSession, sessions))
            sessions.sort(key=lambda session:session[DOSE_FILTER], reverse=True)
            if sessions:
                filteredCenters.append({ **center, "sessions": sessions })
        if p:
            print(json.dumps(filteredCenters, indent=4))
        try:
            filteredCenters.sort(key=lambda x: x.sessions[0][DOSE_FILTER], reverse=True) # sort by centers that have highest available doses
        except:
            pass
        return filteredCenters

    def sendOTP(self):
        # Generate OTP
        url = "".join((API_BASE, "/auth/public/generateOTP"))
        data = {"mobile": MOBILE_NO, "secret": USER_AGENT_SECRET}
        print(data)
        r = requests.post(url=url, json=data, headers=headers)
        try:
            resJson = r.json()
        except Exception:
            print("Error", r)
            traceback.print_exc()
            # return
        if r.status_code != 200:
            print("Error: statusCode={}, resJson={}".format(r.status_code, resJson))
            return
        self.txnId = resJson["txnId"]
        # print("txnId: ", self.txnId)

    def confirmOTP(self):
        otp = input("Enter OTP: ")

        if otp == "x":
            return "x" # Dismiss

        # Validate OTP
        url = "".join((API_BASE, "/auth/public/confirmOTP"))
        data = {"otp": encrypt_string(otp), "txnId": self.txnId}
        print(data)
        r = requests.post(url=url, json=data, headers=headers)
        try:
            resJson = r.json()
        except Exception:
            print("Error confirming OTP", r)
            traceback.print_exc()
            return
        if r.status_code != 200:
            print("Error: statusCode={}, resJson={}".format(r.status_code, resJson))
            return
        self.token = resJson["token"]
        print("token: ", self.token)

    def scheduleAppointment(self, session_id, slot, beneficiaries=[BENEF_ID]):
        url = "".join((API_BASE, "/appointment/schedule"))
        while not self.token:
            print("Unauthorized - Please login")
            self.sendOTP()
            x = self.confirmOTP()
            # x = self.generateAndConfirmOTP()
            if x == "x":
                return "x"
        headers = {"authorization": " ".join(("Bearer", self.token)), **uaHeaders}
        data = {"session_id": session_id, "dose": DOSE, "slot": slot, "beneficiaries": beneficiaries}
        r = requests.post(url=url, json=data, headers=headers)
        try:
            resJson = r.json()
        except Exception:
            print("Error booking appointment", r)
            traceback.print_exc()
            return
        if r.status_code == 401:
            self.token = ""
            print("401")
            self.scheduleAppointment(session_id, slot)
        elif r.status_code != 200:
            print("Error: statusCode={}, resJson={}".format(r.status_code, resJson))
            retry = input("retry? y/n: ")
            if retry == "y":
                self.token = "" # clear
                self.scheduleAppointment(session_id, slot)
            return
        confirmation = resJson.get("appointment_confirmation_no") or resJson.get("appointment_id")
        print(confirmation)
        return confirmation

book = VaccineBooking()
def main():
    centers = book.getCenters()
    if centers:
        print(json.dumps(centers, indent=4))

        if BOOK:
            center = centers[0]
            session = center["sessions"][0]
            sessionId = session["session_id"]
            slot = session["slots"][1]
            # print("Chosen center: \n_________________\n", json.dumps(center, indent=4))
            confirmation = None
            while not confirmation:
                confirmation = book.scheduleAppointment(sessionId, slot)
            
            if confirmation != "x":
                raise Exception("Completed") # In order to terminate the execution
        else:
            book.sendOTP() # Just send an OTP (for alert)
    else:
        print("No centers available!")

threading.Thread(target=lambda: every(5, main)).start()
# target is the callable object to be invoked by the run() method.
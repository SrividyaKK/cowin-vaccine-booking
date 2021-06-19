# Cowin Vaccine Checker/Booking

## What is it?

- A script that can check (and _potentially_) book vaccines on the Cowin site.
- It runs every 5s.
- The vaccine booking still has issues, so feel free to play around with it if you wish.
- Note that the script scrapes the public portal cowin.gov.in, so the results may not correspond exactly to what's there in the booking portal (as the public portal returns cached data that's upto 5 or 10 minutes stale).
- To prevent bot/script activity, only 50 OTP requests can be sent per day and 1000 search requests on the private (booking) portal.

## Installation

- Need to have python3 installed.
- Install the dependencies: `pip install -r requirements.txt`
- Modify `main.py` to have your mobile number, district and preferences
- Run the script: `py ./main.py`

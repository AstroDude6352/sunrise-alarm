import argparse
import time
import serial
import os
from datetime import datetime
from model import train_model, predict_brightness
from garmin_connect import update_sleep_data

def send_to_arduino(duration):
    """Sets up arduino serial connection and sends duration command"""
    try:
        arduino = serial.Serial('/dev/tty.usbmodem14201', 9600, timeout=2)
        time.sleep(2)  
        duration_ms = int(duration * 1000)
        cmd = f"SUNRISE {duration_ms}\n"
        arduino.write(cmd.encode('utf-8'))
        print(f"Sent to Arduino: {cmd.strip()}")
        time.sleep(1)
        arduino.close()
        return True
    except Exception as e:
        print(f"Could not send to Arduino: {e}")
        return False


def update_and_train():
    """Fetches latest data from Garmin sleep data and retrainss model"""
    print("\n" + "="*50)
    print("📡 Fetching latest sleep data from Garmin...")
    print("="*50 + "\n")
    
    # fetch last 30 days of data
    df = update_sleep_data(days=30)
    
    # print statements to show data summary, since it's not available elsewhere
    if df is not None and not df.empty:
        print(f"\nRetrieved {len(df)} days of sleep data")
        print("\nRecent sleep scores:")
        print(df[['Date', 'Avg Score', 'Avg Duration']].head(7).to_string(index=False))
        
        print("\n" + "="*50)
        print("Training ML model with updated data")
        print("="*50 + "\n")
        
        train_model()
        return True
    else:
        print("Failed to update data. Using existing model.")
        return False


def run_prediction(force_update=False):
    """Runs prediction and sends to Arduino"""
    
    # checks if we should update data
    csv_file = "sleep_data.csv"
    should_update = force_update
    
    if not force_update and os.path.exists(csv_file):
        # checks if data is older than 24 hours
        file_age = time.time() - os.path.getmtime(csv_file)
        hours_old = file_age / 3600
        
        if hours_old > 24:
            print(f"Sleep data is {hours_old:.1f} hours old. Updating...")
            should_update = True
        else:
            print(f"Using cached data ({hours_old:.1f} hours old)")
    else:
        should_update = True
    
    # updates if needed
    if should_update:
        success = update_and_train()
        if not success:
            print("Continuing with existing data...")
    
    # makes prediction
    print("\n" + "="*50)
    print("Predicting optimal sunrise duration...")
    print("="*50 + "\n")
    
    r, g, b, duration = predict_brightness()
    
    print(f"Duration: {duration} seconds")
    print(f"Color will match the planet selected on Arduino")
    
    print("\n" + "="*50)
    print("Sending to Arduino...")
    print("="*50 + "\n")
    
    success = send_to_arduino(duration)
    
    if success:
        print("\nSunrise alarm configured successfully!")
        print("Make sure to select your desired planet on the Arduino first!")
    else:
        print("\nFailed to send to Arduino. Check connection.")
    
    return success


def setup_credentials():
    """interactive setup for Garmin credentials"""
    print("\n" + "="*50)
    print("Garmin Connect Setup")
    print("="*50 + "\n")
    
    email = input("Enter your Garmin email: ").strip()
    password = input("Enter your Garmin password: ").strip()
    
    # Save to .env file, will not be included in version control -> can't give away my data!
    with open('.env', 'w') as f:
        f.write(f"GARMIN_EMAIL={email}\n")
        f.write(f"GARMIN_PASSWORD={password}\n")
    
    print("\nCredentials saved to .env file")
    print("You can now run --update or --run commands\n")


# list of possible commands
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sunrise Alarm with Real-Time Garmin Integration"
    )
    parser.add_argument(
        "--setup", 
        action="store_true", 
        help="Setup Garmin credentials"
    )
    parser.add_argument(
        "--update", 
        action="store_true", 
        help="Fetch latest Garmin data and retrain model"
    )
    parser.add_argument(
        "--run", 
        action="store_true", 
        help="Predict sunrise settings and send to Arduino"
    )
    parser.add_argument(
        "--force-update", 
        action="store_true", 
        help="Force data update even if recent data exists"
    )
    parser.add_argument(
        "--train-only", 
        action="store_true", 
        help="Only train model with existing data"
    )
    
    args = parser.parse_args()

    if args.setup:
        setup_credentials()
    elif args.update:
        update_and_train()
    elif args.train_only:
        train_model()
    elif args.run:
        run_prediction(force_update=args.force_update)
    else:
        print("\n🌅 Sunrise Alarm System - Usage:")
        print("="*50)
        print("\n1️⃣  First-time setup:")
        print("   python sunrise_alarm.py --setup")
        print("\n2️⃣  Update data from Garmin & train:")
        print("   python sunrise_alarm.py --update")
        print("\n3️⃣  Run prediction & send to Arduino:")
        print("   python sunrise_alarm.py --run")
        print("   (Select planet on Arduino first!)")
        print("\n4️⃣  Force update and run:")
        print("   python sunrise_alarm.py --run --force-update")
        print("\n5️⃣  Train model with existing data:")
        print("   python sunrise_alarm.py --train-only")
        print("\n" + "="*50 + "\n")
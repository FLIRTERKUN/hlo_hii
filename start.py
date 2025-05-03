import os
from Grabber import app

def main():
    session_file = "Grabber.session"
    
    if os.path.exists(session_file):
        os.remove(session_file)
    
    app.run()

if __name__ == "__main__":
    main()
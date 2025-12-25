### Steps to install

## Clone the Repository
1. First, make sure you have Git installed.
Then run:
```bash
  git clone https://github.com/Saivenkat-206/Scheduling-App.git
```

This will install the source code to your local machine.

Navigate to the project directory:
```bash
  cd Scheduling-App
```

2. Navigate to the backend folder.
3. Run:
   ```bash
      pip install -r requirements.txt
   ```
4. Connect your MYSQL Database to the app.
5. In Database.py file, enter the credentials of MYSQL.
5. To run backend:
  ```bash
     uvicorn app.main:app --reload
  ```
6. Navigate to frontend folder.
   ```bash
     cd frontend
   ```
7. Run:
   ```
     npm install
     npm install @material-ui/core
     npm install @material-ui/icons
   ```
8. Run the fronend:
   ```
     npm run dev
   ```
This will make the app run on your local machine.

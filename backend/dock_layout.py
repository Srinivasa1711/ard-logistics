from flask import Flask, render_template, jsonify
import pyodbc
from datetime import datetime

app = Flask(__name__)

def get_connection():
    conn_str = (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=ARDKPISRV-19\SQLEXPRESS;"
        r"DATABASE=Test;"
        r"UID=yard;"
        r"PWD=yard1234;"
    )
    return pyodbc.connect(conn_str)

def fetch_task_data():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
   SELECT 'TestAveritt' AS CustomerType, RouteNumber AS Identifier, TrailerNumber, Dock, Door, Status, Specialist, StartTime, AcceptedTime
FROM dbo.TestAveritt
WHERE Status IN ('Active', 'In Progress', 'Left', 'Still There')
UNION ALL
SELECT 'TestCustomer' AS CustomerType, Customer AS Identifier, TrailerNumber, Dock, Door, Status, Specialist, StartTime, AcceptedTime
FROM dbo.TestCustomer
WHERE Status IN ('Active', 'In Progress', 'Left', 'Still There');
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    # Convert each row to a dictionary
    data = []
    for row in rows:
        row_dict = dict(zip([column[0] for column in cursor.description], row))
        row_dict['StartTime'] = row_dict['StartTime'].isoformat() if row_dict['StartTime'] else None  # Format StartTime as ISO 8601 string
        row_dict['AcceptedTime'] = row_dict['AcceptedTime'].isoformat() if row_dict['AcceptedTime'] else None  # Format AcceptedTime as ISO 8601 string
        data.append(row_dict)
    
    return data

@app.route('/')
def dock_layout():
    return render_template('Dock_New.html')

@app.route('/tasks')
def tasks():
    data = fetch_task_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5002, debug=True)

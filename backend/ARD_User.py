
from flask import Flask, render_template
from datetime import datetime
import pyodbc
from tenacity import retry, stop_after_attempt, wait_fixed


app = Flask(__name__)

def connect_to_wms():
    connection_string = (
        "DRIVER={Progress OpenEdge 11.7 Driver};"
        "HOST=10.2.100.114;"
        "PORT=8801;"
        "DATABASE=r4_seq;"
        "UID=crystal;"
        "PWD=reports"
    )
    connection = pyodbc.connect(connection_string)
    return connection
    
# Retry decorator with 3 retries and a 2-second wait between attempts
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def fetch_pending_labels():
    connection = connect_to_wms()
    cursor = connection.cursor()
    
    # Query for Pending Labels
    pending_labels_query = """
    SELECT CenterId, COUNT(DISTINCT VIN) AS Pending_Labels
    FROM PUB.wSeqDataMstr
    WHERE StatusCode = '' AND UserField5 <> '' AND CenterId NOT LIKE '%CKD%' AND CenterId NOT LIKE '%PL%'
    GROUP BY CenterId ORDER BY Pending_Labels DESC
    """
    from flask import Flask, render_template
    from datetime import datetime

    cursor.execute(pending_labels_query)
    pending_labels_rows = cursor.fetchall()

    # Query for Skips
    skips_query = """
    SELECT CenterId, COUNT(DISTINCT VIN) AS Skips
    FROM PUB.wSeqDataMstr
    WHERE StatusCode = 'skp' AND OrderNo = 0
    GROUP BY CenterId
    """
    cursor.execute(skips_query)
    skips_rows = cursor.fetchall()

    # Query for Racks Not Shipped
    racks_not_shipped_query = """
    SELECT CenterId, COUNT(CenterId) AS Racks_Not_Shipped
    FROM PUB.wSeqTrksheet
    WHERE Shipped = 0
    GROUP BY CenterId
    """
    cursor.execute(racks_not_shipped_query)
    racks_not_shipped_rows = cursor.fetchall()

    cursor.close()
    connection.close()

    # Map CenterId to Zones and Center Names
    center_id_mapping = {
        "BOS-CN-2": ("BOS Cargo Net", "Zone 1"),
        "AUT-LH-2": ("AUTONEUM Front Carpet LH", "Zone 1"),
        "AUT-RE-2": ("AUTONEUM Rear Carpet", "Zone 1"),
        "AUT-RH-2": ("AUTONEUM Front Carpet RH", "Zone 1"),
        "POA-FT-2": ("POAI Fuel Tanks", "Zone 2"),
        "ELAN-2": ("Elanders Plant 2", "Zone 2"),
        "MAG-RH-2": ("MAGNA Mirrors RH - 167", "Zone 1"),
        "ELAN-1": ("Elanders Plant 1", "Zone 2"),
        "MAG-LH-2": ("MAGNA Mirrors LH - 167", "Zone 1"),
        "IFA-2P-2": ("IFA Rear Prop Shaft", "Zone 1"),
        "VAL-DB-2": ("VALEO DBE", "Zone 1"),
        "GRM-GH-2": ("GRM Grab Handle - 167", "Zone 2"),
        "AGC-LH-2": ("AGC Quarter Glass LH", "Zone 1"),
        "GRM-CC-2": ("GRM Center Console - 167", "Zone 2"),
        "AGC-RH-2": ("AGC Quarter Glass RH", "Zone 1"),
        "DRX-UP-2": ("DRX IP Upper", "Zone 2"),
        "IFA-2P-1": ("IFA Front Prop Shaft", "Zone 1"),
        "AGC-BL-2": ("AGC Backlight", "Zone 1"),
        "AGC-WS-2": ("AGC Windshield", "Zone 1"),
        "DRX-LW-2": ("DRX IP Lowers", "Zone 2"),
        "FSR-TD-2": ("FISCHER Door", "Zone 2"),
        "FSR-TD-1": ("FISCHER Door - P1", "Zone 2"),
        "KASAI-LG-1": ("KASAI Liftgate", "Zone 1"),
        "MAL-HV-2": ("MAHLE HVAC", "Zone 2"),
        "DRX-GB-2": ("DRX Glove Box", "Zone 2"),
        "MAG-LH-1": ("MAGNA Mirrors LH - EVA", "Zone 1"),
        "GRM-EVDS-1": ("GRM EVA Dock Socket", "Zone 1"),
        "TYG-SW-2": ("Steering Wheel - 167", "Zone 1"),
        "KASAI-WN-1": ("KASAI Windshield", "Zone 1"),
        "TYG-SW-1": ("Steering Wheel - EVA", "Zone 1"),
        "GRM-EVGH-1": ("GRM Grab Handle EVA", "Zone 1"),
        "GRM-EVCC-1": ("GRM Center Console EVA", "Zone 1"),
        "MAG-RH-1": ("MAGNA Mirrors RH - EVA", "Zone 1"),
        "BOS-LH-2": ("BOS Rollo Blind LH", "Zone 1"),
        "BOS-RH-2": ("BOS Rollo Blind RH", "Zone 1"),
        "FAA-CP-1": ("Fujikura Cockpit", "Zone 1"),
        "FAA-EP-1": ("Fujikura Engine", "Zone 1"),
        "GRM-GH-1": ("GRM Grab Handle - P1", "Zone 2"),
        "VAL-DB-1": ("VALEO DBE - P1", "Zone 1"),
        "MAL-HV-1": ("MAHLE HVAC - P1", "Zone 2"),
        "AGC-BL-1": ("AGC Backlight - P1", "Zone 1"),
        "AUT-LH-1": ("AUTONEUM Front Carpet LH - P1", "Zone 1"),
        "AUT-RE-1": ("AUTONEUM Rear Carpet - P1", "Zone 1"),
        "AUT-RH-1": ("Autoneum Front Carpet RH - P1", "Zone 1"),
        "BOS-CN-1": ("BOS Cargo Net - P1", "Zone 1"),
        "DRX-LW-1": ("DRX Lowers - P1", "Zone 2"),
        "FAA-CP-PL1": ("Fujikura Cockpit - P1", "Zone 1"),
        "IFA-1P-1": ("IFA Front Shaft - P1", "Zone 1"),
        "IFA-1P-2": ("IFA Rear Shaft - P1", "Zone 1"),
        "POA-FT-1": ("POAI Fuel Tanks - P1", "Zone 2"),
        "AGC-LH-1": ("AGC Quarter Glass LH - P1", "Zone 1"),
        "AGC-RH-1": ("AGC Quarter Glass RH - P1", "Zone 1"),
        "AGC-WS-1": ("AGC Windshield - P1", "Zone 1"),
        "DRX-GB-1": ("DRX Glove Box - P1", "Zone 2"),
        "DRX-UP-1": ("DRX IP Upper - P1", "Zone 2"),
        "GRM-CC-1": ("GRM Center Console - P1", "Zone 2")
    }

    # Convert fetched data to dictionaries for easy lookup
    skips_dict = dict(skips_rows)
    racks_not_shipped_dict = dict(racks_not_shipped_rows)

    replaced_rows = []
    for row in pending_labels_rows:
        center_id = row[0]
        pending_labels = int(row[1])
        skips = skips_dict.get(center_id, 0)
        racks_not_shipped = racks_not_shipped_dict.get(center_id, 0)
        mapped_value = center_id_mapping.get(center_id, (center_id, "Unknown"))
        replaced_rows.append((mapped_value[0], mapped_value[1], pending_labels, skips, racks_not_shipped))

    zones = sorted(set(center[1] for center in center_id_mapping.values()))
    centers = sorted(set(center[0] for center in center_id_mapping.values()))

    return replaced_rows, zones, centers

# Retry decorator with 3 retries and a 2-second wait between attempts
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def fetch_pre_trim_buffers():
    connection = connect_to_wms()
    cursor = connection.cursor()

    # Query for Plant 1 Pre-Trim Buffer
    cursor.execute("""
        SELECT COUNT(DISTINCT VIN) AS Plant_1_Pre_Trim 
        FROM PUB.wSeqChkPnt
        WHERE ChkPntCode = '4911' AND ChkPntDateTime > (
            SELECT ChkPntDateTime
            FROM PUB.wSeqChkPnt
            WHERE ChkPntCode = '4911' AND VIN = (
                SELECT VIN FROM PUB.wSeqChkPnt 
                WHERE ChkPntDateTime = (
                    SELECT MAX(ChkPntDateTime) 
                    FROM PUB.wSeqChkPnt 
                    WHERE ChkPntCode = '4921'
                )
            )
        )
    """)
    plant_1_pre_trim = cursor.fetchone()[0]

    # Query for Plant 2 Pre-Trim Buffer
    cursor.execute("""
        SELECT COUNT(DISTINCT VIN) AS Plant_2_Pre_Trim 
        FROM PUB.wSeqChkPnt
        WHERE ChkPntCode = '4912' AND ChkPntDateTime > (
            SELECT ChkPntDateTime
            FROM PUB.wSeqChkPnt
            WHERE ChkPntCode = '4912' AND VIN = (
                SELECT VIN FROM PUB.wSeqChkPnt 
                WHERE ChkPntDateTime = (
                    SELECT MAX(ChkPntDateTime) 
                    FROM PUB.wSeqChkPnt 
                    WHERE ChkPntCode = '5002'
                )
            )
        )
    """)
    plant_2_pre_trim = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    # Determine colors based on buffer values
    plant_1_pre_trim_color = "rgb(11,211,30)" if plant_1_pre_trim > 115 else "rgb(255,225,28)" if 105 <= plant_1_pre_trim <= 115 else "rgb(226,0,0)"
    plant_2_pre_trim_color = "rgb(11,211,30)" if plant_2_pre_trim > 225 else "rgb(255,225,28)" if 210 <= plant_2_pre_trim <= 225 else "rgb(226,0,0)"

    return plant_1_pre_trim, plant_1_pre_trim_color, plant_2_pre_trim, plant_2_pre_trim_color

def fetch_picks_per_hour():
    connection = connect_to_wms()
    cursor = connection.cursor()
    
    picks_per_hour_query = """
SELECT
    CenterId,
    TO_CHAR(EPDateTime, 'MM/DD/YYYY') AS EPDay,
    CASE
        WHEN TO_CHAR(EPDateTime, 'HH12:00 AM') = '00:00 AM' THEN '12:00 AM'
        WHEN TO_CHAR(EPDateTime, 'HH12:00 PM') = '00:00 PM' THEN '12:00 PM'
        ELSE TO_CHAR(EPDateTime, 'HH12:00 AM')
    END AS EPHour,
    COUNT(DISTINCT VIN) AS Parts_Sequenced
FROM PUB.wSeqDataMstr
WHERE StatusCode = 'EP'
    AND EPDateTime >= NOW()-43200000
    AND CenterId NOT LIKE '%CKD%'
    AND CenterId NOT LIKE '%PL%'
    AND CenterId <> 'XXXX'
GROUP BY CenterId, EPDay, EPHour
    """
    cursor.execute(picks_per_hour_query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    
    picks_data = {}
    for row in rows:
        center_id = row[0]
        if center_id not in picks_data:
            picks_data[center_id] = []
        picks_data[center_id].append({
            'day': row[1],
            'hour': row[2],
            'parts_sequenced': row[3]
        })
    return picks_data

from datetime import datetime, timedelta

def fetch_labels_hour():
    conn = connect_to_wms()
    cursor = conn.cursor()

    query = """
    SELECT 
        CenterId,
        AssemblyChkPtReceivedDate,
        CASE 
            WHEN SUBSTRING(AssemblyChkPtReceivedTime, 1, 2) = '00' THEN '12:00 AM'
            WHEN SUBSTRING(AssemblyChkPtReceivedTime, 1, 2) = '12' THEN '12:00 PM'
            WHEN SUBSTRING(AssemblyChkPtReceivedTime, 1, 2) < '12' THEN 
                SUBSTRING(AssemblyChkPtReceivedTime, 1, 2) || ':00 AM'
            ELSE 
                LPAD(CAST(CAST(SUBSTRING(AssemblyChkPtReceivedTime, 1, 2) AS INTEGER) - 12 AS VARCHAR(2)), 2, ' ') || ':00 PM'
        END AS AssemblyTimeText,
        CAST(EPDateTime AS DATE) AS EPDate,
        CASE
            WHEN TO_CHAR(EPDateTime, 'HH12:00 AM') = '00:00 AM' THEN '12:00 AM'
            WHEN TO_CHAR(EPDateTime, 'HH12:00 PM') = '00:00 PM' THEN '12:00 PM'
            ELSE TO_CHAR(EPDateTime, 'HH12:00 AM')
        END AS EPTimeText,
        COUNT(DISTINCT VIN) AS Pending_Labels
    FROM 
        PUB.wSeqDataMstr
    WHERE 
        CenterId NOT LIKE '%CKD%' 
        AND CenterId NOT LIKE '%PL%' AND CenterId <> 'XXXX'
        AND (EPDateTime >= NOW() - 43200000 OR EPDateTime IS NULL)
        AND AssemblyChkPtReceivedDate >= CURDATE() - 1 
    GROUP BY 
        CenterId, AssemblyChkPtReceivedDate, AssemblyTimeText, EPDate, EPTimeText
    ORDER BY 
        EPDate DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Create the current 12-hour window (most recent last)
    now = datetime.now()
    hourly_window = [(now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0) for i in reversed(range(12))]

    # Store pending labels per center by hour
    label_data = {}

    for row in results:
        center_id = row[0]
        assembly_date = row[1]
        assembly_time_str = row[2]
        ep_date = row[3]
        ep_time_str = row[4]
        pending_count = row[5]

        # Combine date and time into full datetimes
        try:
            start_hour = datetime.strptime(f"{assembly_date} {assembly_time_str}", "%Y-%m-%d %I:%M %p")
        except:
            continue  # skip row if bad format

        if ep_date and ep_time_str:
            try:
                end_hour = datetime.strptime(f"{ep_date} {ep_time_str}", "%Y-%m-%d %I:%M %p")
            except:
                end_hour = now  # fallback
        else:
            end_hour = now  # if EPDate is NULL, assume still pending

        # Loop through each hour in the 12-hour window
        for i, hour in enumerate(hourly_window):
            if start_hour <= hour <= end_hour:
                if center_id not in label_data:
                    label_data[center_id] = [0] * 12
                label_data[center_id][i] += pending_count

    return label_data
	
# Fetch Racks Pending Shipment Information
from datetime import datetime

# Retry decorator with 3 retries and a 2-second wait between attempts
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def fetch_racks_pending():
    connection = connect_to_wms()
    cursor = connection.cursor()
    
    racks_pending_query = """
    SELECT Supplier, PlantCd, TrackingNo, PartName, CompleteDateTime
    FROM PUB.wSeqTrksheet
    WHERE Shipped = 0
    """
    cursor.execute(racks_pending_query)
    rows = cursor.fetchall()
    
    cursor.close()
    connection.close()

    racks_pending_data = []
    
    current_time = datetime.now()  # Get current time to calculate elapsed time

    for row in rows:
        complete_time = row[4]
        time_elapsed = current_time - complete_time

        # Calculate the elapsed time in a readable format
        if time_elapsed.days > 0:
            days = time_elapsed.days
            hours = time_elapsed.seconds // 3600
            minutes = (time_elapsed.seconds % 3600) // 60
            elapsed_time_str = f"{days}d {hours}h {minutes}m"
        elif time_elapsed.seconds >= 3600:
            hours = time_elapsed.seconds // 3600
            minutes = (time_elapsed.seconds % 3600) // 60
            elapsed_time_str = f"{hours}h {minutes}m"
        else:
            minutes = time_elapsed.seconds // 60
            elapsed_time_str = f"{minutes}m"

        # Append data with serialized timedelta
        racks_pending_data.append({
            "Supplier": row[0],
            "PlantCd": row[1],
            "TrackingNo": row[2],
            "PartName": row[3],
            "CompleteDateTime": complete_time.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
            "TimeElapsed": elapsed_time_str,  # Human-readable elapsed time
            "TimeDeltaSeconds": time_elapsed.total_seconds()  # Include total seconds as a number
        })

    # Sort the data by TimeDeltaSeconds in descending order
    racks_pending_data.sort(key=lambda x: x['TimeDeltaSeconds'], reverse=True)

    return racks_pending_data


@app.route('/')
def pending_labels():
    pending_labels_data, zones, centers = fetch_pending_labels()
    plant_1_pre_trim, plant_1_pre_trim_color, plant_2_pre_trim, plant_2_pre_trim_color = fetch_pre_trim_buffers()
    return render_template('pending_Lebels_FilterView.html', 
                           data=pending_labels_data, 
                           zones=zones, 
                           centers=centers, 
                           plant_1_pre_trim=plant_1_pre_trim,
                           plant_1_pre_trim_color=plant_1_pre_trim_color,
                           plant_2_pre_trim=plant_2_pre_trim,
                           plant_2_pre_trim_color=plant_2_pre_trim_color)
def index():
    return render_template("pending_Lebels_FilterView.html")

@app.route('/api/pending_labels', methods=['GET'])
def get_pending_labels():
    data, zones, centers = fetch_pending_labels()
    return jsonify({
        "data": data,
        "zones": zones,
        "centers": centers
    })

@app.route('/api/pre_trim_buffers', methods=['GET'])
def get_pre_trim_buffers():
    plant_1, color_1, plant_2, color_2 = fetch_pre_trim_buffers()
    return jsonify({
        "plant_1_pre_trim": plant_1,
        "plant_1_color": color_1,
        "plant_2_pre_trim": plant_2,
        "plant_2_color": color_2
    })
    
@app.route('/zone')
def zone():
    pending_labels_data, zones, centers = fetch_pending_labels()
    plant_1_pre_trim, plant_1_pre_trim_color, plant_2_pre_trim, plant_2_pre_trim_color = fetch_pre_trim_buffers()
    
    return render_template('pending_Lebels_ZoneView.html', 
                           data=pending_labels_data, 
                           zones=zones, 
                           centers=centers, 
                           plant_1_pre_trim=plant_1_pre_trim,
                           plant_1_pre_trim_color=plant_1_pre_trim_color,
                           plant_2_pre_trim=plant_2_pre_trim,
                           plant_2_pre_trim_color=plant_2_pre_trim_color)
def index():
    return render_template("pending_Lebels_ZoneView.html")

# Route for displaying Racks Pending Shipment
@app.route('/racks_pending')
def racks_pending():
    racks_pending_data = fetch_racks_pending()
    
    # Extract unique suppliers and plant codes for the filters
    suppliers = sorted(list(set(row['Supplier'] for row in racks_pending_data)))
    plant_codes = sorted(list(set(row['PlantCd'] for row in racks_pending_data)))
    
    return render_template('Racks_Pending.html', data=racks_pending_data, suppliers=suppliers, plant_codes=plant_codes)

    
from flask import jsonify

@app.route('/api/racks_pending_data', methods=['GET'])
def racks_pending_data():
    racks_pending_data = fetch_racks_pending()
    return jsonify(racks_pending_data)
def index():
    return render_template("Racks_Pending.html")

@app.route('/charts')
def charts():
    # Fetch data
    picks_per_hour_data = fetch_picks_per_hour()
    labels_hour_data = fetch_labels_hour()

    # Mapping center IDs to actual cell names and zones
    center_id_mapping = {
        "BOS-CN-2": ("BOS Cargo Net", "Zone 1"),
        "AUT-LH-2": ("AUTONEUM Front Carpet LH", "Zone 1"),
        "AUT-RE-2": ("AUTONEUM Rear Carpet", "Zone 1"),
        "AUT-RH-2": ("AUTONEUM Front Carpet RH", "Zone 1"),
        "POA-FT-2": ("POAI Fuel Tanks", "Zone 2"),
        "ELAN-2": ("Elanders Plant 2", "Zone 2"),
        "MAG-RH-2": ("MAGNA Mirrors RH - 167", "Zone 1"),
        "ELAN-1": ("Elanders Plant 1", "Zone 2"),
        "MAG-LH-2": ("MAGNA Mirrors LH - 167", "Zone 1"),
        "IFA-2P-2": ("IFA Rear Prop Shaft", "Zone 1"),
        "VAL-DB-2": ("VALEO DBE", "Zone 1"),
        "GRM-GH-2": ("GRM Grab Handle - 167", "Zone 2"),
        "AGC-LH-2": ("AGC Quarter Glass LH", "Zone 1"),
        "GRM-CC-2": ("GRM Center Console - 167", "Zone 2"),
        "AGC-RH-2": ("AGC Quarter Glass RH", "Zone 1"),
        "DRX-UP-2": ("DRX IP Upper", "Zone 2"),
        "IFA-2P-1": ("IFA Front Prop Shaft", "Zone 1"),
        "AGC-BL-2": ("AGC Backlight", "Zone 1"),
        "AGC-WS-2": ("AGC Windshield", "Zone 1"),
        "DRX-LW-2": ("DRX IP Lowers", "Zone 2"),
        "FSR-TD-2": ("FISCHER Door", "Zone 2"),
        "FSR-TD-1": ("FISCHER Door - P1", "Zone 2"),
        "KASAI-LG-1": ("KASAI Liftgate", "Zone 1"),
        "MAL-HV-2": ("MAHLE HVAC", "Zone 2"),
        "DRX-GB-2": ("DRX Glove Box", "Zone 2"),
        "MAG-LH-1": ("MAGNA Mirrors LH - EVA", "Zone 1"),
        "GRM-EVDS-1": ("GRM EVA Dock Socket", "Zone 1"),
        "TYG-SW-2": ("Steering Wheel - 167", "Zone 1"),
        "KASAI-WN-1": ("KASAI Windshield", "Zone 1"),
        "TYG-SW-1": ("Steering Wheel - EVA", "Zone 1"),
        "GRM-EVGH-1": ("GRM Grab Handle EVA", "Zone 1"),
        "GRM-EVCC-1": ("GRM Center Console EVA", "Zone 1"),
        "MAG-RH-1": ("MAGNA Mirrors RH - EVA", "Zone 1"),
        "BOS-LH-2": ("BOS Rollo Blind LH", "Zone 1"),
        "BOS-RH-2": ("BOS Rollo Blind RH", "Zone 1"),
        "FAA-CP-1": ("Fujikura Cockpit", "Zone 1"),
        "FAA-EP-1": ("Fujikura Engine", "Zone 1"),
        "GRM-GH-1": ("GRM Grab Handle - P1", "Zone 2"),
        "VAL-DB-1": ("VALEO DBE - P1", "Zone 1"),
        "MAL-HV-1": ("MAHLE HVAC - P1", "Zone 2"),
        "AGC-BL-1": ("AGC Backlight - P1", "Zone 1"),
        "AUT-LH-1": ("AUTONEUM Front Carpet LH - P1", "Zone 1"),
        "AUT-RE-1": ("AUTONEUM Rear Carpet - P1", "Zone 1"),
        "AUT-RH-1": ("Autoneum Front Carpet RH - P1", "Zone 1"),
        "BOS-CN-1": ("BOS Cargo Net - P1", "Zone 1"),
        "DRX-LW-1": ("DRX Lowers - P1", "Zone 2"),
        "FAA-CP-PL1": ("Fujikura Cockpit - P1", "Zone 1"),
        "IFA-1P-1": ("IFA Front Shaft - P1", "Zone 1"),
        "IFA-1P-2": ("IFA Rear Shaft - P1", "Zone 1"),
        "POA-FT-1": ("POAI Fuel Tanks - P1", "Zone 2"),
        "AGC-LH-1": ("AGC Quarter Glass LH - P1", "Zone 1"),
        "AGC-RH-1": ("AGC Quarter Glass RH - P1", "Zone 1"),
        "AGC-WS-1": ("AGC Windshield - P1", "Zone 1"),
        "DRX-GB-1": ("DRX Glove Box - P1", "Zone 2"),
        "DRX-UP-1": ("DRX IP Upper - P1", "Zone 2"),
        "GRM-CC-1": ("GRM Center Console - P1", "Zone 2")
    }

    # Combine picks and labels data into a single dataset
    combined_data = {}
    for center_id in set(picks_per_hour_data.keys()).union(labels_hour_data.keys()):
        picks = picks_per_hour_data.get(center_id, [])
        labels = labels_hour_data.get(center_id, [0] * 12)

        combined_data[center_id] = {
            'picks': picks,
            'labels': labels
        }

    # Map center IDs in combined_data to actual cell names
    mapped_combined_data = {}
    for center_id, data in combined_data.items():
        cell_name = center_id_mapping.get(center_id, (center_id, "Unknown"))[0]
        mapped_combined_data[cell_name] = data

    # Extract zones from the center_id_mapping
    zones = sorted(set(zone for _, zone in center_id_mapping.values()))

    return render_template(
        'ARD_Charts.html',
        data=mapped_combined_data,
        zones=zones,
        center_zone_mapping=center_id_mapping
    )
    
@app.route('/api/charts_data', methods=['GET'])
def charts_data():
    # Fetch updated data
    picks_per_hour_data = fetch_picks_per_hour()
    labels_hour_data = fetch_labels_hour()
    
    # Mapping center IDs to actual cell names and zones
    center_id_mapping = {
        "BOS-CN-2": ("BOS Cargo Net", "Zone 1"),
        "AUT-LH-2": ("AUTONEUM Front Carpet LH", "Zone 1"),
        "AUT-RE-2": ("AUTONEUM Rear Carpet", "Zone 1"),
        "AUT-RH-2": ("AUTONEUM Front Carpet RH", "Zone 1"),
        "POA-FT-2": ("POAI Fuel Tanks", "Zone 2"),
        "ELAN-2": ("Elanders Plant 2", "Zone 2"),
        "MAG-RH-2": ("MAGNA Mirrors RH - 167", "Zone 1"),
        "ELAN-1": ("Elanders Plant 1", "Zone 2"),
        "MAG-LH-2": ("MAGNA Mirrors LH - 167", "Zone 1"),
        "IFA-2P-2": ("IFA Rear Prop Shaft", "Zone 1"),
        "VAL-DB-2": ("VALEO DBE", "Zone 1"),
        "GRM-GH-2": ("GRM Grab Handle - 167", "Zone 2"),
        "AGC-LH-2": ("AGC Quarter Glass LH", "Zone 1"),
        "GRM-CC-2": ("GRM Center Console - 167", "Zone 2"),
        "AGC-RH-2": ("AGC Quarter Glass RH", "Zone 1"),
        "DRX-UP-2": ("DRX IP Upper", "Zone 2"),
        "IFA-2P-1": ("IFA Front Prop Shaft", "Zone 1"),
        "AGC-BL-2": ("AGC Backlight", "Zone 1"),
        "AGC-WS-2": ("AGC Windshield", "Zone 1"),
        "DRX-LW-2": ("DRX IP Lowers", "Zone 2"),
        "FSR-TD-2": ("FISCHER Door", "Zone 2"),
        "FSR-TD-1": ("FISCHER Door - P1", "Zone 2"),
        "KASAI-LG-1": ("KASAI Liftgate", "Zone 1"),
        "MAL-HV-2": ("MAHLE HVAC", "Zone 2"),
        "DRX-GB-2": ("DRX Glove Box", "Zone 2"),
        "MAG-LH-1": ("MAGNA Mirrors LH - EVA", "Zone 1"),
        "GRM-EVDS-1": ("GRM EVA Dock Socket", "Zone 1"),
        "TYG-SW-2": ("Steering Wheel - 167", "Zone 1"),
        "KASAI-WN-1": ("KASAI Windshield", "Zone 1"),
        "TYG-SW-1": ("Steering Wheel - EVA", "Zone 1"),
        "GRM-EVGH-1": ("GRM Grab Handle EVA", "Zone 1"),
        "GRM-EVCC-1": ("GRM Center Console EVA", "Zone 1"),
        "MAG-RH-1": ("MAGNA Mirrors RH - EVA", "Zone 1"),
        "BOS-LH-2": ("BOS Rollo Blind LH", "Zone 1"),
        "BOS-RH-2": ("BOS Rollo Blind RH", "Zone 1"),
        "FAA-CP-1": ("Fujikura Cockpit", "Zone 1"),
        "FAA-EP-1": ("Fujikura Engine", "Zone 1"),
        "GRM-GH-1": ("GRM Grab Handle - P1", "Zone 2"),
        "VAL-DB-1": ("VALEO DBE - P1", "Zone 1"),
        "MAL-HV-1": ("MAHLE HVAC - P1", "Zone 2"),
        "AGC-BL-1": ("AGC Backlight - P1", "Zone 1"),
        "AUT-LH-1": ("AUTONEUM Front Carpet LH - P1", "Zone 1"),
        "AUT-RE-1": ("AUTONEUM Rear Carpet - P1", "Zone 1"),
        "AUT-RH-1": ("Autoneum Front Carpet RH - P1", "Zone 1"),
        "BOS-CN-1": ("BOS Cargo Net - P1", "Zone 1"),
        "DRX-LW-1": ("DRX Lowers - P1", "Zone 2"),
        "FAA-CP-PL1": ("Fujikura Cockpit - P1", "Zone 1"),
        "IFA-1P-1": ("IFA Front Shaft - P1", "Zone 1"),
        "IFA-1P-2": ("IFA Rear Shaft - P1", "Zone 1"),
        "POA-FT-1": ("POAI Fuel Tanks - P1", "Zone 2"),
        "AGC-LH-1": ("AGC Quarter Glass LH - P1", "Zone 1"),
        "AGC-RH-1": ("AGC Quarter Glass RH - P1", "Zone 1"),
        "AGC-WS-1": ("AGC Windshield - P1", "Zone 1"),
        "DRX-GB-1": ("DRX Glove Box - P1", "Zone 2"),
        "DRX-UP-1": ("DRX IP Upper - P1", "Zone 2"),
        "GRM-CC-1": ("GRM Center Console - P1", "Zone 2")
    }

    # Combine picks and labels data into a single dataset
    combined_data = {}
    for center_id in set(picks_per_hour_data.keys()).union(labels_hour_data.keys()):
        picks = picks_per_hour_data.get(center_id, [])
        labels = labels_hour_data.get(center_id, [0] * 12)

        combined_data[center_id] = {
            'picks': picks,
            'labels': labels
        }

    # Map center IDs in combined_data to actual cell names
    mapped_combined_data = {}
    for center_id, data in combined_data.items():
        cell_name = center_id_mapping.get(center_id, (center_id, "Unknown"))[0]
        mapped_combined_data[cell_name] = data

    return jsonify(mapped_combined_data)
    
def fetch_efficiency_report():
    connection = connect_to_wms()
    cursor = connection.cursor()

    # SQL query for Efficiency Report
    efficiency_report_query = """
SELECT
    CenterId,
    EPDay,
    EPHour,
    Parts_Sequenced,
    CASE 
    WHEN CenterId IN ('BOS-CN-2', 'AUT-LH-2', 'AUT-RE-2', 'AUT-RH-2', 'POA-FT-2', 
                      'ELAN-2', 'MAG-RH-2', 'MAG-LH-2', 'IFA-2P-2', 'VAL-DB-2', 
                      'GRM-GH-2', 'AGC-LH-2', 'GRM-CC-2', 'AGC-RH-2', 'DRX-UP-2', 
                      'AGC-BL-2', 'AGC-WS-2', 'DRX-LW-2', 'FSR-TD-2', 'MAL-HV-2', 
                      'DRX-GB-2', 'TYG-SW-2', 'BOS-LH-2', 'BOS-RH-2') 
         AND Parts_Sequenced >= 48 THEN '1'
    
    WHEN CenterId IN ('ELAN-1', 'IFA-2P-1', 'FSR-TD-1', 'KASAI-LG-1', 'MAG-LH-1', 
                      'GRM-EVDS-1', 'KASAI-WN-1', 'TYG-SW-1', 'GRM-EVGH-1', 
                      'GRM-EVCC-1', 'MAG-RH-1', 'FAA-CP-1', 'FAA-EP-1', 
                      'AGC-BL-1', 'AGC-LH-1', 'AGC-RH-1', 'AGC-WS-1', 'BOS-CN-1', 
                      'BOS-LH-1', 'BOS-RH-1', 'IFA-1P-1', 'IFA-1P-2', 'VAL-DB-1', 
                      'DRX-GB-1', 'DRX-LW-1', 'DRX-UP-1', 'GRM-CC-1', 'GRM-GH-1', 
                      'MAL-HV-1', 'AUT-LH-1', 'AUT-RE-1', 'AUT-RH-1', 'POA-FT-1') 
         AND Parts_Sequenced >= 24 THEN '1'
    
    ELSE '0'
    END AS QuotaStatus
FROM (
    SELECT
        CenterId,
        TO_CHAR(EPDateTime, 'MM/DD/YYYY') AS EPDay,
        CASE
            WHEN TO_CHAR(EPDateTime, 'HH12:00 AM') = '00:00 AM' THEN '12:00 AM'
            WHEN TO_CHAR(EPDateTime, 'HH12:00 PM') = '00:00 PM' THEN '12:00 PM'
            ELSE TO_CHAR(EPDateTime, 'HH12:00 AM')
        END AS EPHour,
        COUNT(DISTINCT VIN) AS Parts_Sequenced
    FROM PUB.wSeqDataMstr
    WHERE StatusCode = 'EP' 
        AND EPDateTime >= NOW()-43200000 
        AND CenterId NOT LIKE '%CKD%'
        AND CenterId NOT LIKE '%PL%'
    GROUP BY CenterId, EPDay, EPHour
) AS SequencedParts
    """
    
    cursor.execute(efficiency_report_query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    # Structure data as a list of dictionaries
    report_data = [
        {
            "CenterId": row[0],
            "EPDay": row[1],
            "EPHour": row[2],
            "Parts_Sequenced": row[3],
            "QuotaStatus": row[4]
        }
        for row in rows
    ]
    return report_data

@app.route('/efficiency_report')
def efficiency_report():
    report_data = fetch_efficiency_report()
    return render_template('ARD_Efficiency_Report.html', data=report_data)
def index():
    return render_template("ARD_Efficiency_Report.html")
    
@app.route('/ckd')
def ckd():
    # Fetch CKD data before rendering the template
    connection = connect_to_wms()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT 
        CenterId,
        TO_CHAR(EPDateTime, 'MM/DD/YYYY') AS EPDay,
        CASE
            WHEN TO_CHAR(EPDateTime, 'HH12:00 AM') = '00:00 AM' THEN '12:00 AM'
            WHEN TO_CHAR(EPDateTime, 'HH12:00 PM') = '00:00 PM' THEN '12:00 PM'
            ELSE TO_CHAR(EPDateTime, 'HH12:00 AM')
        END AS EPHour,
        COUNT(DISTINCT VIN) AS Parts_Sequenced
    FROM PUB.wSeqDataMstr
    WHERE StatusCode = 'EP'
        AND EPDateTime >= NOW()-43200000
        AND CenterId LIKE '%CKD%' 
    GROUP BY CenterId, EPDay, EPHour
    """)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    # Convert query results to dictionary format
    ckd_data = {}
    for row in rows:
        center_id = row[0]
        if center_id not in ckd_data:
            ckd_data[center_id] = []
        ckd_data[center_id].append({
            'day': row[1],
            'hour': row[2],
            'parts_sequenced': row[3]
        })

    return render_template('ARD_CKD.html', data=ckd_data)
def index():
    return render_template("ARD_CKD.html")
    
@app.route('/api/ckd_data', methods=['GET'])
def ckd_data():
    connection = connect_to_wms()
    cursor = connection.cursor()

    ckd_query = """
    SELECT 
        CenterId,
        TO_CHAR(EPDateTime, 'MM/DD/YYYY') AS EPDay,
        CASE
            WHEN TO_CHAR(EPDateTime, 'HH12:00 AM') = '00:00 AM' THEN '12:00 AM'
            WHEN TO_CHAR(EPDateTime, 'HH12:00 PM') = '00:00 PM' THEN '12:00 PM'
            ELSE TO_CHAR(EPDateTime, 'HH12:00 AM')
        END AS EPHour,
        COUNT(DISTINCT VIN) AS Parts_Sequenced
    FROM PUB.wSeqDataMstr
    WHERE StatusCode = 'EP'
        AND EPDateTime >= NOW()-43200000
        AND CenterId LIKE '%CKD%' 
    GROUP BY CenterId, EPDay, EPHour
    """

    cursor.execute(ckd_query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    ckd_data = {}
    for row in rows:
        center_id = row[0]
        if center_id not in ckd_data:
            ckd_data[center_id] = []
        ckd_data[center_id].append({
            'day': row[1],
            'hour': row[2],
            'parts_sequenced': row[3]
        })

    return jsonify(ckd_data)

if __name__ == '__main__':
    app.run(port=5009, debug=True)

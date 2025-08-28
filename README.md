# Radio Station Inspection System

A web application for managing and visualizing radio station license and inspection data.

## Features

- **File Upload**: Upload Excel files containing license and inspection data
- **Data Processing**: Automatically process and store data in SQLite database
- **Data Matching**: Match stations between license and inspection databases based on station name and frequency
- **Interactive Map**: Visualize radio stations and microwave links on a custom SVG map
- **Statistics**: Real-time statistics about loaded data

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Load Sample Data**: Click "Load Sample Data" to use the provided sample files
2. **Upload Custom Data**: Use the file upload buttons to upload your own Excel files
3. **View Statistics**: See real-time statistics about your data
4. **Visualize on Map**: Click "Load Map Data" to see stations plotted on the map

## Data Format

### License Data (license.xlsx)
Expected columns:
- `SID_LONG`, `SID_LAT`: Station coordinates
- `STN_NAME`: Station name
- `FREQ`: Frequency
- `LINK_ID`: Microwave link identifier
- `CLNT_NAME`: Client name
- Other metadata columns

### Inspection Data (Pemeriksaan stasiun radio.xlsx)
Expected columns:
- `SID_LONG`, `SID_LAT`: Station coordinates
- `STN_NAME`: Station name
- `FREQ`: Frequency
- `STATUS`: Inspection status
- `TANGGAL_PEMERIKSAAN`: Inspection date
- Other metadata columns

## Map Legend

- **Blue circles**: License stations
- **Red circles**: Inspection stations
- **Green lines**: Microwave links between stations
- **Hover**: Show station details in tooltip

## Technologies Used

- **Backend**: Python Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite
- **Data Processing**: Pandas
- **Visualization**: Custom SVG-based mapping
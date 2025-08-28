import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///radio_inspection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class LicenseData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clnt_id = db.Column(db.String(100))
    clnt_name = db.Column(db.String(200))
    stn_name = db.Column(db.String(200))
    freq = db.Column(db.Float)
    sid_long = db.Column(db.Float)
    sid_lat = db.Column(db.Float)
    link_id = db.Column(db.String(100))
    callsign = db.Column(db.String(100))
    province = db.Column(db.String(100))
    city = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InspectionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal_pemeriksaan = db.Column(db.Date)
    clnt_name = db.Column(db.String(200))
    link_id = db.Column(db.String(100))
    stn_name = db.Column(db.String(200))
    stasiun_lawan = db.Column(db.String(200))
    sid_long = db.Column(db.Float)
    sid_lat = db.Column(db.Float)
    freq = db.Column(db.Float)
    freq_pair = db.Column(db.Float)
    sid_long_actual = db.Column(db.Float)
    sid_lat_actual = db.Column(db.Float)
    freq_actual = db.Column(db.Float)
    status = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MatchedStations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey('license_data.id'))
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection_data.id'))
    match_score = db.Column(db.Float)  # Confidence score for the match
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def safe_float_convert(value):
    """Safely convert a value to float, returning None for invalid values"""
    if pd.isna(value) or value == '' or value == '-' or value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_str_convert(value):
    """Safely convert a value to string"""
    if pd.isna(value) or value is None:
        return ''
    return str(value)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_license', methods=['POST'])
def upload_license():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Process the Excel file
            df = pd.read_excel(file)
            
            # Clear existing license data
            LicenseData.query.delete()
            
            # Process each row
            for _, row in df.iterrows():
                license_record = LicenseData(
                    clnt_id=safe_str_convert(row.get('CLNT_ID')),
                    clnt_name=safe_str_convert(row.get('CLNT_NAME')),
                    stn_name=safe_str_convert(row.get('STN_NAME')),
                    freq=safe_float_convert(row.get('FREQ')),
                    sid_long=safe_float_convert(row.get('SID_LONG')),
                    sid_lat=safe_float_convert(row.get('SID_LAT')),
                    link_id=safe_str_convert(row.get('LINK_ID')),
                    callsign=safe_str_convert(row.get('CALLSIGN')),
                    province=safe_str_convert(row.get('PROVINCE')),
                    city=safe_str_convert(row.get('CITY'))
                )
                db.session.add(license_record)
            
            db.session.commit()
            
            # Get statistics
            total_records = LicenseData.query.count()
            unique_sites = db.session.query(LicenseData.sid_long, LicenseData.sid_lat).distinct().count()
            unique_links = db.session.query(LicenseData.link_id).distinct().count()
            
            return jsonify({
                'success': True,
                'message': f'License data uploaded successfully!',
                'stats': {
                    'total_records': total_records,
                    'unique_sites': unique_sites,
                    'unique_links': unique_links
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload an Excel file.'}), 400

@app.route('/upload_inspection', methods=['POST'])
def upload_inspection():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Process the Excel file
            df = pd.read_excel(file)
            
            # Clear existing inspection data
            InspectionData.query.delete()
            
            # Process each row
            for _, row in df.iterrows():
                # Parse date
                tanggal = None
                if pd.notna(row.get('TANGGAL_PEMERIKSAAN')):
                    try:
                        tanggal = pd.to_datetime(row.get('TANGGAL_PEMERIKSAAN')).date()
                    except:
                        tanggal = None
                
                inspection_record = InspectionData(
                    tanggal_pemeriksaan=tanggal,
                    clnt_name=safe_str_convert(row.get('CLNT_NAME')),
                    link_id=safe_str_convert(row.get('LINK_ID')),
                    stn_name=safe_str_convert(row.get('STN_NAME')),
                    stasiun_lawan=safe_str_convert(row.get('STASIUN_LAWAN')),
                    sid_long=safe_float_convert(row.get('SID_LONG')),
                    sid_lat=safe_float_convert(row.get('SID_LAT')),
                    freq=safe_float_convert(row.get('FREQ')),
                    freq_pair=safe_float_convert(row.get('FREQ_PAIR')),
                    sid_long_actual=safe_float_convert(row.get('SID_LONG_Actual')),
                    sid_lat_actual=safe_float_convert(row.get('SID_LAT_Actual')),
                    freq_actual=safe_float_convert(row.get('FREQ.1')),
                    status=safe_str_convert(row.get('STATUS'))
                )
                db.session.add(inspection_record)
            
            db.session.commit()
            
            # Generate matches
            generate_matches()
            
            # Get statistics
            total_records = InspectionData.query.count()
            total_matches = MatchedStations.query.count()
            
            return jsonify({
                'success': True,
                'message': f'Inspection data uploaded successfully!',
                'stats': {
                    'total_records': total_records,
                    'total_matches': total_matches
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload an Excel file.'}), 400

def generate_matches():
    """Generate matches between license and inspection data based on STN_NAME and FREQ"""
    # Clear existing matches
    MatchedStations.query.delete()
    
    # Get all inspection records
    inspections = InspectionData.query.all()
    
    for inspection in inspections:
        if inspection.stn_name and inspection.freq:
            # Look for matching license records
            potential_matches = LicenseData.query.filter(
                LicenseData.stn_name == inspection.stn_name,
                LicenseData.freq == inspection.freq
            ).all()
            
            for license_record in potential_matches:
                match = MatchedStations(
                    license_id=license_record.id,
                    inspection_id=inspection.id,
                    match_score=1.0  # Perfect match
                )
                db.session.add(match)
    
    db.session.commit()

@app.route('/api/map_data')
def get_map_data():
    """Return data for Kepler.gl map visualization"""
    try:
        # Get license data (nodes)
        license_records = LicenseData.query.filter(
            LicenseData.sid_long.isnot(None),
            LicenseData.sid_lat.isnot(None)
        ).all()
        
        nodes_data = []
        for record in license_records:
            nodes_data.append({
                'id': record.id,
                'longitude': record.sid_long,
                'latitude': record.sid_lat,
                'stn_name': record.stn_name,
                'clnt_name': record.clnt_name,
                'freq': record.freq,
                'callsign': record.callsign,
                'province': record.province,
                'city': record.city,
                'type': 'license'
            })
        
        # Get inspection data
        inspection_records = InspectionData.query.filter(
            InspectionData.sid_long.isnot(None),
            InspectionData.sid_lat.isnot(None)
        ).all()
        
        inspection_data = []
        for record in inspection_records:
            inspection_data.append({
                'id': record.id,
                'longitude': record.sid_long,
                'latitude': record.sid_lat,
                'stn_name': record.stn_name,
                'clnt_name': record.clnt_name,
                'freq': record.freq,
                'status': record.status,
                'tanggal_pemeriksaan': record.tanggal_pemeriksaan.isoformat() if record.tanggal_pemeriksaan else None,
                'type': 'inspection'
            })
        
        # Get microwave links (edges)
        links_data = []
        # Group by LINK_ID to create links between stations
        link_groups = {}
        for record in license_records:
            if record.link_id and record.link_id != '':
                if record.link_id not in link_groups:
                    link_groups[record.link_id] = []
                link_groups[record.link_id].append(record)
        
        # Create links between stations with the same LINK_ID
        for link_id, stations in link_groups.items():
            if len(stations) >= 2:
                for i in range(len(stations)):
                    for j in range(i + 1, len(stations)):
                        links_data.append({
                            'link_id': link_id,
                            'from_lat': stations[i].sid_lat,
                            'from_lng': stations[i].sid_long,
                            'to_lat': stations[j].sid_lat,
                            'to_lng': stations[j].sid_long,
                            'from_station': stations[i].stn_name,
                            'to_station': stations[j].stn_name
                        })
        
        return jsonify({
            'nodes': nodes_data,
            'inspection': inspection_data,
            'links': links_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get summary statistics"""
    try:
        license_count = LicenseData.query.count()
        inspection_count = InspectionData.query.count()
        matches_count = MatchedStations.query.count()
        
        # Get unique sites and links
        unique_sites = db.session.query(LicenseData.sid_long, LicenseData.sid_lat).distinct().count()
        unique_links = db.session.query(LicenseData.link_id).filter(LicenseData.link_id != '').distinct().count()
        
        return jsonify({
            'license_records': license_count,
            'inspection_records': inspection_count,
            'matched_stations': matches_count,
            'unique_sites': unique_sites,
            'unique_links': unique_links
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_sample_data', methods=['POST'])
def load_sample_data():
    """Load the sample data files"""
    try:
        # Load license data
        license_df = pd.read_excel('license.xlsx')
        
        # Clear existing license data
        LicenseData.query.delete()
        
        # Process license data
        for _, row in license_df.iterrows():
            license_record = LicenseData(
                clnt_id=safe_str_convert(row.get('CLNT_ID')),
                clnt_name=safe_str_convert(row.get('CLNT_NAME')),
                stn_name=safe_str_convert(row.get('STN_NAME')),
                freq=safe_float_convert(row.get('FREQ')),
                sid_long=safe_float_convert(row.get('SID_LONG')),
                sid_lat=safe_float_convert(row.get('SID_LAT')),
                link_id=safe_str_convert(row.get('LINK_ID')),
                callsign=safe_str_convert(row.get('CALLSIGN')),
                province=safe_str_convert(row.get('PROVINCE')),
                city=safe_str_convert(row.get('CITY'))
            )
            db.session.add(license_record)
        
        # Load inspection data
        inspection_df = pd.read_excel('Pemeriksaan stasiun radio.xlsx')
        
        # Clear existing inspection data
        InspectionData.query.delete()
        
        # Process inspection data
        for _, row in inspection_df.iterrows():
            # Parse date
            tanggal = None
            if pd.notna(row.get('TANGGAL_PEMERIKSAAN')):
                try:
                    tanggal = pd.to_datetime(row.get('TANGGAL_PEMERIKSAAN')).date()
                except:
                    tanggal = None
            
            inspection_record = InspectionData(
                tanggal_pemeriksaan=tanggal,
                clnt_name=safe_str_convert(row.get('CLNT_NAME')),
                link_id=safe_str_convert(row.get('LINK_ID')),
                stn_name=safe_str_convert(row.get('STN_NAME')),
                stasiun_lawan=safe_str_convert(row.get('STASIUN_LAWAN')),
                sid_long=safe_float_convert(row.get('SID_LONG')),
                sid_lat=safe_float_convert(row.get('SID_LAT')),
                freq=safe_float_convert(row.get('FREQ')),
                freq_pair=safe_float_convert(row.get('FREQ_PAIR')),
                sid_long_actual=safe_float_convert(row.get('SID_LONG_Actual')),
                sid_lat_actual=safe_float_convert(row.get('SID_LAT_Actual')),
                freq_actual=safe_float_convert(row.get('FREQ.1')),
                status=safe_str_convert(row.get('STATUS'))
            )
            db.session.add(inspection_record)
        
        db.session.commit()
        
        # Generate matches
        generate_matches()
        
        # Get statistics
        license_count = LicenseData.query.count()
        inspection_count = InspectionData.query.count()
        matches_count = MatchedStations.query.count()
        
        return jsonify({
            'success': True,
            'message': f'Sample data loaded successfully!',
            'stats': {
                'license_records': license_count,
                'inspection_records': inspection_count,
                'matched_stations': matches_count
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error loading sample data: {str(e)}'}), 500

@app.route('/api/matched_stations')
def get_matched_stations():
    """Get details of matched stations"""
    try:
        matches = db.session.query(
            MatchedStations, LicenseData, InspectionData
        ).join(
            LicenseData, MatchedStations.license_id == LicenseData.id
        ).join(
            InspectionData, MatchedStations.inspection_id == InspectionData.id
        ).limit(100).all()  # Limit to first 100 for performance
        
        matched_data = []
        for match, license_data, inspection_data in matches:
            matched_data.append({
                'match_score': match.match_score,
                'license': {
                    'stn_name': license_data.stn_name,
                    'freq': license_data.freq,
                    'clnt_name': license_data.clnt_name,
                    'callsign': license_data.callsign
                },
                'inspection': {
                    'stn_name': inspection_data.stn_name,
                    'freq': inspection_data.freq,
                    'status': inspection_data.status,
                    'tanggal_pemeriksaan': inspection_data.tanggal_pemeriksaan.isoformat() if inspection_data.tanggal_pemeriksaan else None
                }
            })
        
        return jsonify(matched_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
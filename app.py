from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import pandas as pd
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flashing messages
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Store the last processed results
last_results = None

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_csv(file_path):
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Convert LastLoginDate to datetime with error handling
        try:
            # Parse the specific date format: M/D/YYYY h:mm:ss AM/PM
            df['LastLoginDate'] = pd.to_datetime(df['LastLoginDate'], format='%m/%d/%Y %I:%M:%S %p')
        except Exception as e:
            raise Exception(f"Error parsing dates: {str(e)}")
        
        # Get current date
        current_date = datetime.now()
        
        # Calculate 60 days ago
        sixty_days_ago = current_date - timedelta(days=60)
        
        # Filter users who haven't logged in for 60 days
        inactive_users = df[df['LastLoginDate'] < sixty_days_ago]
        
        # Group by license and count users
        license_summary = inactive_users.groupby('License').agg({
            'UserPrincipalName': ['count', lambda x: list(x)],
            'DisplayName': lambda x: list(x)
        }).reset_index()
        
        # Flatten the multi-level columns
        license_summary.columns = ['License', 'User Count', 'User Principal Names', 'Display Names']
        
        # Store the results globally
        global last_results
        last_results = license_summary
        
        return license_summary.to_dict('records')
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")

@app.route('/export-excel')
def export_excel():
    if last_results is None:
        flash('No data available to export')
        return redirect(url_for('upload_file'))
    
    # Create a BytesIO object to store the Excel file
    output = io.BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the summary sheet
        last_results.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create a detailed sheet with all user information
        detailed_data = []
        for _, row in last_results.iterrows():
            for i in range(len(row['User Principal Names'])):
                detailed_data.append({
                    'License': row['License'],
                    'User Principal Name': row['User Principal Names'][i],
                    'Display Name': row['Display Names'][i]
                })
        
        pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Detailed List', index=False)
    
    # Seek to the beginning of the BytesIO object
    output.seek(0)
    
    # Generate filename with current timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'inactive_users_report_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                results = process_csv(file_path)
                return render_template('results.html', results=results)
            except Exception as e:
                flash(str(e))
                return redirect(request.url)
            finally:
                # Clean up the uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('Invalid file type. Please upload a CSV file.')
            return redirect(request.url)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 
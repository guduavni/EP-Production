# EP-Simulator Admin Interface Guide

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- MongoDB 4.4 or higher
- Node.js (for frontend assets, if needed)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd EP-Simulator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following content:
   ```
   FLASK_APP=run_simple.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=mongodb://localhost:27017/ep_simulator
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

## Running the Application

### Development Mode
```bash
python run_simple.py
```

Access the admin interface at: http://localhost:5003/admin/

### Production Mode
For production, use Gunicorn with Nginx:
```bash
gunicorn --bind 0.0.0.0:8000 run_simple:app
```

## Admin Interface Features

### Dashboard
- Overview of system statistics
- Recent exam results
- Quick access to all admin sections

### User Management
- View and manage all users
- Assign roles and permissions
- Reset passwords

### Exam Results
- View detailed exam results
- Access test transcripts and images
- Export exam data

### Test Scripts
- Manage test scripts
- Set difficulty levels
- Enable/disable scripts

## Troubleshooting

### Common Issues
1. **MongoDB Connection Error**: Ensure MongoDB is running and the connection string in `.env` is correct.
2. **Missing Dependencies**: Run `pip install -r requirements.txt` to ensure all dependencies are installed.
3. **Port Already in Use**: Change the port in `run_simple.py` if the default port (5003) is in use.

### Logs
Check the application logs for detailed error messages:
```bash
tail -f nohup.out  # If running with nohup
```

## Support
For additional support, please contact the development team or open an issue in the repository.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

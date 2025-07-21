# EP-Simulator - ICAO English Proficiency Assessment

An automated assessment system for evaluating pilots' English language proficiency according to ICAO standards, featuring a secure admin interface, role-based access control, and comprehensive assessment tools.

## ✨ Features

### Admin Dashboard
- **Real-time Statistics**: View key metrics at a glance
- **Recent Exams**: Quick access to the most recent assessments
- **System Overview**: Monitor overall system health and usage

### User Management
- **Role-Based Access Control**: Admin, Examiner, and Candidate roles
- **User Profiles**: Detailed user information and activity tracking
- **Bulk Operations**: Manage multiple users efficiently

### Exam Management
- **Comprehensive Results**: View detailed exam results and analytics
- **Transcripts & Media**: Access test transcripts and associated media files
- **Script Management**: Create and manage test scripts with different difficulty levels

### Reporting
- **Performance Analytics**: Track candidate progress over time
- **Custom Reports**: Generate and export detailed reports
- **Audit Logs**: Monitor system activities and changes

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EP-Production
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   FLASK_APP=run_simple.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=mongodb://localhost:27017/ep_simulator
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```
   This will create test users and sample data.

### Running the Application

#### Development Mode
```bash
python run_simple.py
```
Access the admin interface at: http://localhost:5003/admin/

#### Production Mode
```bash
./run_production.sh
```
Access the admin interface at: http://localhost:8000/admin/

### Default Admin Credentials
- **Email**: admin@example.com
- **Password**: admin123

## 🔧 Database Management

### Resetting the Database
To reset the database with test data:
```bash
python reset_db.py
```

Use the `--force` flag to skip confirmation:
```bash
python reset_db.py --force
```

## 📚 Documentation

For detailed documentation, please refer to the [ADMIN_GUIDE.md](ADMIN_GUIDE.md) file.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
- **Reporting**: Generate detailed assessment reports in PDF format
- **System Configuration**: Customize assessment criteria and settings

### Assessment Features
- **Multi-Stage Evaluation**:
  - Self-introduction and experience
  - Picture description
  - Aviation scenario simulation
  - Follow-up questions
- **Speech Recognition**: Powered by OpenAI Whisper for accurate transcription
- **AI-Powered Analysis**: GPT-based evaluation of responses
- **Automated Scoring**: Based on ICAO's 6 criteria:
  - Pronunciation
  - Structure
  - Vocabulary
  - Fluency
  - Comprehension
  - Interaction

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- MongoDB 5.0+
- Redis (for caching and rate limiting)
- Node.js 16+ (for frontend assets)
- OpenAI API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/ep-simulator.git
   cd ep-simulator
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```

5. **Initialize the database**:
   ```bash
   flask init-db
   ```

## 🏃‍♂️ Running the Application

### Development Mode
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Production Deployment
For production deployment, we recommend using Gunicorn with Nginx:
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 wsgi:app
```

### Access the Application
- **Admin Interface**: http://localhost:5000/admin
- **Candidate Interface**: http://localhost:5000/
- **API Documentation**: http://localhost:5000/api/docs

## 🏗️ Project Structure

```
ep-simulator/
├── app/                      # Application package
│   ├── __init__.py          # Application factory
│   ├── models/              # Database models
│   ├── routes/              # Application routes
│   ├── services/            # Business logic
│   ├── utils/               # Utility functions
│   └── templates/           # Jinja2 templates
├── tests/                   # Test suite
├── migrations/              # Database migrations
├── static/                  # Static files
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
├── .env.example           # Example environment variables
└── wsgi.py                # WSGI entry point
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Application entry point | `app.py` |
| `FLASK_ENV` | Environment (development/production) | `development` |
| `SECRET_KEY` | Secret key for session management | Randomly generated |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/` |
| `MONGODB_DB` | Database name | `ep_simulator` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `MAIL_SERVER` | SMTP server | - |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Use TLS for email | `true` |
| `MAIL_USERNAME` | Email username | - |
| `MAIL_PASSWORD` | Email password | - |

## 📚 API Documentation

API documentation is available at `/api/docs` when running the application.

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ICAO Language Proficiency Requirements](https://www.icao.int/Pages/default.aspx)
- [OpenAI](https://openai.com/) for their powerful AI models
- [Flask](https://flask.palletsprojects.com/) and the Python ecosystem
- The open-source community for their invaluable contributions

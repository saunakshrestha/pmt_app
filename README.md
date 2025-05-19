
# PMT (Project Management Tool)

A modern project management application built with Django that provides multi-tenant support, real-time updates, and comprehensive task tracking capabilities.

## 🚀 Features

- **Multi-Tenant Architecture**: Isolated workspaces for different organizations
- **User Authentication & Authorization**: Secure access control with custom user model
- **Project Management**: Create and manage projects with team members
- **Task Tracking**: Organize tasks with boards, sprints, and labels
- **Activity Logging**: Track all changes to maintain accountability
- **Real-time Updates**: Instant notifications using WebSockets
- **RESTful API**: Comprehensive API endpoints for integration

## 📋 Requirements

- Python 3.12+
- Django 5.2+
- PostgreSQL database
- Redis (for real-time functionality)

## 🔧 Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pmt_app.git
   cd pmt_app
   ```

2. Set up a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:
   ```
   cp .env.example .env
   ```
   
5. Configure your environment variables in the `.env` file:
   ```
   DB_NAME="pmt"
   DB_HOST="localhost"
   DB_PORT="5432"
   DB_USER="your_db_user"
   DB_PASSWORD="your_db_password"
   ```

6. Apply migrations:
   ```
   python manage.py migrate
   ```

7. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

8. Run the development server:
   ```
   python manage.py runserver
   ```

## 🏗️ Project Structure

- **accounts**: User authentication and tenant management
- **projects**: Core project management functionality
- **realtime**: WebSocket-based real-time notifications
- **pmt_app**: Main project settings and configuration

## 📝 API Documentation

The application uses Django Ninja to provide a modern, OpenAPI-compliant REST API. Interactive documentation is automatically generated and available at the following URLs:

- **Accounts API**: `/accounts/v1/docs`
  - Authentication endpoints
  - User management
  - Tenant operations

- **Projects API**: `/projects/v1/docs`
  - Project CRUD operations
  - Task management
  - Role-based permissions

You can test all API endpoints directly through the interactive Swagger UI. The documentation includes request/response schemas, authentication requirements, and endpoint descriptions.

## 👨‍💻 Development

### Setting Up Development Environment

1. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```
   python manage.py test
   ```

## 📄 License

[MIT License](LICENSE)

## 👥 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
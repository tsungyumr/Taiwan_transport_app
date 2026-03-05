# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**台灣交通時刻表 App** - A Flutter mobile application for Taiwan transportation timetables including:
- 大台北公車 (Taipei/New Taipei City buses)
- 台鐵時刻表 (Taiwan Railways)
- 高鐵時刻表 (Taiwan High Speed Rail)

## Technology Stack

### Frontend
- **Framework**: Flutter 3.x
- **Language**: Dart
- **State Management**: Riverpod + Provider
- **HTTP Client**: http
- **JSON**: json_annotation + json_serializable
- **UI**: Material Design 3

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.13
- **Browser Automation**: Playwright
- **HTTP Client**: httpx
- **Database**: SQLite (aiosqlite)
- **Data Parsing**: BeautifulSoup4, lxml

## Project Structure

```
Taiwan_transport_app/
├── backend/                    # FastAPI backend
│   ├── main.py              # Main API server with Playwright integration
│   ├── main_playwright.py   # Playwright-only version
│   ├── requirements.txt     # Python dependencies
│   └── venv/                # Virtual environment
├── transport_flutter/         # Flutter app
│   ├── lib/
│   │   ├── main.dart       # App entry point
│   │   ├── models/         # Data models
│   │   ├── providers/      # State management
│   │   ├── services/       # API services
│   │   └── screens/        # UI screens
│   ├── pubspec.yaml         # Flutter dependencies
│   └── README.md            # Flutter template
└── UI_PLAN_BUS_ROUTE.md      # Bus route UI specification
```

## Common Development Tasks

### Backend (Python/FastAPI)
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the API server
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Playwright tests
python test_playwright.py
```

### Frontend (Flutter)
```bash
# Navigate to Flutter directory
cd transport_flutter

# Install dependencies
flutter pub get

# Run the app
flutter run

# Build for release
flutter build apk --release
flutter build ios --release

# Run tests
flutter test
```

## API Endpoints

### Railway (台鐵)
- `GET /api/railway/timetable` - Search train timetable
- Query params: `from_station`, `to_station`, `date`, `time`

### Bus (公車)
- `GET /api/bus/routes` - List bus routes (mock)
- `GET /api/bus/{route}` - Get bus route info (mock)

### Health
- `GET /api/health` - Health check
- `GET //` - Root endpoint

## Key Files to Understand

### Backend
- `backend/main.py` - Main API server with Playwright integration for TRA scraping
- `backend/main_playwright.py` - Simplified Playwright-only version
- `backend/TRA_scraper.py` - Taiwan Railways scraper
- `backend/analyze_sites.py` - Site analysis utilities

### Frontend
- `transport_flutter/lib/main.dart` - App entry point
- `transport_flutter/lib/screens/home_screen.dart` - Main navigation screen
- `transport_flutter/lib/models/bus_route.dart` - Bus route data models
- `transport_flutter/lib/providers/bus_provider.dart` - Bus data provider
- `transport_flutter/lib/services/bus_api_service.dart` - Bus API service

## Development Guidelines

1. **Backend-First Development**: Backend APIs should be implemented first, then frontend screens
2. **Playwright Integration**: Use Playwright for web scraping, especially for TRA and THSR
3. **Mock Data Strategy**: Use mock data for complex APIs (like TaipeiBusScraper) until real integration
4. **State Management**: Use Riverpod for state management, Provider for simple cases
5. **API Design**: Follow RESTful patterns with proper HTTP status codes

## Testing

### Backend Tests
- Unit tests in `test_*.py` files
- Playwright integration tests
- Health check endpoints

### Frontend Tests
- Widget tests in `test/` directory
- Integration tests for navigation flows
- Mock API responses for testing

## Build and Deployment

### Backend
- Run in production with `uvicorn main:app --host 0.0.0.0 --port 8000`
- Use systemd or Docker for production deployment
- Consider adding reverse proxy (Nginx) for SSL termination

### Frontend
- Build with `flutter build apk --release` for Android
- Build with `flutter build ios --release` for iOS
- Use App Store Connect and Google Play Console for distribution

## Architecture Notes

The application follows a client-server architecture:
- **Client**: Flutter mobile app
- **Server**: FastAPI backend with Playwright for web scraping
- **Data Flow**: Mobile → Backend API → Web Scraping → Mobile
- **State**: Managed locally in Flutter, refreshed via API calls

The backend handles the complexity of web scraping and data parsing, while the frontend focuses on user experience and presentation.
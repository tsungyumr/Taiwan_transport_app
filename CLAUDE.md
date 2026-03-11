# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**台灣交通時刻表 App** - A Flutter mobile application for Taiwan transportation timetables including:
- 大台北公車 (Taipei/New Taipei City buses) - TDX API
- 台鐵時刻表 (Taiwan Railways) - TDX API
- 高鐵時刻表 (Taiwan High Speed Rail) - TDX API

All data sources now use TDX (Transport Data Exchange) API with OAuth 2.0 authentication.

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
- **TDX API**: OAuth 2.0 authentication for Taiwan transport data (TRA & THSR)
- **Browser Automation**: Playwright (deprecated, kept for fallback)
- **HTTP Client**: httpx
- **Database**: SQLite (aiosqlite)
- **Data Parsing**: BeautifulSoup4, lxml

## Project Structure

```
Taiwan_transport_app/
├── backend/                    # FastAPI backend
│   ├── main.py              # Main API server
│   ├── tdx_auth.py          # TDX OAuth 2.0 authentication
│   ├── tra_tdx_service.py   # Taiwan Railways TDX API service
│   ├── thsr_tdx_service.py  # High Speed Rail TDX API service
│   ├── bus_tdx_service.py   # Bus TDX API service
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

### Railway (台鐵) - TDX API
- `GET /api/railway/stations` - List all TRA stations (244 stations)
- `GET /api/railway/timetable` - Search train timetable
  - Query params: `from_station`, `to_station`, `date`, `time`

### High Speed Rail (高鐵) - TDX API
- `GET /api/thsr/stations` - List all THSR stations (12 stations)
- `GET /api/thsr/timetable` - Search THSR timetable
  - Query params: `from_station`, `to_station`, `date`

### Bus (公車) - TDX API (大台北地區)
- `GET /api/bus/routes` - List bus routes (1044 routes)
  - Query params: `route_name` (optional filter)
- `GET /api/bus/timetable/{route_id}` - Get bus timetable
- `GET /api/bus/realtime/{route_id}` - Get real-time bus arrivals

### Health
- `GET /api/health` - Health check
- `GET //` - Root endpoint

## Key Files to Understand

### Backend
- `backend/main.py` - Main API server with TDX integration
- `backend/tdx_auth.py` - TDX OAuth 2.0 authentication module
- `backend/tra_tdx_service.py` - Taiwan Railways TDX API service
- `backend/thsr_tdx_service.py` - High Speed Rail TDX API service
- `backend/bus_tdx_service.py` - Bus TDX API service (Taipei/NewTaipei)

### Frontend
- `transport_flutter/lib/main.dart` - App entry point
- `transport_flutter/lib/screens/railway_screen.dart` - TRA timetable screen
- `transport_flutter/lib/screens/thsr_screen.dart` - THSR timetable screen
- `transport_flutter/lib/screens/bus_screen.dart` - Bus routes screen
- `transport_flutter/lib/models/models.dart` - Data models
- `transport_flutter/lib/services/api_service.dart` - API service

## Development Guidelines

1. **Backend-First Development**: Backend APIs should be implemented first, then frontend screens
2. **TDX API Integration**: Both TRA and THSR now use TDX API with OAuth 2.0
3. **Playwright**: Deprecated for TRA/THSR, kept for fallback only
4. **Mock Data Strategy**: Use mock data for complex APIs (like TaipeiBusScraper) until real integration
5. **State Management**: Use Riverpod for state management, Provider for simple cases
6. **API Design**: Follow RESTful patterns with proper HTTP status codes

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
- **Server**: FastAPI backend
- **Data Sources**:
  - **台鐵**: TDX API (OAuth 2.0) ✓
  - **高鐵**: TDX API (OAuth 2.0) ✓
  - **公車**: TDX API (OAuth 2.0) ✓ - 大台北地區 1044 條路線
- **Data Flow**: Mobile → Backend API → TDX API → Mobile
- **State**: Managed locally in Flutter, refreshed via API calls

### TDX API Integration

All transportation data (TRA, THSR, Bus) now use TDX API with OAuth 2.0 authentication:

#### Authentication
- **Flow**: Client credentials
- **Token Validity**: 24 hours
- **Client ID**: `tsungyumr-01112815-ad21-4504`

#### Taiwan Railways (台鐵)
- **Endpoints**:
  - `/Rail/TRA/Station` - 244 stations
  - `/Rail/TRA/TrainType` - 55 train types
  - `/Rail/TRA/GeneralTimetable` - Train schedules
- **Station Name Normalization**: "台" → "臺"

#### High Speed Rail (高鐵)
- **Endpoints**:
  - `/Rail/THSR/Station` - 12 stations
  - `/Rail/THSR/GeneralTimetable` - Train schedules

#### Bus (公車) - 大台北地區
- **Endpoints**:
  - `/Bus/Route/City/Taipei` - Taipei routes (418)
  - `/Bus/Route/City/NewTaipei` - New Taipei routes (626)
  - `/Bus/Stop/City/{City}` - Bus stops
  - `/Bus/RealTimeByFrequency/City/{City}/{Route}` - Real-time bus locations
- **Total Routes**: 1044 (Taipei + NewTaipei)
# University Matching App

An AI-powered application that matches students with universities and programs based on their personality, preferences, and academic goals. The app uses advanced AI algorithms to analyze user profiles and provide personalized recommendations.

## 🚀 Features

### Core Functionality
- **AI-Powered Matching**: Advanced algorithms analyze personality and preferences
- **Comprehensive Database**: Access to thousands of universities and programs worldwide
- **Personalized Recommendations**: Tailored suggestions based on academic goals and financial situation
- **School Data Collection**: Automated scraping of school statistics and information
- **User Profiles**: Detailed personality analysis through questionnaires
- **Matching Algorithm**: Multi-factor scoring system for optimal matches

### Technical Features
- **Modern Frontend**: Next.js with Shadcn UI components
- **Robust Backend**: FastAPI with comprehensive API endpoints
- **Database**: Supabase/PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based secure authentication
- **Browser Automation**: Playwright for web scraping
- **AI Integration**: OpenAI GPT-4 for personality analysis and matching

## 🏗️ Architecture

```
university-matching-app/
├── api/                    # FastAPI backend
│   ├── main.py            # Main FastAPI application
│   ├── auth.py            # Authentication logic
│   ├── schemas.py         # Pydantic schemas
│   ├── matching.py        # Matching algorithm
│   ├── questionnaire.py   # Questionnaire service
│   └── school_scraper.py  # School data collection
├── database/              # Database models and configuration
│   ├── models.py          # SQLAlchemy models
│   └── database.py        # Database connection
├── frontend/              # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   └── lib/               # Utility functions
├── alembic/               # Database migrations
└── requirements.txt       # Python dependencies
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations
- **PostgreSQL/Supabase**: Database
- **OpenAI GPT-4**: AI personality analysis
- **Playwright**: Browser automation
- **JWT**: Authentication

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Shadcn/ui**: Component library
- **React Query**: Data fetching
- **React Hook Form**: Form handling
- **Framer Motion**: Animations

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- PostgreSQL database
- OpenAI API key
- Playwright browsers

## 🚀 Quick Start

### 1. Clone the Repository
   ```bash
   git clone <repository-url>
cd university-matching-app
```

### 2. Backend Setup

#### Install Python Dependencies
   ```bash
   pip install -r requirements.txt
```

#### Set up Environment Variables
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/university_matching

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# JWT
JWT_SECRET_KEY=your_jwt_secret_key

# Supabase (optional)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

#### Initialize Database
```bash
# Create database tables
python -c "from database.database import init_db; init_db()"

# Run migrations (if using Alembic)
alembic upgrade head
```

#### Install Playwright Browsers
```bash
playwright install
```

#### Start Backend Server
```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

#### Install Node.js Dependencies
```bash
cd frontend
npm install
```

#### Set up Environment Variables
Create a `.env.local` file in the frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Start Frontend Development Server
```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📚 API Documentation

### Authentication Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### User Profile Endpoints
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile

### Questionnaire Endpoints
- `POST /questionnaire/submit` - Submit questionnaire and generate personality profile

### University Endpoints
- `GET /universities` - Get universities with filtering
- `GET /universities/{id}` - Get specific university

### School Endpoints
- `GET /schools` - Get schools with filtering
- `POST /schools/scrape` - Scrape school data

### Matching Endpoints
- `POST /matches/generate` - Generate matches for user
- `GET /matches` - Get user's matches
- `PUT /matches/{id}/favorite` - Toggle favorite status
- `PUT /matches/{id}/notes` - Update match notes

## 🎯 Usage Guide

### 1. User Registration
1. Visit the application homepage
2. Click "Get Started" to register
3. Fill in basic information (name, email, password)
4. Complete the personality questionnaire

### 2. Personality Assessment
The questionnaire covers:
- Learning style preferences
- Personality traits
- Career interests
- Study preferences
- Financial considerations

### 3. AI Analysis
The system uses GPT-4 to:
- Analyze questionnaire responses
- Generate personality profile
- Identify strengths and development areas
- Determine learning preferences

### 4. University Matching
The matching algorithm considers:
- **Academic Fit** (30%): Acceptance rates, rankings, program alignment
- **Financial Fit** (25%): Tuition costs, budget constraints
- **Location Fit** (20%): Geographic preferences, climate
- **Personality Fit** (25%): Learning environment, social atmosphere

### 5. Results and Recommendations
Users receive:
- Ranked list of university matches
- Detailed match scores
- Program recommendations
- Comparison tools
- Application guidance

## 🔧 Configuration

### Database Models

#### User Model
- Basic information (name, email, age, etc.)
- Personality profile (AI-generated)
- Questionnaire responses
- Preferences (majors, locations, budget)
- Matching criteria

#### University Model
- Basic information (name, location, type)
- Academic statistics (acceptance rate, rankings)
- Financial information (tuition, fees)
- Programs and facilities
- Scraped data metadata

#### School Model
- High school information
- Academic performance metrics
- College preparation statistics
- Extracurricular activities
- Facilities and programs

#### Matching Models
- User-University matches
- Match scores and breakdowns
- User preferences and notes
- Favorite selections

### AI Integration

#### Personality Analysis
- Uses GPT-4 to analyze questionnaire responses
- Generates structured personality profiles
- Identifies learning styles and preferences
- Provides career guidance insights

#### Matching Algorithm
- Multi-factor scoring system
- Weighted criteria based on importance
- AI-powered personality compatibility
- Fallback mechanisms for missing data

#### School Data Collection
- Browser automation with Playwright
- AI-powered data extraction
- Confidence scoring for data quality
- Automated updates and verification

## 🧪 Testing

### Backend Testing
```bash
# Run API tests
pytest api/tests/

# Test specific components
python -m pytest api/tests/test_matching.py
python -m pytest api/tests/test_questionnaire.py
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Backend Deployment
1. Set up production database
2. Configure environment variables
3. Run database migrations
4. Deploy with Gunicorn or similar

### Frontend Deployment
1. Build production version
2. Deploy to Vercel, Netlify, or similar
3. Configure API endpoints

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/docs`

## 🔮 Future Enhancements

- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Integration with application systems
- [ ] Real-time chat support
- [ ] Virtual campus tours
- [ ] Scholarship matching
- [ ] Alumni network integration
- [ ] Multi-language support
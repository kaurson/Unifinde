# Vector-Based University Matching System

## Overview

This system implements a pure vector-based matching algorithm that uses embeddings to find the best matches between students and universities. The system converts both user profiles and university profiles into high-dimensional vectors and uses cosine similarity to find the most compatible matches.

## Key Features

### 🧠 **Semantic Understanding**
- Converts questionnaire summaries and university descriptions into semantic vectors
- Understands context and meaning, not just keyword matching
- Captures nuanced relationships between student preferences and university characteristics

### ⚡ **High Performance**
- Fast similarity search using optimized vector operations
- Caching system for university embeddings to improve response times
- Fallback mechanisms for reliability

### 🎯 **Pure Vector Matching**
- Uses only semantic similarity for matching
- No rule-based filters or adjustments
- Maintains transparency and explainability

### 🔄 **Hybrid Comparison**
- Allows comparison between vector and traditional matching methods
- Provides insights into different matching approaches

## Architecture

### Core Components

1. **VectorMatchingService** (`api/vector_matcher.py`)
   - Handles embedding generation and similarity calculations
   - Manages caching and fallback mechanisms
   - Provides comprehensive profile text generation

2. **MatchingService** (`api/matching.py`)
   - Integrates vector and traditional matching
   - Provides comparison functionality
   - Handles user similarity matching

3. **API Endpoints** (`api/main.py`)
   - `/matches/generate` - Generate matches using vector or traditional methods
   - `/matches/compare` - Compare different matching approaches
   - `/matches/similar-users` - Find users with similar profiles
   - `/matches/clear-cache` - Clear embedding cache

## How It Works

### 1. Profile Vectorization

**User Profile Text Generation:**
```python
# Combines all user information into comprehensive text
- Basic demographics (age, name, income)
- Personality profile (LLM-generated analysis)
- Questionnaire responses
- Academic preferences and achievements
- Extracurricular activities
- Career goals and aspirations
- Financial constraints
- Location preferences
```

**University Profile Text Generation:**
```python
# Creates rich university descriptions
- Basic information (name, location, type)
- Academic statistics (acceptance rate, rankings)
- Financial information (tuition, aid availability)
- Mission and vision statements
- Program offerings
- Campus facilities and environment
- Student life and culture
```

### 2. Embedding Generation

The system uses OpenAI's `text-embedding-3-small` model to generate 1536-dimensional vectors:

```python
# Primary method: OpenAI embeddings
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=profile_text,
    encoding_format="float"
)

# Fallback: Sentence transformers
embedding = sentence_transformer.encode(profile_text)
```

### 3. Similarity Calculation

Uses cosine similarity to measure compatibility:

```python
similarity = cosine_similarity(vec1, vec2)[0][0]
```

### 4. Pure Vector Matching

The system relies entirely on semantic similarity without any additional filters or adjustments:

```python
# Sort by similarity score and return top matches
matches.sort(key=lambda x: x["similarity_score"], reverse=True)
return matches[:limit]
```

## API Usage

### Generate Matches

```bash
POST /matches/generate
{
  "use_vector_matching": true,
  "limit": 20
}
```

**Response:**
```json
{
  "message": "Generated 20 matches using vector similarity",
  "matches": [
    {
      "university_id": 1,
      "university_name": "Stanford University",
      "similarity_score": 0.85,
      "confidence": "high",
      "match_reasons": [
        "Excellent overall compatibility based on your profile",
        "Offers your preferred major(s): Computer Science",
        "Located in your preferred state: California"
      ],
      "university_data": {...}
    }
  ],
  "matching_method": "vector_similarity"
}
```

### Compare Matching Methods

```bash
GET /matches/compare?limit=10
```

**Response:**
```json
{
  "vector_matches": [...],
  "traditional_matches": [...],
  "common_universities": 7,
  "vector_only": 3,
  "traditional_only": 2,
  "overlap_percentage": 70.0
}
```

### Find Similar Users

```bash
GET /matches/similar-users?limit=10
```

**Response:**
```json
{
  "similar_users": [
    {
      "user_id": 2,
      "username": "johndoe",
      "name": "John Doe",
      "similarity_score": 0.78,
      "common_interests": [
        "Common majors: Computer Science",
        "Common locations: California"
      ]
    }
  ],
  "total_found": 5
}
```

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Dependencies

```txt
# Vector database and embeddings
pgvector>=0.2.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0

# AI and LLM
openai>=1.0.0
```

## Testing

Run the test script to see the system in action:

```bash
python test_vector_matching.py
```

This will:
1. Create a test user with comprehensive profile
2. Create test universities with various characteristics
3. Test vector matching vs traditional matching
4. Compare results and show overlap
5. Test similar user finding

## Performance Considerations

### Caching
- University embeddings are cached to avoid regeneration
- Cache can be cleared via API endpoint
- Improves response times for repeated queries

### Fallback Mechanisms
- Falls back to sentence transformers if OpenAI is unavailable
- Falls back to traditional matching if vector matching fails
- Ensures system reliability

### Scalability
- Vector operations are optimized using numpy
- Batch processing possible for large datasets
- Can be extended to use dedicated vector databases (Pinecone, Weaviate)

## Advantages of Pure Vector Matching

### 1. **Semantic Understanding**
- Understands that "computer science" and "software engineering" are related
- Captures personality traits and learning styles
- Considers context and meaning, not just exact matches

### 2. **Discovery**
- Can find unexpected good matches based on overall compatibility
- Discovers non-obvious relationships between profiles
- Provides more diverse and interesting recommendations

### 3. **Simplicity**
- No complex rule-based filtering logic
- Easy to understand and maintain
- Consistent matching approach

### 4. **Explainability**
- Provides detailed reasoning for each match
- Shows which factors contributed to the score
- Maintains transparency while using AI

### 5. **Flexibility**
- Easy to add new features without changing core algorithm
- Can weight different aspects dynamically
- Supports both exact matches and fuzzy discovery

## Future Enhancements

### 1. **Vector Database Integration**
- Store embeddings in dedicated vector database
- Enable faster similarity search for large datasets
- Support for real-time updates

### 2. **Multi-Modal Embeddings**
- Include images and visual content
- Process campus photos and facilities
- Enhanced visual matching

### 3. **Collaborative Filtering**
- Learn from user behavior and feedback
- Improve recommendations over time
- Personalize weights based on user preferences

### 4. **Advanced Similarity Metrics**
- Experiment with different similarity functions
- Add weighted similarity based on feature importance
- Support for multi-dimensional similarity

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check API key configuration
   - Verify API quota and limits
   - System will fallback to sentence transformers

2. **Memory Issues**
   - Clear embedding cache regularly
   - Monitor memory usage with large datasets
   - Consider batch processing for large operations

3. **Performance Issues**
   - Enable caching for university embeddings
   - Use appropriate batch sizes
   - Monitor database query performance

### Debug Mode

Enable detailed logging by setting log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When adding new features to the vector matching system:

1. **Profile Text Generation**: Update `_create_user_profile_text()` and `_create_university_profile_text()` methods
2. **Match Reasoning**: Update `_generate_match_reasons()` method
3. **Testing**: Add test cases to `test_vector_matching.py`

## License

This vector matching system is part of the University Matching App project. 
"""
Unit Tests for Core Tools
Phase 8.4.1: Backend Unit Tests

Tests for the most commonly used and critical tools.
"""

import pytest
from pathlib import Path
import sys

# Add tools directory to path
tools_dir = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(tools_dir))


@pytest.mark.unit
class TestCalculateReadingTime:
    """Test calculate_reading_time.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from calculate_reading_time import calculate_reading_time
        self.tool = calculate_reading_time

    def test_empty_text(self):
        """Test with empty text"""
        result = self.tool("")
        assert result['reading_time_minutes'] == 0
        assert result['word_count'] == 0

    def test_short_text(self):
        """Test with short text (< 1 minute)"""
        text = "This is a short text with only ten words here."
        result = self.tool(text)
        assert result['word_count'] == 10
        assert result['reading_time_minutes'] == 1  # Should round up

    def test_medium_text(self):
        """Test with medium text (~200 words)"""
        text = " ".join(["word"] * 200)
        result = self.tool(text)
        assert result['word_count'] == 200
        assert result['reading_time_minutes'] == 1  # 200 words / 200 wpm

    def test_long_text(self):
        """Test with long text (~1000 words)"""
        text = " ".join(["word"] * 1000)
        result = self.tool(text)
        assert result['word_count'] == 1000
        assert result['reading_time_minutes'] == 5  # 1000 words / 200 wpm

    def test_text_with_punctuation(self):
        """Test with text containing punctuation"""
        text = "Hello, world! This is a test. How are you?"
        result = self.tool(text)
        assert result['word_count'] == 9
        assert result['reading_time_minutes'] == 1

    def test_text_with_numbers(self):
        """Test with text containing numbers"""
        text = "In 2024, there were 100 tests completed successfully."
        result = self.tool(text)
        assert result['word_count'] == 8


@pytest.mark.unit
class TestSearchIndex:
    """Test search_index.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from search_index import search_articles
        self.tool = search_articles

    def test_empty_query(self):
        """Test with empty query"""
        articles = [
            {'id': 1, 'title': 'Test', 'content': 'Content'}
        ]
        result = self.tool("", articles)
        assert len(result) == 0

    def test_simple_search(self):
        """Test simple keyword search"""
        articles = [
            {'id': 1, 'title': 'Python Programming', 'content': 'Learn Python'},
            {'id': 2, 'title': 'Java Programming', 'content': 'Learn Java'},
        ]
        result = self.tool("Python", articles)
        assert len(result) >= 1
        assert any('Python' in r['title'] for r in result)

    def test_case_insensitive_search(self):
        """Test that search is case-insensitive"""
        articles = [
            {'id': 1, 'title': 'PYTHON programming', 'content': 'content'},
        ]
        result = self.tool("python", articles)
        assert len(result) >= 1

    def test_multiple_matches(self):
        """Test with multiple matching articles"""
        articles = [
            {'id': 1, 'title': 'Python basics', 'content': 'Python intro'},
            {'id': 2, 'title': 'Advanced Python', 'content': 'Python advanced'},
            {'id': 3, 'title': 'Java basics', 'content': 'Java intro'},
        ]
        result = self.tool("Python", articles)
        assert len(result) >= 2


@pytest.mark.unit
class TestGenerateStatistics:
    """Test generate_statistics.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from generate_statistics import generate_statistics
        self.tool = generate_statistics

    def test_empty_data(self):
        """Test with empty dataset"""
        result = self.tool([])
        assert result['count'] == 0

    def test_single_value(self):
        """Test with single value"""
        result = self.tool([5])
        assert result['count'] == 1
        assert result['mean'] == 5
        assert result['median'] == 5
        assert result['min'] == 5
        assert result['max'] == 5

    def test_multiple_values(self):
        """Test with multiple values"""
        data = [1, 2, 3, 4, 5]
        result = self.tool(data)
        assert result['count'] == 5
        assert result['mean'] == 3.0
        assert result['median'] == 3
        assert result['min'] == 1
        assert result['max'] == 5

    def test_odd_count_median(self):
        """Test median with odd number of values"""
        data = [1, 3, 5, 7, 9]
        result = self.tool(data)
        assert result['median'] == 5

    def test_even_count_median(self):
        """Test median with even number of values"""
        data = [1, 2, 3, 4]
        result = self.tool(data)
        assert result['median'] == 2.5  # Average of 2 and 3

    def test_with_duplicates(self):
        """Test with duplicate values"""
        data = [5, 5, 5, 10, 10]
        result = self.tool(data)
        assert result['count'] == 5
        assert result['mean'] == 7.0
        assert result['median'] == 5


@pytest.mark.unit
class TestValidateData:
    """Test validate_data.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from validate_data import validate_data
        self.tool = validate_data

    def test_valid_email(self):
        """Test with valid email"""
        result = self.tool("test@example.com", "email")
        assert result['is_valid'] is True

    def test_invalid_email(self):
        """Test with invalid email"""
        result = self.tool("invalid-email", "email")
        assert result['is_valid'] is False

    def test_valid_url(self):
        """Test with valid URL"""
        result = self.tool("https://example.com", "url")
        assert result['is_valid'] is True

    def test_invalid_url(self):
        """Test with invalid URL"""
        result = self.tool("not-a-url", "url")
        assert result['is_valid'] is False

    def test_valid_json(self):
        """Test with valid JSON"""
        result = self.tool('{"key": "value"}', "json")
        assert result['is_valid'] is True

    def test_invalid_json(self):
        """Test with invalid JSON"""
        result = self.tool('{invalid json}', "json")
        assert result['is_valid'] is False


@pytest.mark.unit
class TestFormatText:
    """Test format_text.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from format_text import format_text
        self.tool = format_text

    def test_uppercase(self):
        """Test uppercase formatting"""
        result = self.tool("hello world", "uppercase")
        assert result['formatted_text'] == "HELLO WORLD"

    def test_lowercase(self):
        """Test lowercase formatting"""
        result = self.tool("HELLO WORLD", "lowercase")
        assert result['formatted_text'] == "hello world"

    def test_title_case(self):
        """Test title case formatting"""
        result = self.tool("hello world", "title")
        assert result['formatted_text'] == "Hello World"

    def test_capitalize(self):
        """Test capitalize formatting"""
        result = self.tool("hello world", "capitalize")
        assert result['formatted_text'] == "Hello world"

    def test_trim_whitespace(self):
        """Test whitespace trimming"""
        result = self.tool("  hello world  ", "trim")
        assert result['formatted_text'] == "hello world"

    def test_remove_extra_spaces(self):
        """Test removing extra spaces"""
        result = self.tool("hello    world", "normalize_spaces")
        assert result['formatted_text'] == "hello world"


@pytest.mark.unit
class TestCalculateDifficulty:
    """Test calculate_difficulty.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from calculate_difficulty import calculate_difficulty
        self.tool = calculate_difficulty

    def test_simple_text(self):
        """Test with simple text"""
        text = "The cat sat on the mat. It was a nice day."
        result = self.tool(text)
        assert 'difficulty_score' in result
        assert result['difficulty_score'] >= 0
        assert result['difficulty_score'] <= 100

    def test_complex_text(self):
        """Test with complex text"""
        text = "The multifaceted ramifications of contemporary socioeconomic paradigms necessitate comprehensive analytical frameworks."
        result = self.tool(text)
        assert 'difficulty_score' in result
        assert result['difficulty_score'] > 50  # Should be harder

    def test_empty_text(self):
        """Test with empty text"""
        result = self.tool("")
        assert result['difficulty_score'] == 0


@pytest.mark.unit
class TestExtractKeywords:
    """Test extract_keywords.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from extract_keywords import extract_keywords
        self.tool = extract_keywords

    def test_simple_text(self):
        """Test keyword extraction from simple text"""
        text = "Python is a programming language. Python is popular for data science."
        result = self.tool(text)
        assert 'keywords' in result
        assert isinstance(result['keywords'], list)
        assert len(result['keywords']) > 0
        # "Python" should appear as it's repeated
        assert any('python' in kw.lower() for kw in result['keywords'])

    def test_empty_text(self):
        """Test with empty text"""
        result = self.tool("")
        assert result['keywords'] == []

    def test_short_text(self):
        """Test with very short text"""
        text = "Hello world"
        result = self.tool(text)
        assert isinstance(result['keywords'], list)


@pytest.mark.unit
class TestDetectLanguage:
    """Test detect_language.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from detect_language import detect_language
        self.tool = detect_language

    def test_english_text(self):
        """Test English text detection"""
        text = "This is a sentence in English language."
        result = self.tool(text)
        assert result['language'] == 'en'
        assert result['confidence'] > 0.8

    def test_russian_text(self):
        """Test Russian text detection"""
        text = "Это предложение на русском языке."
        result = self.tool(text)
        assert result['language'] == 'ru'
        assert result['confidence'] > 0.8

    def test_short_text(self):
        """Test with short text (low confidence)"""
        text = "Hi"
        result = self.tool(text)
        assert 'language' in result
        # Confidence might be lower for very short text


@pytest.mark.unit
class TestCountWords:
    """Test count_words.py tool"""

    def setup_method(self):
        """Import the tool for each test"""
        from count_words import count_words
        self.tool = count_words

    def test_simple_text(self):
        """Test word counting with simple text"""
        text = "hello world hello"
        result = self.tool(text)
        assert result['word_counts']['hello'] == 2
        assert result['word_counts']['world'] == 1
        assert result['total_words'] == 3

    def test_empty_text(self):
        """Test with empty text"""
        result = self.tool("")
        assert result['total_words'] == 0

    def test_text_with_punctuation(self):
        """Test with punctuation"""
        text = "Hello, world! Hello."
        result = self.tool(text)
        assert result['total_words'] == 3
        # Should normalize "Hello" and "Hello."


# Test fixtures and helpers
@pytest.fixture
def sample_article():
    """Sample article for testing"""
    return {
        'id': 1,
        'title': 'Sample Article',
        'content': 'This is a sample article for testing purposes.',
        'tags': ['test', 'sample'],
        'category': 'Testing'
    }


@pytest.fixture
def sample_articles():
    """Sample articles collection for testing"""
    return [
        {
            'id': 1,
            'title': 'Python Basics',
            'content': 'Introduction to Python programming',
            'tags': ['python', 'programming'],
            'category': 'Programming'
        },
        {
            'id': 2,
            'title': 'JavaScript Guide',
            'content': 'Learn JavaScript fundamentals',
            'tags': ['javascript', 'programming'],
            'category': 'Programming'
        },
        {
            'id': 3,
            'title': 'Database Design',
            'content': 'Best practices for database design',
            'tags': ['database', 'sql'],
            'category': 'Database'
        }
    ]

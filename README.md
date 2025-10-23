# 🔍 AI Code Quality Reviewer

A sophisticated code review tool that combines traditional rule-based analysis with AI-powered insights using OpenAI's GPT models. Built with modern software engineering principles: SOLID, OOP design patterns, and Test-Driven Development (TDD).

![Tests](https://img.shields.io/badge/tests-193%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Pylint](https://img.shields.io/badge/pylint-10.00%2F10-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)

## ✨ Features

### Hybrid Review System
- **Rule-Based Reviewers**: Fast, deterministic checks
  - Style Checker: Naming conventions, formatting, code organization
  - Complexity Analyzer: Cyclomatic complexity detection
  - Security Scanner: Hardcoded secrets, SQL injection, dangerous functions
  
- **AI-Powered Reviewer**: Context-aware semantic analysis
  - Architecture and design issues
  - Logic flaws and edge cases
  - Best practices and idioms
  - Performance optimizations
  - Maintainability concerns

### Multiple Review Modes
- **Quick Scan**: Rule-based only (fast, free)
- **Standard**: Hybrid approach (balanced)
- **Deep Analysis**: AI-focused (thorough)

### Professional Web Interface
- Clean, responsive Streamlit UI
- Real-time code review with progress indication
- Configurable reviewers and settings
- Quality score visualization
- Issue grouping by severity and category
- Export results (JSON, Markdown, CSV)

### Multi-Language Support
- Python
- JavaScript
- TypeScript

## 🏗️ Architecture

Built following **SOLID principles** and **design patterns**:

- **Strategy Pattern**: Pluggable reviewers (StyleReviewer, ComplexityReviewer, SecurityReviewer, AIReviewer)
- **Composite Pattern**: Combine multiple reviewers into comprehensive analysis
- **Template Method**: Common review workflow across all reviewers
- **Dependency Injection**: OpenAI client injection for testability

### Project Structure
```
my-ai-project/
├── app.py                          # Streamlit web application
├── src/
│   ├── models/
│   │   ├── code_models.py          # ParsedCode, CodeMetadata
│   │   └── review_models.py        # ReviewResult, ReviewIssue, Severity, IssueCategory
│   ├── services/
│   │   ├── code_parser.py          # Multi-language code parser
│   │   ├── review_engine.py        # Review orchestration
│   │   └── ai_reviewer.py          # OpenAI integration
│   └── streamlit_utils.py          # UI business logic
├── tests/
│   └── unit/
│       ├── test_code_parser.py     # 43 tests
│       ├── test_review_engine.py   # 51 tests
│       ├── test_review_models.py   # 31 tests
│       ├── test_ai_reviewer.py     # 35 tests
│       └── test_streamlit_app.py   # 33 tests
├── requirements.txt
├── pytest.ini
└── .env                            # API configuration
```

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- OpenAI API key (for AI reviews)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd my-ai-project
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure OpenAI API key**
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### Running the Application

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## 📖 Usage

### Web Interface

1. **Select Review Mode**
   - Quick Scan: Fast rule-based checks only
   - Standard: Hybrid (recommended)
   - Deep Analysis: AI-focused thorough review

2. **Configure Settings** (optional)
   - Enable/disable specific reviewers
   - Choose AI model (gpt-4o-mini, gpt-4o, gpt-4)
   - Adjust complexity threshold
   - Set temperature for AI responses

3. **Enter Code**
   - Paste your code in the text area
   - Select programming language
   - Click "Run Review"

4. **View Results**
   - Quality score and metrics
   - Issues grouped by severity/category
   - Detailed suggestions for each issue
   - Export results in multiple formats

### Programmatic Usage

```python
from src.services.code_parser import CodeParser
from src.services.review_engine import ReviewEngine

# Parse code
parser = CodeParser()
parsed_code = parser.parse("""
def example():
    password = "hardcoded123"
    return password
""", "python")

# Run review (hybrid mode)
config = {
    "enable_style": True,
    "enable_complexity": True,
    "enable_security": True,
    "enable_ai": True,
    "ai_model": "gpt-4o-mini"
}

engine = ReviewEngine(config=config)
result = engine.review(parsed_code)

# Access results
print(f"Quality Score: {result.quality_score}/100")
print(f"Total Issues: {result.total_issues}")
print(f"Critical Issues: {result.critical_count}")

for issue in result.issues:
    print(f"{issue.severity.value}: {issue.message}")
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/unit/
```

### With Coverage Report
```bash
pytest tests/unit/ --cov=src --cov-report=html
```

View coverage report: `htmlcov/index.html`

### Test Statistics
- **193 total tests** (all passing)
- **100% code coverage** ✨
- **10.00/10 pylint score** ⭐
- **TDD methodology** used throughout
- Tests organized by component

### Run Specific Test Suites
```bash
# Code parser tests
pytest tests/unit/test_code_parser.py

# Review engine tests
pytest tests/unit/test_review_engine.py

# AI reviewer tests
pytest tests/unit/test_ai_reviewer.py

# Streamlit utilities tests
pytest tests/unit/test_streamlit_app.py
```

## 📊 Review Results

### Quality Score Calculation
- Start at 100 points
- Deduct based on severity:
  - Critical: -20 points
  - High: -10 points
  - Medium: -5 points
  - Low: -2 points
  - Info: -1 point

### Issue Categories
- **Style**: Formatting, naming conventions, code organization
- **Complexity**: High cyclomatic complexity, deep nesting
- **Security**: Hardcoded secrets, SQL injection, unsafe operations
- **Performance**: Inefficiencies, unnecessary operations
- **Best Practices**: Language idioms, design patterns
- **Documentation**: Missing/unclear comments and docstrings
- **Bug Risk**: Potential bugs, edge cases, error handling

## 🎯 Configuration Options

### Review Engine Config
```python
config = {
    # Enable/disable reviewers
    "enable_style": True,
    "enable_complexity": True,
    "enable_security": True,
    "enable_ai": True,
    
    # Complexity settings
    "max_complexity": 10,
    
    # AI settings
    "ai_model": "gpt-4o-mini",  # or "gpt-4o", "gpt-4"
    "ai_temperature": 0.3,       # 0.0-1.0
    "ai_max_tokens": 2000,
    "ai_timeout": 30,
    
    # Severity filtering
    "min_severity": "low"  # Filter out lower severity issues
}
```

## 💡 AI Models

| Model       | Speed      | Cost          | Best For                     |
| ----------- | ---------- | ------------- | ---------------------------- |
| gpt-4o-mini | ⚡ Fastest  | $ Cheapest    | Quick reviews, simple code   |
| gpt-4o      | ⚖️ Balanced | $$ Moderate   | Most use cases               |
| gpt-4       | 🎯 Thorough | $$$ Expensive | Critical code, complex logic |

### Cost Estimates (per 1000 lines)
- **gpt-4o-mini**: ~$0.001 - $0.005
- **gpt-4o**: ~$0.01 - $0.05
- **gpt-4**: ~$0.10 - $0.50

## 🏆 Code Quality Metrics

This project practices what it preaches:

- ✅ **100% test coverage** (619/619 statements)
- ✅ **10.00/10 pylint score** (perfect code quality)
- ✅ **193 passing tests** (comprehensive test suite)
- ✅ **SOLID principles** throughout
- ✅ **Design patterns** (Strategy, Composite, Template Method)
- ✅ **Type hints** on all functions
- ✅ **Comprehensive docstrings**
- ✅ **TDD methodology**
- ✅ **Clean architecture** with separation of concerns

## 🔒 Security

- API keys stored in `.env` (never committed)
- Input validation on all user inputs
- Size limits on code submissions
- No code execution (only parsing)
- Secure API communication via HTTPS

## 🤝 Contributing

This project was built using TDD. When contributing:

1. Write tests first (RED)
2. Implement feature (GREEN)
3. Refactor (REFACTOR)
4. Maintain 100% coverage
5. Ensure pylint score remains 10.00/10

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenAI](https://openai.com/)
- Tested with [pytest](https://pytest.org/)
- Type validation with [Pydantic](https://pydantic-docs.helpmanual.io/)

## 📧 Contact

Questions or feedback? Open an issue or contact the maintainers.

---

**Built with ❤️ using Test-Driven Development**

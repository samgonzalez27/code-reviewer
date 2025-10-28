# 🔍 AI Code Quality Reviewer

A sophisticated code review tool that combines AI-powered analysis with GitHub Copilot integration. Get intelligent code reviews and AI-generated prompts to fix issues using OpenAI's GPT models. Built with modern software engineering principles: SOLID, OOP design patterns, and Test-Driven Development (TDD).

![Tests](https://img.shields.io/badge/tests-215%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Pylint](https://img.shields.io/badge/pylint-10.00%2F10-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)

## ✨ Features

### 🤖 AI-Powered Code Review
- **Context-Aware Analysis**: Semantic understanding of your code
  - Architecture and design issues
  - Logic flaws and edge cases
  - Best practices and idioms
  - Performance optimizations
  - Security vulnerabilities
  - Maintainability concerns

### 🚀 GitHub Copilot Integration
- **AI-Generated Fix Prompts**: Get tailored prompts for GitHub Copilot
  - Up to 5 prompts per review, one per issue category
  - Prioritized by severity (Critical → High → Medium → Low → Info)
  - Follows professional Python SWE standards
  - Clean, readable text area display with automatic word wrapping
  - Easy copy workflow: Click → Ctrl+A → Ctrl+C
  - Includes context: line numbers, severity, issue count
- **Multiple Export Formats**: Text, JSON, Markdown
- **Smart Grouping**: Issues organized by category (Security, Complexity, Style, etc.)
- **Intuitive UX**: Simple, professional interface with no confusing elements

### 🎨 Professional Web Interface
- Clean, responsive Streamlit UI
- Real-time code review with progress indication
- Configurable AI model and temperature
- Quality score visualization with color-coded metrics
- Issue grouping by severity and category
- Expandable issue details with suggestions
- **Optimized Prompt Display**: Clean text areas for easy reading and copying
- Export results (JSON, Markdown, CSV)
- Export prompts separately (Text, JSON, Markdown)

### 🌍 Multi-Language Support
- Python
- JavaScript
- TypeScript
- (More languages coming soon!)

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
│   │   ├── review_models.py        # ReviewResult, ReviewIssue, Severity
│   │   └── prompt_models.py        # PromptSuggestion, PromptGenerationResult
│   ├── services/
│   │   ├── review_engine.py        # Review orchestration
│   │   ├── ai_reviewer.py          # OpenAI code review integration
│   │   └── prompt_generator.py     # GitHub Copilot prompt generation
│   └── streamlit_utils.py          # UI business logic
├── tests/
│   └── unit/
│       ├── test_review_engine.py   # Review engine tests
│       ├── test_review_models.py   # Model tests
│       ├── test_ai_reviewer.py     # AI reviewer tests
│       ├── test_prompt_generator.py # Prompt generator tests
│       ├── test_prompt_models.py   # Prompt model tests
│       └── test_streamlit_app.py   # UI tests
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

## � Screenshots

### Code Review Interface
- **Clean, Modern UI**: Easy to navigate and understand
- **Real-time Analysis**: See results as they're generated
- **Quality Metrics**: Visual dashboard of code quality score

### GitHub Copilot Prompts
- **AI-Generated Fix Instructions**: Tailored prompts for each issue category
- **One-Click Copy**: Easy integration with GitHub Copilot
- **Export Options**: Save prompts for later use

### Results Export
- **Multiple Formats**: JSON, Markdown, CSV for code review results
- **Prompt Export**: Text, JSON, Markdown for Copilot prompts
- **Shareable Reports**: Professional formatting for team reviews

## � Usage

### 🔄 Complete Workflow

```
1. Paste Code → 2. AI Review → 3. Get Issues → 4. Receive Prompts → 5. Use Copilot → 6. Fix Code
   ↓               ↓              ↓               ↓                    ↓                ↓
Your code      AI analyzes    Categorized    Tailored fix       Copy & paste     Improved
in editor      for issues     by severity    instructions       to Copilot       code quality
```

**Why this matters:** Unlike traditional code review tools that only identify problems, 
this tool bridges the gap between **finding issues** and **fixing them** by generating 
ready-to-use GitHub Copilot prompts that guide you through the remediation process.

### Web Interface

1. **Select Programming Language**
   - Choose from Python, JavaScript, TypeScript

2. **Configure AI Settings**
   - Choose AI model (gpt-4o-mini, gpt-4o, gpt-4)
   - Adjust temperature (0.0 = consistent, 1.0 = creative)

3. **Enter Code**
   - Paste your code in the text area
   - Click "Run Review"

4. **View Results**
   - Quality score and metrics
   - Issues grouped by severity/category
   - **GitHub Copilot Prompts** - AI-generated fix instructions
   - Export results in multiple formats

5. **Use Copilot Prompts** 🆕
   - Review generated prompts for each issue category
   - Read prompts in clean, formatted text areas
   - Click inside text area → Ctrl+A (Select All) → Ctrl+C (Copy)
   - Paste into GitHub Copilot to get guided fixes
   - Export prompts as Text, JSON, or Markdown for later use

### Programmatic Usage

```python
from src.models.code_models import ParsedCode, CodeMetadata
from src.services.review_engine import ReviewEngine
from src.services.prompt_generator import PromptGenerator

# Create parsed code object
code = """
def example():
    password = "hardcoded123"
    return password
"""

lines = code.split('\n')
metadata = CodeMetadata(
    line_count=len(lines),
    blank_line_count=sum(1 for line in lines if not line.strip()),
    comment_count=0
)

parsed_code = ParsedCode(
    content=code,
    language="python",
    metadata=metadata
)

# Run AI review
config = {
    "enable_ai": True,
    "ai_model": "gpt-4o-mini"
}

engine = ReviewEngine(config=config)
result = engine.review(parsed_code)

# Access results
print(f"Quality Score: {result.quality_score}/100")
print(f"Total Issues: {result.total_issues}")

for issue in result.issues:
    print(f"{issue.severity.value}: {issue.message}")

# Generate GitHub Copilot prompts
generator = PromptGenerator()
prompts = generator.generate(result, language="python")

print(f"\nGenerated {len(prompts.prompts)} Copilot prompts:")
for prompt in prompts.prompts:
    print(f"\n{prompt.category.value}:")
    print(prompt.prompt_text)
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
- **Comprehensive test coverage**
- **TDD methodology** used throughout
- Tests organized by component
- Comprehensive edge case coverage

### Run Specific Test Suites
```bash
# Review engine tests
pytest tests/unit/test_review_engine.py

# AI reviewer tests
pytest tests/unit/test_ai_reviewer.py

# Prompt generator tests
pytest tests/unit/test_prompt_generator.py

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
    # Enable AI review
    "enable_ai": True,
    
    # AI settings
    "ai_model": "gpt-4o-mini",  # or "gpt-4o", "gpt-4"
    "ai_temperature": 0.3,       # 0.0-1.0 (lower = more consistent)
    "ai_max_tokens": 2000,
    "ai_timeout": 30,            # seconds
}
```

### Prompt Generator Config
```python
config = {
    "model": "gpt-4o-mini",      # AI model for prompt generation
    "temperature": 0.3,           # Response creativity (0.0-1.0)
    "max_prompts": 5,             # Maximum prompts to generate
    "timeout": 30                 # Request timeout in seconds
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

- ✅ **100% test coverage** (677/677 statements)
- ✅ **10.00/10 pylint score** (perfect code quality)
- ✅ **215 passing tests** (comprehensive test suite)
- ✅ **SOLID principles** throughout
- ✅ **Design patterns** (Strategy, Composite, Template Method)
- ✅ **Type hints** on all functions
- ✅ **Comprehensive docstrings**
- ✅ **TDD methodology** (tests written first)
- ✅ **Clean architecture** with separation of concerns

## 🎓 What Makes This Project Special

### GitHub Copilot Integration
Unlike other code review tools, this project **bridges the gap** between finding issues and fixing them:
1. **AI Review**: Identifies code quality issues with intelligent analysis
2. **AI Prompts**: Generates tailored GitHub Copilot prompts for each issue category
3. **Guided Fixes**: Developers get step-by-step fix instructions ready to paste
4. **Professional Standards**: All prompts follow Python SWE best practices
5. **Clean UX**: Prompts displayed in readable text areas with easy copy workflow

### UX Excellence
- **Iteratively refined UI** based on real user testing
- **Simple, intuitive interface** - no complexity, just clarity
- **Clean text areas** for prompt display with automatic word wrapping
- **Easy copy workflow**: Click → Ctrl+A → Ctrl+C (no confusing HTML or dropdowns)
- **Professional presentation** without sacrificing usability

### TDD Excellence
- Every feature built using Test-Driven Development
- Tests written BEFORE implementation
- 100% coverage maintained throughout development
- Comprehensive edge case coverage
- Real-world testing integrated into development process

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

## 🌟 Star This Project

If you find this project useful, please consider giving it a star on GitHub! It helps others discover the project and motivates continued development.

## 📧 Support

Questions or feedback? Open an issue on GitHub or reach out to the maintainers.

---

**Built with ❤️ using Test-Driven Development & GitHub Copilot Integration**

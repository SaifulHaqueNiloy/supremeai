# SupremeAI 2.0 — Contributing Guide

**Version**: 2.0.0  
**Last Updated**: 2025-01-04  
**Status**: Active  

---

## 🎯 Welcome Contributors!

Thank you for your interest in contributing to SupremeAI 2.0! This guide will help you understand how to contribute effectively to this AI-native engineering platform.

### 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure](#project-structure)
5. [How to Contribute](#how-to-contribute)
6. [Development Workflow](#development-workflow)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation Guidelines](#documentation-guidelines)
9. [Pull Request Process](#pull-request-process)
10. [Code Review Process](#code-review-process)
11. [Community](#community)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- ✅ Be respectful and inclusive
- ✅ Welcome diverse perspectives
- ✅ Accept constructive feedback gracefully
- ✅ Focus on what's best for the community
- ✅ Show empathy towards other community members

### Unacceptable Behavior

- ❌ Harassment or discriminatory language
- ❌ Personal attacks or trolling
- ❌ Publishing others' private information
- ❌ Any conduct that would be inappropriate in a professional setting

**Reporting**: If you experience unacceptable behavior, please email conduct@supremeai.com.

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - Backend development
- **Node.js 18+** - Frontend development
- **PostgreSQL 15+** - Database
- **Redis 7+** - Caching and sessions
- **Git** - Version control
- **Docker & Docker Compose** - Containerization
- **pnpm** - Package manager

### Quick Start

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/supremeai.git
cd supremeai

# 3. Add upstream remote
git remote add upstream https://github.com/paykaribazaronline/supremeai.git

# 4. Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# 5. Install frontend dependencies
cd ../apps/studio-client
pnpm install

# 6. Set up environment variables
cp ../backend/.env.example ../backend/.env
# Edit .env with your configuration

# 7. Start databases (using Docker)
docker-compose up -d postgres redis

# 8. Run database migrations
cd ../backend
alembic upgrade head

# 9. Start backend
uvicorn core.app_user:app --reload

# 10. Start frontend (in another terminal)
cd apps/studio-client
pnpm dev

# 11. Visit http://localhost:3000
```

---

## 🛠️ Development Environment Setup

### Backend Setup

#### 1. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt
```

#### 2. Environment Variables

Create `.env` file in `backend/`:

```env
# Environment
ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/supremeai

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
GOOGLE_API_KEY=...

# External Services
QDRANT_URL=https://cluster.qdrant.tech
QDRANT_API_KEY=...
NEO4J_URL=neo4j://localhost:7687
NEO4J_PASSWORD=...

# Monitoring
SENTRY_DSN=...
```

#### 3. Database Setup

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Create database
psql -U postgres -c "CREATE DATABASE supremeai;"

# Run migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py
```

#### 4. Run Backend

```bash
# Development server with auto-reload
uvicorn core.app_user:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up backend
```

**Access**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

### Frontend Setup

#### 1. Node.js Environment

```bash
# Install dependencies
cd apps/studio-client
pnpm install

# Or with npm
npm install
```

#### 2. Environment Variables

Create `.env.local` in `apps/studio-client/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

#### 3. Run Frontend

```bash
# Development server
pnpm dev

# Or with Docker
docker-compose up frontend
```

**Access**: http://localhost:3000

---

### IDE Setup

#### VS Code (Recommended)

**Extensions**:
- Python (Microsoft)
- Pylance (Microsoft)
- ESLint (Microsoft)
- Prettier (Prettier)
- GitLens (GitKraken)
- Mermaid Markdown Syntax Highlighting
- Thunder Client (REST Client)

**Settings** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 📁 Project Structure

```
supremeai_2.0/
├── backend/                    # FastAPI backend
│   ├── core/                   # Core framework
│   │   ├── config.py           # Configuration
│   │   ├── security/           # Security module
│   │   ├── database/           # Database connections
│   │   └── middleware/         # Middleware
│   ├── api/                    # API routes
│   │   └── v1/                 # API v1
│   ├── services/               # Business logic
│   │   ├── llm/                # LLM gateway
│   │   ├── agent/              # Agent system
│   │   ├── memory/             # Memory system
│   │   └── tools/              # Tools
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas
│   ├── agents/                 # AI agents
│   ├── tests/                  # Tests
│   └── main.py                 # Entry point
│
├── apps/                       # Frontend applications
│   ├── studio-client/          # Main web app
│   │   ├── src/
│   │   │   ├── components/     # React components
│   │   │   ├── pages/          # Pages
│   │   │   ├── stores/         # State management
│   │   │   ├── services/       # API services
│   │   │   └── utils/          # Utilities
│   │   └── public/             # Static assets
│   ├── admin/                  # Admin dashboard
│   └── mobile/                 # Mobile app
│
├── cloudflare-worker/          # Edge layer
├── infrastructure/             # Infrastructure as Code
├── config/                     # Configuration files
├── docs/                       # Documentation
│   ├── knowledge-base/         # AI-native docs
│   ├── api/                    # API docs
│   └── operations/             # Operations guides
├── scripts/                    # Automation scripts
├── tools/                      # Development tools
└── shared/                     # Shared libraries
```

---

## 🤝 How to Contribute

### Types of Contributions

We welcome all types of contributions:

1. **Bug Reports** - Report bugs and issues
2. **Feature Requests** - Suggest new features
3. **Documentation** - Improve or add documentation
4. **Code** - Fix bugs or implement features
5. **Tests** - Add or improve tests
6. **Design** - UI/UX improvements
7. **Translation** - Translate documentation
8. **Review** - Review pull requests

---

### Reporting Bugs

**Before reporting**:
- Check existing issues to avoid duplicates
- Collect relevant information (logs, screenshots, steps to reproduce)

**Bug Report Template**:
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 2.0.0]

## Screenshots
If applicable

## Additional Context
Any other relevant information
```

---

### Suggesting Features

**Feature Request Template**:
```markdown
## Feature Description
Clear description of the feature

## Problem It Solves
What problem does this solve?

## Proposed Solution
How should it be implemented?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Mockups, examples, etc.
```

---

## 🔄 Development Workflow

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/amazing-feature

# Or for bug fixes
git checkout -b fix/bug-description

# Or for documentation
git checkout -b docs/improve-readme
```

**Branch Naming Convention**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions
- `chore/` - Maintenance tasks

---

### 2. Make Changes

**Best Practices**:
- Write clean, readable code
- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits atomic and focused

**Code Style**:

**Python** (Backend):
```python
# Use Black formatter
black .

# Use isort for imports
isort .

# Use flake8 for linting
flake8 .

# Type hints required
def process_data(data: dict[str, Any]) -> Result:
    pass
```

**TypeScript** (Frontend):
```typescript
// Use ESLint
pnpm lint

// Use Prettier
pnpm format

// Type safety required
interface User {
  id: string;
  email: string;
}
```

---

### 3. Test Your Changes

#### Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=.

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run specific test
pytest tests/unit/test_auth.py::test_login -v
```

**Test Requirements**:
- ✅ All new features must have tests
- ✅ All bug fixes must have regression tests
- ✅ Test coverage must not decrease
- ✅ All tests must pass

#### Frontend Tests

```bash
# Run tests
pnpm test

# Run with coverage
pnpm test -- --coverage

# Run in watch mode
pnpm test -- --watch
```

#### Documentation Tests

```bash
# Test code examples in documentation
python docs/knowledge-base/templates/test_documentation.py
```

---

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(auth): add OAuth2 support

- Add OAuth2 authentication flow
- Support Google and GitHub providers
- Update documentation
- Add tests

Closes #123"
```

**Conventional Commits Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Test additions or changes
- `chore` - Maintenance tasks

**Examples**:
```
feat(agents): add tool chaining support
fix(auth): resolve token expiration issue
docs(api): update authentication examples
refactor(memory): optimize query performance
test(llm): add integration tests for gateway
```

---

### 5. Push to Your Fork

```bash
# Push to your fork
git push origin feature/amazing-feature
```

---

### 6. Create Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template
5. Submit for review

**PR Template**:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Documentation
- [ ] Documentation updated
- [ ] Code examples tested
- [ ] CHANGELOG.md updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No merge conflicts
- [ ] All checks passing

## Related Issues
Closes #123
Relates to #456
```

---

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_auth.py
│   ├── test_agents.py
│   └── test_tools.py
├── integration/             # Integration tests
│   ├── test_api.py
│   └── test_database.py
├── e2e/                     # End-to-end tests
│   └── test_workflows.py
└── conftest.py              # Test configuration
```

### Writing Tests

**Unit Tests**:
```python
import pytest
from services.llm.gateway import LLMGateway

def test_llm_gateway_generate():
    """Test LLM generation"""
    gateway = LLMGateway()
    result = gateway.generate(
        provider="openai",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
    assert result is not None
    assert len(result) > 0
```

**Integration Tests**:
```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_login_endpoint():
    """Test login endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### Test Coverage

- **Target**: >90% coverage
- **Critical paths**: 100% coverage
- **New features**: Must include tests

```bash
# Check coverage
pytest tests/ --cov=. --cov-report=html

# View report
open htmlcov/index.html
```

---

## 📝 Documentation Guidelines

### Documentation Structure

```
docs/
├── knowledge-base/         # AI-native knowledge base
│   ├── INDEX.md           # Start here
│   ├── 01-PROJECT_OVERVIEW.md
│   ├── 03-ARCHITECTURE.md
│   ├── 11-API_DOCUMENTATION.md
│   └── templates/         # Documentation templates
├── api/                   # API-specific docs
├── operations/            # Operations guides
└── README.md              # Documentation index
```

### Writing Documentation

**Use Templates**:
```bash
# For API endpoints
cp docs/knowledge-base/templates/API_ENDPOINT_TEMPLATE.md docs/api/v1/new-endpoint.md

# For modules
cp docs/knowledge-base/templates/MODULE_DOCUMENTATION_TEMPLATE.md docs/modules/new-module.md
```

**Documentation Standards**:
- ✅ Clear, concise language
- ✅ Code examples for everything
- ✅ Verification steps included
- ✅ Cross-references to related docs
- ✅ Diagrams for complex concepts
- ✅ Error handling documented
- ✅ Security considerations noted

### Code Examples

**Requirements**:
- All code examples must be tested
- Multiple languages when applicable
- Comments explaining complex parts
- Expected output shown

**Example**:
```python
# ✅ Good example
import httpx

async def fetch_user(user_id: str) -> dict:
    """Fetch user by ID
    
    Args:
        user_id: User's unique identifier
    
    Returns:
        User data dictionary
    
    Raises:
        HTTPException: If user not found
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/users/{user_id}"
        )
        response.raise_for_status()
        return response.json()

# Usage
user = await fetch_user("123")
print(user)  # {'id': '123', 'name': 'John Doe'}
```

---

## 🔀 Pull Request Process

### PR Requirements

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] Self-review completed

### PR Review Process

1. **Automated Checks** - CI/CD runs tests
2. **Code Review** - At least one approval required
3. **Documentation Review** - Docs team reviews
4. **Security Review** - Security team reviews (if needed)
5. **Merge** - Squash and merge to main

### Review Timeline

- **Initial Response**: Within 48 hours
- **Full Review**: Within 1 week
- **Merge**: After approval

---

## 👥 Code Review Process

### As a Reviewer

**Checklist**:
- [ ] Code is correct and efficient
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] No security vulnerabilities
- [ ] No performance issues
- [ ] Follows best practices
- [ ] Backward compatible (or migration guide provided)

**Providing Feedback**:
```markdown
## Summary
Brief overview of the PR

## Strengths
- Good test coverage
- Clear documentation

## Suggestions
- Consider using async/await here
- Add error handling for edge case

## Questions
- Why did you choose this approach?
- Have you considered X?

## Approval
✅ Approved with minor suggestions
```

### As an Author

**Responding to Feedback**:
- Be open to suggestions
- Ask questions if unclear
- Make requested changes promptly
- Thank reviewers for their time

---

## 🌐 Community

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and ideas
- **Discord** - Real-time chat (coming soon)
- **Email** - support@supremeai.com

### Getting Help

- **Documentation**: [docs/](docs/)
- **FAQ**: [docs/FAQ.md](FAQ.md)
- **Discussions**: [GitHub Discussions](https://github.com/.../discussions)
- **Issues**: [GitHub Issues](https://github.com/.../issues)

### Contributing Levels

1. **First-time Contributor** - Start with good first issues
2. **Regular Contributor** - Regular PRs and reviews
3. **Core Contributor** - Maintainers and reviewers
4. **Maintainer** - Full project maintainers

**Path to Maintainer**:
1. Make consistent contributions
2. Help with code reviews
3. Help with documentation
4. Be nominated by existing maintainers
5. Vote by maintainers

---

## 📊 Contribution Guidelines

### What to Contribute

**Good First Issues**:
- Documentation improvements
- Bug fixes
- Test coverage improvements
- Small feature additions

**Advanced Contributions**:
- New features
- Architecture changes
- Performance improvements
- Security enhancements

### What Not to Contribute

- ❌ Breaking changes without discussion
- ❌ Large refactors without ADR
- ❌ Code without tests
- ❌ Documentation without examples

---

## 🎓 Learning Resources

### SupremeAI 2.0

- [Documentation](docs/knowledge-base/INDEX.md)
- [Video Tutorials](https://youtube.com/...)
- [Architecture Guide](docs/knowledge-base/03-ARCHITECTURE.md)
- [API Reference](docs/knowledge-base/11-API_DOCUMENTATION.md)

### Technologies Used

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/docs/)
- [Neo4j](https://neo4j.com/docs/)
- [Qdrant](https://qdrant.tech/documentation/)

---

## ✅ Checklist for Contributors

### Before Starting
- [ ] Read this guide completely
- [ ] Set up development environment
- [ ] Run tests to ensure everything works
- [ ] Check existing issues and PRs

### During Development
- [ ] Create feature branch
- [ ] Write tests first (TDD)
- [ ] Follow code style guidelines
- [ ] Update documentation
- [ ] Test thoroughly

### Before Submitting
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Self-review completed
- [ ] No merge conflicts

---

## 📞 Support

### Questions?

- **Documentation**: [docs/](docs/)
- **Discussions**: [GitHub Discussions](https://github.com/.../discussions)
- **Issues**: [GitHub Issues](https://github.com/.../issues)
- **Email**: support@supremeai.com

### Feedback

We value your feedback! Please let us know:
- What could be improved in this guide?
- What's missing or unclear?
- What helped you the most?

---

## 🙏 Thank You!

Thank you for contributing to SupremeAI 2.0! Your contributions help make this project better for everyone.

**Happy Coding! 🚀**

---

**Document Status**: ✅ Complete and Verified  
**Version**: 2.0.0  
**Last Updated**: 2025-01-04  
**Owner**: Documentation Team  
**Classification**: Public  
**Next Review**: 2025-02-04
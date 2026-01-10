# Code Quality Standards

## Linting & Formatting

### Backend (Python)
- **Formatter**: Black (line length: 127)
- **Linter**: Flake8 (with E203 ignored for Black compatibility)
- **Type Checking**: mypy (with missing imports ignored for now)
- **Style Guide**: PEP 8

### Frontend (TypeScript/React)
- **Formatter**: Prettier
- **Linter**: ESLint with TypeScript rules
- **Type Checking**: TypeScript compiler

## Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

Hooks will run:
- Black formatting check
- Flake8 linting
- ESLint + Prettier for frontend
- Basic unit tests
- File validation (YAML, JSON, etc.)

## Code Review Guidelines

### What to Review
1. **Functionality**: Does it work as intended?
2. **Testing**: Are there adequate tests?
3. **Security**: Any security vulnerabilities?
4. **Performance**: Any performance issues?
5. **Readability**: Is the code easy to understand?
6. **Documentation**: Is it well documented?

### Review Checklist
- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] No security issues
- [ ] Error handling appropriate
- [ ] Logging added where needed
- [ ] Documentation updated
- [ ] No hardcoded secrets/credentials
- [ ] Performance considered

## Testing Requirements

### Before Merge
- All unit tests pass
- All integration tests pass
- Code coverage > 80%
- No critical security issues

### Test Coverage Goals
- Critical paths: 95%+
- Core services: 90%+
- Utilities: 80%+
- Frontend components: 75%+

## Performance Standards

- API response time: < 200ms (P95)
- Voice agent latency: < 2s (end-to-end)
- Database query time: < 100ms (P95)
- Frontend load time: < 3s (First Contentful Paint)

## Documentation Standards

### Code Comments
- Explain "why", not "what"
- Complex logic must be commented
- Public APIs must have docstrings

### README Files
- Each major component should have README
- Include setup instructions
- Include usage examples

## Technical Debt Tracking

Track technical debt in:
- GitHub Issues (labeled "technical-debt")
- Architecture Decision Records (ADRs)
- Code comments with TODO/FIXME

## Code Metrics

Monitor:
- Cyclomatic complexity (< 10 per function)
- Code duplication (< 3%)
- Test coverage (> 80%)
- Code churn (track changes)


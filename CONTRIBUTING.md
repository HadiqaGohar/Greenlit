# Contributing to Greenlit AI 🎬

Thank you for your interest in contributing to Greenlit AI! We welcome contributions from developers, filmmakers, and anyone passionate about improving production workflows.

## 🎯 How to Contribute

### 🐛 Bug Reports
- Use the GitHub issue tracker
- Describe the bug clearly with steps to reproduce
- Include screenshots or screen recordings when helpful
- Mention your browser/OS version

### 💡 Feature Requests  
- Check existing issues first to avoid duplicates
- Describe the feature and its use case
- Explain how it benefits film/TV production workflows
- Consider the cinematic theme and user experience

### 🔧 Code Contributions

#### Setup Development Environment
1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/greenlit-ai.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📏 Code Standards

### Frontend (Next.js/TypeScript)
- Use TypeScript for type safety
- Follow React best practices and hooks patterns
- Maintain the cinematic design theme
- Use Tailwind CSS classes consistently
- Add proper error handling and loading states

### Backend (FastAPI/Python)
- Follow PEP 8 style guidelines
- Use type hints with Pydantic models
- Add proper error handling and validation
- Include docstrings for functions and classes
- Write tests for new endpoints

### Design Guidelines
- Maintain the "script supervisor's desk" aesthetic
- Use the established color palette:
  - Charcoal: `#0B0B0D` (backgrounds)
  - Amber: `#D4A017` (accents)  
  - Parchment: `#F5F1E8` (text)
  - Verified: `#4C9A6E` (success)
  - Flagged: `#C0392B` (errors)
- Include film motifs (sprockets, reels, clapperboards)
- Ensure accessibility compliance

## 🧪 Testing

### Frontend Testing
```bash
npm run test
npm run lint
```

### Backend Testing
```bash
pytest
black --check .
flake8
```

### Manual Testing
- Test the complete workflow: script input → analysis → report
- Verify mobile responsiveness
- Check keyboard navigation and screen reader compatibility
- Test with various script formats and content types

## 📝 Commit Guidelines

### Commit Message Format
```
type(scope): description

[optional body]
[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style/formatting changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(frontend): add PDF export functionality
fix(backend): resolve Parallel API timeout issues
docs(readme): update installation instructions
style(components): improve film grain texture effect
```

## 🎬 Film Industry Context

When contributing, consider:
- **Production Workflow**: How does this fit into pre-production processes?
- **Industry Standards**: Follow film/TV production terminology and practices
- **User Experience**: Production coordinators and researchers are the primary users
- **Accuracy**: Fact-checking and research quality are paramount
- **Performance**: Productions work under tight deadlines

## 🚀 Pull Request Process

1. **Update Documentation**: Include relevant docs updates
2. **Add Tests**: Ensure new features have adequate test coverage  
3. **Check Design**: Maintain the cinematic theme and accessibility
4. **Verify Functionality**: Test the full user workflow
5. **Clean History**: Use clear, descriptive commit messages

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Added/updated tests
- [ ] Verified mobile responsiveness
- [ ] Checked accessibility

## Film Industry Impact
How does this improve production workflows?

## Screenshots/Demo
Include visual evidence of changes
```

## 🏆 Recognition

Contributors will be:
- Listed in the README acknowledgments
- Mentioned in release notes for significant contributions  
- Invited to provide feedback on future roadmap decisions

## 📞 Getting Help

- **Questions**: Open a GitHub discussion
- **Real-time Chat**: Join our community Slack (link in README)
- **Documentation**: Check the project wiki
- **API Issues**: Review the backend API documentation

## 📄 Code of Conduct

- Be respectful and professional
- Welcome newcomers and diverse perspectives
- Focus on constructive feedback
- Respect the film industry context and terminology
- Help maintain a positive, collaborative environment

## 🎭 Film Industry Terminology

When contributing, use proper industry terms:
- **Script Supervisor**: Person who ensures continuity and accuracy
- **Production Notes**: Detailed annotations and research findings
- **Claims**: Factual statements requiring verification  
- **Continuity**: Consistency across scenes and shots
- **Clearance**: Legal permission to use copyrighted material

---

**Ready to contribute? We're excited to see what you'll build! 🎬✨**

*Remember: Every great film starts with attention to detail in pre-production.*
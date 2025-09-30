# UN SDG Advocate 🌍

An AI-powered tool that analyzes GitHub repositories and determines their alignment with the United Nations Sustainable Development Goals (SDGs). The application provides confidence scores for each of the 17 SDGs and can automatically create pull requests with the analysis results.

## Features

- 🔍 **Repository Analysis**: Analyzes GitHub repositories using AI to determine SDG alignment
- 📊 **Confidence Scoring**: Provides confidence levels (High/Medium/Low) for each SDG match
- ✏️ **Interactive Editing**: Edit and modify SDG predictions through an intuitive modal interface
- ➕ **Add/Remove SDGs**: Dynamically add or remove SDG predictions
- 🔄 **Automatic Pull Requests**: Create GitHub pull requests with analysis results in JSON format
- 💻 **Modern UI**: Clean, responsive React.js interface with real-time loading states

## Architecture

- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, and React Icons
- **Backend**: Flask API with AI classification using sentence-transformers
- **Integration**: GitHub API for automated pull request creation

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- GitHub Personal Access Token (for PR functionality)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd UNSDG-advocate
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
export GITHUB_TOKEN=your_github_token_here  # See GITHUB_SETUP.md for details
python app.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:5000

## Usage

1. **Enter GitHub URL**: Input any public GitHub repository URL
2. **Analyze**: Click "Let's find out" to start AI analysis
3. **Review Results**: View SDG predictions with confidence levels
4. **Edit (Optional)**: Use "Maybe, we need some edits" to modify predictions
5. **Create PR**: Click "Yes, that's our goal" to create a pull request with results

## SDG Analysis Output

The tool generates a `unsdg.json` file containing:

```json
{
  "sdg_analysis": {
    "analyzed_at": "2025-01-11T10:30:00.000Z",
    "repository": "https://github.com/user/repo",
    "predictions": {
      "SDG 1": 0.85,
      "SDG 3": 0.72,
      "SDG 4": 0.91
    },
    "summary": {
      "total_sdgs": 3,
      "high_confidence": 2,
      "medium_confidence": 1,
      "low_confidence": 0
    }
  }
}
```

## Configuration

### GitHub Token Setup

See `GITHUB_SETUP.md` for detailed instructions on creating and configuring your GitHub Personal Access Token.

### Environment Variables

```bash
GITHUB_TOKEN=your_token_here  # Required for pull request functionality
```

## API Endpoints

### POST /api/classify

Analyzes a GitHub repository for SDG alignment.

**Request:**

```json
{
  "url": "https://github.com/user/repository"
}
```

**Response:**

```json
{
  "sdg_predictions": {
    "SDG 1": 0.85,
    "SDG 3": 0.72
  }
}
```

### POST /api/create-pr

Creates a pull request with SDG analysis results.

**Request:**

```json
{
  "owner": "username",
  "repo": "repository",
  "content": "JSON content",
  "message": "Add UN SDG analysis results",
  "description": "PR description"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:

- Check existing issues in the repository
- Create a new issue with detailed description
- Include logs and error messages when applicable

A responsive website for categorizing the open source projects into different UN SDG's goals that closely align with their repository by reading their directory.

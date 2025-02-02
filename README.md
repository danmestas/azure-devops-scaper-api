# 🚀 Azure DevOps Intelligence Engine

[![GitHub Stars](https://img.shields.io/github/stars/yourusername/azure-devops-scraper-api?style=for-the-badge)](https://github.com/yourusername/azure-devops-scraper-api/stargazers)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

The **Enterprise-Grade** Azure DevOps Intelligence Platform that transforms your ticket chaos into actionable insights.

![API Demo](https://via.placeholder.com/800x400.png?text=Swagger+UI+Demo+Shot)

## ⚡ Features

- **Full Spectrum Data Capture** - Tickets, Bugs, Tasks, Epics
- **Military-Grade Security** - PAT encryption ready
- **Query Like a God** - WIQL on steroids
- **Analytics Ready** - Clean Pydantic models
- **Blazing Fast** - Async-first architecture

## 🛠️ Installation

```bash
# Clone with credentials
git clone https://github.com/yourusername/azure-devops-scraper-api
cd azure-devops-scraper-api

# Build environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure secrets
cp .env.example .env && nano .env
```

## 🔥 Ignition

```bash
uvicorn app.main:app --reload
```

**Access Points:**
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/`

## 💻 API Examples

```bash
# Get all tickets
curl -X 'GET' 'http://localhost:8000/api/v1/tickets' -H 'accept: application/json'

# Custom WIQL query
curl -X 'GET' 'http://localhost:8000/api/v1/tickets?query=SELECT+[System.Id]+FROM+WorkItems+WHERE+[System.Tags]+CONTAINS+"CRITICAL"' -H 'accept: application/json'
```

## 🌌 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_DEVOPS_ORG` | Azure DevOps organization name | `contoso-devops` |
| `AZURE_DEVOPS_PAT` | Personal Access Token | `v6tb7****qir2a` |
| `DEFAULT_WIQL` | Base query for tickets | `SELECT [System.Id]...` |

## 🚨 Roadmap

- [ ] Data Lake Integration
- [ ] Live Query Analytics
- [ ] Auto-PAT Rotation
- [ ] Query Presets

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feat/armageddon`)
3. Commit changes (`git commit -am 'Add apocalyptic feature'`)
4. Push to branch (`git push origin feat/armageddon`)
5. Open Pull Request

## 📜 License

Apache 2.0 - See [LICENSE](LICENSE) for details.
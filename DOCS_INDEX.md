# Documentation Index

This index helps you navigate the Lookbook-MPC documentation efficiently. All files have been organized into logical folders with duplicate information removed and outdated content consolidated.

## 🚀 Getting Started

**Start here for setup and basic usage:**

1. **[README.md](README.md)** - Project overview, quick start, and architecture
2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Step-by-step installation instructions
3. **[PROJECT_KNOWLEDGE_BASE.md](PROJECT_KNOWLEDGE_BASE.md)** - Comprehensive system knowledge base

## 📁 Documentation Structure

### Core Files (Root Level)
- **[README.md](README.md)** - Project overview and quick start
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Installation and setup instructions
- **[PROJECT_KNOWLEDGE_BASE.md](PROJECT_KNOWLEDGE_BASE.md)** - Complete system knowledge base
- **[START_HERE_AGENT.xml](START_HERE_AGENT.xml)** - AI agent configuration and guidelines

### 📋 PRP Folder - Product Requirement Prompts
**Location: [PRP/](PRP/)**

Contains all planning and requirement documents:
- **[PRP/lookbook.PRD](PRP/lookbook.PRD)** - Product Requirements Document
- **[PRP/lookbook.PRP](PRP/lookbook.PRP)** - Main execution plan and technical specifications
- **[PRP/IMPORT-PRODUCT-PLAN.md](PRP/IMPORT-PRODUCT-PLAN.md)** - Product import system requirements
- **[PRP/PERSONNA_MANAGEMENET-PLAN.md](PRP/PERSONNA_MANAGEMENET-PLAN.md)** - Agent persona management specs
- **[PRP/PERSONNA_MANAGEMENET-PLAN-OUTCOME.md](PRP/PERSONNA_MANAGEMENET-PLAN-OUTCOME.md)** - Persona system implementation results
- **[PRP/PERSONNA_MANAGEMENET_DASHBOARD_PLAN.md](PRP/PERSONNA_MANAGEMENET_DASHBOARD_PLAN.md)** - Dashboard UI specifications
- **[PRP/PLAN-AKENEO.md](PRP/PLAN-AKENEO.md)** - Akeneo integration requirements
- **[PRP/plan.md](PRP/plan.md)** - General project roadmap

### 📚 Doc Folder - Technical Documentation
**Location: [doc/](doc/)**

Contains all technical guides and documentation:

#### Core Technical Guides
- **[doc/RECOMMENDATION_ENGINE_GUIDE.md](doc/RECOMMENDATION_ENGINE_GUIDE.md)** - ⭐ **NEW** Complete guide to the AI recommendation system
- **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)** - System architecture and design patterns
- **[doc/TECHNICAL_GUIDE.md](doc/TECHNICAL_GUIDE.md)** - Comprehensive technical implementation details
- **[doc/FEATURES_AND_CAPABILITIES.md](doc/FEATURES_AND_CAPABILITIES.md)** - Complete feature overview

#### Setup and Operations
- **[doc/ENVIRONMENT_SETUP.md](doc/ENVIRONMENT_SETUP.md)** - Environment configuration
- **[doc/DEPLOYMENT.md](doc/DEPLOYMENT.md)** - Production deployment instructions
- **[doc/DEPLOYMENT_SUCCESS.md](doc/DEPLOYMENT_SUCCESS.md)** - Deployment validation and success metrics
- **[doc/DEBUG_GUIDE.md](doc/DEBUG_GUIDE.md)** - Troubleshooting and performance optimization

#### User Documentation
- **[doc/USER_GUIDE.md](doc/USER_GUIDE.md)** - Usage patterns and examples
- **[doc/QUICK_REFERENCE.md](doc/QUICK_REFERENCE.md)** - Essential commands and configuration
- **[doc/QUICK_START.md](doc/QUICK_START.md)** - Quick setup guide

#### Specialized Documentation
- **[doc/VISION_ANALYSIS_README.md](doc/VISION_ANALYSIS_README.md)** - AI vision analysis system
- **[doc/BEAUTIFUL_DASHBOARD_SUMMARY.md](doc/BEAUTIFUL_DASHBOARD_SUMMARY.md)** - Dashboard UI documentation
- **[doc/DOCUMENTATION_REORGANIZATION_SUMMARY.md](doc/DOCUMENTATION_REORGANIZATION_SUMMARY.md)** - Documentation restructuring notes
- **[doc/FINAL_CLEANUP_VALIDATION.md](doc/FINAL_CLEANUP_VALIDATION.md)** - System validation checklist
- **[doc/SCRIPTS_CLEANUP_SUMMARY.md](doc/SCRIPTS_CLEANUP_SUMMARY.md)** - Scripts organization documentation

## 🤖 Understanding the Recommendation Engine

**⭐ NEW: Comprehensive Recommendation Engine Guide**

The **[doc/RECOMMENDATION_ENGINE_GUIDE.md](doc/RECOMMENDATION_ENGINE_GUIDE.md)** provides complete documentation of how the AI-powered recommendation system works:

### Key Sections:
- **Architecture Overview** - Complete data flow from user input to recommendations
- **Component Deep Dive** - Intent Parser, Smart Recommender, Rules Engine, LLM Providers
- **Code Examples** - Input/output examples for every major function
- **Database Schema** - Product tables and scoring algorithms
- **API Response Format** - Complete JSON response structures
- **Error Handling** - Fallback mechanisms and troubleshooting
- **Performance** - Caching, optimization, and monitoring

### Quick Understanding:
```
User: "I go to dance"
  ↓
Intent Parser (LLM) → {"activity": "dancing", "occasion": "party"}
  ↓  
Smart Recommender → Generate keywords: ["party", "stylish", "trendy"]
  ↓
Product Search → Find matching items with relevance scores
  ↓
Outfit Assembly → Create complete outfit combinations
  ↓
Response: Natural language + product recommendations
```

## 🖥️ Admin Dashboard

**For the Next.js admin dashboard:**
- **[shadcn/README.md](shadcn/README.md)** - Dashboard overview and features
- **[shadcn/TESTING_GUIDE.md](shadcn/TESTING_GUIDE.md)** - Testing procedures for dashboard
- **[shadcn/TROUBLESHOOTING.md](shadcn/TROUBLESHOOTING.md)** - Dashboard-specific troubleshooting

## 📋 Quick Reference

### Essential Commands
```bash
# Start all services
ollama serve                    # Terminal 1
python vision_sidecar.py        # Terminal 2
python main.py                  # Terminal 3
cd shadcn && npm run dev        # Terminal 4
```

### Key URLs
- **API Documentation**: http://localhost:8000/docs
- **Demo Interface**: http://localhost:8000/demo
- **Admin Dashboard**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

### Essential API Endpoints
- `POST /v1/ingest/products` - Ingest products from catalog
- `POST /v1/recommendations` - Generate outfit recommendations
- `POST /v1/chat` - Chat interaction with AI fashion assistant
- `GET /v1/ingest/stats` - Get system statistics

## 💡 How to Use This Documentation

### For New Users
1. Read **[README.md](README.md)** for project overview
2. Check **[doc/FEATURES_AND_CAPABILITIES.md](doc/FEATURES_AND_CAPABILITIES.md)** to understand capabilities
3. Follow **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for installation
4. Use **[doc/USER_GUIDE.md](doc/USER_GUIDE.md)** for daily operations

### For Developers
1. Start with **[README.md](README.md)** and **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)**
2. **[doc/RECOMMENDATION_ENGINE_GUIDE.md](doc/RECOMMENDATION_ENGINE_GUIDE.md)** - Understand the core AI system
3. Review **[doc/TECHNICAL_GUIDE.md](doc/TECHNICAL_GUIDE.md)** for implementation details
4. Use **[PROJECT_KNOWLEDGE_BASE.md](PROJECT_KNOWLEDGE_BASE.md)** for deep technical knowledge
5. Check **[doc/DEBUG_GUIDE.md](doc/DEBUG_GUIDE.md)** for troubleshooting

### For System Administrators
1. **[doc/DEPLOYMENT.md](doc/DEPLOYMENT.md)** for production setup
2. **[doc/ENVIRONMENT_SETUP.md](doc/ENVIRONMENT_SETUP.md)** for configuration
3. **[doc/DEBUG_GUIDE.md](doc/DEBUG_GUIDE.md)** for monitoring and optimization
4. Admin dashboard docs for management interface

### For Product Managers
1. **[PRP/lookbook.PRD](PRP/lookbook.PRD)** - Product requirements and specifications
2. **[doc/FEATURES_AND_CAPABILITIES.md](doc/FEATURES_AND_CAPABILITIES.md)** - Complete feature overview
3. **[PRP/](PRP/)** folder - All planning documents and outcomes

## 📖 Documentation Principles

### Organized Structure
- **Root Level**: Essential files everyone needs
- **PRP Folder**: Planning and requirements (for development planning)
- **Doc Folder**: Technical documentation (for implementation and operations)

### Quality Features
- ✅ **No Duplicates** - Each piece of information exists in one place
- ✅ **Clear Purpose** - Each file has a specific, well-defined role
- ✅ **Cross-Referenced** - Easy navigation between related topics
- ✅ **Code Examples** - Practical examples with input/output samples
- ✅ **Updated & Current** - Reflects the actual implemented system

### Recent Improvements
- 📁 **Better Organization** - Files grouped by purpose (PRP, doc)
- 🤖 **Recommendation Engine Guide** - Complete AI system documentation
- 💬 **Code Comments** - Detailed comments added to core recommendation code
- 🔍 **Input/Output Examples** - Clear examples for every major function
- 🧹 **Consolidated Content** - Removed outdated and duplicate information

## 🔗 Related Documentation

### Testing Documentation
- **[tests/README.md](tests/README.md)** - Test suite documentation
- **[scripts/OPENROUTER_BENCHMARK_README.md](scripts/OPENROUTER_BENCHMARK_README.md)** - Benchmarking tools

### Legacy Documentation
- **[docs/README.md](docs/README.md)** - Additional legacy documentation resources

---

**Documentation Structure**: 
- **Root Files**: 4 essential files
- **PRP Folder**: 8 planning documents  
- **Doc Folder**: 15 technical guides
- **Total**: Well-organized, comprehensive documentation

**Status**: ✅ **Production Ready** - All features documented with clear examples

---

**Last Updated**: December 2024
**Documentation Version**: 3.0 (Reorganized + Enhanced)
**Maintenance**: Updated with new folder structure and recommendation engine documentation
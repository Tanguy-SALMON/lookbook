# PROJECT KNOWLEDGE BASE
# Modern Chat Dashboard for Fashion E-commerce

## 🚀 PROJECT OVERVIEW

**Project Name:** Modern Chat Dashboard
**Purpose:** Advanced chat interface for fashion e-commerce customer support with AI-powered recommendations
**Market:** Thailand fashion e-commerce (COS Thailand)
**Currency:** Thai Baht (THB)
**Technology Stack:** HTML5 + Tailwind CSS + Vanilla JavaScript + FastAPI Backend + MySQL + Ollama LLM + CloudFront CDN
**Current Status:** ✅ **FULLY OPERATIONAL** - Complete recommendation system with working chat interface

## 🎯 CORE FUNCTIONALITY

The modern chat dashboard provides:
- **Real-time customer communication** with intuitive message interface
- **Customer intelligence indicators** showing online status, message count, and purchase intent
- **Product recommendation integration** with visual product cards
- **Advanced customer profiling** with purchase history and behavior analytics
- **Responsive design** optimized for desktop, tablet, and mobile devices

## 🎨 MODERN UI ARCHITECTURE

### **Design System:**
- **Framework:** Tailwind CSS v3.x with utility-first approach
- **Color Palette:** Professional gray scale with blue accents (`--accent-blue: #1890ff`)
- **Typography:** Onest font family with responsive sizing
- **Icons:** Inline SVG icons for optimal performance
- **Layout:** Flexbox and CSS Grid for responsive design

### **Component Structure:**
```
┌─────────────────────────────────────────────────────┐
│ Navigation Sidebar (80px) │ Main Content │ Right Panel │
│ - User avatar            │              │ (320px)     │
│ - Menu items            │   Chat Area   │ - Profile   │
│ - Active indicators     │              │ - Analytics │
│                         │              │ - Media     │
└─────────────────────────────────────────────────────┘
```

## 🗂️ FILE STRUCTURE

### **Critical Frontend Files:**
- **`docs/demo.html`** - **MAIN CHAT INTERFACE** - Complete responsive dashboard with AI recommendations
- **`docs/test_chat_frontend.html`** - **SIMPLE TEST INTERFACE** - Minimal UI for API testing
- **`docs/index.html`** - **DOCUMENTATION HUB** - Navigation and system overview
- **`assets/images/`** - Avatar images and UI assets
- **Inline CSS** - Tailwind utilities + custom properties for advanced effects

### **Backend Architecture:**
- **`main.py`** - FastAPI application with navigation landing page
- **`lookbook_mpc/api/routers/chat.py`** - Chat API endpoints with AI integration
- **`lookbook_mpc/services/smart_recommender.py`** - LLM-powered product recommendation engine
- **`lookbook_mpc/domain/use_cases.py`** - ChatTurn use case with outfit recommendations
- **`lookbook_mpc/adapters/intent.py`** - Natural language intent parsing

### **Key Sections:**
- **Navigation Sidebar** - User menu and active state management
- **Message List** - Customer conversations with intelligent indicators
- **Chat Area** - Message bubbles with product recommendations
- **Customer Profile** - Analytics and purchase behavior insights

## 💡 ADVANCED FEATURES

### **Purchase Intent Visualization:**
```css
.intent-bar {
    /* Circular progress indicator around avatar */
    background: conic-gradient(
        #ff6b6b 0deg,           /* Low intent - Red */
        #ffa726 calc(360deg * 0.25),  /* Medium-low - Orange */
        #ffcc02 calc(360deg * 0.5),   /* Medium - Yellow */
        #66bb6a calc(360deg * 0.75),  /* Medium-high - Light Green */
        #4caf50 360deg          /* High intent - Green */
    );
}
```

**Implementation Examples:**
- `width: 37%` = 37% purchase likelihood (orange zone)
- `width: 75%` = 75% purchase likelihood (green zone)
- `width: 88%` = 88% purchase likelihood (dark green zone)

### **Smart Status Indicators:**
```html
<!-- Triple indicator system on each avatar -->
<div class="message-avatar">
    <!-- Purchase intent ring -->
    <div class="intent-bar"><span style="width: 75%;"></span></div>
    <!-- Customer avatar -->
    <img src="avatar.webp" alt="Customer">
    <!-- Online status dot -->
    <span class="online-status online"></span>
    <!-- Message count badge -->
    <span class="notification-badge">6</span>
</div>
```

**Status Types:**
- **Online** - Green dot (`#52c41a`)
- **Away** - Amber dot (`#faad14`)
- **Offline** - Gray dot (`#8c8c8c`)

## 🛠️ TECHNICAL IMPLEMENTATION

### **CSS Architecture:**
- **95% Tailwind Utilities** - Modern utility-first approach
- **5% Custom CSS** - Complex gradients, masks, and pseudo-elements only
- **CSS Variables** - Semantic color system and responsive typography
- **Zero Bootstrap** - Pure Tailwind implementation

### **Responsive Design:**
```css
/* Mobile-first responsive breakpoints */
@media (max-width: 768px) { /* Mobile layout */ }
@media (min-width: 1280px) { /* Desktop optimized */ }
@media (min-width: 2560px) { /* 4K displays */ }
```

### **Performance Optimizations:**
- **Inline SVG icons** - No external icon dependencies
- **WebP images** - Modern image format with fallbacks
- **CSS containment** - Optimized rendering performance
- **Minimal JavaScript** - Pure vanilla JS for interactions

## 📱 COMPONENT SPECIFICATIONS

### **Message Bubbles:**
```html
<!-- Received message -->
<div class="max-w-[70%] p-3 px-4 rounded-2xl text-sm bg-gray-100 text-gray-800 self-start rounded-bl-sm">
    Message content
    <div class="text-xs text-gray-400 mt-1 text-right">14:30</div>
</div>

<!-- Sent message -->
<div class="max-w-[70%] p-3 px-4 rounded-2xl text-sm bg-blue-500 text-white self-end rounded-br-sm">
    Message content
    <div class="text-xs text-white/80 mt-1 text-right">14:32</div>
</div>
```

### **Product Recommendations:**
```html
<div class="bg-white border border-gray-200 rounded-xl p-4 mt-3 max-w-md">
    <div class="text-sm text-gray-600 mb-2">Product suggestion:</div>
    <div class="grid grid-cols-2 gap-3">
        <div class="border border-gray-200 rounded-lg overflow-hidden bg-white transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-md">
            <img src="product.jpg" class="w-full h-40 object-cover object-top">
            <div class="p-2">
                <div class="text-xs font-medium text-gray-800 mb-1">Product Name</div>
                <div class="text-xs font-semibold text-blue-500">฿1,990</div>
            </div>
        </div>
    </div>
</div>
```

### **Chat Input (Modern Design):**
```html
<div class="p-6 border-t border-gray-200 bg-gray-50">
    <div class="flex items-center gap-3 bg-white rounded-full px-4 py-3 border border-gray-200 shadow-sm">
        <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0">
            <img src="user-avatar.webp" class="w-full h-full object-cover">
        </div>
        <div class="flex items-center ml-auto gap-2">
            <!-- Drafts indicator -->
            <div class="bg-yellow-100 rounded-full px-3 py-1.5 text-sm text-gray-500">
                📄 1 Drafts
            </div>
            <!-- Action buttons -->
            <button class="w-8 h-8 bg-gray-100 rounded-full">📎</button>
            <button class="px-4 py-2 bg-blue-500 text-white rounded-full">
                Send ➤
            </button>
        </div>
    </div>
</div>
```

## 🎯 CUSTOMER ANALYTICS

### **Right Sidebar Intelligence:**
- **Customer Profile** - Avatar, name, last seen status
- **Purchase Analytics** - Customer ID, join date, total orders, lifetime value
- **Social Integration** - LINE, Facebook, Instagram, Shopee connections
- **Media Performance** - Accessory sales with product grid visualization
- **Category Labels** - Smart tagging system for customer segmentation

### **Sample Customer Data:**
```
Customer: Moise Kean
- ID: #MK2024001
- Join Date: Dec 15, 2023
- Total Orders: 23
- Lifetime Value: ฿89,350
- Purchase Intent: 75% (High)
- Status: Online
- Unread Messages: 3
```

## 🚀 DEVELOPMENT GUIDELINES

### **Coding Standards:**
- **Tailwind-first approach** - Use utilities before custom CSS
- **Semantic HTML** - Proper accessibility attributes
- **Mobile-responsive** - Test on all screen sizes
- **Performance-conscious** - Optimize images and minimize JavaScript

### **Adding New Features:**
1. **Design in Tailwind** - Use existing utility classes
2. **Custom CSS only for** - Complex gradients, masks, animations
3. **Maintain accessibility** - ARIA labels and keyboard navigation
4. **Test responsiveness** - Verify on mobile, tablet, desktop

### **File Organization:**
```
docs/
├── demo.html              # Main chat interface
├── assets/
│   └── images/            # Avatar and UI images
└── README.md             # Interface documentation
```

## 🔧 CONFIGURATION

### **Color System (CSS Variables):**
```css
:root {
    --primary-bg: #f8f9fb;      /* Light gray background */
    --accent-blue: #1890ff;      /* Primary blue for actions */
    --accent-green: #52c41a;     /* Success/online status */
    --text-primary: #1f2937;     /* Primary text color */
    --text-secondary: #6b7280;   /* Secondary text */
    --border-color: #e8eaed;     /* Border color */
    --message-bg: #f1f3f5;      /* Message background */
}
```

### **CDN Configuration:**
```bash
# Production CloudFront URL for COS Thailand products
S3_BASE_URL="https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/"
```

### **Typography Scale:**
```css
--font-size-xs: 11px;    /* Small labels */
--font-size-sm: 13px;    /* Body text */
--font-size-base: 14px;  /* Default size */
--font-size-md: 16px;    /* Headings */
--font-size-lg: 18px;    /* Large headings */
--font-size-xl: 20px;    /* Hero text */
```

## 🎉 CURRENT STATUS & FEATURES

### ✅ **Fully Implemented:**
- **Modern Chat Interface** - Complete responsive design with working AI chat
- **Purchase Intent Indicators** - Visual progress rings around avatars
- **Triple Status System** - Online status + message count + purchase intent
- **Product Integration** - Visual product cards with hover effects and real COS Thailand products
- **Customer Analytics** - Comprehensive profile and behavior insights
- **Responsive Design** - Works on all devices (mobile to 4K displays)
- **Performance Optimized** - Fast loading with minimal dependencies
- **AI Recommendation System** - LLM-powered outfit suggestions with real products
- **Navigation System** - Beautiful landing page with easy access to all interfaces
- **API Integration** - Complete backend/frontend communication
- **Real Product Data** - COS Thailand catalog with pricing in Thai Baht
- **Connection Status** - Real-time backend connectivity monitoring

### 🎯 **Key Achievements:**
- **95% CSS Reduction** - From 800+ lines of custom CSS to 150 lines
- **Modern Design System** - Tailwind utility-first architecture
- **Enhanced UX** - Intuitive purchase intent visualization
- **Production Ready** - Complete chat dashboard interface
- **AI Integration Success** - Natural language processing with outfit recommendations
- **Real-time Product Integration** - Live COS Thailand product catalog
- **Multi-Interface System** - Demo, test, and documentation interfaces
- **Beautiful Navigation** - Professional landing page with system overview
- **Developer Experience** - Complete API documentation and testing tools

### 🔮 **Future Enhancements:**
- **Real-time messaging** - WebSocket integration for instant communication
- **User authentication** - Session management and personalized recommendations
- **Shopping cart integration** - Direct purchase from chat recommendations
- **Multi-language support** - Thai/English localization
- **Voice input** - Speech-to-text for mobile users
- **Offline support** - Service worker for offline functionality
- **Advanced analytics** - Customer behavior tracking and A/B testing

## 🤖 AI RECOMMENDATION SYSTEM (BACKEND READY)

### **LLM-Powered Chat Responses:**
- **100% AI-generated responses** - No hardcoded messages, all natural conversations
- **Contextual understanding** - Interprets user intents (dancing, business, casual, etc.)
- **Real product integration** - AI responses enhanced with actual product suggestions

### **Working Examples:**
**Before (Generic):**
- "I understand you're looking for something great to wear!"
- No product suggestions
- Repetitive fallback messages

**After (AI-Powered):**
- Natural responses: "Perfect! I'll help you find stylish outfits for dancing..."
- **2 real outfit suggestions** with products, prices, and images
- Each conversation generates unique, contextual responses

### **Smart Recommendation Engine:**
```
User: "I go to dance"
↓
LLM Intent Parser: {activity: "dancing", occasion: "party", natural_response: "Perfect! I'll help..."}
↓
Smart Recommender: Finds products using generated keywords
↓
Response: Natural LLM text + 2 outfit suggestions with real products
```

### **API Response Structure:**
```json
{
  "replies": [{
    "type": "recommendations",
    "message": "Perfect! I'll help you find stylish outfits for dancing...",
    "outfits": 2
  }],
  "outfits": [{
    "title": "Casual And Comfortable Coordinated Set",
    "items": [{
      "sku": "0888940046012",
      "title": "RIBBED TANK TOP",
      "price": 790.0,
      "image_url": "https://cdn.../image.jpg",
      "color": "black",
      "category": "activewear"
    }],
    "total_price": 3380.0,
    "explanation": "This black top paired with black bottom creates the perfect look...",
    "outfit_type": "coordinated_set"
  }]
}
```

### **🔄 FLEXIBLE LLM PROVIDER SYSTEM (NEW)**

The system now supports **both local (Ollama) and cloud (OpenRouter) LLM providers** with seamless switching:

#### **Provider Options:**
- **Ollama (Local):** Fast, free, private - runs qwen3, llama3.2 locally
- **OpenRouter (Cloud):** Access to free models like qwen-2.5-7b:free, no local setup needed
- **Automatic Fallback:** OpenRouter → Ollama if API key missing

#### **Configuration Examples:**

**Development (Local Ollama):**
```bash
export LLM_PROVIDER="ollama"
export LLM_MODEL="qwen3:4b-instruct"
export OLLAMA_HOST="http://localhost:11434"
```

**Production (OpenRouter Free):**
```bash
export LLM_PROVIDER="openrouter" 
export OPENROUTER_API_KEY="sk-or-v1-..."
export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"
```

#### **Benefits:**
- ✅ **Easy switching** between local and cloud models
- ✅ **Cost optimization** with free OpenRouter models
- ✅ **No code changes** - purely environment-driven
- ✅ **Consistent API** across all providers
- ✅ **Automatic fallback** for reliability

#### **Testing Commands:**
```bash
# Test the flexible provider system
poetry run python scripts/test_llm_providers.py

# Demo switching between providers  
poetry run python scripts/demo_provider_switch.py

# Benchmark OpenRouter free models
poetry run python scripts/benchmark_models_openrouter.py --models "qwen/qwen-2.5-7b-instruct:free"
```

#### **Files Added:**
- `lookbook_mpc/adapters/llm_providers.py` - Provider abstraction layer
- `FLEXIBLE_LLM_SETUP.md` - Detailed configuration guide
- `scripts/test_llm_providers.py` - Provider testing utility
- `scripts/demo_provider_switch.py` - Switching demonstration

---

## 🌟 **NAVIGATION SYSTEM**

### **Main Landing Page**: `http://localhost:8000/`
- **Beautiful HTML interface** with navigation cards
- **System status indicators** showing feature availability  
- **Quick links** to all available pages
- **Real-time health checking** via JavaScript

### **Available Interfaces:**
| URL | Description | Purpose |
|-----|-------------|---------|
| `http://localhost:8000/` | **Main Landing Page** | Navigation hub with system info |
| `http://localhost:8000/demo` | **Full Demo Interface** | Complete chat UI with recommendations |
| `http://localhost:8000/test` | **Test Chat Frontend** | Simple testing interface |
| `http://localhost:8000/docs-index` | **Documentation Hub** | File listings and quick tests |
| `http://localhost:8000/docs` | **API Documentation** | Swagger UI for API testing |
| `http://localhost:8000/redoc` | **ReDoc Documentation** | Alternative API docs |
| `http://localhost:8000/health` | **Health Check** | JSON service status |
| `http://localhost:8000/ready` | **Readiness Probe** | Dependency status |

## 🛠️ **TECHNICAL CONFIGURATION**

### **Environment Variables:**

**Core Settings:**
```bash
# LLM Provider Selection (NEW)
LLM_PROVIDER="ollama"                    # or "openrouter"
LLM_MODEL="qwen3:4b-instruct"           # Primary model name
LLM_TIMEOUT=30                          # Request timeout

# OpenRouter Settings (NEW)
OPENROUTER_API_KEY="sk-or-v1-..."      # Get from openrouter.ai/keys
OPENROUTER_MODEL="qwen/qwen-2.5-7b-instruct:free"  # Free model

# Ollama Settings (Existing)
OLLAMA_HOST="http://localhost:11434"
OLLAMA_VISION_MODEL="qwen2.5vl:7b"
OLLAMA_TEXT_MODEL="qwen3:4b"
OLLAMA_TEXT_MODEL_FAST="llama3.2:1b-instruct-q4_K_M"

# Database & Storage
S3_BASE_URL="https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/"
MYSQL_APP_URL="mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC"
```

### **Working Test Queries:**
- ✅ "I want to go dancing tonight" → Returns 2 outfit recommendations
- ✅ "I need party outfits" → Returns 2 outfit recommendations  
- ✅ "Show me something for parties" → Returns outfit suggestions
- ✅ "I want elegant clothes" → Returns styled recommendations

### **API Response Format:**
```json
{
  "session_id": "string",
  "replies": [
    {
      "type": "recommendations", 
      "message": "Natural LLM response with context",
      "outfits": 2
    }
  ],
  "outfits": [
    {
      "title": "Casual And Comfortable Coordinated Set",
      "items": [
        {
          "sku": "0888940046012",
          "title": "RIBBED TANK TOP",
          "price": 790.0,
          "image_url": "https://d29c1z66frfv6c.cloudfront.net/.../image.jpg",
          "color": "black",
          "category": "activewear",
          "relevance_score": 27.0
        }
      ],
      "total_price": 3380.0,
      "rationale": "Style explanation and reasoning",
      "score": 0.85,
      "outfit_type": "coordinated_set"
    }
  ]
}
```

---

**Last Updated:** September 2025
**Interface Status:** ✅ **FULLY OPERATIONAL** - Complete chat system with AI recommendations
**AI Backend:** ✅ **INTEGRATED AND WORKING** - LLM recommendation engine fully operational
**Design System:** ✅ Tailwind CSS architecture with custom enhancements
**Responsive Coverage:** ✅ Mobile, tablet, desktop, and 4K display support
**Performance:** ✅ Optimized for speed and accessibility
**Navigation:** ✅ Beautiful landing page with easy access to all interfaces
**Product Integration:** ✅ Real COS Thailand products with CloudFront image delivery
**Connection Status:** ✅ Real-time backend connectivity monitoring
**Current Phase:** ✅ **PRODUCTION READY** - Full stack fashion recommendation system operational

## 🔒 OPERATIONS, QA, AND ROLLOUT

    Environments and routing
        Canonical admin root: /admin for all backend pages. /dashboard may redirect to /admin.
        Shared layout: app/admin/layout.tsx provides the left rail + secondary panel + header for every /admin/** page.
    Navigation IA (wired)
        Rail icons (top→bottom): Dashboard → Data/CRUD → Chat Suite → Agents/Rules → Settings/Admin.
        Secondary subnav lists context links; active states derive from pathname; aria-current="page" on active link.
    CRUD and data integrity
        Keep existing handlers and API routes; only visual/class changes on pages.
        Primary CRUD routes: /admin/items, /admin/outfit-items, /admin/outfits, /admin/products, /admin/chat-logs, /admin/chat-sessions, /admin/chat-strategies, /admin/rules, /admin/users.
        Product Vision Attributes are managed via the Products page modal; no standalone CRUD required.
    Priority pages and acceptance criteria
        Chat History (/admin/chat-history): must mirror docs/demo.html exactly (chat list, thread, composer, sticky toolbars, avatars/badges).
        System Status, Settings, Users: adopt common shell, consistent tables, filters, empty/loading states.
    Test checklist (manual, low-tech)
        Layout parity vs demo at 1440px and 768px; no horizontal scroll.
        Sidebar rail visible on all /admin routes; correct group and link highlighting on refresh and navigation.
        Keyboard: Tab order, focus-visible rings, Enter to submit, Esc to close modals.
        Tables: Row height, hover, sticky header, pagination and CRUD actions still work.
    Performance and stability
        Tailwind-first: remove ad-hoc CSS when equivalent utilities exist; allow arbitrary values only if demo requires.
        Image policy: prefer WebP; avatars via ui-avatars.com acceptable for demo.
        Avoid heavy JS; throttled scroll handlers only where needed; no third-party UI libs beyond Shadcn/Radix.
    Security and access
        Admin auth check in app/admin/layout.tsx using lib/auth; block unauthenticated access.
        Sanitize user-rendered content in chat bubbles; no HTML injection.
    Delivery artifacts
        Unified git-style diffs per modified file, plus a brief rationale per change.
        Per-page verification sheet: sidebar/header, gutters, grids, buttons/inputs, tables, tabs, empty/loading, dark mode.
    Next steps after visual unification
        Wire chat to backend (WebSocket or SSE); debounce search; persist composer draft per session.
        Product preview modal on Products page; inline edit for key attributes; tie to vision attributes.
        Lightweight telemetry: console.time marks for initial render; Core Web Vitals check in Chromium/Firefox.

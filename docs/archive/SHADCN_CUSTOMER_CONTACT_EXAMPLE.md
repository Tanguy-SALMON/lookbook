# Customer Contact Buttons - Conditional Display Example

## 🎯 **How It Works**

The customer contact buttons (Phone, Video, Search, Settings) only appear when viewing customer-related pages. This keeps the interface clean and contextual.

## 📍 **Pages Where Buttons Appear**

### ✅ **SHOWS Buttons:**
- `/admin/chat-history` - When viewing customer conversations
- `/admin/customers` - When managing customer profiles
- `/admin/chat-sessions` - When monitoring active chat sessions

### ❌ **HIDES Buttons:**
- `/admin` - Dashboard (no customer context)
- `/admin/items` - Product management
- `/admin/users` - Admin user management
- `/admin/settings` - System settings
- `/admin/rules` - Business rules
- All other admin pages

## 🔧 **Implementation Code**

```jsx
{/* Customer Contact Actions - Only show when viewing customer-related pages */}
{(pathname.includes('chat-history') || 
  pathname.includes('customers') || 
  pathname.includes('chat-sessions')) && (
  <div id="customer-contact-actions" className="flex items-center gap-2 bg-gray-100 p-2 rounded-3xl border border-gray-200">
    <button 
      id="contact-phone-btn"
      className="w-9 h-9 border-0 bg-transparent rounded-full flex items-center justify-center cursor-pointer transition-colors duration-200 text-gray-600 text-base hover:bg-gray-200"
      title="Call customer"
      aria-label="Call customer"
    >
      <Phone size={20} strokeWidth={1.5} />
    </button>
    <button 
      id="contact-video-btn"
      className="w-9 h-9 border-0 bg-transparent rounded-full flex items-center justify-center cursor-pointer transition-colors duration-200 text-gray-600 text-base hover:bg-gray-200"
      title="Video call customer"
      aria-label="Video call customer"
    >
      <Video size={20} strokeWidth={1.5} />
    </button>
    <button 
      id="contact-search-btn"
      className="w-9 h-9 border-0 bg-transparent rounded-full flex items-center justify-center cursor-pointer transition-colors duration-200 text-gray-600 text-base hover:bg-gray-200"
      title="Search customer info"
      aria-label="Search customer info"
    >
      <Search size={20} strokeWidth={1.5} />
    </button>
    <button 
      id="contact-settings-btn"
      className="w-9 h-9 border-0 bg-transparent rounded-full flex items-center justify-center cursor-pointer transition-colors duration-200 text-gray-600 text-base hover:bg-gray-200"
      title="Customer settings"
      aria-label="Customer settings"
    >
      <Settings size={20} strokeWidth={1.5} />
    </button>
  </div>
)}
```

## 📱 **Visual Example**

### Page: `/admin/chat-history`
```
Header: [Admin User Avatar] ← → [📞 📹 🔍 ⚙️] Contact Actions
```

### Page: `/admin/items`
```
Header: [Admin User Avatar] ← → (no contact buttons)
```

## 🧪 **Testing Logic**

```javascript
// Test in browser console:
const pathname = window.location.pathname;
const shouldShow = pathname.includes('chat-history') || 
                   pathname.includes('customers') || 
                   pathname.includes('chat-sessions');

console.log('Current path:', pathname);
console.log('Should show contact buttons:', shouldShow);
```

## 🎨 **Button Details**

Each button has:
- **Unique ID**: Easy to target with CSS/JS
- **Tooltip**: `title` attribute for hover help
- **Accessibility**: `aria-label` for screen readers
- **Hover Effect**: `hover:bg-gray-200` for interaction feedback
- **Consistent Size**: `w-9 h-9` for uniform appearance

## 📋 **Button Functions**

| Button | Icon | Function | Use Case |
|--------|------|----------|----------|
| Phone | 📞 | Call customer | Voice support calls |
| Video | 📹 | Video call | Face-to-face support |
| Search | 🔍 | Search info | Find customer details |
| Settings | ⚙️ | Customer settings | Manage customer preferences |

## 🚀 **Benefits**

1. **Clean Interface**: No unnecessary buttons on non-customer pages
2. **Contextual Tools**: Relevant actions when needed
3. **Improved UX**: Users see tools only when applicable
4. **Professional Look**: Organized, purposeful interface
5. **Easy Maintenance**: Single conditional logic controls display

This creates a smart, context-aware interface that adapts to what the user is doing!
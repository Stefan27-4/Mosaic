# Data Donation Feature - UI Preview

## Settings Tab UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings Tab                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Settings                                                       │
│  ═════════                                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🔬 Contribute to Science                               │   │
│  │                                                         │   │
│  │  Help improve AI research by donating your anonymized  │   │
│  │  training logs. Your data will be securely uploaded to │   │
│  │  our research database and used to advance language    │   │
│  │  model technology. All personal information is removed │   │
│  │  before upload.                                         │   │
│  │                                                         │   │
│  │  ┌──────────────┐  Status messages appear here...      │   │
│  │  │ Donate Data  │  ✅ Success: Uploaded 5 files        │   │
│  │  └──────────────┘  or                                   │   │
│  │                    ❌ Error: No files found             │   │
│  │                    or                                   │   │
│  │                    ⏳ Preparing upload...               │   │
│  │                                                         │   │
│  │  📁 Files Location: /home/user/.mosaic/data/trajectories│  │
│  │  📦 File Format: .jsonl.gz (compressed JSON)           │   │
│  │  🔒 Privacy: All personal data is anonymized           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Color Scheme (Lovable Software Theme)

- **Background:** Deep Midnight Blue (#0F172A)
- **Cards:** Dark Slate (#1E293B)
- **Accent/Button:** Vivid Purple (#8B5CF6)
- **Text:** Off-white (#F8FAFC)
- **Success:** Green (#10B981)
- **Error:** Red (#EF4444)
- **Warning:** Amber (#F59E0B)

## Button States

### Normal State
- Text: "Donate Data"
- Color: Purple (#8B5CF6)
- Enabled: Yes

### Uploading State
- Text: "Uploading..."
- Color: Purple (#8B5CF6)
- Enabled: No (disabled)

### After Success
- Text: "Donate Data" (reset)
- Status Label: "✅ Success: Successfully uploaded N file(s)"
- Color: Green

### After Error
- Text: "Donate Data" (reset)
- Status Label: "❌ Error: [error message]"
- Color: Red

## User Flow

1. User clicks Settings tab
2. User reads the description
3. User clicks "Donate Data" button
4. Button changes to "Uploading..." and becomes disabled
5. Status shows "⏳ Preparing upload..."
6. Background thread runs upload process
7. On completion, button re-enables
8. Status shows success (✅) or error (❌) message

## Integration Points

The Settings Tab can be integrated into existing Mosaic applications:

```python
# In main application
from mosaic.gui.settings_tab import SettingsTab

# Add to tab view
settings_tab = SettingsTab(parent_widget)
settings_tab.pack(fill="both", expand=True)
```

See `examples/settings_tab_example.py` for a complete working example.

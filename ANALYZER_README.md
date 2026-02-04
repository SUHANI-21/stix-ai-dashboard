# STIX Intelligence Analyzer

## Version Detection & Validation Page

A dedicated Streamlit page for analyzing STIX bundles with comprehensive version detection, structural validation, and detailed statistics.

---

## 📋 Features

### 1. **STIX Format Identification Module**

- Automatically detects STIX version (1.x, 2.0, 2.1)
- Identifies format (XML or JSON)
- Extracts file metadata (size, object count, bundle status)
- Provides detailed error reporting if detection fails

### 2. **STIX Validation Layer**

- Validates STIX 1.x, 2.0, 2.1 using official schema validators
- Reports structured errors and warnings
- Shows validation summary (pass/fail)
- Lists all validation issues with details

### 3. **Statistics & Analysis**

- Counts total objects in bundle
- Breaks down object types (indicators, malware, identity, campaigns, etc.)
- Shows threat indicator statistics
- Provides object type distribution chart

### 4. **File Preview & Reports**

- Shows first 100 lines of file content
- Syntax-highlighted JSON/XML preview
- Downloadable validation report (TXT format)
- Session-based data management (auto-cleanup)

---

## 🛠 Tech Stack

```
Frontend:
├── Streamlit 1.28+        (Web UI framework)
├── Plotly                 (Charts & visualizations)
└── PyVis                  (Network graphs)

Backend:
├── Python 3.9+
├── stix2                  (STIX 2.x library)
├── stix-python            (STIX 1.x library)
├── stix2-validator        (Validation engine)
├── stix2-elevator         (Conversion utilities)
└── lxml                   (XML processing)

Data:
└── Session-based temp storage (auto-cleanup)
```

---

## 📁 Project Structure

```
stix_intelligence_analyzer/
├── pages/
│   ├── stix_analyzer.py          ← MAIN ANALYZER PAGE (this file)
│   └── ...                        (other pages from dashboard)
│
├── modules/
│   ├── enhanced_detector.py       (Version detection wrapper)
│   ├── enhanced_validator.py      (Validation wrapper)
│   ├── formatter.py               (Result formatting for UI)
│   ├── utils.py                   (File handling & helpers)
│   ├── version_detector.py        (Original simple detector)
│   ├── validator.py               (Original simple validator)
│   └── ...                        (other modules)
│
├── copied_modules/                (Extracted from source_code/)
│   ├── version_checker_ingress.py
│   ├── Oneto2.py
│   ├── twotolatest.py
│   ├── check_family.py
│   └── configuration/
│
├── dashboard.py                   (Main Streamlit app entry)
├── requirements_analyzer.txt      (Dependencies)
└── README.md
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd stix_intelligence_analyzer
pip install -r requirements_analyzer.txt
```

### 2. Run the Streamlit App

```bash
streamlit run dashboard.py
```

### 3. Navigate to STIX Analyzer Page

Once the dashboard loads:

- Go to "STIX Analyzer" page in the sidebar
- Upload your STIX file (JSON or XML)
- Click "Analyze" to start the analysis

---

## 📖 How It Works

### **Analysis Pipeline**

```
Upload File
    ↓
Save to Session Temp Dir
    ↓
Version Detection
├─ Parse JSON → Extract spec_version
├─ Parse XML → Extract version attribute
└─ Return: version, format, object count
    ↓
Structural Validation
├─ Validate against STIX 2.1 schema
├─ Extract errors and warnings
└─ Return: is_valid, error_count, warning_count
    ↓
Statistics Extraction
├─ Count objects by type
├─ Extract threat indicators
└─ Return: object_count, threat_count, breakdown
    ↓
Display Results
├─ Detection cards
├─ Validation summary
├─ Statistics charts
├─ File preview
└─ Download report
    ↓
Session Cleanup
└─ Auto-delete temp files on next session
```

---

## 🔍 Module Details

### **enhanced_detector.py**

Wraps the original `VersionChecker` with additional metadata:

- Returns file size, object count, bundle status
- Handles both JSON (STIX 2.x) and XML (STIX 1.x)
- Provides detailed error messages

**Key Function:**

```python
EnhancedVersionChecker.detect_stix_full(filepath) → dict
```

### **enhanced_validator.py**

Comprehensive validation using stix2validator:

- Validates against STIX 2.1 schema
- Extracts and formats errors/warnings
- Extracts detailed statistics

**Key Functions:**

```python
EnhancedValidator.validate_stix_detailed(filepath) → dict
EnhancedValidator.extract_statistics(filepath) → dict
```

### **formatter.py**

Formats results for Streamlit UI display:

- Detection card formatting
- Validation summary formatting
- Statistics table formatting
- File preview extraction

**Key Functions:**

```python
ResultFormatter.format_detection_card(result)
ResultFormatter.format_validation_summary(result)
ResultFormatter.get_file_preview(filepath, lines=100)
```

### **utils.py**

Utility functions for file and error handling:

- Session-based file management
- JSON parsing helpers
- Error formatting
- Conversion path management

**Key Classes:**

```python
FileManager          # Handle temp file storage & cleanup
JsonHelper           # JSON parsing utilities
ErrorHandler         # Error message formatting
ConversionHelper     # Conversion path management
```

---

## 💾 Data Management

### Session-Based Storage

- Files uploaded are saved to a temporary directory
- All processing happens on temp files
- **No persistent storage** - files are cleared when:
  - Page is refreshed
  - Session expires
  - User clears the upload

### File Locations

- Temp directory: `%TEMP%/stix_analyzer_<random>/`
- Each session gets its own isolated directory
- Auto-cleanup on page reset

---

## 📊 Output Examples

### Detection Results

```
Version: STIX 1.2
Format: XML
Is Bundle: Yes
Object Count: 15
File Size (KB): 125.43
```

### Validation Results

```
Status: ✅ VALID
Errors: 0
Warnings: 0
```

### Statistics

```
Total Objects: 15
Threat Indicators: 8
Malware Objects: 3
Identity Objects: 2
Campaign Objects: 1
Attack Pattern Objects: 1
Tool Objects: 0
Vulnerability Objects: 0
```

### Downloadable Report

A text file containing:

- File metadata
- Version detection results
- Validation status and issues
- Complete statistics
- Analysis conclusion

---

## 🔒 Security & Privacy

✅ **Session-Based Analysis**

- No cloud uploads
- Local processing only
- Auto-cleanup after session

✅ **No Data Persistence**

- Temp files deleted on refresh
- No database logging
- No audit trail across sessions

---

## 🐛 Troubleshooting

### Issue: "Unsupported or invalid STIX input"

**Solution:** Ensure your file is:

- Valid JSON (STIX 2.0/2.1) or XML (STIX 1.x)
- Contains proper STIX structure
- Encoded in UTF-8

### Issue: Validation fails but file looks valid

**Solution:**

- Check for custom objects (we allow them)
- Verify schema compliance
- Check warning details for hints

### Issue: File preview is empty

**Solution:**

- File might be too large (showing first 100 lines only)
- Try downloading the report instead

---

## 📝 Example Files

Test with STIX files from:

- `stix_test_data/` directory (original STIX samples)
- Your own STIX bundles

---

## 🔄 Future Enhancements

- [ ] STIX 1.x → 2.1 conversion preview
- [ ] Custom validation rules
- [ ] Multi-file batch processing
- [ ] Advanced threat analysis
- [ ] Data persistence (optional)

---

## 👥 Team

- **Original Dashboard:** Neha Agarwal (stix-ai-dashboard)
- **STIX Analyzer Page:** Enhanced version detection & validation module

---

## 📄 License

Same as parent stix-ai-dashboard project

---

## 📞 Support

For issues or questions:

1. Check error messages in the app
2. Review the detailed validation report
3. Verify file format and content
4. Check console logs for detailed errors

---

**Happy STIX Analyzing! 🚀**

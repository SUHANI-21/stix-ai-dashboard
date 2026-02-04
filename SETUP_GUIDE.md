# 🚀 STIX Intelligence Analyzer - Setup & Getting Started Guide

## ✅ Project Successfully Created!

Your STIX Intelligence Analyzer has been integrated into your teammate's Streamlit dashboard. Here's what's been set up:

---

## 📁 What Was Created

### **New Files & Modules**

```
stix_intelligence_analyzer/
├── pages/
│   └── stix_analyzer.py              ← NEW: Main analyzer page (12KB)
│
├── modules/
│   ├── enhanced_detector.py           ← NEW: Enhanced version detection
│   ├── enhanced_validator.py          ← NEW: Enhanced validation with errors
│   ├── formatter.py                   ← NEW: Result formatting for UI
│   ├── utils.py                       ← NEW: File handling & utilities
│   └── [existing modules...]
│
├── copied_modules/                    ← NEW: Copies from source_code/
│   ├── version_checker_ingress.py
│   ├── Oneto2.py
│   ├── twotolatest.py
│   ├── check_family.py
│   └── configuration/
│
├── requirements_analyzer.txt          ← NEW: Dependencies
├── ANALYZER_README.md                 ← NEW: Detailed documentation
└── SETUP_GUIDE.md                     ← This file
```

---

## 🛠 Installation Steps

### **Step 1: Install Dependencies**

```bash
cd stix_intelligence_analyzer
pip install -r requirements_analyzer.txt
```

**What gets installed:**

- Streamlit 1.28+ (UI framework)
- stix2 & stix-python (STIX libraries)
- stix2-validator (Validation engine)
- stix2-elevator (Conversion utilities)
- lxml (XML processing)
- plotly, pyvis (Visualizations)

### **Step 2: Verify Installation**

```bash
# Check Streamlit installation
streamlit --version

# Check Python packages
pip list | grep stix

# Test imports (optional)
python -c "from stix2 import parse; print('✅ STIX2 OK')"
python -c "from stix2validator import validate_string; print('✅ Validator OK')"
```

### **Step 3: Run the Application**

```bash
# From the stix_intelligence_analyzer directory
streamlit run dashboard.py
```

**Expected output:**

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### **Step 4: Navigate to STIX Analyzer**

1. Open `http://localhost:8501` in your browser
2. You should see the Streamlit dashboard
3. Look for "STIX Analyzer" in the sidebar or pages menu
4. Click to open the STIX Version Detection & Validation page

---

## 🎯 Using the STIX Analyzer

### **Basic Workflow**

```
1. Upload STIX File
   └─ Click file uploader in left sidebar
   └─ Select JSON (STIX 2.0/2.1) or XML (STIX 1.x) file

2. Analyze
   └─ Click "Analyze" button
   └─ Wait for processing...

3. Review Results
   ├─ Version Detection: See what STIX version was detected
   ├─ Validation: Check if structure is valid
   ├─ Statistics: See object counts and types
   ├─ File Preview: View first 100 lines
   └─ Download Report: Save analysis as TXT

4. Clear & Try Again
   └─ Click "Clear" button to reset
```

### **What You'll See**

**Version Detection Results:**

- STIX Version (1.x, 2.0, 2.1)
- Format (XML or JSON)
- Is Bundle? (Yes/No)
- Object Count
- File Size

**Validation Results:**

- Overall Status (✅ Valid / ❌ Invalid)
- Error Count & Details
- Warning Count & Details

**Statistics:**

- Total Objects
- Threat Indicators
- Malware Objects
- Identity Objects
- Campaign Objects
- Attack Patterns
- Tools
- Vulnerabilities
- Visual chart of object distribution

**File Preview:**

- First 100 lines of your STIX file
- Syntax-highlighted (JSON/XML)
- Readable formatting

**Downloadable Report:**

- Complete analysis in TXT format
- Can be imported into Excel/docs

---

## 🧪 Testing with Sample Files

### **Option 1: Use Sample STIX Files from Your Project**

```bash
# Navigate to test data
cd ../stix_test_data/

# You'll find files like:
# - Mandiant_APT1_Report.xml              (STIX 1.x)
# - Appendix_G_IOCs_Full.xml              (STIX 1.x)
# - various JSON files                    (STIX 2.x)
```

### **Option 2: Create a Simple Test File**

**Simple STIX 2.1 JSON (save as `test.json`):**

```json
{
  "type": "bundle",
  "id": "bundle--12345678-1234-1234-1234-123456789012",
  "objects": [
    {
      "type": "indicator",
      "id": "indicator--12345678-1234-1234-1234-123456789012",
      "created": "2023-01-01T00:00:00.000Z",
      "modified": "2023-01-01T00:00:00.000Z",
      "pattern": "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
      "labels": ["malicious-activity"],
      "valid_from": "2023-01-01T00:00:00.000Z"
    }
  ]
}
```

Then upload this to the analyzer!

---

## 📊 Features Overview

### **1. Version Detection**

✅ Automatically identifies STIX version and format
✅ Works with STIX 1.0, 1.0.1, 1.1, 1.1.1, 1.2, 2.0, 2.1
✅ Provides detailed metadata (file size, object count)

### **2. Structural Validation**

✅ Validates against STIX 2.1 schema
✅ Reports errors and warnings
✅ Supports custom objects
✅ Detailed error messages

### **3. Statistics & Analysis**

✅ Object count by type
✅ Threat indicator metrics
✅ Visual distribution chart
✅ Malware, campaign, attack pattern counts

### **4. File Preview**

✅ First 100 lines displayed
✅ Syntax-highlighted (JSON/XML)
✅ Full file content preserved

### **5. Report Generation**

✅ Downloadable TXT report
✅ Complete analysis summary
✅ All statistics included

---

## 🔧 How It Works Under the Hood

### **Module Architecture**

```
stix_analyzer.py (Main Page)
    ├── FileManager (utils.py)
    │   └── Handle file uploads to temp directory
    │
    ├── EnhancedVersionChecker (enhanced_detector.py)
    │   └── detect_stix_full() → version, format, size, object_count
    │
    ├── EnhancedValidator (enhanced_validator.py)
    │   ├── validate_stix_detailed() → errors, warnings
    │   └── extract_statistics() → object counts, types
    │
    ├── ResultFormatter (formatter.py)
    │   ├── format_detection_card()
    │   ├── format_validation_summary()
    │   ├── get_file_preview()
    │   └── get_statistics_table()
    │
    └── Session State Management
        └── Streamlit session_state for temp storage
```

### **Data Flow**

```
User Uploads File
    ↓
FileManager.save_uploaded_file()
    ↓ (file goes to temp directory)
    ↓
EnhancedVersionChecker.detect_stix_full()
    ↓ (Returns: version, format, metadata)
    ↓
EnhancedValidator.validate_stix_detailed()
    ↓ (Returns: is_valid, errors, warnings)
    ↓
EnhancedValidator.extract_statistics()
    ↓ (Returns: object counts, types)
    ↓
ResultFormatter.format_*()
    ↓ (Prepare for UI display)
    ↓
Display in Streamlit UI
    ↓
User can download report
    ↓
Session ends → FileManager.cleanup_session()
    ↓ (Auto-delete temp files)
```

---

## 📝 Configuration & Customization

### **Modify File Preview Lines**

In `stix_analyzer.py`, find this section:

```python
preview_content, preview_type = ResultFormatter.get_file_preview(
    st.session_state.file_path,
    lines=100  # ← Change this number
)
```

Change `100` to any number you prefer.

### **Change Statistics Displayed**

Edit `enhanced_validator.py` `extract_statistics()` method to add/remove object type counters.

### **Customize UI Theme**

Modify the CSS in the `<style>` section of `stix_analyzer.py`.

---

## 🐛 Troubleshooting

### **Issue: "ModuleNotFoundError: No module named 'stix2'"**

```bash
# Solution: Install missing packages
pip install stix2 stix2-validator stix-python stix2-elevator
```

### **Issue: File upload fails**

**Check:**

- File is valid JSON or XML
- File is UTF-8 encoded
- File size is reasonable (< 10MB)

### **Issue: Validation fails but file looks correct**

**Possible reasons:**

- STIX version mismatch
- Missing mandatory fields
- Invalid relationship references
- Custom objects that need `allow_custom=True` (we support this)

### **Issue: "Page not found" or no analyzer page**

**Solution:**

1. Ensure `pages/stix_analyzer.py` exists
2. Restart Streamlit: `Ctrl+C` and run `streamlit run dashboard.py` again
3. Refresh browser

### **Issue: Temp files not being deleted**

**Manual cleanup:**

```bash
# Windows
rmdir /S %TEMP%\stix_analyzer_*

# Linux/Mac
rm -rf /tmp/stix_analyzer_*
```

---

## 📚 Documentation Files

| File                            | Purpose                        |
| ------------------------------- | ------------------------------ |
| `ANALYZER_README.md`            | Detailed feature documentation |
| `SETUP_GUIDE.md`                | This file - Quick start guide  |
| `pages/stix_analyzer.py`        | Main analyzer page code        |
| `modules/enhanced_detector.py`  | Version detection code         |
| `modules/enhanced_validator.py` | Validation code                |
| `modules/formatter.py`          | UI formatting code             |
| `modules/utils.py`              | Utility functions              |

---

## 🎓 Learning Resources

### **About STIX:**

- [OASIS STIX Official Docs](https://oasis-open.github.io/cti-documentation/)
- [STIX 2.1 Specification](https://docs.oasis-open.org/cti/stix/v2.1/cti-stix-v2.1.html)
- [STIX 1.x Reference](https://stixproject.github.io/releases/1.2/STIX_Language_v1.2.pdf)

### **About Streamlit:**

- [Streamlit Docs](https://docs.streamlit.io/)
- [Streamlit Components](https://docs.streamlit.io/library/components)

### **Related Libraries:**

- [stix2 Python Library](https://github.com/oasis-open/cti-python-stix2)
- [stix2-validator](https://github.com/oasis-open/cti-stix-validator)
- [stix2-elevator](https://github.com/oasis-open/cti-stix-elevator)

---

## 📞 Next Steps

### **If Everything Works:**

✅ Great! Your STIX analyzer is ready to use!
✅ Try uploading different STIX files
✅ Explore the validation features
✅ Check out the reports

### **If You Want to Extend:**

- Add conversion preview (STIX 1.x → 2.1)
- Add threat classification (ML model)
- Add credibility assessment
- Add batch processing
- Add database persistence

---

## 🎉 Summary

You now have a **fully functional STIX Intelligence Analysis Tool** that:

✅ Detects STIX versions (1.x, 2.0, 2.1)
✅ Validates structural integrity
✅ Extracts comprehensive statistics
✅ Shows file previews
✅ Generates downloadable reports
✅ Manages session-based data
✅ Integrated with your team's dashboard

**Ready to analyze some STIX files? Let's go! 🚀**

---

**Last Updated:** February 4, 2026
**Version:** 1.0

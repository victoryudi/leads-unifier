<div align="center">
  
# 🔄 Leads Unifier

[![Python Version](https://img.shields.io/badge/python-3.6+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![MIT License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](http://makeapullrequest.com)

**Seamlessly unify your contact lists, eliminate duplicates, and maintain data clarity.**

[Key Features](#-key-features) •
[Quick Start](#-quick-start) •
[Usage](#-usage) •
[Contribute](#-contributing)

---

</div>

## 🎯 Overview

Tired of managing multiple contact lists? **Leads Unifier** is your solution for consolidating numerous CSV contact lists into a single, clean, and organized dataset. Perfect for sales teams, marketers, and anyone dealing with multiple lead sources.

## ✨ Key Features

- **Smart Duplicate Detection** - Intelligently identifies and merges duplicate contacts
- **Automatic Column Recognition** - Finds name, email, and phone fields regardless of column naming
- **Data Preservation** - Keeps the most complete information when merging duplicates
- **Real-time Progress** - Beautiful progress tracking and logging
- **Data Normalization** - Standardizes emails and phone numbers automatically

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/victoryudi/leads-unifier.git

# Navigate to the project
cd leads-unifier

# Install dependencies
pip install -r requirements.txt

# Run the unifier
python leads_unifier.py
```

## 📋 Requirements

Your CSV files should contain at least these columns (naming can vary):
- **Name** (e.g., 'name', 'full name', 'contact')
- **Email** (e.g., 'email', 'e-mail', 'mail')
- **Phone** (e.g., 'phone', 'telephone', 'mobile')

## 🚀 Usage

1. **Place Your Files**
   ```
   leads-unifier/
   ├── input/
   │   ├── leads_list1.csv
   │   ├── leads_list2.csv
   │   └── more_leads.csv
   ```

2. **Run the Script**
   ```bash
   python leads_unifier.py
   ```

3. **Get Your Results**
   ```
   leads-unifier/
   ├── output/
   │   └── combined_leads.csv
   ├── logs/
   │   └── processing_20240223_143022.log
   ```

## 📊 What You Get

```
▶ Processing leads_list1.csv
  ✓ Found: name, email, phone
  ✓ Extracted 1,500 contacts

▶ Processing leads_list2.csv
  ✓ Found: email, phone, full_name
  ✓ Extracted 2,300 contacts

✨ Complete! 
  • Files Processed: 2
  • Total Contacts: 3,800
  • Duplicates Removed: 450
  • Final Unique Leads: 3,350
```

## 💡 Perfect For

- **Sales Teams** - Combine leads from multiple campaigns
- **Marketing Teams** - Merge contact lists from different events
- **Recruiters** - Consolidate candidate lists
- **Event Organizers** - Unify attendee lists from multiple sources

## 🛠 Configuration

```python
# config.py
INPUT_DIR = "input/*.csv"
OUTPUT_FILE = "output/combined_leads.csv"
LOG_DIR = "logs"
```

## 🤝 Contributing

We love your input! We want to make contributing to Leads Unifier as easy and transparent as possible.

You can help by:
- 🐛 Reporting bugs
- 📝 Improving documentation
- 🔍 Reviewing pull requests
- ✨ Adding new features

## 🔮 Roadmap

- [ ] Web interface for drag-and-drop processing
- [ ] Custom column mapping interface
- [ ] Advanced duplicate detection algorithms
- [ ] Export to multiple formats (XLSX, JSON)
- [ ] API integration capabilities

## 📜 License

[MIT License](LICENSE) - feel free to use this project commercially, modify it, or share it with others.

## 💌 Contact & Support

Found a bug? Have a feature request? We'd love to hear from you!

- 🐛 [Submit an issue](https://github.com/victoryudi/leads-unifier/issues)
- 🌟 Star the repo if you find it useful!
- 🔄 Fork it and submit your PRs

---

<div align="center">

Made with ❤️ by Yudi

</div>
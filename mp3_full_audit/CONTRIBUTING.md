# Contributing to **mp3_full_audit**

Thank you for your interest in contributing!  
This project is a Bash‑based audit tool designed primarily for **Playnite** users and **UniPlaySong** users who maintain large MP3 libraries. Contributions are welcome, whether they involve bug fixes, feature ideas, documentation improvements, or Playnite‑related enhancements.

---

## **🧭 Project Scope**

This tool focuses on:

- Auditing MP3 files stored in Playnite‑style game‑ID folders  
- Extracting metadata (duration, bitrate, ID3 tags)  
- Cross‑referencing Playnite’s exported CSV  
- Producing clean, spreadsheet‑friendly CSV reports  
- Identifying mismatches, missing metadata, or misfiled tracks  

Future versions may include:

- Missing‑music reports  
- Coverage analysis  
- Optional UniPlaySong integration  
- Potential Playnite extension groundwork  

---

## **📁 Repository Structure**

``` dir
/mp3_full_audit-vX.Y.Z.sh   # Versioned releases
/README.md                  # Overview & usage
/RELEASES.md                # User-facing release notes
/CHANGELOG.md               # Developer-facing history
/CONTRIBUTING.md            # This file
/LICENSE.md                 # MIT License
```

---

## **🛠 How to Contribute**

### **1. Fork the repository**

Click **Fork** in the top-right corner of the GitHub page.

### **2. Create a feature branch**

``` bash
git checkout -b feature/my-improvement
```

### **3. Make your changes**

Please keep changes focused and well‑commented.

### **4. Test your changes**

Ensure the script runs correctly on:

- Git Bash (Windows)  
- Linux or macOS (optional but appreciated)  

### **5. Commit your work**

Use clear commit messages:

``` bash
git commit -m "Add AWK loader for Playnite CSV"
```

### **6. Submit a Pull Request**

Explain:

- What you changed  
- Why you changed it  
- Any testing you performed  

---

## **🧪 Coding Guidelines**

- Keep the script POSIX‑friendly where possible  
- Avoid process substitution (`< <(...)`) for Git Bash compatibility  
- Use AWK for heavy parsing  
- Escape all CSV fields  
- Maintain readability and clarity  
- Prefer small, modular helper functions  

---

## **📦 Versioning**

This project uses **Semantic Versioning**:

- **MAJOR** — breaking changes  
- **MINOR** — new features  
- **PATCH** — fixes and refinements  

---

## **📜 License**

This project is licensed under the **MIT License**, which allows:

- Personal use  
- Commercial use  
- Modification  
- Distribution  

See `LICENSE.md` for details.

---

## **💬 Questions or Ideas?**

Feel free to open:

- **Issues** for bugs or feature requests  
- **Discussions** for brainstorming  
- **Pull Requests** for contributions  

Your input is welcome — especially if you’re a Playnite or UniPlaySong user.

---

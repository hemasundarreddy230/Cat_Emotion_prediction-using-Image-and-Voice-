# 🚀 How to Run CatCare AI Project

## ✅ **Server is Currently Running!**
**Access the project at:** http://127.0.0.1:8000/

---

## 📋 **Prerequisites**

Before running the project, ensure you have:

1. **Python 3.8+** installed
   - Check: `python --version`
   
2. **pip** (Python package manager)
   - Check: `pip --version`

3. **Virtual Environment** (recommended)
   - Already set up in `venv/` folder

---

## 🎯 **Quick Start (First Time Setup)**

### **Step 1: Navigate to Project Directory**
```bash
cd "D:\INTERNSHIP PROJECT\backend"
```

### **Step 2: Activate Virtual Environment**

**On Windows (CMD):**
```cmd
venv\Scripts\activate
```

**On Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**On Linux/Mac:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### **Step 3: Install Dependencies** (First time only)
```bash
pip install -r requirements.txt
```

### **Step 4: Run Database Migrations** (First time only)
```bash
python manage.py migrate
```

### **Step 5: Create Superuser** (Optional - for admin access)
```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin account.

### **Step 6: Collect Static Files** (First time only)
```bash
python manage.py collectstatic --noinput
```

### **Step 7: Run the Development Server**
```bash
python manage.py runserver
```

### **Step 8: Open in Browser**
Navigate to: **http://127.0.0.1:8000/**

---

## 🔄 **Daily Usage (After First Setup)**

### **1. Activate Virtual Environment**
```bash
# Windows CMD
venv\Scripts\activate

# Windows PowerShell
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### **2. Run Server**
```bash
python manage.py runserver
```

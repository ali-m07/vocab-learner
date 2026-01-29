FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# کپی requirements و نصب
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی فایل‌های پروژه
COPY vocab_learner.py .
COPY daily_review.py .
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# ایجاد دایرکتوری برای داده‌ها
RUN mkdir -p /app/data /app/uploads

# پورت
EXPOSE 5000

# اجرای اپلیکیشن
CMD ["python", "app.py"]

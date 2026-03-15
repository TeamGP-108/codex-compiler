FROM wasmer/nginx-python:latest

# কপি প্রজেক্ট ফাইল
COPY . /app

# ওয়ার্কিং ডিরেক্টরি সেট
WORKDIR /app

# ডিপেন্ডেন্সি ইনস্টল
RUN pip install --no-cache-dir -r requirements.txt

# টেম্প ডিরেক্টরি তৈরি
RUN mkdir -p /app/temp

# পোর্ট এক্সপোজ
EXPOSE 8000

# অ্যাপ রান
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

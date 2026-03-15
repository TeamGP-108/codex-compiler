from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import time
from typing import Dict, Optional
import asyncio
from datetime import datetime

from .models import CodeSubmission, SubmissionResponse, ExecutionResult, Language
from .executor import executor

app = FastAPI(
    title="বাংলা জাজ - কোড কম্পাইলার",
    description="একটি সম্পূর্ণ বাংলা ভাষায় তৈরি অনলাইন জাজ সিস্টেম",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS মিডলওয়্যার
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# স্ট্যাটিক ফাইল
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ইন-মেমরি স্টোরেজ
submissions: Dict[str, dict] = {}

# এপিআই রুট
@app.get("/", response_class=HTMLResponse)
async def root():
    """হোম পেজ"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>বাংলা জাজ - অনলাইন কোড কম্পাইলার</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 800px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 20px;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature-card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
            .feature-icon {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .feature-title {
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
            .feature-desc {
                color: #666;
                font-size: 0.9em;
            }
            .api-links {
                background: #f0f0f0;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .api-links h3 {
                color: #333;
                margin-bottom: 15px;
            }
            .api-links ul {
                list-style: none;
            }
            .api-links li {
                margin: 10px 0;
            }
            .api-links a {
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }
            .api-links a:hover {
                text-decoration: underline;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 1.1em;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px 5px;
                transition: opacity 0.3s;
            }
            .btn:hover {
                opacity: 0.9;
            }
            .footer {
                margin-top: 30px;
                text-align: center;
                color: #888;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🇧🇩 বাংলা জাজ</h1>
            <div class="subtitle">
                একটি সম্পূর্ণ বাংলা ভাষায় তৈরি অনলাইন জাজ সিস্টেম
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">দ্রুত এক্সিকিউশন</div>
                    <div class="feature-desc">৫ সেকেন্ডের মধ্যে ফলাফল</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-title">নিরাপদ স্যান্ডবক্স</div>
                    <div class="feature-desc">অবিশ্বস্ত কোড নিরাপদে চালান</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🌐</div>
                    <div class="feature-title">১২+ ভাষা</div>
                    <div class="feature-desc">পাইথন, জাভা, সি++ সহ আরও অনেক</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📝</div>
                    <div class="feature-title">REST API</div>
                    <div class="feature-desc">সহজ JSON API ইন্টিগ্রেশন</div>
                </div>
            </div>
            
            <div class="api-links">
                <h3>📚 API ডকুমেন্টেশন</h3>
                <ul>
                    <li><a href="/docs" target="_blank">Swagger UI ডক্স</a> - ইন্টারেক্টিভ এপিআই টেস্টিং</li>
                    <li><a href="/redoc" target="_blank">ReDoc ডক্স</a> - বিস্তারিত ডকুমেন্টেশন</li>
                    <li><a href="/languages" target="_blank">/languages</a> - সাপোর্টেড ভাষার তালিকা</li>
                    <li><a href="/stats" target="_blank">/stats</a> - সিস্টেম স্ট্যাটাস</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <a href="/docs" class="btn">🚀 API টেস্ট করুন</a>
                <a href="/redoc" class="btn">📖 ডক্স দেখুন</a>
            </div>
            
            <div class="footer">
                Wasmer Edge-এ হোস্ট করা | মুক্ত সোর্স কোড কম্পাইলার
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/languages")
async def get_languages():
    """সাপোর্টেড ল্যাঙ্গুয়েজের তালিকা"""
    versions = await executor.get_language_versions()
    return {
        "languages": [
            {
                "name": lang.value,
                "version": versions.get(lang.value, "Unknown"),
                "compiled": lang.value in ["cpp", "c", "java", "typescript"]
            }
            for lang in Language
        ],
        "total": len(Language)
    }

@app.get("/stats")
async def get_stats():
    """সিস্টেম স্ট্যাটাস"""
    return {
        "total_submissions": len(submissions),
        "active_submissions": len([s for s in submissions.values() if s["status"] == "processing"]),
        "supported_languages": len(Language),
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/execute", response_model=SubmissionResponse)
async def execute_code(submission: CodeSubmission):
    """সিঙ্ক্রোনাস কোড এক্সিকিউশন"""
    
    submission_id = str(uuid.uuid4())
    
    try:
        # কোড এক্সিকিউট
        result = await executor.execute(submission)
        
        # স্টোর
        submissions[submission_id] = {
            "status": "completed",
            "result": result.dict(),
            "language": submission.language.value,
            "timestamp": datetime.now().isoformat()
        }
        
        return SubmissionResponse(
            id=submission_id,
            status="completed",
            result=result
        )
        
    except Exception as e:
        error_result = ExecutionResult(
            error=str(e),
            status="error",
            status_code=-1
        )
        
        submissions[submission_id] = {
            "status": "error",
            "result": error_result.dict(),
            "error": str(e)
        }
        
        return SubmissionResponse(
            id=submission_id,
            status="error",
            result=error_result
        )

@app.post("/submit", response_model=SubmissionResponse)
async def submit_code(submission: CodeSubmission, background_tasks: BackgroundTasks):
    """অ্যাসিঙ্ক্রোনাস কোড সাবমিশন"""
    
    submission_id = str(uuid.uuid4())
    
    # স্টোরেজে সংরক্ষণ
    submissions[submission_id] = {
        "status": "queued",
        "submission": submission.dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    # ব্যাকগ্রাউন্ড টাস্ক
    background_tasks.add_task(process_submission_background, submission_id, submission.dict())
    
    return SubmissionResponse(
        id=submission_id,
        status="queued"
    )

@app.get("/submission/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: str):
    """সাবমিশনের স্ট্যাটাস দেখা"""
    
    if submission_id not in submissions:
        raise HTTPException(status_code=404, detail="সাবমিশন পাওয়া যায়নি")
    
    sub = submissions[submission_id]
    
    return SubmissionResponse(
        id=submission_id,
        status=sub["status"],
        result=ExecutionResult(**sub["result"]) if "result" in sub else None
    )

async def process_submission_background(submission_id: str, submission_data: dict):
    """ব্যাকগ্রাউন্ডে সাবমিশন প্রসেস করা"""
    
    try:
        # স্ট্যাটাস আপডেট
        submissions[submission_id]["status"] = "processing"
        
        # সাবমিশন অবজেক্ট তৈরি
        submission = CodeSubmission(**submission_data)
        
        # কোড এক্সিকিউট
        result = await executor.execute(submission)
        
        # স্ট্যাটাস আপডেট
        submissions[submission_id].update({
            "status": "completed",
            "result": result.dict()
        })
        
    except Exception as e:
        submissions[submission_id].update({
            "status": "error",
            "error": str(e)
        })

@app.delete("/submission/{submission_id}")
async def delete_submission(submission_id: str):
    """সাবমিশন ডিলিট করা"""
    if submission_id in submissions:
        del submissions[submission_id]
        return {"message": "সাবমিশন ডিলিট করা হয়েছে"}
    raise HTTPException(status_code=404, detail="সাবমিশন পাওয়া যায়নি")

@app.get("/health")
async def health_check():
    """হেলথ চেক এন্ডপয়েন্ট"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("WASMER_ENV", "production")
    }

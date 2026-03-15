from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class Language(str, Enum):
    """সাপোর্টেড প্রোগ্রামিং ল্যাঙ্গুয়েজ"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    BASH = "bash"
    POWERSHELL = "powershell"
    R = "r"
    PERL = "perl"
    LUA = "lua"

class CodeSubmission(BaseModel):
    """কোড সাবমিশনের জন্য মডেল"""
    code: str = Field(..., description="সোর্স কোড", min_length=1, max_length=10000)
    language: Language = Field(..., description="প্রোগ্রামিং ল্যাঙ্গুয়েজ")
    stdin: Optional[str] = Field("", description="ইনপুট ডাটা")
    time_limit: Optional[int] = Field(5, description="টাইম লিমিট (সেকেন্ডে)", ge=1, le=30)
    
class ExecutionResult(BaseModel):
    """এক্সিকিউশন রেজাল্টের জন্য মডেল"""
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    execution_time: float = 0.0
    status: str = "success"  # success, error, timeout
    status_code: int = 0
    
class SubmissionResponse(BaseModel):
    """সাবমিশন রেসপন্সের জন্য মডেল"""
    id: str
    status: str
    result: Optional[ExecutionResult] = None

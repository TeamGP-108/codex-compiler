import subprocess
import time
import os
import tempfile
import shutil
import signal
import asyncio
import sys
from pathlib import Path
from typing import Dict, Optional

from .models import CodeSubmission, ExecutionResult, Language

class CodeExecutor:
    """কোড এক্সিকিউশনের জন্য প্রধান ক্লাস"""
    
    def __init__(self):
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # ল্যাঙ্গুয়েজ কনফিগারেশন
        self.language_configs = {
            Language.PYTHON: {
                "extension": ".py",
                "run_cmd": [sys.executable, "{file}"],
                "version_cmd": [sys.executable, "--version"]
            },
            Language.JAVASCRIPT: {
                "extension": ".js",
                "run_cmd": ["node", "{file}"],
                "version_cmd": ["node", "--version"]
            },
            Language.TYPESCRIPT: {
                "extension": ".ts",
                "compile_cmd": ["tsc", "{file}", "--outDir", "{dir}"],
                "run_cmd": ["node", "{file}".replace(".ts", ".js")],
                "version_cmd": ["tsc", "--version"]
            },
            Language.JAVA: {
                "extension": ".java",
                "compile_cmd": ["javac", "{file}"],
                "run_cmd": ["java", "-cp", "{dir}", "Main"],
                "version_cmd": ["java", "-version"]
            },
            Language.CPP: {
                "extension": ".cpp",
                "compile_cmd": ["g++", "{file}", "-o", "{exe}", "-std=c++17"],
                "run_cmd": ["{exe}"],
                "version_cmd": ["g++", "--version"]
            },
            Language.C: {
                "extension": ".c",
                "compile_cmd": ["gcc", "{file}", "-o", "{exe}", "-std=c11"],
                "run_cmd": ["{exe}"],
                "version_cmd": ["gcc", "--version"]
            },
            Language.RUBY: {
                "extension": ".rb",
                "run_cmd": ["ruby", "{file}"],
                "version_cmd": ["ruby", "--version"]
            },
            Language.PHP: {
                "extension": ".php",
                "run_cmd": ["php", "{file}"],
                "version_cmd": ["php", "--version"]
            },
            Language.BASH: {
                "extension": ".sh",
                "run_cmd": ["bash", "{file}"],
                "version_cmd": ["bash", "--version"]
            },
            Language.R: {
                "extension": ".r",
                "run_cmd": ["Rscript", "{file}"],
                "version_cmd": ["Rscript", "--version"]
            },
            Language.LUA: {
                "extension": ".lua",
                "run_cmd": ["lua", "{file}"],
                "version_cmd": ["lua", "-v"]
            }
        }
    
    async def get_language_versions(self) -> Dict[str, str]:
        """প্রতিটি ল্যাঙ্গুয়েজের ভার্সন তথ্য রিটার্ন করে"""
        versions = {}
        for lang, config in self.language_configs.items():
            try:
                if "version_cmd" in config:
                    process = await asyncio.create_subprocess_exec(
                        *config["version_cmd"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    version = stdout.decode() or stderr.decode()
                    versions[lang.value] = version.strip().split('\n')[0]
                else:
                    versions[lang.value] = "Unknown"
            except Exception:
                versions[lang.value] = "Not installed"
        return versions
    
    async def execute(self, submission: CodeSubmission) -> ExecutionResult:
        """মূল এক্সিকিউশন ফাংশন"""
        
        result = ExecutionResult()
        exec_dir = None
        
        try:
            # টেম্পোরারি ডিরেক্টরি তৈরি
            exec_dir = tempfile.mkdtemp(dir=self.temp_dir)
            config = self.language_configs[submission.language]
            
            # ফাইল পাথ তৈরি
            file_path = Path(exec_dir) / f"code{config['extension']}"
            exe_path = Path(exec_dir) / "a.out"
            
            # কোড ফাইল তৈরি
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(submission.code)
            
            # কম্পাইলেশন (যদি প্রয়োজন হয়)
            if "compile_cmd" in config:
                compile_cmd = [
                    arg.replace("{file}", str(file_path))
                       .replace("{dir}", exec_dir)
                       .replace("{exe}", str(exe_path))
                    for arg in config["compile_cmd"]
                ]
                
                compile_process = await asyncio.create_subprocess_exec(
                    *compile_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=exec_dir
                )
                
                try:
                    _, stderr = await asyncio.wait_for(
                        compile_process.communicate(),
                        timeout=10
                    )
                    
                    if compile_process.returncode != 0:
                        result.stderr = stderr.decode()
                        result.error = "কম্পাইলেশন এরর"
                        result.status = "error"
                        result.status_code = compile_process.returncode
                        return result
                        
                except asyncio.TimeoutError:
                    compile_process.kill()
                    result.error = "কম্পাইলেশন টাইম আউট"
                    result.status = "error"
                    return result
            
            # রান কমান্ড প্রস্তুত
            run_cmd = [
                arg.replace("{file}", str(file_path))
                   .replace("{dir}", exec_dir)
                   .replace("{exe}", str(exe_path))
                   .replace("{classname}", "Main")
                for arg in config["run_cmd"]
            ]
            
            # কোড এক্সিকিউট
            start_time = time.time()
            
            process = await asyncio.create_subprocess_exec(
                *run_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=exec_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=submission.stdin.encode()),
                    timeout=submission.time_limit
                )
                
                result.execution_time = time.time() - start_time
                result.stdout = stdout.decode('utf-8', errors='ignore')
                result.stderr = stderr.decode('utf-8', errors='ignore')
                result.status_code = process.returncode
                
                if process.returncode != 0:
                    result.status = "error"
                    if process.returncode == -signal.SIGKILL:
                        result.error = "প্রসেস কিল করা হয়েছে (সম্ভবত টাইম আউট)"
                        
            except asyncio.TimeoutError:
                process.kill()
                result.execution_time = time.time() - start_time
                result.error = f"টাইম আউট! {submission.time_limit} সেকেন্ডের বেশি সময় লেগেছে"
                result.status = "timeout"
                result.status_code = -1
                
        except Exception as e:
            result.error = str(e)
            result.status = "error"
            result.status_code = -1
            
        finally:
            # ক্লিনআপ
            if exec_dir and os.path.exists(exec_dir):
                try:
                    shutil.rmtree(exec_dir, ignore_errors=True)
                except Exception:
                    pass
        
        return result

# সিঙ্গেলটন ইনস্ট্যান্স
executor = CodeExecutor()

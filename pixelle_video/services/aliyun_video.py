"""
阿里云万相视频生成服务

支持通过阿里云DashScope API生成动态视频
"""

import asyncio
import httpx
from pathlib import Path
from typing import Optional
from loguru import logger
from dataclasses import dataclass


@dataclass
class AliyunVideoResult:
    """阿里云视频生成结果"""
    url: str
    duration: float
    task_id: str
    model: str


class AliyunVideoService:
    """
    阿里云万相视频生成服务
    
    支持模型:
    - wan2.6-t2v: 文生视频
    - wan2.7-t2v: 文生视频（推荐）
    - wan2.6-i2v: 图生视频
    
    Usage:
        service = AliyunVideoService(api_key="sk-xxx")
        result = await service.generate(
            prompt="一只猫咪在花园奔跑",
            duration=5,
            resolution="720P"
        )
    """
    
    BASE_URL = "https://dashscope.aliyuncs.com"
    API_ENDPOINT = "/api/v1/services/aigc/video-generation/video-synthesis"
    TASK_ENDPOINT = "/api/v1/tasks/{task_id}"
    
    def __init__(
        self,
        api_key: str,
        model: str = "wan2.6-t2v",
        timeout: int = 600,
        max_wait_attempts: int = 60
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_wait_attempts = max_wait_attempts
    
    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720P",
        ratio: str = "16:9",
        prompt_extend: bool = True,
        seed: Optional[int] = None
    ) -> AliyunVideoResult:
        """
        生成动态视频
        
        Args:
            prompt: 视频描述（英文更佳）
            duration: 视频时长（2-15秒）
            resolution: 分辨率（480P/720P/1080P）
            prompt_extend: 是否启用智能改写
            seed: 随机种子
        
        Returns:
            AliyunVideoResult: 包含视频URL和元数据
        """
        logger.info(f"🎬 阿里云万相生成视频: {prompt[:50]}...")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Step 1: 提交生成任务
            task_id = await self._submit_task(
                client, prompt, duration, resolution, ratio, prompt_extend, seed
            )
            logger.debug(f"   Task ID: {task_id}")
            
            # Step 2: 等待生成完成
            video_url, actual_duration = await self._wait_for_completion(
                client, task_id
            )
            
            logger.success(f"✅ 视频生成完成: {video_url}")
            
            return AliyunVideoResult(
                url=video_url,
                duration=actual_duration,
                task_id=task_id,
                model=self.model
            )
    
    async def _submit_task(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        duration: int,
        resolution: str,
        ratio: str,
        prompt_extend: bool,
        seed: Optional[int]
    ) -> str:
        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "duration": duration,
                "resolution": resolution,
                "ratio": ratio,
                "prompt_extend": prompt_extend
            }
        }
        
        if seed is not None:
            payload["parameters"]["seed"] = seed
        
        response = await client.post(
            f"{self.BASE_URL}{self.API_ENDPOINT}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"
            },
            json=payload
        )
        
        if response.status_code != 200:
            raise RuntimeError(
                f"阿里云API提交失败: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        task_id = data.get("output", {}).get("task_id")
        
        if not task_id:
            raise RuntimeError(f"未获取到task_id: {data}")
        
        return task_id
    
    async def _wait_for_completion(
        self,
        client: httpx.AsyncClient,
        task_id: str
    ) -> tuple[str, float]:
        """等待异步任务完成"""
        for attempt in range(self.max_wait_attempts):
            await asyncio.sleep(10)
            
            response = await client.get(
                f"{self.BASE_URL}{self.TASK_ENDPOINT.format(task_id=task_id)}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            data = response.json()
            status = data.get("output", {}).get("task_status")
            
            if attempt % 3 == 0:
                elapsed = attempt * 10 // 60
                logger.debug(f"   [{elapsed}分钟] 状态: {status}")
            
            if status == "SUCCEEDED":
                video_url = data.get("output", {}).get("video_url")
                
                if not video_url:
                    raise RuntimeError(f"任务成功但未返回video_url: {data}")
                
                # 获取视频时长
                duration = await self._get_video_duration(client, video_url)
                
                return video_url, duration
            
            elif status == "FAILED":
                error_msg = data.get("output", {}).get("message", "未知错误")
                raise RuntimeError(f"阿里云生成失败: {error_msg}")
        
        raise RuntimeError(f"等待超时 ({self.max_wait_attempts * 10}秒)")
    
    async def _get_video_duration(
        self,
        client: httpx.AsyncClient,
        video_url: str
    ) -> float:
        # 下载视频片段来探测时长
        response = await client.get(video_url, timeout=120.0)
        
        if response.status_code != 200:
            return 5.0  # 默认时长
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(response.content)
            temp_path = f.name
        
        # 使用ffprobe获取时长
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
             temp_path],
            capture_output=True, text=True
        )
        
        # 清理临时文件
        Path(temp_path).unlink(missing_ok=True)
        
        try:
            return float(result.stdout.strip())
        except:
            return 5.0
    
    async def download_video(
        self,
        video_url: str,
        save_path: Path
    ) -> Path:
        """下载视频到本地"""
        logger.info(f"📥 下载视频: {save_path}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(video_url)
            
            if response.status_code != 200:
                raise RuntimeError(f"视频下载失败: {response.status_code}")
            
            save_path.write_bytes(response.content)
            logger.success(f"   保存成功: {save_path.stat().st_size // (1024*1024)} MB")
            
            return save_path
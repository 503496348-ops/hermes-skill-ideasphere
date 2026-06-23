# -*- coding: utf-8 -*-
"""
灵感象限-Ideasphere · Video Processor
AtomCollide-智械工坊 · 2026

融合自 huggingface/diffusers 的视频处理能力。

处理能力:
  - 视频质量优化
  - 视频格式转换
  - 视频帧提取
  - 视频合成

Usage:
    from modules.video_processor import VideoProcessor
    processor = VideoProcessor()
    result = processor.optimize_video("/path/to/video.mp4")
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VideoFormat(Enum):
    """视频格式"""
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"
    GIF = "gif"


class VideoQuality(Enum):
    """视频质量"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class VideoInfo:
    """视频信息"""
    file_path: str
    format: VideoFormat
    width: int
    height: int
    duration: float
    fps: float
    bitrate: int
    size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """处理结果"""
    input_path: str
    output_path: str
    success: bool
    original_info: Optional[VideoInfo] = None
    processed_info: Optional[VideoInfo] = None
    processing_time: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class VideoProcessor:
    """
    视频处理器
    
    融合自 huggingface/diffusers 的视频处理能力。
    """
    
    def __init__(self):
        """初始化处理器"""
        self.supported_formats = {fmt.value for fmt in VideoFormat}
        self.quality_presets = {
            VideoQuality.LOW: {"width": 480, "height": 360, "bitrate": 500000},
            VideoQuality.MEDIUM: {"width": 720, "height": 480, "bitrate": 1000000},
            VideoQuality.HIGH: {"width": 1280, "height": 720, "bitrate": 2000000},
            VideoQuality.ULTRA: {"width": 1920, "height": 1080, "bitrate": 4000000},
        }
    
    def get_video_info(self, video_path: str) -> Optional[VideoInfo]:
        """
        获取视频信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频信息
        """
        path = Path(video_path)
        if not path.exists():
            return None
        
        try:
            # 尝试使用ffprobe获取视频信息
            import subprocess
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # 提取视频流信息
                video_stream = None
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break
                
                if video_stream:
                    format_info = data.get("format", {})
                    return VideoInfo(
                        file_path=str(path),
                        format=VideoFormat(path.suffix[1:].lower()),
                        width=int(video_stream.get("width", 0)),
                        height=int(video_stream.get("height", 0)),
                        duration=float(format_info.get("duration", 0)),
                        fps=eval(video_stream.get("r_frame_rate", "0/1")),
                        bitrate=int(format_info.get("bit_rate", 0)),
                        size_bytes=int(format_info.get("size", 0)),
                        metadata={
                            "codec": video_stream.get("codec_name"),
                            "pixel_format": video_stream.get("pix_fmt"),
                        }
                    )
        except Exception:
            pass
        
        # 如果ffprobe不可用，返回基本信息
        return VideoInfo(
            file_path=str(path),
            format=VideoFormat(path.suffix[1:].lower()),
            width=0,
            height=0,
            duration=0.0,
            fps=0.0,
            bitrate=0,
            size_bytes=path.stat().st_size,
        )
    
    def optimize_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        quality: VideoQuality = VideoQuality.HIGH,
        target_format: Optional[VideoFormat] = None,
    ) -> ProcessingResult:
        """
        优化视频
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            quality: 目标质量
            target_format: 目标格式
            
        Returns:
            处理结果
        """
        import time
        start_time = time.time()
        
        input_path_obj = Path(input_path)
        if not input_path_obj.exists():
            return ProcessingResult(
                input_path=input_path,
                output_path="",
                success=False,
                issues=["输入文件不存在"],
            )
        
        # 确定输出路径
        if output_path is None:
            suffix = target_format.value if target_format else input_path_obj.suffix[1:]
            output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_optimized.{suffix}")
        
        # 获取原始视频信息
        original_info = self.get_video_info(input_path)
        
        # 检查是否需要优化
        needs_optimization = False
        issues = []
        recommendations = []
        
        if original_info:
            # 检查分辨率
            preset = self.quality_presets[quality]
            if original_info.width > preset["width"] or original_info.height > preset["height"]:
                needs_optimization = True
                recommendations.append(f"降低分辨率到 {preset['width']}x{preset['height']}")
            
            # 检查比特率
            if original_info.bitrate > preset["bitrate"]:
                needs_optimization = True
                recommendations.append(f"降低比特率到 {preset['bitrate']}")
            
            # 检查格式
            if target_format and original_info.format != target_format:
                needs_optimization = True
                recommendations.append(f"转换格式到 {target_format.value}")
        
        # 如果不需要优化，直接返回
        if not needs_optimization:
            return ProcessingResult(
                input_path=input_path,
                output_path=input_path,
                success=True,
                original_info=original_info,
                processed_info=original_info,
                processing_time=time.time() - start_time,
                recommendations=["视频已经是最优状态"],
            )
        
        # 执行优化
        try:
            import subprocess
            
            # 构建ffmpeg命令
            cmd = ["ffmpeg", "-i", input_path, "-y"]
            
            # 设置分辨率
            preset = self.quality_presets[quality]
            cmd.extend(["-vf", f"scale={preset['width']}:{preset['height']}"])
            
            # 设置比特率
            cmd.extend(["-b:v", str(preset["bitrate"])])
            
            # 设置格式
            if target_format:
                cmd.extend(["-f", target_format.value])
            
            cmd.append(output_path)
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                processed_info = self.get_video_info(output_path)
                return ProcessingResult(
                    input_path=input_path,
                    output_path=output_path,
                    success=True,
                    original_info=original_info,
                    processed_info=processed_info,
                    processing_time=time.time() - start_time,
                    recommendations=recommendations,
                )
            else:
                return ProcessingResult(
                    input_path=input_path,
                    output_path=output_path,
                    success=False,
                    original_info=original_info,
                    issues=[f"ffmpeg执行失败: {result.stderr[:200]}"],
                    processing_time=time.time() - start_time,
                )
                
        except Exception as e:
            return ProcessingResult(
                input_path=input_path,
                output_path=output_path,
                success=False,
                original_info=original_info,
                issues=[f"处理失败: {str(e)}"],
                processing_time=time.time() - start_time,
            )
    
    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        frame_interval: float = 1.0,
        max_frames: int = 100,
    ) -> List[str]:
        """
        提取视频帧
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            frame_interval: 帧间隔（秒）
            max_frames: 最大帧数
            
        Returns:
            提取的帧文件路径列表
        """
        import subprocess
        
        path = Path(video_path)
        if not path.exists():
            return []
        
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 构建ffmpeg命令
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"fps=1/{frame_interval}",
                "-frames:v", str(max_frames),
                str(output_dir_path / "frame_%04d.png"),
                "-y"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # 返回提取的帧文件路径
                return sorted([
                    str(f) for f in output_dir_path.glob("frame_*.png")
                ])
        except Exception:
            pass
        
        return []
    
    def create_video_from_frames(
        self,
        frame_paths: List[str],
        output_path: str,
        fps: float = 30.0,
        quality: VideoQuality = VideoQuality.HIGH,
    ) -> ProcessingResult:
        """
        从帧创建视频
        
        Args:
            frame_paths: 帧文件路径列表
            output_path: 输出路径
            fps: 帧率
            quality: 视频质量
            
        Returns:
            处理结果
        """
        import time
        start_time = time.time()
        
        if not frame_paths:
            return ProcessingResult(
                input_path="",
                output_path=output_path,
                success=False,
                issues=["没有帧文件"],
            )
        
        try:
            import subprocess
            
            # 创建帧列表文件
            frame_list_path = Path(output_path).parent / "frame_list.txt"
            with open(frame_list_path, "w") as f:
                for frame_path in frame_paths:
                    f.write(f"file '{frame_path}'\n")
                    f.write(f"duration {1/fps}\n")
            
            # 构建ffmpeg命令
            preset = self.quality_presets[quality]
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(frame_list_path),
                "-vf", f"scale={preset['width']}:{preset['height']}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-y",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # 清理临时文件
            frame_list_path.unlink(missing_ok=True)
            
            if result.returncode == 0:
                processed_info = self.get_video_info(output_path)
                return ProcessingResult(
                    input_path="frames",
                    output_path=output_path,
                    success=True,
                    processed_info=processed_info,
                    processing_time=time.time() - start_time,
                )
            else:
                return ProcessingResult(
                    input_path="frames",
                    output_path=output_path,
                    success=False,
                    issues=[f"ffmpeg执行失败: {result.stderr[:200]}"],
                    processing_time=time.time() - start_time,
                )
                
        except Exception as e:
            return ProcessingResult(
                input_path="frames",
                output_path=output_path,
                success=False,
                issues=[f"处理失败: {str(e)}"],
                processing_time=time.time() - start_time,
            )
    
    def generate_report(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """生成处理报告"""
        success_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)
        
        return {
            "total_processed": len(results),
            "success": success_count,
            "failed": failed_count,
            "issues": [issue for r in results for issue in r.issues],
            "recommendations": [rec for r in results for rec in r.recommendations],
            "total_processing_time": sum(r.processing_time for r in results),
        }


# ── Self-test ──

if __name__ == "__main__":
    import tempfile
    
    print("🔍 Video Processor 自测")
    print("=" * 50)
    
    # 创建测试目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件（模拟视频）
        test_video = Path(tmpdir) / "test.mp4"
        test_video.write_bytes(b"fake video content")
        
        # 运行处理
        processor = VideoProcessor()
        
        # 获取视频信息
        info = processor.get_video_info(str(test_video))
        if info:
            print(f"\n📊 视频信息:")
            print(f"  格式: {info.format.value}")
            print(f"  大小: {info.size_bytes} bytes")
        
        # 优化视频
        result = processor.optimize_video(
            str(test_video),
            quality=VideoQuality.MEDIUM,
        )
        
        print(f"\n📊 处理结果:")
        print(f"  成功: {result.success}")
        print(f"  处理时间: {result.processing_time:.2f}s")
        
        if result.issues:
            print(f"\n⚠️ 问题:")
            for issue in result.issues:
                print(f"  - {issue}")
        
        if result.recommendations:
            print(f"\n💡 建议:")
            for rec in result.recommendations:
                print(f"  - {rec}")
    
    print("\n✅ 自测完成")

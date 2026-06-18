#!/usr/bin/env python3
"""
Pipeline Manifest（灵感象限-Ideasphere）
功能：记录流水线各阶段状态，支持断点续跑和阶段恢复
参考 KrillinAI 的 krillinai_manifest.json 设计

作者：AtomCollide-智械工坊团队
"""

import os
import json
import time
from datetime import datetime

MANIFEST_FILENAME = "ideasphere_manifest.json"


class PipelineManifest:
    """流水线状态管理器"""

    STAGES = ["clip", "concat", "transcribe", "translate", "burn", "export"]

    def __init__(self, workdir):
        self.workdir = workdir
        self.manifest_path = os.path.join(workdir, MANIFEST_FILENAME)
        self._data = self._load()

    def _load(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "workdir": self.workdir,
            "stages": {},
            "outputs": {},
            "metadata": {},
        }

    def _save(self):
        self._data["updated_at"] = datetime.now().isoformat()
        os.makedirs(self.workdir, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def stage_start(self, stage_name, inputs=None):
        """记录阶段开始"""
        self._data["stages"][stage_name] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "inputs": inputs or {},
            "outputs": {},
            "error": None,
        }
        self._save()

    def stage_complete(self, stage_name, outputs=None):
        """记录阶段完成"""
        if stage_name in self._data["stages"]:
            self._data["stages"][stage_name]["status"] = "completed"
            self._data["stages"][stage_name]["completed_at"] = datetime.now().isoformat()
            if outputs:
                self._data["stages"][stage_name]["outputs"] = outputs
                self._data["outputs"].update(outputs)
        self._save()

    def stage_fail(self, stage_name, error_msg):
        """记录阶段失败"""
        if stage_name in self._data["stages"]:
            self._data["stages"][stage_name]["status"] = "failed"
            self._data["stages"][stage_name]["error"] = error_msg
            self._data["stages"][stage_name]["failed_at"] = datetime.now().isoformat()
        self._save()

    def is_stage_completed(self, stage_name):
        """检查阶段是否已完成"""
        stage = self._data["stages"].get(stage_name)
        return stage is not None and stage.get("status") == "completed"

    def get_stage_output(self, stage_name, key=None):
        """获取阶段输出"""
        stage = self._data["stages"].get(stage_name, {})
        outputs = stage.get("outputs", {})
        if key:
            return outputs.get(key)
        return outputs

    def get_upstream_output(self, key):
        """从全局输出中获取上游阶段的产出"""
        return self._data["outputs"].get(key)

    def should_skip(self, stage_name):
        """判断是否应跳过此阶段（已完成且输出存在）"""
        if not self.is_stage_completed(stage_name):
            return False
        # 检查输出文件是否存在
        outputs = self.get_stage_output(stage_name)
        for key, path in outputs.items():
            if isinstance(path, str) and not os.path.exists(path):
                return False
        return True

    def set_metadata(self, key, value):
        """设置元数据"""
        self._data["metadata"][key] = value
        self._save()

    def get_metadata(self, key=None):
        """获取元数据"""
        if key:
            return self._data["metadata"].get(key)
        return self._data["metadata"]

    def summary(self):
        """输出流水线状态摘要"""
        lines = [
            f"📋 流水线状态 ({self.workdir})",
            f"   创建: {self._data.get('created_at', 'N/A')}",
            f"   更新: {self._data.get('updated_at', 'N/A')}",
            "",
        ]
        for stage in self.STAGES:
            info = self._data["stages"].get(stage)
            if not info:
                lines.append(f"   ⬜ {stage}: 未开始")
            elif info["status"] == "completed":
                lines.append(f"   ✅ {stage}: 已完成")
            elif info["status"] == "running":
                lines.append(f"   🔄 {stage}: 运行中")
            elif info["status"] == "failed":
                lines.append(f"   ❌ {stage}: 失败 - {info.get('error', 'unknown')}")
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ideasphere 流水线状态管理")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录")
    parser.add_argument("--action", "-a", choices=["summary", "reset", "output"],
                        default="summary", help="操作")
    parser.add_argument("--stage", "-s", default=None, help="指定阶段（用于 output）")
    args = parser.parse_args()

    manifest = PipelineManifest(args.workdir)

    if args.action == "summary":
        print(manifest.summary())
    elif args.action == "reset":
        if os.path.exists(manifest.manifest_path):
            os.remove(manifest.manifest_path)
            print("✅ Manifest 已重置")
        else:
            print("ℹ️ 无 manifest 文件")
    elif args.action == "output":
        if args.stage:
            outputs = manifest.get_stage_output(args.stage)
            print(json.dumps(outputs, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(manifest._data["outputs"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate a short video from a story using static template"""
import asyncio
from pathlib import Path
from loguru import logger
from pixelle_video import pixelle_video

STORY = """# 星光的秘密

从前，在一个小山村里，住着一个叫小星星的女孩。

每天夜晚，她都会爬到村后的小山坡上，仰望满天繁星。她总觉得，那些闪烁的星星在向她诉说着什么秘密。

终于有一天，一颗流星划过天际，落在了不远处的森林里。小星星鼓起勇气，循着光芒走进了森林。

在一棵老橡树下，她发现了一颗发光的石头。石头轻轻地说：「每颗星星都是一盏灯，为迷路的人照亮回家的路。」

小星星恍然大悟。从此，每当有人迷路时，她就会举起那颗星星石，为人们指引方向。

后来，整个村子都学会了她的善良。每个夜晚，村子里都会亮起温暖的灯火，像地上的星星一样闪耀。

而那颗星星石的故事，也被一代代传颂：真正的光明，来自愿意为他人点灯的心。"""


async def main():
    await pixelle_video.initialize()

    story_lines = [l.strip() for l in STORY.split("\n\n")]
    scenes = story_lines[1:]  # skip title

    # Generate video
    result = await pixelle_video.generate_video(
        text="\n\n".join(scenes),
        pipeline="standard",
        mode="fixed",
        title="星光的秘密",
        n_scenes=len(scenes),
        split_mode="paragraph",
        frame_template="1080x1920/static_default.html",
        media_workflow=None,
        tts_inference_mode="qwen_tts",
        tts_voice="vivian",
        tts_speed=1.0,
        bgm_path="default.mp3",
        bgm_volume=0.15,
        template_params={
            "author": "Pixelle Studio",
            "brand": "Pixelle-Video"
        }
    )

    path = Path(result.video_path)
    logger.success(f"\n✨ Video generated: {path}")
    logger.success(f"   Duration: {result.duration:.1f}s")
    logger.success(f"   Size: {path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())

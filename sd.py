import os
import pyJianYingDraft as draft
from pyJianYingDraft import Intro_type, Transition_type, trange

tutorial_asset_dir = os.path.join(os.path.dirname(__file__), 'readme_assets', 'tutorial')

# 创建剪映草稿
script = draft.Script_file(1080, 1080) # 1080x1080分辨率

# # 添加音频、视频和文本轨道
script.add_track(draft.Track_type.audio).add_track(draft.Track_type.video).add_track(draft.Track_type.text)
image_material = draft.Video_material(os.path.join(tutorial_asset_dir, 'cry.png'))

script.add_material(image_material)

video_segment = draft.Video_segment(image_material, trange("0s", "4.2s")) # 片段将位于轨道上的0s-4.2s（取素材前4.2s内容，注意此处4.2s表示持续时长）
script.add_segment(video_segment)

# 保存草稿（覆盖掉原有的draft_content.json）
base_dir = r"D:\\JianyingPro Drafts\\demo"
script.dump(os.path.join(base_dir, "draft_content.json"))
# base_dir = os.path.dirname(__file__)
# script.dump(os.path.join(base_dir, "sd_draft_content.json"))

from gradio_client import Client, handle_file
import os
import pyJianYingDraft as draft
from pyJianYingDraft import Intro_type, Transition_type, trange, Clip_settings,Text_intro, Text_outro
import json
from pydub import AudioSegment
import shutil
import math

voice_track_name = '语音'
bgm_track_name = '背景音乐'
project_name = '戴尔·卡耐基'
video_track_name = '视频'
sentence_track_name = '文本'
sentence_count = 30
gap_rate = 0.4
limit_len = 85
start_index = 0
total_project_count = 1
bg_random_index = 0
volume = 0.3

def tts(text, index):
    save_base_path = os.path.join(os.path.dirname(__file__), project_name)
    if not os.path.exists(save_base_path):
        os.makedirs(save_base_path)
    audio_path = os.path.join(save_base_path, f"audio_{index}.wav")
    # 如果存在，直接返回
    if os.path.exists(audio_path):
        return audio_path
    client = Client("http://127.0.0.1:7860/")
    result = client.predict(
            ref_audio_orig=handle_file('./voice/voice.MP3'),
            ref_text="",
            gen_text=text,
            model="F5-TTS",
            remove_silence=False,
            cross_fade_duration=0.1,
            speed=1,
            api_name="/infer"
        )
    # print(result)
    # 拷贝到文件夹下
    shutil.copy(result[0], audio_path)
    return audio_path

def main():
    asset_dir = os.path.join(os.path.dirname(__file__), project_name)
    base_dir = os.path.dirname(__file__)
    bg_dir = os.path.join(os.path.dirname(__file__), 'bgm')
    bg_list = os.listdir(bg_dir)
    bg_path = os.path.join(bg_dir, bg_list[bg_random_index])

    # 读取json 文件
    with open(os.path.join(base_dir, f"{project_name}.json"), "r", encoding="utf-8") as f:
        sentences = json.load(f)

    for i in range(start_index, start_index + total_project_count):
        # 创建剪映草稿
        script = draft.Script_file(1920, 1080) # 1080x1080分辨率

        # 添加音频、视频和文本轨道
        script.add_track(draft.Track_type.audio, voice_track_name) \
            .add_track(draft.Track_type.audio, bgm_track_name) \
            .add_track(draft.Track_type.video, video_track_name) \
            .add_track(draft.Track_type.text, sentence_track_name)

        edit_project(script, sentences, asset_dir, i, bg_path)

def edit_project(script, sentences, asset_dir, id, bg_path):
    start_time = 0
    for index, sentence in enumerate(sentences[id * sentence_count:(id + 1) * sentence_count]):
        base_index = id * sentence_count  + index
        print(base_index, sentence)
        # 如果句子长度超过110
        if len(sentence) > limit_len:
            continue
        voice = tts(sentence, base_index)
        # 生成音频, 获得音频路径
        audio_path = voice
        # 读取音频时长，获取时长
        audio_duration = AudioSegment.from_mp3(audio_path).duration_seconds
        audio_material = draft.Audio_material(audio_path)
        script.add_material(audio_material)
        print(audio_path)
        
        # 修复：确保时间范围不超过素材时长，向下取整
        audio_duration = math.floor(audio_duration * 10) / 10  # 保留一位小数，向下取整
        print('time',audio_duration)
        gap_time = audio_duration * gap_rate
        total_time = audio_duration + gap_time
        audio_segment = draft.Audio_segment(audio_material, trange(f"{start_time}s", f"{audio_duration}s"))
        script.add_segment(audio_segment, track_name=voice_track_name)
        sentence, max_len = add_enter(sentence)
        reverse_flag = 1
        transform_x = reverse_flag * (0.15 - max_len * 0.04)
        text_segment = draft.Text_segment(sentence, trange(f"{start_time}s", f"{total_time}s"),  # 文本将持续整个视频（注意script.duration在上方片段添加到轨道后才会自动更新）
                                        style=draft.Text_style(color=(255.0, 255.0, 255.0), align=1, bold=False),
                                        clip_settings=Clip_settings(transform_x= transform_x))          # 白色字幕
        text_segment.add_animation(Text_intro.复古打字机).add_animation(Text_outro.向上擦除)
        script.add_segment(text_segment)
        print(f'{base_index} 增加文本\n{audio_duration}s\n{sentence}')
        start_time += total_time

    # 创建图片
    sticker_material = draft.Video_material(os.path.join(asset_dir, 'bg.png'))
    script.add_material(sticker_material) # 随手添加素材是好习惯
    sticker_segment = draft.Video_segment(sticker_material, trange(0, script.duration))
    script.add_segment(sticker_segment)
    
    
    
    # 添加背景音乐
    bgm_material = draft.Audio_material(bg_path)
    script.add_material(bgm_material)
    bgm_name = os.path.basename(bg_path)
    bgm_duration = AudioSegment.from_file(bg_path, format="m4a").duration_seconds
    bgm_duration = math.floor(bgm_duration * 10) / 10  # 保留一位小数，向下取整
    
    script_duration = script.duration / 1000000 # 获取视频时长
    size = math.ceil(script_duration / bgm_duration)
    print(script_duration, bgm_duration,bgm_name, size)
    # 将背景音乐填充满视频中
    for i in range(0, size - 1):
        bgm_segment = draft.Audio_segment(bgm_material, trange(f"{i * bgm_duration}s", f"{bgm_duration}s"), volume=volume)
        script.add_segment(bgm_segment, track_name=bgm_track_name)
    
    rest_time = script_duration - (size - 1) * bgm_duration
    bgm_segment = draft.Audio_segment(bgm_material, trange(f"{(size - 1) * bgm_duration}s", f"{rest_time}s"), volume=volume)
    script.add_segment(bgm_segment, track_name=bgm_track_name)
    dir_path = r"I:\\uploads_jianying\\JianyingPro Drafts"
    base_dir = os.path.join(dir_path, f"{project_name}{id+1}")
    # 保存草稿（覆盖掉原有的draft_content.json）
    script.dump(os.path.join(base_dir, "draft_content.json"))
    
    # ctrl = draft.Jianying_controller()
    # ctrl.export_draft(f"{project_name}{id+1}", "I:\\福利")

def add_enter(sentence):
    result = ""
    max_len = 0
    curr_len = 0
    split_index = []
    temp_str = ""
    for index, char in enumerate(sentence):
        curr_len += 1
        temp_str += char
        if char == "，" or char == "。" or char == "！" or char == "、":
            result += temp_str + "\n"
            max_len = max(max_len, curr_len)
            curr_len = 0
            temp_str = ""
        elif curr_len > 12:
            # 从中间分割
            mid = len(temp_str) // 2
            result += temp_str[:mid] + "\n"
            temp_str = temp_str[mid:]
            max_len = max(max_len, curr_len)
            curr_len = len(temp_str)
    
    if temp_str:  # 处理剩余的字符
        result += temp_str
        max_len = max(max_len, curr_len)
    # 去除逗号，句号，感叹号，顿号
    result = result.replace("，", "").replace("。", "").replace("！", "").replace("、", "")
    
    return result, max_len

if __name__ == "__main__":
    main()
    # voice = tts("梦境所反映的画面、幻想等，都是做梦者心中所向")
    # 播放音频
    # print(voice[0])

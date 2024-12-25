from gradio_client import Client, handle_file
import os
import pyJianYingDraft as draft
from pyJianYingDraft import Intro_type, Transition_type, trange, Clip_settings,Text_intro, Text_outro
import json
from pydub import AudioSegment
import shutil
import math
import asyncio
import random
from jiangyin_api import export_video, create_draft, publish_to_web

voice_track_name = '语音'
bgm_track_name = '背景音乐'
project_name = '彼得·林奇'
video_track_name = '视频'
sentence_track_name = '文本'
sentence_count = 30
gap_rate = 0.5
limit_len = 85
start_project_index = 2
total_project_count = 1
bg_random_index = 3
reverse_flag = 1
volume = 0.2
export_filename = 'data.json'
export_folder = 'I:\\福利'
draft_folder = 'I:\\uploads_jianying\\JianyingPro Drafts'
author_desc = '''
1969年加入富达管理研究公司（Fidelity Investments）成为研究员，1977年成为麦哲伦基金（Magellan Fund）的基金经理人，1990年5月主动辞去基金经理人的职务。在彼得·林奇管理麦哲伦基金的13年间，基金管理的资产从2000万美元增长至140亿美元，基金投资人超过100万人，成为富达的旗舰基金，年平均复利报酬率达29.2%。林奇强调投资者应该投资自己了解的行业和公司，通过深入了解公司的业务、产品和市场，可以更好地判断其投资价值。他还特别关注那些被市场忽视的小公司，认为这些公司往往具有巨大的成长潜力。
'''

save_base_path = os.path.join(os.path.dirname(__file__), project_name)

data_path = os.path.join(save_base_path, export_filename)

async def main():
    asset_dir = os.path.join(os.path.dirname(__file__), project_name)
    base_dir = os.path.dirname(__file__)
    bg_dir = os.path.join(os.path.dirname(__file__), 'bgm')
    bg_list = os.listdir(bg_dir)
    bg_path = os.path.join(bg_dir, bg_list[bg_random_index])
    if not os.path.exists(save_base_path):
        os.makedirs(save_base_path)
    if not os.path.exists(data_path):
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

    # 读取json 文件
    with open(os.path.join(base_dir, f"{project_name}.json"), "r", encoding="utf-8") as f:
        sentences = json.load(f)

    for i in range(start_project_index, start_project_index + total_project_count):
        # 创建剪映草稿
        script = draft.Script_file(1920, 1080) # 1080x1080分辨率

        # 添加音频、视频和文本轨道
        script.add_track(draft.Track_type.audio, voice_track_name) \
            .add_track(draft.Track_type.audio, bgm_track_name) \
            .add_track(draft.Track_type.video, video_track_name) \
            .add_track(draft.Track_type.text, sentence_track_name)
        draft_name = f"{project_name}{i+1}"

        sentences_list = sentences[i * sentence_count:(i + 1) * sentence_count]
        await create_draft_by_yingdao(draft_name, i, sentences_list)
        await edit_project(script, sentences_list, asset_dir, i, bg_path, draft_name)
        # print('------exporting---------')
        await export_video_by_yingdao(draft_name, i)
        await publish_to_web_by_yingdao(i, author_desc)

async def publish_to_web_by_yingdao(i, author_desc):
    data = get_data_item(i)
    data["author_desc"] = author_desc
    await publish_to_web(data)

def tts(text, index):
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

async def create_draft_by_yingdao(draft_name, id, sentences_list):
    draft_folder_path = os.path.join(draft_folder, draft_name)
    if os.path.exists(draft_folder_path):
       return
    await create_draft(draft_name)
    random_index = random.randint(0, len(sentences_list) - 1)
    data = {
        "filename": f"{draft_name}.mp4",
        "id": id,
        "exported": False,
        "published": False,
        "sentence_list": sentences_list,
        "title": f"{project_name}:{sentences_list[random_index]}",
        "tag": [
            project_name,
        ]
    }
    save_data_item(data)

async def edit_project(script, sentences, asset_dir, id, bg_path, draft_name):
    start_time = 0
    for index, sentence in enumerate(sentences):
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
        gap_time = audio_duration * gap_rate if audio_duration >= 2 else 1 + audio_duration * gap_rate
        total_time = audio_duration + gap_time
        audio_segment = draft.Audio_segment(audio_material, trange(f"{start_time}s", f"{audio_duration}s"))
        script.add_segment(audio_segment, track_name=voice_track_name)
        sentence, max_len = add_enter(sentence)
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
    dir_path = draft_folder
    base_dir = os.path.join(dir_path, draft_name)
    # 保存草稿（覆盖掉原有的draft_content.json）
    script.dump(os.path.join(base_dir, "draft_content.json"))
    
    # 如果不存在，就创建

    # ctrl = draft.Jianying_controller()
    # ctrl.export_draft(f"{project_name}{id+1}", "I:\\福利")

async def export_video_by_yingdao(draft_name, id):
    export_path = os.path.join(export_folder, f"{draft_name}.mp4")
    data = get_data_item(id)
    print(export_path, data)
    if os.path.exists(export_path) or data["exported"] == True:
        data["exported"] = True
    else:
        print('-------------export---------')
        try:
            await export_video(draft_name)
            data["exported"] = True
        except Exception as e:
            print(e)
        
    save_data_item(data)

def get_data_item(id):
    with open(data_path, 'r', encoding='utf-8') as f:
        data_list = json.load(f)
    for item in data_list:
        if item["id"] == id:
            return item
    return None

def save_data_item(data):
    with open(data_path, 'r', encoding='utf-8') as f:
        data_list = json.load(f)
    
    # 方法1: 使用enumerate找到索引后替换
    for i, item in enumerate(data_list):
        if item["id"] == data["id"]:
            data_list[i] = data
            break
    else:  # 如果没找到匹配项,就添加新数据
        data_list.append(data)

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

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
    asyncio.run(main())
    # voice = tts("梦境所反映的画面、幻想等，都是做梦者心中所向")
    # 播放音频
    # print(voice[0])

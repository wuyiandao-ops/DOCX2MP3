import edge_tts
import asyncio

# 語音名稱全中文化映射表
VOICE_NAME_MAP = {
    # --- 台灣 (TW) ---
    "zh-TW-HsiaoChenNeural": "曉臻 (女)",
    "zh-TW-YunJheNeural": "雲哲 (男)",
    "zh-TW-HsiaoYuNeural": "曉雨 (女)",
    
    # --- 中國 (CN) ---
    "zh-CN-XiaoxiaoNeural": "曉曉 (女)",
    "zh-CN-YunxiNeural": "雲希 (男)",
    "zh-CN-YunjianNeural": "雲健 (男)",
    "zh-CN-YunyangNeural": "雲揚 (男)",
    "zh-CN-XiaoyiNeural": "曉依 (女)",
    "zh-CN-XiaochenNeural": "曉辰 (女)",
    "zh-CN-XiaohanNeural": "曉涵 (女)",
    "zh-CN-XiaomengNeural": "曉夢 (女)",
    "zh-CN-XiaomoNeural": "曉墨 (女)",
    "zh-CN-XiaoqiuNeural": "曉秋 (女)",
    "zh-CN-XiaoruiNeural": "曉睿 (女)",
    "zh-CN-XiaoshuangNeural": "曉雙 (女)",
    "zh-CN-XiaoxuanNeural": "曉萱 (女)",
    "zh-CN-XiaozhenNeural": "曉甄 (女)",
    "zh-CN-YunfengNeural": "雲楓 (男)",
    "zh-CN-YunhaoNeural": "雲皓 (男)",
    "zh-CN-YunxiaNeural": "雲夏 (男)",
    "zh-CN-YunyeNeural": "雲野 (男)",
    "zh-CN-YunzeNeural": "雲澤 (男)"
}

# --- Edge TTS (雲端極速並行) ---
async def get_voices_by_region(region: str):
    """
    根據區域獲取支援的語音清單。
    """
    voices_manager = await edge_tts.VoicesManager.create()
    locale_map = {"TW": "zh-TW", "CN": "zh-CN"}
    target_locale = locale_map.get(region, "zh-TW")
    voices = voices_manager.find(Locale=target_locale)
    return sorted(voices, key=lambda x: x["ShortName"])

def get_voice_display_name(voice_info: dict):
    """
    獲取轉換後的中文顯示名稱。
    """
    short_name = voice_info["ShortName"]
    # 如果在對照表內則使用中文名，否則使用原始 FriendlyName 的簡化版
    if short_name in VOICE_NAME_MAP:
        return VOICE_NAME_MAP[short_name]
    
    # 備用方案：如果映射表沒抓到，則進行基礎翻譯
    gender = "男" if voice_info["Gender"] == "Male" else "女"
    friendly_name = voice_info["FriendlyName"].replace("Microsoft ", "").replace(" Online (Natural)", "").replace(" (Neural)", "")
    # 移除區域前綴，只保留人名
    if "-" in friendly_name:
        friendly_name = friendly_name.split("-")[-1]
    return f"{friendly_name} ({gender})"

async def generate_audio_async(text: str, voice: str, rate: str, pitch: str, retries=2):
    """
    單段語音合成，直接與微軟伺服器溝通。
    """
    for attempt in range(retries + 1):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            if audio_data:
                return audio_data
        except Exception as e:
            if attempt == retries: raise e
            await asyncio.sleep(0.5)
    return b""

# --- 格式化輔助 ---
def format_rate(speed_factor: float):
    percentage = int((speed_factor - 1.0) * 100)
    return f"{'+' if percentage >= 0 else ''}{percentage}%"

def format_pitch(pitch_hz: int):
    return f"{'+' if pitch_hz >= 0 else ''}{pitch_hz}Hz"

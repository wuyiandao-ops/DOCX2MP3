import zipfile
import io
import re

def is_important_sentence(line: str) -> bool:
    """偵測是否為重要的佛典開端句"""
    patterns = [
        r'^第.+[卷品]',
        r'^爾時',
        r'^如是我聞',
        r'^世尊',
        r'^佛告',
        r'^大眾聞已',
    ]
    return any(re.search(p, line.strip()) for p in patterns)

def get_pause_text(ms: int) -> str:
    """將毫秒轉換為對應數量的全型逗號與空格，模擬停頓"""
    if ms < 200:
        return '，'
    num = max(1, ms // 250)
    return '，' * num + ' '

def split_text_smartly(text, max_chars=3000):
    if not text: return []
    if len(text) <= max_chars: return [text]
    
    parts = []
    while text:
        if len(text) <= max_chars:
            parts.append(text)
            break
        sub_text = text[:max_chars]
        split_point = -1
        delimiters = ['。', '！', '？', '\n', '.', '!', '?']
        for d in delimiters:
            pos = sub_text.rfind(d)
            if pos > split_point: split_point = pos
        if split_point == -1: split_point = max_chars
        else: split_point += 1
        parts.append(text[:split_point])
        text = text[split_point:].strip()
    return parts

def apply_replacement_rules(text, rules):
    """
    導入您腳本中的專業預處理邏輯：
    1. 跳過 # 註解行
    2. 處理 [pause] 標記
    3. 清洗非經文字元
    4. 段落間加入「。/換行」強化呼吸感
    """
    # 拆分為多行處理
    lines = text.replace('\r', '\n').split('\n')
    processed_lines = []

    for line in lines:
        strip_line = line.strip()
        
        # ── 1. 支援註解功能 (# 開頭不唸) ──
        if not strip_line or strip_line.startswith(('#', '＃')):
            continue

        # ── 2. 處理自定義停頓 ──
        line = re.sub(r'\[pause=(\d+)\]|\[p=(\d+)\]',
                      lambda m: get_pause_text(int(m.group(1) or m.group(2))),
                      strip_line)
        
        # ── 3. 文字清洗 (保留中文字與標點) ──
        line = re.sub(r'[^\w\s\u4e00-\u9fff。，！？、；：，.!?;:]', ' ', line)
        line = re.sub(r'\s+', ' ', line).strip()
        
        if line:
            processed_lines.append(line)

    # ── 4. 套用資料庫詞彙替換規則 ──
    # 在套用規則前先將行合併，並在段落間加入點號確保 AI 呼吸
    # 使用 '。\n' 連接，這比單純空格更能讓 AI 有斷句感
    full_text = '。\n'.join(processed_lines)

    if not rules: return full_text
    
    for rule in rules:
        if rule.original_text:
            full_text = full_text.replace(rule.original_text, rule.replace_with or "")
            
    return full_text

def zip_mp3_files(mp3_data_list):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, data in mp3_data_list:
            zf.writestr(filename, data)
    return buf.getvalue()

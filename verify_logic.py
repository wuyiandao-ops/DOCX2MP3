from utils import split_text_smartly, apply_replacement_rules
from tts_logic import format_rate, format_pitch

# 測試文字切分 (模擬長文)
long_text = "這是一個很長的文章。" * 1000  # 約 10,000 字
parts = split_text_smartly(long_text, max_chars=1000)
print(f"切分測試：將 10000 字切分為 {len(parts)} 段 (預期約 10 段)")

# 測試替換邏輯
class MockRule:
    def __init__(self, orig, target):
        self.original_text = orig
        self.replace_with = target

rules = [MockRule("般若", "波惹"), MockRule("世界", "宇宙")]
test_text = "般若波羅蜜多心經，拯救世界。"
replaced = apply_replacement_rules(test_text, rules)
print(f"替換測試：{test_text} -> {replaced}")
assert "波惹" in replaced
assert "宇宙" in replaced

# 測試語速/音高格式
print(f"格式測試：1.5x -> {format_rate(1.5)}")
print(f"格式測試：-5Hz -> {format_pitch(-5)}")
assert format_rate(1.5) == "+50%"
assert format_pitch(-5) == "-5Hz"

print("\n✅ 核心邏輯驗證成功！")

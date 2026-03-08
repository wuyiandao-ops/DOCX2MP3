from docx import Document
import io

def extract_text(file_buffer):
    """
    從 DOCX 檔案流中提取純文字
    :param file_buffer: 檔案緩衝區 (來自 Streamlit 的 st.file_uploader)
    :return: 提取後的完整字串，段落間以換行符分隔
    """
    try:
        # 使用 python-docx 讀取檔案流
        doc = Document(file_buffer)
        full_text = []
        
        # 遍歷所有段落並提取文字
        for para in doc.paragraphs:
            if para.text.strip():  # 忽略空白行
                full_text.append(para.text)
        
        return '\n'.join(full_text)
    except Exception as e:
        raise ValueError(f"無法解析 DOCX 檔案：{str(e)}")

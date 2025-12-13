import re, csv, io

def relationships_csv_to_text(csv_block: str) -> list[str]:
    """
    将 Relationships 的 CSV 块解析成自然语言格式：
    INTERNET → TCP/IP：TCP/IP is the fundamental ...
    支持字段和内容带引号的情况。
    """
    cleaned = "\n".join(line.strip() for line in csv_block.splitlines() if line.strip())
    cleaned = cleaned.lstrip("\ufeff")

    reader = csv.reader(io.StringIO(cleaned))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV 为空")
    headers = [h.strip().strip('"') for h in rows[0]]
    try:
        idx_source = headers.index("source")
        idx_target = headers.index("target")
        idx_desc = headers.index("description")
    except ValueError:
        raise ValueError(f"表头中缺少字段: {headers}")
    result = []
    for r in rows[1:]:
        if len(r) <= max(idx_source, idx_target, idx_desc):
            continue
        source = r[idx_source].strip().strip('"')
        target = r[idx_target].strip().strip('"')
        description = r[idx_desc].strip().strip('"').replace("<SEP>", " ")
        description = re.sub(r'\s+', ' ', description)
        result.append(f"{source} → {target}：{description}")

    return result

def capture_relationships_csv(text: str) -> str:
    """
    从完整文本中捕获 Relationships 的原始 CSV 内容（不解析）。
    返回纯 CSV 字符串。
    """
    match = re.search(r"-----Relationships-----\s*```csv(.*?)```", text, re.S)
    if not match:
        raise ValueError("未找到 Relationships 段落")
    return match.group(1).strip()

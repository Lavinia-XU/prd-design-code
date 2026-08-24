import argparse
import html
import json
import subprocess
import sys
from pathlib import Path

_TEMPLATE_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "references" / "02-template-contracts" / "common-design-template-registry.json"
_TEMPLATE_REGISTRY = {}
try:
    _TEMPLATE_REGISTRY = json.loads(_TEMPLATE_REGISTRY_PATH.read_text(encoding="utf-8")).get("templates", {})
except Exception:
    _TEMPLATE_REGISTRY = {}


def esc(value):
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def slug(value):
    text = str(value or "item").strip().lower()
    safe = []
    for ch in text:
        if ch.isalnum():
            safe.append(ch)
        else:
            safe.append("-")
    result = "".join(safe).strip("-")
    return result or "item"


def rich_value(value):
    if isinstance(value, list):
        return list_html(value)
    if isinstance(value, dict):
        return table_html([{"key": key, "value": item} for key, item in value.items()], [("key", "字段"), ("value", "内容")])
    return esc(value)


def list_html(items):
    if not items:
        return "<p class=\"muted\">暂无</p>"
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


FOOTER_BUTTON_LABELS = {
    "cancel": "取消",
    "confirm": "确定",
    "close": "关闭",
    "previous": "上一步",
    "next-or-complete": "下一步/完成",
}


def footer_button_label(button_id):
    return FOOTER_BUTTON_LABELS.get(str(button_id), str(button_id))


def table_html(rows, columns):
    if not rows:
        return "<p class=\"muted\">暂无</p>"
    thead = "<tr>" + "".join(f"<th>{esc(label)}</th>" for _, label in columns) + "</tr>"
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{esc(row.get(key, ''))}</td>" for key, _ in columns) + "</tr>")
    return f"<table><thead>{thead}</thead><tbody>{''.join(body)}</tbody></table>"


def render_tree(nodes):
    if not nodes:
        return "<p class=\"muted\">暂无导航结构</p>"
    parts = ["<ul>"]
    for node in nodes:
        if isinstance(node, dict):
            parts.append(f"<li>{esc(node.get('label', '未命名'))}")
            children = node.get("children") or []
            if children:
                parts.append(render_tree(children))
            parts.append("</li>")
        else:
            parts.append(f"<li>{esc(node)}</li>")
    parts.append("</ul>")
    return "".join(parts)


MODE_LABELS = {
    "reuse-framework": "复用框架",
    "component-reuse": "组件复用",
    "direct-reference": "直接引用",
    "new-development": "全新开发",
}
STATUS_LABELS = {"verified": "已验证", "pending": "待核验", "blocked": "阻塞", "na": "不适用"}


def _normalize_page_item(item):
    """兼容新旧两种开发项结构，统一为六列行数据。"""
    if not isinstance(item, dict):
        return {"id": "", "name": str(item), "mode": "", "mapping": "", "requirements": "", "acceptance": ""}
    if "developmentItem" in item or "developmentMode" in item or "developmentDescription" in item:
        return {
            "id": "",
            "name": item.get("developmentItem") or item.get("item") or item.get("label") or "",
            "mode": item.get("developmentMode") or item.get("mode") or item.get("way") or "",
            "mapping": "",
            "requirements": item.get("developmentDescription") or item.get("description") or item.get("detail") or "",
            "acceptance": "",
        }
    mode = item.get("mode") or ""
    status = item.get("mappingStatus") or ""
    target = item.get("target") or {}
    mapping_parts = []
    if item.get("mappingRef"):
        mapping_parts.append(item["mappingRef"])
    if status:
        mapping_parts.append(STATUS_LABELS.get(status, status))
    if target.get("path"):
        mapping_parts.append(target["path"])
    if target.get("export"):
        mapping_parts.append(target["export"])
    reqs = item.get("requirements") or []
    acc = item.get("acceptanceCriteria") or []
    return {
        "id": item.get("id") or "",
        "name": item.get("name") or item.get("scope") or "",
        "mode": MODE_LABELS.get(mode, mode),
        "mapping": "；".join(mapping_parts),
        "requirements": "；".join(reqs) if isinstance(reqs, list) else str(reqs or ""),
        "acceptance": "；".join(acc) if isinstance(acc, list) else str(acc or ""),
    }


def render_coding_summary(guide, mode="overview"):
    if not guide:
        guide = {}

    if mode == "page":
        rows = [_normalize_page_item(item) for item in (guide.get("pageItems") or [])]
        parts = []

        ctx = guide.get("pageContext") or {}
        if ctx:
            ctx_lines = []
            for key, label in (("pageId", "页面ID"), ("pageType", "页面类型"), ("route", "路由"), ("codeAvailability", "代码可用状态"), ("visualBaselineRef", "视觉基线参考")):
                if ctx.get(key):
                    ctx_lines.append(f"{label}：{ctx[key]}")
            parts.append(f"<div><strong>页面实现前提</strong>{list_html(ctx_lines)}</div>")

        rules = guide.get("implementationRules") or []
        if rules:
            parts.append(f"<div><strong>页面实现规则</strong>{list_html(rules)}</div>")

        if rows:
            cols = [("id", "编号"), ("name", "开发对象"), ("mode", "开发方式"), ("mapping", "复用与代码映射"), ("requirements", "实现要求"), ("acceptance", "完成判定")]
            parts.append(f"<div><strong>开发项编码指导表</strong>{table_html(rows, cols)}</div>")

        mc = guide.get("mockContract") or {}
        if mc:
            parts.append(f"<div><strong>Mock数据契约</strong>{list_html([f'{k}：{v}' for k, v in mc.items()])}</div>")
        sc = guide.get("stateContract") or {}
        if sc:
            parts.append(f"<div><strong>状态契约</strong>{list_html([f'{k}：{v}' for k, v in sc.items()])}</div>")
        acc = guide.get("acceptanceCriteria") or []
        if acc:
            parts.append(f"<div><strong>页面验收标准</strong>{list_html(acc)}</div>")
        oos = guide.get("outOfScope") or []
        if oos:
            parts.append(f"<div><strong>范围外事项</strong>{list_html(oos)}</div>")

        mock_data = guide.get("pageMockData") or []
        if mock_data:
            parts.append(f"<div><strong>页面级Mock数据要求</strong>{list_html(mock_data)}</div>")

        notes = guide.get("pageNotes") or []
        if notes:
            parts.append(f"<div><strong>页面级补充说明</strong>{list_html(notes)}</div>")

        return f"<div class=\"stack\">{''.join(parts) if parts else '<p class=\"muted\">暂无页面级Coding指导</p>'}</div>"

    items = guide.get("overviewItems") or []
    rows = []
    for item in items:
        if isinstance(item, dict):
            rows.append({
                "outputItem": item.get("outputItem") or item.get("item") or item.get("label") or "",
                "description": item.get("description") or item.get("detail") or "",
            })
        else:
            rows.append({"outputItem": str(item), "description": ""})

    parts = []
    if rows:
        parts.append(f"<div><strong>总览AI Coding指导</strong>{table_html(rows, [('outputItem', '输出项'), ('description', '说明')])}</div>")

    mock_data = guide.get("overviewMockData") or []
    if mock_data:
        parts.append(f"<div><strong>全局Mock数据要求</strong>{list_html(mock_data)}</div>")

    notes = guide.get("overviewNotes") or []
    if notes:
        parts.append(f"<div><strong>全局编码约束</strong>{list_html(notes)}</div>")

    return f"<div class=\"stack\">{''.join(parts) if parts else '<p class=\"muted\">暂无总结性AI Coding指导</p>'}</div>"


def markdown_table(rows, columns):
    if not rows:
        return "暂无"
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, divider]
    for row in rows:
        values = [str(row.get(key, "")).replace("|", "\\|").replace("\n", "<br>") for key, _ in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def markdown_list(items):
    return "\n".join(f"- {item}" for item in items) if items else "- 暂无"


def markdown_coding_guide(guide, mode="overview"):
    guide = guide or {}
    if mode == "overview":
        rows = guide.get("overviewItems") or []
        normalized = []
        for item in rows:
            if isinstance(item, dict):
                normalized.append({"outputItem": item.get("outputItem") or item.get("item") or item.get("label") or "", "description": item.get("description") or item.get("detail") or ""})
            else:
                normalized.append({"outputItem": str(item), "description": ""})
        parts = ["### 总览 AI Coding指导", markdown_table(normalized, [("outputItem", "输出项"), ("description", "说明")])]
        if guide.get("overviewMockData"):
            parts.extend(["#### 全局Mock数据要求", markdown_list(guide.get("overviewMockData"))])
        if guide.get("overviewNotes"):
            parts.extend(["#### 全局编码约束", markdown_list(guide.get("overviewNotes"))])
        return "\n\n".join(parts)

    rows = guide.get("pageItems") or []
    normalized = [_normalize_page_item(item) for item in rows]
    parts = []
    ctx = guide.get("pageContext") or {}
    if ctx:
        ctx_lines = []
        for key, label in (("pageId", "页面ID"), ("pageType", "页面类型"), ("route", "路由"), ("codeAvailability", "代码可用状态"), ("visualBaselineRef", "视觉基线参考")):
            if ctx.get(key):
                ctx_lines.append(f"{label}：{ctx[key]}")
        parts.extend(["#### 页面实现前提", markdown_list(ctx_lines)])
    rules = guide.get("implementationRules") or []
    if rules:
        parts.extend(["#### 页面实现规则", markdown_list(rules)])
    parts.append("### 页面级 AI Coding指导")
    parts.append(markdown_table(normalized, [("id", "编号"), ("name", "开发对象"), ("mode", "开发方式"), ("mapping", "复用与代码映射"), ("requirements", "实现要求"), ("acceptance", "完成判定")]))
    mc = guide.get("mockContract") or {}
    if mc:
        parts.extend(["#### Mock数据契约", markdown_list([f"{k}：{v}" for k, v in mc.items()])])
    sc = guide.get("stateContract") or {}
    if sc:
        parts.extend(["#### 状态契约", markdown_list([f"{k}：{v}" for k, v in sc.items()])])
    acc = guide.get("acceptanceCriteria") or []
    if acc:
        parts.extend(["#### 页面验收标准", markdown_list(acc)])
    oos = guide.get("outOfScope") or []
    if oos:
        parts.extend(["#### 范围外事项", markdown_list(oos)])
    if guide.get("pageMockData"):
        parts.extend(["#### 页面级Mock数据要求", markdown_list(guide.get("pageMockData"))])
    if guide.get("pageNotes"):
        parts.extend(["#### 页面级补充说明", markdown_list(guide.get("pageNotes"))])
    return "\n\n".join(parts)


def normalize_component_rows(rows):
    normalized = []
    for row in rows or []:
        if not isinstance(row, dict):
            normalized.append(row)
            continue
        item = dict(row)
        if not item.get("iduxComponent"):
            item["iduxComponent"] = item.get("componentName") or item.get("idux") or item.get("idux_component") or ""
        normalized.append(item)
    return normalized


def markdown_restore_requirement(restore):
    if isinstance(restore, dict):
        parts = []
        description = restore.get("description") or restore.get("requirement") or ""
        if description:
            parts.append(str(description))
        components = normalize_component_rows(restore.get("components") or restore.get("componentMapping") or [])
        if components:
            parts.append(markdown_table(components, [("area", "页面骨架区域"), ("iduxComponent", "组件名称"), ("source", "组件来源"), ("usage", "还原要求")]))
        return "\n\n".join(parts)
    if isinstance(restore, list):
        return markdown_list(restore)
    return str(restore)


def markdown_template_contract(page):
    template_contract = page.get("templateContract") or {}
    wireframe_data = page.get("wireframe") or page.get("asciiWireframe") or {}
    if not isinstance(wireframe_data, dict):
        wireframe_data = {}
    template_id = str(template_contract.get("templateId") or wireframe_data.get("templateId") or "").strip()
    if not template_id:
        return ""
    navigation_type = str(template_contract.get("navigationType") or wireframe_data.get("navigationType") or "").strip()
    template_source = str(template_contract.get("templateSource") or wireframe_data.get("layoutSource") or "").strip()
    template = _TEMPLATE_REGISTRY.get(template_id, {})
    lines = ["#### 模板契约"]
    base = f"（custom，base：{template_contract.get('baseTemplateId', '')}）" if template_id == "custom" else ""
    lines.append(f"- templateId：{template_id}{base}；navigationType：{navigation_type or '-'}")
    if template_source:
        lines.append(f"- templateSource：{template_source}")
    required = template_contract.get("requiredRegions") or template.get("requiredRegions") or []
    if required:
        lines.append(f"- 模板必需区域：{'、'.join(required)}")
    region_order = template_contract.get("regionOrder") or []
    if region_order:
        lines.append(f"- 区域顺序：{'、'.join(region_order)}")
    footer_contract = template.get("footer") or {}
    if footer_contract:
        align = footer_contract.get("alignment") or "-"
        footer_note = f"- 底部操作契约：对齐方式：{align}（{'必填' if footer_contract.get('required') else '可选'}）"
        button_order = footer_contract.get("buttonOrder") or []
        if button_order:
            footer_note += f"；按钮顺序：{'、'.join(footer_button_label(b) for b in button_order)}"
        lines.append(footer_note)
    return "\n".join(lines)


def markdown_page(page, inherited_nav=None):
    nav = page_navigation(page, inherited_nav)
    lines = [f"## {page_label(page)}", "", f"- 页面目标：{page.get('purpose', '')}", f"- 页面类型：{page.get('type', '')}", f"- 页面布局：{page.get('layout', '')}", "", "### 导航位置", markdown_table([nav], [("primary", "一级导航"), ("secondary", "二级导航"), ("tertiary", "三级导航"), ("tab", "Tab页面")])]
    restore = page.get("restoreRequirement") or page.get("pageTypeRestoreRequirement")
    if restore:
        lines.extend(["", "### 页面类型还原要求", markdown_restore_requirement(restore)])
    wireframe = page.get("wireframe") or page.get("asciiWireframe")
    if isinstance(wireframe, dict):
        wireframe = wireframe.get("ascii") or wireframe.get("text") or ""
    if wireframe:
        lines.extend(["", "### Wireframe / ASCII 线框图", "```text", str(wireframe), "```"])
    lines.extend(["", "### 页面内容区块"])
    for block in page.get("sections", []):
        lines.extend([f"#### {block.get('title', '未命名区块')}", str(block.get('description', ''))])
        for key, label in [("toolbar", "工具栏/筛选搜索"), ("actions", "按钮/可点击操作"), ("displayRules", "展示形式与取值范围"), ("interactionNotes", "交互、反馈与状态说明"), ("validationRules", "校验、联动与边界状态")]:
            if block.get(key):
                lines.extend([f"**{label}**", markdown_list(block.get(key))])
        if block.get("filterComponent") or block.get("filterComponentDescription"):
            lines.extend(["**筛选区组件说明**", markdown_list([item for item in [block.get("filterComponent"), block.get("filterComponentDescription")] if item])])
        if block.get("filterFields"):
            lines.extend(["**筛选字段**", markdown_table(block.get("filterFields"), [("name", "字段名称"), ("component", "组件/筛选方式"), ("mode", "匹配方式"), ("options", "选项范围"), ("default", "默认值"), ("description", "说明")])])
        if block.get("tableFields") or block.get("columns"):
            lines.extend(["**表格字段**", markdown_table(normalize_component_rows(block.get("tableFields") or block.get("columns")), [("name", "字段名称"), ("display", "展示形式"), ("iduxComponent", "组件名称"), ("description", "说明")])])
        if block.get("formFields"):
            lines.extend(["**表单字段**", markdown_table(normalize_component_rows(block.get("formFields")), [("name", "字段名称"), ("component", "组件类型"), ("iduxComponent", "iDux组件名称"), ("required", "必填"), ("default", "默认值"), ("rules", "选项/规则"), ("tips", "提示信息或联动关系")])])
    lines.extend(["", "### 底部操作", markdown_list(page.get("footerActions", []))])
    contract_md = markdown_template_contract(page)
    if contract_md:
        lines.extend(["", contract_md])
    lines.extend(["", markdown_coding_guide(page.get("codingGuide", {}), mode="page")])
    return "\n\n".join(lines)


def render_markdown_source(data, pages):
    overview = data.get("overview", {})
    page_cols = [("module", "业务模块"), ("id", "页面ID"), ("name", "页面名称"), ("type", "页面类型"), ("purpose", "页面用途"), ("entry", "入口方式"), ("interaction", "关键交互"), ("designSource", "设计来源"), ("codingMode", "编码方式")]
    sections = [("overview", f"# {data.get('title', '需求设计说明书')}\n\n## 概览\n\n### 需求概括\n{overview.get('summary', '')}\n\n### 页面总览表\n{markdown_table(overview.get('pageOverview', []), page_cols)}\n\n{markdown_coding_guide(data.get('codingGuide', {}), mode='overview')}")]
    for page, inherited_nav in pages:
        base = "page-" + slug(page.get("id", ""))
        sections.append((base, markdown_page(page, inherited_nav)))
    return "".join(f'<section class="markdown-section" id="source-{esc(base)}"><pre class="markdown-source">{esc(text)}</pre></section>' for base, text in sections)


def render_preview_content(data, pages, validation_info=None):
    validation_info = validation_info or {}
    banner = ""
    status = validation_info.get("status", "unknown")
    if status != "passed":
        if validation_info.get("legacy"):
            banner = "<div class=\"validation-banner\" style=\"background:#fff8e1;border:1px solid #b45309;padding:8px 12px;margin-bottom:12px;border-radius:4px;\"><strong>校验未通过</strong> — 本说明书使用旧版自由文本线框，未完成模板契约校验，不得作为 Coding 基线，需修正后再编码。</div>"
        else:
            banner = "<div class=\"validation-banner\" style=\"background:#fdecea;border:1px solid #c62828;padding:8px 12px;margin-bottom:12px;border-radius:4px;\"><strong>校验未通过</strong> — 说明书未通过校验，需修正后再编码。</div>"
    return banner + render_overview(data) + "\n" + "\n".join(render_page(page, inherited_nav) for page, inherited_nav in pages)


def build_view(content):
    return f'<div class="view">{content}</div>'


def render_overview(data):
    overview = data.get("overview", {})
    page_cols = [("module", "业务模块"), ("id", "页面ID"), ("name", "页面名称"), ("type", "页面类型"), ("purpose", "页面用途"), ("entry", "入口方式"), ("interaction", "关键交互"), ("designSource", "设计来源"), ("codingMode", "编码方式")]
    return f"""
    <section class="page" id="overview">
      <h1>{esc(data.get('title', '需求设计说明书'))}</h1>
      <div class="card"><h2>需求概括</h2><p>{esc(overview.get('summary', ''))}</p></div>
      <div class="card"><h2>导航结构</h2>{render_tree(data.get('navigation', []))}</div>
      <div class="card"><h2>页面总览表</h2>{table_html(overview.get('pageOverview', []), page_cols)}</div>
      <div class="card"><h2>总结性AI Coding指导</h2>{render_coding_summary(data.get('codingGuide', {}))}</div>
    </section>
    """


def optional_list_block(title, items):
    if not items:
        return ""
    return f"<div><strong>{esc(title)}</strong>{list_html(items)}</div>"


def optional_table_block(title, rows, columns):
    if not rows:
        return ""
    return f"<div><strong>{esc(title)}</strong>{table_html(rows, columns)}</div>"


def normalize_legacy_fields(items, mode):
    rows = []
    for item in items or []:
        if isinstance(item, dict):
            rows.append(item)
            continue
        text = str(item)
        name, sep, rest = text.partition("：")
        if not sep:
            name, sep, rest = text.partition(":")
        if mode == "form":
            rows.append({
                "name": name.strip() if sep else text,
                "component": "",
                "iduxComponent": "",
                "required": "",
                "default": "",
                "rules": rest.strip() if sep else "",
                "tips": "",
            })
        else:
            rows.append({
                "name": name.strip() if sep else text,
                "display": "",
                "iduxComponent": "",
                "description": rest.strip() if sep else "",
            })
    return rows


def render_block_detail(block):
    details = []
    block_type = str(block.get("type") or block.get("title") or "")
    table_columns = [("name", "字段名称"), ("display", "展示形式"), ("iduxComponent", "组件名称"), ("description", "说明")]
    form_columns = [("name", "字段名称"), ("component", "组件类型"), ("iduxComponent", "iDux组件名称"), ("required", "必填"), ("default", "默认值"), ("rules", "选项/规则"), ("tips", "提示信息或联动关系")]

    html_text = optional_list_block("工具栏/筛选搜索", block.get("toolbar", []))
    if html_text:
        details.append(html_text)

    filter_mode = block.get("filterMode") or block.get("filterType")
    filter_source = block.get("filterSource")
    filter_component = block.get("filterComponent") or block.get("filterContainerComponent")
    filter_component_description = block.get("filterComponentDescription")
    filter_fields = normalize_component_rows(block.get("filterFields") or [])
    if filter_mode or filter_source or filter_component or filter_component_description or filter_fields:
        filter_intro = []
        if filter_source:
            filter_intro.append(f"筛选方式来源：{esc(filter_source)}")
        if filter_mode:
            filter_intro.append(f"筛选组件类型：{esc(filter_mode)}")
        if filter_component:
            filter_intro.append(f"筛选容器/组合组件：{esc(filter_component)}")
        if filter_component_description:
            filter_intro.append(f"组件使用说明：{esc(filter_component_description)}")
        filter_html = optional_list_block("筛选区组件说明", filter_intro)
        filter_table = optional_table_block("筛选字段", filter_fields, [("name", "字段名称"), ("component", "组件/筛选方式"), ("mode", "匹配方式"), ("options", "选项范围"), ("default", "默认值"), ("description", "说明")])
        details.append(filter_html + filter_table)

    table_fields = block.get("tableFields") or block.get("columns") or []
    form_fields = block.get("formFields") or []
    legacy_fields = block.get("fields", [])
    if not table_fields and not form_fields and legacy_fields:
        if "表单" in block_type:
            form_fields = normalize_legacy_fields(legacy_fields, "form")
        elif "表格" in block_type or "列表" in block_type:
            table_fields = normalize_legacy_fields(legacy_fields, "table")

    html_text = optional_table_block("表格字段", normalize_component_rows(table_fields), table_columns)
    if html_text:
        details.append(html_text)
    html_text = optional_table_block("表单字段", normalize_component_rows(form_fields), form_columns)
    if html_text:
        details.append(html_text)

    if legacy_fields and not table_fields and not form_fields:
        html_text = optional_list_block("字段/指标", legacy_fields)
        if html_text:
            details.append(html_text)

    detail_map = [
        ("actions", "按钮/可点击操作"),
        ("displayRules", "展示形式与取值范围"),
        ("interactionNotes", "交互、反馈与状态说明"),
        ("validationRules", "校验、联动与边界状态"),
    ]
    for key, label in detail_map:
        html_text = optional_list_block(label, block.get(key, []))
        if html_text:
            details.append(html_text)
    if not details:
        return ""
    return '<div class="stack">' + "".join(details) + "</div>"


def render_template_contract(page):
    template_contract = page.get("templateContract") or {}
    wireframe_data = page.get("wireframe") or page.get("asciiWireframe") or {}
    if not isinstance(wireframe_data, dict):
        wireframe_data = {}
    template_id = str(template_contract.get("templateId") or wireframe_data.get("templateId") or "").strip()
    if not template_id:
        return ""
    navigation_type = str(template_contract.get("navigationType") or wireframe_data.get("navigationType") or "").strip()
    template_source = str(template_contract.get("templateSource") or wireframe_data.get("layoutSource") or "").strip()
    template = _TEMPLATE_REGISTRY.get(template_id, {})
    lines = []
    base = f"（custom，base：{esc(template_contract.get('baseTemplateId', ''))}）" if template_id == "custom" else ""
    lines.append(f"templateId：{esc(template_id)}{base}；navigationType：{esc(navigation_type or '-')}")
    if template_source:
        lines.append(f"templateSource：{esc(template_source)}")
    required = template_contract.get("requiredRegions") or template.get("requiredRegions") or []
    if required:
        lines.append(f"模板必需区域：{esc('、'.join(required))}")
    region_order = template_contract.get("regionOrder") or []
    if region_order:
        lines.append(f"区域顺序：{esc('、'.join(region_order))}")
    footer_contract = template.get("footer") or {}
    if footer_contract:
        align = footer_contract.get("alignment") or "-"
        footer_note = f"底部操作契约：对齐方式：{align}（{'必填' if footer_contract.get('required') else '可选'}）"
        button_order = footer_contract.get("buttonOrder") or []
        if button_order:
            footer_note += f"；按钮顺序：{esc('、'.join(footer_button_label(b) for b in button_order))}"
        lines.append(footer_note)
    return f"<div><strong>模板契约</strong>{list_html(lines)}</div>"


def render_page_coding(page):
    guide = page.get("codingGuide", {})
    contract_html = render_template_contract(page)
    if not guide:
        return contract_html + "<p class=\"muted\">暂无页面级Coding指导</p>"
    return contract_html + render_coding_summary(guide, mode="page")


def page_navigation(page, inherited_nav=None):
    nav = page.get("navigation") or {}
    if not nav:
        nav_path = str(page.get("navPath") or "").strip()
        if nav_path:
            parts = [item.strip() for item in nav_path.split("/")]
            nav = {
                "primary": parts[0] if len(parts) > 0 else "",
                "secondary": parts[1] if len(parts) > 1 else "",
                "tertiary": parts[2] if len(parts) > 2 else "",
                "tab": parts[3] if len(parts) > 3 else "",
            }
    if not nav and inherited_nav:
        nav = inherited_nav
    return nav


def normalize_footer_actions(value):
    if isinstance(value, dict):
        actions = value.get("actions") or []
        normalized = []
        for action in actions:
            if isinstance(action, dict):
                label = action.get("label") or action.get("name") or action.get("text") or ""
                kind = action.get("type") or action.get("kind") or ""
                normalized.append(f"{label}{f'（{kind}）' if kind else ''}".strip())
            else:
                normalized.append(str(action))
        return {
            "visible": bool(value.get("visible", bool(actions))),
            "container_type": str(value.get("containerType") or value.get("container") or ""),
            "alignment": str(value.get("alignment") or ""),
            "source": str(value.get("source") or value.get("ruleSource") or ""),
            "actions": normalized,
        }
    if isinstance(value, list):
        return {"visible": bool(value and value != ["无"]), "container_type": "", "alignment": "", "source": "", "actions": [str(item) for item in value]}
    if value:
        return {"visible": True, "container_type": "", "alignment": "", "source": "", "actions": [str(value)]}
    return {"visible": False, "container_type": "", "alignment": "", "source": "", "actions": []}


def render_footer_actions(page):
    footer = normalize_footer_actions(page.get("footerActions", []))
    if not footer["visible"]:
        return "<p class=\"muted\">无</p>"
    meta = []
    if footer["container_type"]:
        meta.append(f"容器：{footer['container_type']}")
    if footer["alignment"]:
        meta.append(f"对齐：{footer['alignment']}")
    if footer["source"]:
        meta.append(f"规则来源：{footer['source']}")
    meta_html = f"<p><strong>布局约束：</strong>{esc('；'.join(meta))}</p>" if meta else ""
    return meta_html + list_html(footer["actions"])


def render_navigation_table(page, inherited_nav=None):
    nav = page_navigation(page, inherited_nav)
    rows = [{
        "primary": nav.get("primary", ""),
        "secondary": nav.get("secondary", ""),
        "tertiary": nav.get("tertiary", ""),
        "tab": nav.get("tab", ""),
    }]
    columns = [("primary", "一级导航"), ("secondary", "二级导航"), ("tertiary", "三级导航"), ("tab", "Tab页面")]
    return table_html(rows, columns)


def render_restore_requirement(page):
    requirement = page.get("restoreRequirement") or page.get("pageTypeRestoreRequirement")
    if not requirement:
        return ""
    if isinstance(requirement, dict):
        parts = ["<h3>页面类型还原要求</h3>"]
        description = requirement.get("description") or requirement.get("requirement") or ""
        if description:
            parts.append(f"<p>{esc(description)}</p>")
        components = normalize_component_rows(requirement.get("components") or requirement.get("componentMapping") or [])
        if components:
            parts.append(table_html(components, [("area", "页面骨架区域"), ("iduxComponent", "组件名称"), ("source", "组件来源"), ("usage", "还原要求")]))
        return "".join(parts)
    if isinstance(requirement, list):
        return f"<h3>页面类型还原要求</h3>{list_html(requirement)}"
    return f"<h3>页面类型还原要求</h3><p>{esc(requirement)}</p>"


def render_wireframe(page):
    wireframe_data = page.get("wireframe") or page.get("asciiWireframe") or ""
    if isinstance(wireframe_data, dict):
        wireframe_text = str(wireframe_data.get("ascii") or wireframe_data.get("text") or "").strip()
        note = str(wireframe_data.get("note") or wireframe_data.get("description") or page.get("wireframeNote") or page.get("wireframeDescription") or "").strip()
        layout_source = str(wireframe_data.get("layoutSource") or "").strip()
        variants = wireframe_data.get("variants") or []
        if not wireframe_text and not note and not layout_source and not variants:
            return ""
        parts = ["<div class=\"wireframe-block\"><h3>Wireframe / ASCII 线框图</h3>"]
        if wireframe_text:
            if len(wireframe_text) < 8:
                parts.append("<p class=\"wireframe-warning\">线框图内容过短，未按页面模板完整绘制，请检查设计说明。</p>")
            parts.append(f"<pre>{esc(wireframe_text)}</pre>")
        if note:
            parts.append(f"<p>{esc(note)}</p>")
        if layout_source:
            parts.append(f"<p><strong>线框图结构依据：</strong>{esc(layout_source)}</p>")
        if variants:
            rendered_variants = [v for v in variants if str((v or {}).get("ascii") or "").strip()]
            if rendered_variants:
                parts.append("<h4>线框变体（Wireframe Variants）</h4>")
                for variant in rendered_variants:
                    vid = esc(str(variant.get("id") or ""))
                    preserve = esc("、".join(variant.get("preserveRegions") or []))
                    changed = esc("、".join(variant.get("changedRegions") or []))
                    var_ascii = esc(str(variant.get("ascii") or "").strip())
                    parts.append(f"<div class=\"variant-block\"><p><strong>变体 {vid}</strong>"
                                 + (f"　保留区域：{preserve}" if preserve else "")
                                 + (f"　变化区域：{changed}" if changed else "") + "</p>")
                    if var_ascii:
                        parts.append(f"<pre>{var_ascii}</pre>")
                    parts.append("</div>")
        parts.append("</div>")
        return "".join(parts)

    wireframe = str(wireframe_data).strip()
    if not wireframe:
        return ""
    note = str(page.get("wireframeNote") or page.get("wireframeDescription") or "").strip()
    note_html = f"<p>{esc(note)}</p>" if note else ""
    return f"<div class=\"wireframe-block\"><h3>Wireframe / ASCII 线框图</h3>{note_html}<pre>{esc(wireframe)}</pre></div>"


def render_page(page, inherited_nav=None):
    sections = []
    for block in page.get("sections", []):
        sections.append(f"""
        <div class="section-block">
          <h3>{esc(block.get('title', '未命名区块'))}</h3>
          <p>{esc(block.get('description', ''))}</p>
          {render_block_detail(block)}
        </div>
        """)
    return f"""
    <section class="page" id="page-{esc(slug(page.get('id', 'page')))}">
      <h1>{esc(page_label(page))}</h1>
      <div class="card"><h2>页面基础信息</h2><dl class="meta-list"><dt>页面目标</dt><dd>{esc(page.get('purpose', ''))}</dd><dt>页面类型</dt><dd>{esc(page.get('type', ''))}</dd><dt>页面布局</dt><dd>{esc(page.get('layout', ''))}</dd></dl>{render_navigation_table(page, inherited_nav)}{render_restore_requirement(page)}</div>
      {render_wireframe(page)}
      <div class="card"><h2>页面内容区块</h2>{''.join(sections)}</div>
      <div class="card"><h2>底部操作</h2>{render_footer_actions(page)}</div>
      <div class="card"><h2>页面级AI Coding指导</h2>{render_page_coding(page)}</div>
    </section>
    """


def page_label(page):
    page_id = page.get("id") or ""
    name = page.get("name") or "未命名页面"
    return f"{page_id}-{name}" if page_id else name


def build_navigation(data, pages):
    entries = ["<div class='nav-section'>总览</div>", "<button class='nav-item active' data-target='overview'>总览</button>"]
    for page, _ in pages:
        entries.append(f"<button class='nav-item nav-indent-1' data-target='page-{esc(slug(page.get('id', 'page')))}'>{esc(page_label(page))}</button>")
    return "\n".join(entries)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--template-registry", default=str(_TEMPLATE_REGISTRY_PATH))
    parser.add_argument("--allow-legacy-wireframe", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    pages = [(page, page.get("navigation")) for page in data.get("pages", [])]

    strict = not args.allow_legacy_wireframe

    validator = Path(__file__).resolve().parent / "validate_demo_spec.py"
    cmd = [sys.executable, str(validator), "--input", str(input_path), "--template-registry", str(args.template_registry)]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    report = {}
    if proc.stdout.strip():
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            report = {}
    validation_ok = bool(report.get("valid", False))
    validation_errors = report.get("errors") or []

    if strict and not validation_ok:
        sys.stderr.write(proc.stdout or "")
        print(json.dumps({"status": "validation_failed", "errorCount": len(validation_errors), "errors": validation_errors}, ensure_ascii=False))
        sys.exit(1)

    legacy = any(isinstance(p.get("wireframe"), str) or isinstance(p.get("asciiWireframe"), str) for p in data.get("pages", []))
    validation_info = {"status": "passed" if validation_ok and not legacy else ("warning" if not strict else "failed"), "legacy": legacy}

    template = Path(__file__).resolve().parents[1] / "assets" / "demo-spec-template.html"
    html_text = template.read_text(encoding="utf-8")
    html_text = html_text.replace("{{TITLE}}", esc(data.get("title", "需求设计说明书")))
    html_text = html_text.replace("{{NAV}}", build_navigation(data, pages))
    html_text = html_text.replace("{{SOURCE_CONTENT}}", render_markdown_source(data, pages))
    html_text = html_text.replace("{{PREVIEW_CONTENT}}", render_preview_content(data, pages, validation_info))
    output_path.write_text(html_text, encoding="utf-8")
    print(json.dumps({"status": "success", "validationStatus": validation_info["status"], "warningCount": report.get("warningCount", 0), "infoCount": report.get("infoCount", 0), "output": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

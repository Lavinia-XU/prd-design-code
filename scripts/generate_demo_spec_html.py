import argparse
import html
import json
from pathlib import Path


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


def list_html(items):
    if not items:
        return "<p class=\"muted\">暂无</p>"
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


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


def render_coding_summary(guide, mode="overview"):
    if not guide:
        guide = {}

    if mode == "page":
        items = guide.get("pageItems") or []
        rows = []
        for item in items:
            if isinstance(item, dict):
                rows.append({
                    "developmentItem": item.get("developmentItem") or item.get("item") or item.get("label") or "",
                    "developmentMode": item.get("developmentMode") or item.get("mode") or item.get("way") or "",
                    "developmentDescription": item.get("developmentDescription") or item.get("description") or item.get("detail") or "",
                })
            else:
                rows.append({"developmentItem": str(item), "developmentMode": "", "developmentDescription": ""})

        parts = []
        if rows:
            parts.append(f"<div><strong>开发项编码指导表</strong>{table_html(rows, [('developmentItem', '开发项'), ('developmentMode', '开发方式'), ('developmentDescription', '开发描述')])}</div>")

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


def render_experience_goal(overview):
    goal = overview.get("experienceGoal")
    if isinstance(goal, dict):
        goals = goal.get("goals") or goal.get("practicalGoals") or []
        scene = goal.get("scene") or goal.get("visualScene") or ""
        return f"""
          <div class="stack">
            <div><strong>目标选项</strong>{list_html(goals)}</div>
            <div><strong>画面感</strong><p>{esc(scene) if scene else '暂无'}</p></div>
          </div>
        """
    if isinstance(goal, list):
        return list_html(goal)
    legacy_goal = overview.get("demoGoal", "")
    if legacy_goal:
        return f"<p>{esc(legacy_goal)}</p>"
    return "<p class=\"muted\">暂无体验目标</p>"


def render_overview(data):
    overview = data.get("overview", {})
    scope_cols = [("task", "需求内容 / 任务"), ("scope", "所属范围"), ("include", "是否进入Demo"), ("handling", "处理方式")]
    page_cols = [("module", "业务模块"), ("id", "页面ID"), ("name", "页面名称"), ("type", "页面类型"), ("purpose", "页面用途"), ("entry", "入口方式"), ("interaction", "关键交互"), ("designSource", "设计来源"), ("codingMode", "编码方式")]
    return f"""
    <section class="page" id="overview">
      <h1>{esc(data.get('title', '需求设计说明书'))}</h1>
      <div class="card"><h2>需求概括</h2><p>{esc(overview.get('summary', ''))}</p></div>
      <div class="card"><h2>体验目标</h2>{render_experience_goal(overview)}</div>
      <div class="card"><h2>Demo范围判断</h2>{table_html(overview.get('scopeTable', []), scope_cols)}</div>
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
                "required": "",
                "default": "",
                "rules": rest.strip() if sep else "",
                "tips": "",
            })
        else:
            rows.append({
                "name": name.strip() if sep else text,
                "display": "",
                "description": rest.strip() if sep else "",
            })
    return rows


def render_block_detail(block):
    details = []
    block_type = str(block.get("type") or block.get("title") or "")
    table_columns = [("name", "字段名称"), ("display", "展示形式"), ("description", "说明")]
    form_columns = [("name", "字段名称"), ("component", "组件类型"), ("required", "必填"), ("default", "默认值"), ("rules", "选项/规则"), ("tips", "提示信息或联动关系")]

    html_text = optional_list_block("工具栏/筛选搜索", block.get("toolbar", []))
    if html_text:
        details.append(html_text)

    filter_mode = block.get("filterMode") or block.get("filterType")
    filter_source = block.get("filterSource")
    filter_fields = block.get("filterFields") or []
    if filter_mode or filter_source or filter_fields:
        filter_intro = []
        if filter_source:
            filter_intro.append(f"筛选方式来源：{esc(filter_source)}")
        if filter_mode:
            filter_intro.append(f"筛选组件类型：{esc(filter_mode)}")
        filter_html = optional_list_block("筛选区说明", filter_intro)
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

    html_text = optional_table_block("表格字段", table_fields, table_columns)
    if html_text:
        details.append(html_text)
    html_text = optional_table_block("表单字段", form_fields, form_columns)
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


def render_page_coding(page):
    guide = page.get("codingGuide", {})
    if not guide:
        return "<p class=\"muted\">暂无页面级Coding指导</p>"
    return render_coding_summary(guide, mode="page")


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
    return f"<h3>页面类型还原要求</h3><p>{esc(requirement)}</p>"


def render_wireframe(page):
    wireframe_data = page.get("wireframe") or page.get("asciiWireframe") or ""
    if isinstance(wireframe_data, dict):
        wireframe_text = str(wireframe_data.get("ascii") or wireframe_data.get("text") or "").strip()
        note = str(wireframe_data.get("note") or wireframe_data.get("description") or page.get("wireframeNote") or page.get("wireframeDescription") or "").strip()
        layout_source = str(wireframe_data.get("layoutSource") or "").strip()
        regions = wireframe_data.get("regions") or []
        if not wireframe_text and not note and not layout_source and not regions:
            return ""
        parts = ["<div class=\"wireframe-block\"><h3>Wireframe / ASCII 线框图</h3>"]
        if note:
            parts.append(f"<p>{esc(note)}</p>")
        if layout_source:
            parts.append(f"<p><strong>线框图结构依据：</strong>{esc(layout_source)}</p>")
        if regions:
            parts.append(table_html(regions, [
                ("区域名称", "name"),
                ("位置", "position"),
                ("内容", "content"),
            ]))
        if wireframe_text:
            parts.append(f"<pre>{esc(wireframe_text)}</pre>")
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
    <section class="page" id="{esc('page-' + slug(page.get('id', '')))}">
      <h1>{esc(page.get('id', ''))}-{esc(page.get('name', '未命名页面'))}</h1>
      <div class="card"><h2>页面目标</h2><p>{esc(page.get('purpose', ''))}</p></div>
      <div class="card"><h2>页面基础信息</h2><dl class="meta-list"><dt>页面类型</dt><dd>{esc(page.get('type', ''))}</dd><dt>页面布局</dt><dd>{esc(page.get('layout', ''))}</dd></dl><h3>导航位置</h3>{render_navigation_table(page, inherited_nav)}{render_restore_requirement(page)}</div>
      <div class="card"><h2>Wireframe / ASCII 线框图</h2>{render_wireframe(page) or '<p class="muted">暂无</p>'}</div>
      <div class="card"><h2>页面内容区块</h2>{''.join(sections) or '<p class="muted">暂无</p>'}</div>
      <div class="card"><h2>底部操作</h2>{list_html(page.get('footerActions', []))}</div>
      <div class="card"><h2>页面级AI Coding指导</h2>{render_page_coding(page)}</div>
    </section>
    """


def flatten_pages(pages, inherited_nav=None):
    result = []
    for page in pages:
        current_nav = page_navigation(page, inherited_nav)
        result.append((page, current_nav))
        result.extend(flatten_pages(page.get("children", []) or [], current_nav))
    return result


def page_label(page):
    page_id = str(page.get("id") or "").strip()
    name = str(page.get("name") or "未命名页面").strip()
    return f"{page_id}-{name}" if page_id else name


def build_page_nav(pages, level=0):
    parts = []
    for page in pages:
        label = page_label(page)
        target = esc("page-" + slug(page.get("id", label)))
        indent = min(level + 1, 4)
        parts.append(f"<button class=\"nav-item nav-indent-{indent}\" data-target=\"{target}\">{esc(label)}</button>")
        children = page.get("children") or []
        if children:
            parts.extend(build_page_nav(children, level + 1))
    return parts


def build_nav(data):
    parts = ["<div class=\"nav-section\">总览</div>", "<button class=\"nav-item\" data-target=\"overview\">总览</button>"]
    parts.append("<div class=\"nav-section\">页面目录</div>")
    parts.extend(build_page_nav(data.get("pages", [])))
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate demo design specification HTML from JSON.")
    parser.add_argument("--input", required=True, help="Path to demo spec JSON file")
    parser.add_argument("--output", required=True, help="Path to output HTML file")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(json.dumps({"status": "error", "message": f"Input file not found: {input_path}"}, ensure_ascii=False))
        return

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {exc}"}, ensure_ascii=False))
        return

    skill_dir = Path(__file__).resolve().parents[1]
    template_path = skill_dir / "assets" / "demo-spec-template.html"
    template = template_path.read_text(encoding="utf-8")

    title = data.get("title") or "需求设计说明书"
    pages = flatten_pages(data.get("pages", []))
    content = render_overview(data) + "\n" + "\n".join(render_page(page, inherited_nav) for page, inherited_nav in pages)
    html_text = template.replace("{{TITLE}}", esc(title)).replace("{{NAV}}", build_nav(data)).replace("{{CONTENT}}", content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    print(json.dumps({"status": "success", "output": str(output_path), "pages": len(pages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

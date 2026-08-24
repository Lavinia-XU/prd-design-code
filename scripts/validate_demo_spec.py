#!/usr/bin/env python3
"""Demo 设计说明书模板契约校验器。

对 Demo JSON 执行 Common Design 模板契约校验，任何模板结构不完整、页面类型不匹配、
组件映射缺失、底部操作区冲突或步骤变体缺失都会阻断 HTML 生成。

用法:
  python3 scripts/validate_demo_spec.py --input demo-spec.json \\
      --template-registry references/02-template-contracts/common-design-template-registry.json \\
      --strict

输出: 结构化 JSON 错误列表（非 0 exit code 表示校验失败）。
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 校验规则登记表（唯一扩展入口）
# ---------------------------------------------------------------------------
# 新增校验规则的固定流程（禁止另建脚本或独立文档）：
#   1. 在 RULES 登记一条（ruleId 唯一、errorCode、来源文档、实现方法、测试）；
#   2. 实现对应 check_xxx 方法，输出统一结构化错误
#      （pageId/errorCode/severity/path/message/expected/actual/sourceRef/fixSuggestion）；
#   3. 在 run() 中按顺序注册调用；
#   4. 在 tests/test_validate_demo_spec.py 补充用例；
#   5. 在 references/01-workflow/05-quality-and-rules.md 登记表中同步一条。
# 模板/数据类规则（requiredRegions、footer、variants、requiredComponents 等）
# 直接维护 references/02-template-contracts/common-design-template-registry.json，
# 无需改动校验代码。
# ---------------------------------------------------------------------------
RULES = [
    {"ruleId": "RULE-01", "errorCode": "SCHEMA_*", "name": "JSON schema 基础结构", "check": "check_schema", "source": "references/01-workflow/01-output-templates.md", "tests": "test_valid_table_basic_passes"},
    {"ruleId": "RULE-02", "errorCode": "DUPLICATE_PAGE_ID", "name": "页面 ID 唯一性", "check": "check_unique_page_ids", "source": "references/01-workflow/01-output-templates.md", "tests": ""},
    {"ruleId": "RULE-03", "errorCode": "OVERVIEW_MISMATCH", "name": "overview.pageOverview 与 pages 一致", "check": "check_overview_consistency", "source": "references/01-workflow/01-output-templates.md", "tests": ""},
    {"ruleId": "RULE-04", "errorCode": "TEMPLATE_NOT_REGISTERED", "name": "templateId 已注册", "check": "check_template_registered", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_unregistered_type_fails"},
    {"ruleId": "RULE-05", "errorCode": "CUSTOM_OVERRIDE_*", "name": "custom 模板 override 完整性", "check": "check_custom_override", "source": "SKILL.md 强制模板契约与线框校验", "tests": "test_custom_without_override_fails, test_valid_override_passes"},
    {"ruleId": "RULE-06", "errorCode": "TYPE_TEMPLATE_MISMATCH", "name": "type 与 templateId 一致", "check": "check_type_template_match", "source": "SKILL.md 强制模板契约与线框校验", "tests": ""},
    {"ruleId": "RULE-07", "errorCode": "UNREGISTERED_TYPE", "name": "禁止未注册页面类型名称", "check": "check_unregistered_type", "source": "SKILL.md 强制模板契约与线框校验", "tests": "test_unregistered_type_fails"},
    {"ruleId": "RULE-08", "errorCode": "NAVIGATION_TYPE_UNSUPPORTED", "name": "navigationType 在模板支持范围", "check": "check_navigation_type", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": ""},
    {"ruleId": "RULE-09", "errorCode": "REQUIRED_REGION_MISSING", "name": "必需页面骨架区块存在", "check": "check_skeleton_regions", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_missing_title_bar_fails, test_missing_pagination_fails"},
    {"ruleId": "RULE-10", "errorCode": "WIREFRAME_REGION_MISSING", "name": "requiredRegions 全部出现在 wireframe.regions", "check": "check_skeleton_regions", "source": "references/01-workflow/03-demo-design-spec.md 结构化线框契约", "tests": "test_missing_pagination_fails"},
    {"ruleId": "RULE-11", "errorCode": "REGION_ORDER_MISMATCH", "name": "regionOrder 与模板顺序一致", "check": "check_region_order", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": ""},
    {"ruleId": "RULE-12", "errorCode": "REQUIRED_COMPONENT_MISSING", "name": "requiredComponents 已声明", "check": "check_required_components", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_stepper_uses_tabs_fails"},
    {"ruleId": "RULE-13", "errorCode": "SECTION_MISSING_IN_WIREFRAME / WIREFRAME_REGION_NO_BASIS", "name": "sections 与 wireframe.regions 双向一致", "check": "check_section_wireframe_consistency", "source": "SKILL.md 强制模板契约与线框校验", "tests": "test_section_wireframe_mismatch_fails"},
    {"ruleId": "RULE-14", "errorCode": "TABLE_REGION_MISSING / TABLE_SEMANTIC_MISSING", "name": "table 页面含 Toolbar/Table/Pagination", "check": "check_table_semantics", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_missing_pagination_fails, test_table_page_as_card_fails"},
    {"ruleId": "RULE-15", "errorCode": "MODAL_*", "name": "modal 页面含外壳/关闭入口/底部操作", "check": "check_modal_semantics", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_modal_missing_close_fails"},
    {"ruleId": "RULE-16", "errorCode": "DRAWER_*", "name": "drawer 页面含外壳/对象上下文/列表/关闭入口", "check": "check_drawer_semantics", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_drawer_footer_alignment_fails"},
    {"ruleId": "RULE-17", "errorCode": "STEPPER_MISSING", "name": "stepper 页面含 Stepper", "check": "check_stepper_semantics", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_stepper_uses_tabs_fails"},
    {"ruleId": "RULE-18", "errorCode": "STEP_VARIANT_MISSING", "name": "多步骤页面含主结构图与每步变体", "check": "check_step_variants", "source": "SKILL.md 强制模板契约与线框校验", "tests": "test_multi_step_missing_variants_fails"},
    {"ruleId": "RULE-19", "errorCode": "VARIANT_SHELL_NOT_PRESERVED", "name": "变体保留公共页面外壳", "check": "check_variant_shell_preserved", "source": "SKILL.md 强制模板契约与线框校验", "tests": "test_multi_step_missing_variants_fails"},
    {"ruleId": "RULE-20", "errorCode": "FOOTER_ALIGNMENT_MISMATCH", "name": "footerActions 与模板对齐规则一致", "check": "check_footer_alignment", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_drawer_footer_alignment_fails, test_form_config_footer_right_fails"},
    {"ruleId": "RULE-21", "errorCode": "FOOTER_ORDER_MISMATCH", "name": "footerActions 按钮顺序一致", "check": "check_footer_button_order", "source": "references/02-template-contracts/common-design-template-registry.json", "tests": "test_form_config_footer_right_fails"},
    {"ruleId": "RULE-22", "errorCode": "WIREFRAME_CONTENT_MISMATCH", "name": "wireframe 与页面内容区块一致", "check": "check_wireframe_content_consistency", "source": "SKILL.md 强制模板契约与线框校验", "tests": ""},
    {"ruleId": "RULE-23", "errorCode": "CODING_ITEM_ID_MISSING", "name": "codingGuide 含稳定开发项 ID", "check": "check_coding_item_ids", "source": "references/01-workflow/04-interaction-coding-guidelines.md", "tests": ""},
    {"ruleId": "RULE-24", "errorCode": "PATH_WITHOUT_VERIFY", "name": "partial/unavailable 时 target.path 为空", "check": "check_path_without_verify", "source": "SKILL.md 代码可用状态", "tests": "test_partial_path_not_empty_fails"},
    {"ruleId": "RULE-25", "errorCode": "VUE3_SYNTAX", "name": "禁止 Vue3 专属绑定语法作为实现要求", "check": "check_vue3_syntax", "source": "references/01-workflow/04-interaction-coding-guidelines.md", "tests": ""},
    {"ruleId": "RULE-26", "errorCode": "COMPONENT_MAPPING_MISSING", "name": "非普通文本字段声明组件映射", "check": "check_component_mapping", "source": "references/01-workflow/03-demo-design-spec.md", "tests": ""},
    {"ruleId": "RULE-27", "errorCode": "LEGACY_WIREFRAME", "name": "legacy 自由文本线框兼容模式", "check": "check_legacy_wireframe", "source": "SKILL.md 强制模板契约与线框校验（兼容模式）", "tests": "test_legacy_wireframe_warning_non_strict"},
    {"ruleId": "RULE-28", "errorCode": "MANIFEST_* / ORPHAN_CONTAINER", "name": "页面清单闭环：总览确认页面/容器与 pages（含 children）完整一致", "check": "check_manifest_closure", "source": "references/01-workflow/03-demo-design-spec.md 设计闭环", "tests": "test_manifest_page_missing_fails, test_orphan_container_warns"},
    {"ruleId": "RULE-29", "errorCode": "OPERATION_*", "name": "操作目标闭环：open-container 目标存在、容器类型正确、高影响操作二次确认", "check": "check_operation_closure", "source": "references/01-workflow/03-demo-design-spec.md 设计闭环", "tests": "test_operation_target_missing_fails, test_operation_confirm_missing_fails"},
    {"ruleId": "RULE-30", "errorCode": "TABS_*", "name": "Tab 变体闭环：多内容 Tab 页面强制完整变体、公共外壳与内容区、sections 绑定 tabId", "check": "check_tab_variants", "source": "references/01-workflow/03-demo-design-spec.md 设计闭环", "tests": "test_tabs_missing_variants_fails, test_tabs_variant_count_mismatch_fails, test_tabs_orphan_variant_fails, test_tabs_variant_no_shell_fails, test_tabs_variant_no_content_fails"},
    {"ruleId": "RULE-31", "errorCode": "CODING_CLOSURE_*", "name": "页面级 Coding 闭环：pageContext 一致、每页至少一个开发项、无孤立开发项", "check": "check_coding_closure", "source": "references/01-workflow/03-demo-design-spec.md 设计闭环", "tests": "test_coding_page_context_mismatch_fails, test_coding_no_items_fails"},
    {"ruleId": "RULE-32", "errorCode": "WIREFRAME_ASCII_TOO_SHORT / WIREFRAME_ASCII_NOT_DRAWN", "name": "线框图绘制质量：ascii 必须按模板绘制，禁止只有几个字或一句话", "check": "check_wireframe_drawing_quality", "source": "references/01-workflow/03-demo-design-spec.md 设计闭环", "tests": "test_ascii_too_short_fails, test_ascii_not_drawn_fails"},
    {"ruleId": "RULE-33", "errorCode": "WIREFRAME_REGION_NOT_DRAWN", "name": "线框图双向一致性：regions 声明的内容性区块必须在 ascii 中有绘制痕迹", "check": "check_wireframe_region_drawn", "source": "references/01-workflow/03-demo-design-spec.md 设计闭环", "tests": "test_ascii_region_not_drawn_warns"},
]

# 页面 type（中文）与标准模板的映射
TYPE_TEMPLATE_MAP = {
    "基础表格页": "page-table-basic",
    "左树表格页": "page-table-tree",
    "概览表格页": "page-table-overview",
    "概览左树表格页": "page-table-overview-tree",
    "弹窗列表页": "page-list-modal",
    "抽屉列表页": "page-list-drawer",
    "下钻详情页": "page-detail-drilldown",
    "抽屉详情页": "page-detail-drawer",
    "日志详情页": "page-detail-log",
    "配置表单页": "page-form-config",
    "步骤条配置页": "page-form-stepper",
    "弹窗表单页": "page-form-modal",
    "抽屉表单页": "page-form-drawer",
    "仪表盘页": "page-dashboard",
}

# 模板区域关键词别名（中英文），用于 region 语义匹配
REGION_ALIASES = {
    "global-navigation": ["global", "navigation", "导航", "侧边栏", "侧栏"],
    "title-bar": ["title", "标题", "返回入口", "页头"],
    "filter": ["filter", "筛选", "搜索区", "查询区"],
    "toolbar": ["toolbar", "工具栏", "操作栏", "工具条"],
    "table": ["table", "表格", "列表主体", "数据列表"],
    "pagination": ["pagination", "分页"],
    "tree": ["tree", "树", "左树"],
    "overview": ["overview", "概览", "统计", "指标", "汇总"],
    "modal-shell": ["modal", "弹窗", "dialog", "对话框"],
    "modal-header": ["modal", "header", "弹窗标题", "标题栏"],
    "modal-footer": ["modal", "footer", "底部", "确认", "取消", "弹窗底部"],
    "drawer-shell": ["drawer", "抽屉"],
    "drawer-header": ["drawer", "header", "抽屉标题", "标题栏"],
    "drawer-footer": ["drawer", "footer", "底部", "确认", "取消", "抽屉底部"],
    "object-context": ["object", "context", "对象上下文", "上下文", "所属对象"],
    "object-summary": ["object", "summary", "摘要", "对象信息", "基本信息"],
    "object-info": ["object", "info", "对象信息", "基本信息", "信息卡"],
    "detail-content": ["detail", "详情", "详情内容", "内容区"],
    "action-area": ["action", "操作区", "操作入口"],
    "log-filter": ["log", "filter", "日志", "筛选", "时间范围"],
    "log-content": ["log", "日志", "时间线", "timeline", "日志内容"],
    "form-content": ["form", "表单", "配置项", "字段区"],
    "stepper": ["stepper", "步骤", "步骤条"],
    "step-content": ["step", "步骤内容", "当前步骤"],
    "dashboard-content": ["dashboard", "仪表", "看板", "图表"],
    "footer": ["footer", "底部", "底部操作区", "底部按钮"],
}

# Vue 3 专属绑定语法（不得作为实现要求出现）
VUE3_PATTERNS = [
    "v-model", "v-if", "v-for", "v-show", "v-else", "v-bind",
    "@click", "@change", "@input", "@submit", ":disabled",
    ":visible", ":loading", ":data", ":model", ":options", ":columns",
]


def norm(text):
    return re.sub(r"[-_/\\\s]", "", str(text).lower())


def region_text(region):
    if not isinstance(region, dict):
        return ""
    parts = [region.get("id", ""), region.get("templateRegion", ""),
             region.get("position", ""), region.get("content", ""),
             region.get("component", "")]
    return " ".join(str(p) for p in parts).lower()


def region_matches(region, template_region):
    """region 是否对应模板区域（按别名分词匹配）。"""
    text = region_text(region)
    for alias in REGION_ALIASES.get(template_region, [template_region]):
        if alias.lower() in text:
            return True
    return False


def has_semantic(regions, keywords):
    """regions 文本中是否出现任一关键词。"""
    text = " ".join(region_text(r) for r in regions)
    return any(k.lower() in text for k in keywords)


REGION_ASCII_KEYS = {
    # 模板区域 -> ascii 线框图中应出现的绘制痕迹关键词（用于检查线框图是否按模板绘制）
    "global-navigation": ["导航", "侧边栏", "菜单", "global"],
    "title-bar": ["标题", "页头", "返回", "title"],
    "toolbar": ["工具栏", "操作栏", "toolbar"],
    "filter": ["筛选", "查询", "filter"],
    "table": ["表格", "列表", "table"],
    "pagination": ["分页", "上一页", "下一页", "pagination"],
    "form": ["表单", "form"],
    "form-content": ["表单", "form"],
    "modal-header": ["弹窗标题", "标题", "关闭"],
    "modal-footer": ["确定", "取消", "底部"],
    "drawer-header": ["标题", "关闭"],
    "object-summary": ["摘要", "概览", "上下文", "summary"],
    "object-context": ["摘要", "上下文", "context"],
    "tab-bar": ["tab", "标签页", "页签"],
    "tab-content": ["内容", "content"],
    "stepper": ["步骤", "stepper"],
    "step-content": ["步骤", "内容"],
    "footer": ["底部", "确定", "取消", "上一步", "下一步"],
    "drawer-footer": ["确定", "取消", "底部"],
    "overview": ["概览", "统计", "overview"],
    "detail-content": ["详情", "detail"],
    "tree": ["树", "tree"],
    "search": ["搜索", "search"],
}

# ascii 线框图绘制完整性检查中跳过纯结构外壳区域（无文字标签预期，避免误报）
DRAWING_SKIP_REGIONS = {
    "global-navigation", "modal-shell", "drawer-shell", "shell",
}


def walk_text(obj):
    """提取对象中所有字符串文本（用于 Vue3 语法与组件扫描）。"""
    texts = []
    if isinstance(obj, str):
        texts.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            texts.extend(walk_text(v))
    elif isinstance(obj, list):
        for v in obj:
            texts.extend(walk_text(v))
    return texts


def _walk_pages(pages, base_path="$.pages"):
    """递归展开 pages 及其 children，产出 (page, json_path) 序列（设计闭环用）。"""
    for i, page in enumerate(pages or []):
        path = f"{base_path}[{i}]"
        yield page, path
        yield from _walk_pages(page.get("children") or [], f"{path}.children")


# 操作目标闭环：已知操作类型（尽可能结构化）
KNOWN_ACTIONS = {
    "open-container", "confirm", "download", "refresh", "delete",
    "batch-delete", "disable", "enable", "revoke", "submit",
    "navigate", "close", "other",
}
# 高影响操作：必须配置二次确认
HIGH_RISK_ACTIONS = {"delete", "batch-delete", "disable", "enable", "revoke"}
# Tab 变体闭环：公共页面外壳区域关键词（preserveRegions 必须至少保留其一）
SHELL_REGION_KEYS = (
    "global-navigation", "global-nav", "title-bar", "page-shell",
    "drawer-shell", "drawer-header", "modal-shell", "modal-header",
    "object-summary", "object-context", "footer", "stepper",
    "tab-bar", "tabs", "content-container",
)


class Validator:
    def __init__(self, data, registry, strict=True):
        self.data = data
        self.registry = registry
        self.strict = strict
        self.errors = []
        self.page_ids = set()

    def add_error(self, page_id, code, severity, path, message,
                  expected, actual, source_ref="", fix=""):
        self.errors.append({
            "pageId": page_id,
            "errorCode": code,
            "severity": severity,
            "path": path,
            "message": message,
            "expected": expected,
            "actual": actual,
            "sourceRef": source_ref,
            "fixSuggestion": fix,
        })

    def page_template(self, page):
        """获取页面 templateId（templateContract > wireframe > page 级）。"""
        tc = page.get("templateContract") or {}
        wf = page.get("wireframe") or {}
        return (tc.get("templateId") or wf.get("templateId") or "").strip()

    def page_nav_type(self, page):
        tc = page.get("templateContract") or {}
        wf = page.get("wireframe") or {}
        return (tc.get("navigationType") or wf.get("navigationType") or "").strip()

    def page_wireframe(self, page):
        return page.get("wireframe")

    def page_sections(self, page):
        return page.get("sections") or []

    def page_footer_actions(self, page):
        return page.get("footerActions") or []

    # ---- 校验项 ----
    def check_schema(self):
        if not isinstance(self.data, dict):
            self.add_error("-", "JSON_SCHEMA", "error", "$", "顶层必须是 JSON 对象",
                           "object", type(self.data).__name__, fix="提供合法 Demo JSON")
            return
        for key in ("title", "overview", "pages"):
            if key not in self.data:
                self.add_error("-", "JSON_SCHEMA", "error", f"$.{key}",
                               f"缺少必需字段 {key}", f"存在 {key}", "缺失",
                               fix=f"补充 {key} 字段")
        if not isinstance(self.data.get("pages"), list):
            self.add_error("-", "JSON_SCHEMA", "error", "$.pages",
                           "pages 必须是数组", "array", type(self.data.get("pages")).__name__)

    def check_unique_page_ids(self):
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            if not pid:
                self.add_error("-", "PAGE_ID_MISSING", "error", f"{path}.id",
                               "页面缺少 id", "非空 id", "空",
                               fix="为每个页面补充唯一 id")
            elif pid in self.page_ids:
                self.add_error(pid, "DUPLICATE_PAGE_ID", "error", f"{path}.id",
                               f"页面 id 重复: {pid}", "唯一 id", f"重复 {pid}",
                               fix="修改为唯一 id")
            else:
                self.page_ids.add(pid)

    def check_overview_consistency(self):
        overview = self.data.get("overview") or {}
        page_overview = overview.get("pageOverview") or []
        overview_ids = {str(p.get("id", "")) for p in page_overview if p.get("id")}
        page_ids = {str(p.get("id", "")) for p, _ in self.all_pages if p.get("id")}
        if overview_ids != page_ids:
            self.add_error("-", "OVERVIEW_MISMATCH", "error", "$.overview.pageOverview",
                           "overview.pageOverview 与 pages（含 children）不一致",
                           f"页面 id 集合 {sorted(page_ids)}",
                           f"总览 id 集合 {sorted(overview_ids)}",
                           fix="同步 overview.pageOverview 与 pages")

    def check_template_registered(self):
        templates = self.registry.get("templates", {})
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            tid = self.page_template(page)
            if not tid:
                self.add_error(pid, "TEMPLATE_NOT_BOUND", "error", f"$.pages[{self._idx(page)}].templateContract.templateId",
                               "页面未绑定标准页面模板，不允许只写业务自定义名称",
                               "已注册 templateId", "空",
                               source_ref=self.registry.get("sourceBase", ""),
                               fix="绑定标准 templateId 或使用 custom 模板并填写 override")
            elif tid == "custom":
                self.check_custom_override(page)
            elif tid not in templates:
                self.add_error(pid, "TEMPLATE_NOT_REGISTERED", "error",
                               f"$.pages[{self._idx(page)}].templateContract.templateId",
                               f"templateId 未注册: {tid}", f"已注册模板 {sorted(templates)}",
                               tid, source_ref=self.registry.get("sourceBase", ""),
                               fix="使用注册表中的 templateId 或 custom 模板")

    def check_custom_override(self, page):
        pid = page.get("id", "")
        tc = page.get("templateContract") or {}
        base = tc.get("baseTemplateId", "")
        override = tc.get("override") or {}
        if not base or base not in self.registry.get("templates", {}):
            self.add_error(pid, "CUSTOM_BASE_MISSING", "error",
                           f"$.pages[{self._idx(page)}].templateContract.baseTemplateId",
                           "custom 模板必须指定已注册的 baseTemplateId",
                           "已注册 baseTemplateId", base or "空",
                           source_ref=self.registry.get("sourceBase", ""),
                           fix="填写 baseTemplateId 指向某个标准模板")
        if not override.get("enabled"):
            self.add_error(pid, "CUSTOM_OVERRIDE_MISSING", "error",
                           f"$.pages[{self._idx(page)}].templateContract.override",
                           "custom 模板必须启用 override", "override.enabled=true", "false",
                           fix="启用 override 并填写覆盖来源与理由")
        for key in ("source", "reason"):
            if not override.get(key):
                self.add_error(pid, "CUSTOM_OVERRIDE_INCOMPLETE", "error",
                               f"$.pages[{self._idx(page)}].templateContract.override.{key}",
                               f"custom 模板缺少 override.{key}", f"非空 {key}",
                               str(override.get(key, "")),
                               fix=f"填写 override.{key}（用户确认/PRD/Product Design/已有代码）")
        if not override.get("affectedRules"):
            self.add_error(pid, "CUSTOM_OVERRIDE_INCOMPLETE", "error",
                           f"$.pages[{self._idx(page)}].templateContract.override.affectedRules",
                           "custom 模板缺少 override.affectedRules",
                           "被覆盖的模板约束列表", "空",
                           fix="列出被覆盖的具体模板约束")

    def check_type_template_match(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            ptype = str(page.get("type", ""))
            tid = self.page_template(page)
            expected = TYPE_TEMPLATE_MAP.get(ptype)
            if ptype and expected and tid != "custom" and expected != tid:
                self.add_error(pid, "TYPE_TEMPLATE_MISMATCH", "error",
                               f"$.pages[{self._idx(page)}].type",
                               f"页面 type 与 templateId 不一致: {ptype}",
                               expected, tid,
                               source_ref=self.registry.get("sourceBase", ""),
                               fix=f"将 templateId 改为 {expected} 或将 type 与模板匹配")

    def check_unregistered_type(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            ptype = str(page.get("type", ""))
            tid = self.page_template(page)
            if ptype and ptype not in TYPE_TEMPLATE_MAP and tid != "custom" and tid:
                self.add_error(pid, "UNREGISTERED_TYPE", "error",
                               f"$.pages[{self._idx(page)}].type",
                               f"使用了未注册页面类型名称: {ptype}",
                               f"已注册类型 {sorted(TYPE_TEMPLATE_MAP)}", ptype,
                               source_ref=self.registry.get("sourceBase", ""),
                               fix="改用已注册页面类型，或使用 custom 模板并填写 override")

    def check_navigation_type(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            if not template:
                continue
            nav = self.page_nav_type(page)
            supported = template.get("navigationTypes") or []
            if not supported:
                continue
            if nav and nav not in supported:
                self.add_error(pid, "NAVIGATION_TYPE_UNSUPPORTED", "error",
                               f"$.pages[{self._idx(page)}].templateContract.navigationType",
                               f"navigationType 不在模板支持范围: {nav}",
                               f"支持 {supported}", nav,
                               source_ref=template.get("source", ""),
                               fix=f"改为 {supported} 之一，或使用 custom 模板覆盖")

    def check_skeleton_regions(self):
        """必需页面骨架区块是否存在（wireframe.regions 或 templateContract 声明）。"""
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            if not template:
                continue
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            for req in template.get("requiredRegions", []):
                if not any(region_matches(r, req) for r in regions):
                    self.add_error(pid, "REQUIRED_REGION_MISSING", "error",
                                   f"$.pages[{self._idx(page)}].wireframe.regions",
                                   f"必需页面骨架区块缺失: {req}",
                                   f"wireframe 包含 {req}", "缺失",
                                   source_ref=template.get("source", ""),
                                   fix=f"在 wireframe.regions 中补充 {req} 区块")

    def check_region_order(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            if not template:
                continue
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            order = template.get("requiredRegions", [])
            # 取 wireframe regions 中能匹配模板区域的顺序
            matched = []
            for r in regions:
                for req in order:
                    if region_matches(r, req) and req not in matched:
                        matched.append(req)
                        break
            expected_order = [o for o in order if o in matched]
            if matched != expected_order:
                self.add_error(pid, "REGION_ORDER_MISMATCH", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "regionOrder 与模板顺序不一致",
                               " → ".join(expected_order), " → ".join(matched),
                               source_ref=template.get("source", ""),
                               fix="按模板 requiredRegions 顺序排列 wireframe.regions")

    def check_required_components(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            if not template:
                continue
            required_components = template.get("requiredComponents", {})
            if not required_components:
                continue
            declared = self._declared_component_text(page)
            for region, comps in required_components.items():
                for comp in comps:
                    if comp not in declared:
                        self.add_error(pid, "REQUIRED_COMPONENT_MISSING", "error",
                                       f"$.pages[{self._idx(page)}].restoreRequirement / componentContract",
                                       f"模板必需组件未声明: {region} -> {comp}",
                                       f"声明 {comp}", "缺失",
                                       source_ref=template.get("source", ""),
                                       fix=f"在 restoreRequirement 或 componentContract 中声明 {comp}")

    def _declared_component_text(self, page):
        texts = []
        rr = page.get("restoreRequirement") or {}
        texts.extend(walk_text(rr))
        tc = page.get("templateContract") or {}
        texts.extend(walk_text(tc.get("componentContract") or {}))
        texts.extend(walk_text(page.get("components") or {}))
        return " ".join(texts)

    def check_section_wireframe_consistency(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            sections = self.page_sections(page)
            # 方向 A: wireframe 区域必须有模板依据
            if regions:
                for r in regions:
                    rid = str(r.get("id", ""))
                    if not r.get("templateRegion") and not any(
                            region_matches(r, req) for req in (template or {}).get("requiredRegions", [])):
                        self.add_error(pid, "WIREFRAME_REGION_NO_BASIS", "error",
                                       f"$.pages[{self._idx(page)}].wireframe.regions[{rid}]",
                                       f"wireframe 区块 {rid} 没有 sections 或 templateContract 依据",
                                       "templateRegion 或模板区域", "无依据",
                                       fix="为该区块标注 templateRegion 或补充 templateContract 依据")
            # 方向 B: sections 必需区块出现在 wireframe
            for s in sections:
                title = str(s.get("title", ""))
                if not title:
                    continue
                # 跳过纯文本区块（普通描述区块不强制出现在线框）
                if not any(k in title for k in ("列表", "表格", "筛选", "工具栏", "操作", "弹窗", "抽屉",
                                                "表单", "步骤", "概览", "详情", "分页", "树", "日志", "卡片")):
                    continue
                if not any(title in region_text(r) or any(k in region_text(r) for k in
                                                         [title[:2], title[-2:]] if len(title) >= 2)
                           for r in regions):
                    self.add_error(pid, "SECTION_MISSING_IN_WIREFRAME", "error",
                                   f"$.pages[{self._idx(page)}].sections",
                                   f"sections 声明的区块 {title} 未出现在 wireframe",
                                   f"wireframe 包含 {title}", "缺失",
                                   fix=f"在 wireframe.regions 或 ascii 中补充 {title} 区块")

    def check_table_semantics(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            if not tid or not tid.startswith(("page-table", "page-list")):
                continue
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            checks = [("toolbar", ["toolbar", "工具栏", "操作栏"]),
                      ("table", ["table", "表格", "列表"]),
                      ("pagination", ["pagination", "分页"])]
            for name, keys in checks:
                if not has_semantic(regions, keys):
                    self.add_error(pid, "TABLE_REGION_MISSING", "error",
                                   f"$.pages[{self._idx(page)}].wireframe.regions",
                                   f"表格类页面缺少 {name} 区块", f"包含 {name}", "缺失",
                                   source_ref=self.registry.get("templates", {}).get(tid, {}).get("source", ""),
                                   fix=f"在 wireframe.regions 中补充 {name}")

    def check_modal_semantics(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            if not tid or not tid.endswith(("modal",)):
                continue
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            if not has_semantic(regions, ["modal", "弹窗", "dialog"]):
                self.add_error(pid, "MODAL_SHELL_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "弹窗类页面缺少 Modal 外壳", "包含 modal 外壳", "缺失",
                               fix="在 wireframe 中补充 modal-shell 区域")
            if not has_semantic(regions, ["close", "关闭", "取消"]):
                self.add_error(pid, "MODAL_CLOSE_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "弹窗类页面缺少关闭入口", "包含关闭入口", "缺失",
                               fix="在 wireframe 中补充关闭入口")
            if not has_semantic(regions, ["footer", "底部", "确认", "取消"]):
                self.add_error(pid, "MODAL_FOOTER_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "弹窗类页面缺少底部操作", "包含底部操作", "缺失",
                               fix="在 wireframe 中补充 modal-footer 底部操作区")

    def check_drawer_semantics(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            if not tid or "drawer" not in tid:
                continue
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            if not has_semantic(regions, ["drawer", "抽屉"]):
                self.add_error(pid, "DRAWER_SHELL_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "抽屉类页面缺少 Drawer 外壳", "包含 drawer 外壳", "缺失",
                               fix="在 wireframe 中补充 drawer-shell 区域")
            if tid.startswith("page-list-") and not has_semantic(regions, ["object", "上下文", "对象"]):
                self.add_error(pid, "DRAWER_OBJECT_CONTEXT_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "抽屉列表页缺少对象上下文", "包含对象上下文", "缺失",
                               fix="在 wireframe 中补充 object-context 区域")
            if not has_semantic(regions, ["close", "关闭", "取消"]):
                self.add_error(pid, "DRAWER_CLOSE_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "抽屉类页面缺少关闭入口", "包含关闭入口", "缺失",
                               fix="在 wireframe 中补充关闭入口")
            if tid.startswith("page-list-") and not has_semantic(regions, ["table", "表格", "列表"]):
                self.add_error(pid, "DRAWER_LIST_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "抽屉列表页缺少列表主体", "包含列表主体", "缺失",
                               fix="在 wireframe 中补充 table 区域")

    def check_stepper_semantics(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            if tid != "page-form-stepper":
                continue
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            if not has_semantic(regions, ["stepper", "步骤"]):
                self.add_error(pid, "STEPPER_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "步骤条配置页缺少 Stepper", "包含 stepper 区域", "缺失",
                               fix="在 wireframe 中补充 stepper 区域（IxStepper）")

    def check_step_variants(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            if not template or not template.get("variants", {}).get("required"):
                continue
            wf = self.page_wireframe(page)
            variants = (wf or {}).get("variants") or [] if isinstance(wf, dict) else []
            if not variants:
                self.add_error(pid, "STEP_VARIANT_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.variants",
                               "多步骤页面缺少步骤变体图",
                               "主结构图 + 每个步骤一张完整变体图", "无变体",
                               source_ref=template.get("source", ""),
                               fix="为每个步骤补充完整 wireframe 变体（preserveRegions + changedRegions + ascii）")

    def check_variant_shell_preserved(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            variants = (wf or {}).get("variants") or [] if isinstance(wf, dict) else []
            for i, v in enumerate(variants):
                preserved = v.get("preserveRegions") or []
                changed = v.get("changedRegions") or []
                if not preserved:
                    self.add_error(pid, "VARIANT_SHELL_NOT_PRESERVED", "error",
                                   f"$.pages[{self._idx(page)}].wireframe.variants[{i}].preserveRegions",
                                   f"变体 {v.get('id', i)} 未声明保留的公共页面外壳",
                                   "preserveRegions 非空", "空",
                                   fix="声明变体保留的公共外壳区域（如 title-bar/stepper/footer）")
                # 变体不应同时保留又修改同一区域
                overlap = set(preserved) & set(changed)
                if overlap:
                    self.add_error(pid, "VARIANT_REGION_CONFLICT", "error",
                                   f"$.pages[{self._idx(page)}].wireframe.variants[{i}]",
                                   f"变体 {v.get('id', i)} 的区域同时出现在 preserveRegions 与 changedRegions: {sorted(overlap)}",
                                   "区域互斥", "重叠",
                                   fix="调整 preserveRegions 与 changedRegions 使区域不重叠")

    def check_footer_alignment(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            footer_contract = (template or {}).get("footer", {})
            if not footer_contract.get("required"):
                continue
            tc = page.get("templateContract") or {}
            declared_alignment = (tc.get("footerContract") or {}).get("alignment", "")
            expected_alignment = footer_contract.get("alignment", "")
            override = tc.get("override") or {}
            if declared_alignment and expected_alignment and \
                    declared_alignment != expected_alignment and not override.get("enabled"):
                self.add_error(pid, "FOOTER_ALIGNMENT_MISMATCH", "error",
                               f"$.pages[{self._idx(page)}].templateContract.footerContract.alignment",
                               f"footer 对齐方式与模板不一致: {declared_alignment}",
                               expected_alignment, declared_alignment,
                               source_ref=template.get("source", ""),
                               fix=f"改为 {expected_alignment}，或启用 override 并填写覆盖来源")

    def check_footer_button_order(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self.registry.get("templates", {}).get(tid)
            footer_contract = (template or {}).get("footer", {})
            expected_order = footer_contract.get("buttonOrder") or []
            if not expected_order:
                continue
            actions = self.page_footer_actions(page)
            if not actions:
                continue
            actual_kinds = [self._action_kind(a) for a in actions]
            actual_kinds = [k for k in actual_kinds if k]
            expected_kinds = [k for k in expected_order if k in actual_kinds]
            if actual_kinds != expected_kinds:
                self.add_error(pid, "FOOTER_BUTTON_ORDER_MISMATCH", "error",
                               f"$.pages[{self._idx(page)}].footerActions",
                               f"footerActions 按钮顺序与模板不一致",
                               " → ".join(expected_kinds), " → ".join(actual_kinds),
                               source_ref=template.get("source", ""),
                               fix="按模板 buttonOrder 调整按钮顺序")

    def _action_kind(self, action):
        if isinstance(action, str):
            text = action
        elif isinstance(action, dict):
            text = " ".join(str(v) for v in action.values())
        else:
            return ""
        text = str(text).lower()
        mapping = [("previous", ["上一步", "previous"]),
                   ("next-or-complete", ["下一步", "完成", "next", "提交"]),
                   ("cancel", ["取消", "cancel"]),
                   ("confirm", ["确定", "确认", "保存", "confirm", "ok"]),
                   ("close", ["关闭", "close"])]
        for kind, keys in mapping:
            if any(k in text for k in keys):
                return kind
        return ""

    def check_wireframe_content_consistency(self):
        """线框中的返回/关闭/分页/筛选/工具栏与页面内容区块一致。"""
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii", "")).lower()
            regions = wf.get("regions") or []
            sections = self.page_sections(page)
            section_text = " ".join(walk_text(sections)).lower()
            checks = [
                ("返回", ["返回", "back"], ["title", "标题", "返回"]),
                ("分页", ["分页", "pagination"], ["分页", "pagination", "table", "表格"]),
                ("筛选", ["筛选", "查询"], ["筛选", "查询", "filter"]),
                ("工具栏", ["工具栏", "操作栏"], ["工具栏", "操作栏", "toolbar"]),
            ]
            for label, ascii_keys, region_keys in checks:
                if any(k in ascii_text for k in ascii_keys):
                    ok = has_semantic(regions, region_keys) or any(k in section_text for k in ascii_keys)
                    if not ok:
                        self.add_error(pid, "WIREFRAME_CONTENT_MISMATCH", "error",
                                       f"$.pages[{self._idx(page)}].wireframe.ascii",
                                       f"线框出现 {label} 交互，但页面内容区块未声明对应区块",
                                       f"存在 {label} 区块", "缺失",
                                       fix=f"在 sections 或 wireframe.regions 中声明 {label} 区块")

    def check_wireframe_drawing_quality(self):
        """RULE-32 线框图绘制质量：ascii 必须按模板绘制，禁止只有几个字或一句话。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "").strip()
            path = f"$.pages[{self._idx(page)}].wireframe.ascii"
            if len(ascii_text) < 8:
                self.add_error(pid, "WIREFRAME_ASCII_TOO_SHORT", "error", path,
                               "线框图内容过短，未按页面模板绘制完整结构",
                               "包含标题栏、内容区、底部操作等区块的字符画", f"仅 {len(ascii_text)} 个字符",
                               fix="按模板 requiredRegions 绘制完整 ASCII 线框图，禁止用一句话替代")
                continue
            tid = self.page_template(page)
            template = (self.registry.get("templates") or {}).get(tid) or {}
            required = template.get("requiredRegions") or []
            if not required:
                continue
            matched_regions = []
            for req in required:
                keys = REGION_ASCII_KEYS.get(req, [])
                if any(k in ascii_text for k in keys):
                    matched_regions.append(req)
            if len(matched_regions) < 2:
                self.add_error(pid, "WIREFRAME_ASCII_NOT_DRAWN", "error", path,
                               f"线框图未按模板 {tid} 绘制（应覆盖标题栏/内容区/底部操作等区域）",
                               f"ascii 中出现 {len(matched_regions)} 个模板区域的绘制痕迹（{', '.join(matched_regions) or '无'}）",
                               "至少 2 个模板必需区域有绘制痕迹",
                               fix=f"参考模板 {tid} 的 requiredRegions，绘制包含标题栏、内容区、底部操作区的 ASCII 线框图")

    def check_wireframe_region_drawn(self):
        """RULE-33 线框图双向一致性：regions 声明的内容性区块，ascii 中必须有绘制痕迹。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "").strip()
            regions = wf.get("regions") or []
            if not isinstance(regions, list) or len(ascii_text) < 8:
                continue
            for r in regions:
                if not isinstance(r, dict):
                    continue
                region_name = str(r.get("templateRegion") or r.get("id") or "")
                if region_name in DRAWING_SKIP_REGIONS:
                    continue
                keys = REGION_ASCII_KEYS.get(region_name, [])
                if not keys:
                    continue
                if not any(k in ascii_text for k in keys):
                    self.add_error(pid, "WIREFRAME_REGION_NOT_DRAWN", "warning",
                                   f"$.pages[{self._idx(page)}].wireframe.ascii",
                                   f"regions 声明了 {region_name} 区块，但 ascii 线框图中未绘制对应区域",
                                   f"regions 含 {region_name}", f"ascii 未出现 {region_name} 相关绘制痕迹",
                                   fix=f"在 ascii 线框图中补画 {region_name} 区域（或补充对应文字标签）")

    def check_coding_item_ids(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            cg = page.get("codingGuide") or {}
            items = cg.get("pageItems") or []
            for i, item in enumerate(items):
                if not item.get("id"):
                    self.add_error(pid, "CODING_ITEM_ID_MISSING", "error",
                                   f"$.pages[{self._idx(page)}].codingGuide.pageItems[{i}].id",
                                   "codingGuide 开发项缺少稳定 ID",
                                   "非空 id（如 P01-C01）", "空",
                                   fix="为每个开发项补充稳定 ID，供 Coding Plan/Execution/Verification 追踪")

    def check_path_without_verify(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            code_avail = str(page.get("codeAvailability", "") or
                             (page.get("templateContract") or {}).get("codeAvailability", ""))
            cg = page.get("codingGuide") or {}
            for i, item in enumerate(cg.get("pageItems") or []):
                target = item.get("target") or {}
                path = target.get("path", "")
                if code_avail in ("partial", "unavailable") and path:
                    self.add_error(pid, "PATH_WITHOUT_VERIFY", "error",
                                   f"$.pages[{self._idx(page)}].codingGuide.pageItems[{i}].target.path",
                                   f"代码状态为 {code_avail} 时 target.path 必须为空",
                                   "空 path（待映射阶段核验）", path,
                                   fix="清空 target.path，标记 mappingStatus=pending 或 blocked")

    def check_vue3_syntax(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            cg = page.get("codingGuide") or {}
            texts = []
            texts.extend(walk_text(cg.get("implementationRules") or []))
            for item in cg.get("pageItems") or []:
                texts.extend(walk_text(item.get("requirements") or []))
                texts.extend(walk_text(item.get("acceptanceCriteria") or []))
                texts.extend(walk_text(item.get("prohibitedChanges") or []))
            texts.extend(walk_text(page.get("restoreRequirement") or {}))
            joined = " ".join(texts)
            for pat in VUE3_PATTERNS:
                if pat in joined:
                    self.add_error(pid, "VUE3_SYNTAX_IN_REQUIREMENTS", "error",
                                   f"$.pages[{self._idx(page)}].codingGuide",
                                   f"实现要求中出现 Vue 3 专属绑定语法: {pat}",
                                   "业务组件名称或能力描述", pat,
                                   fix=f"移除 {pat}，改为业务组件或能力描述（如 IxTable 行内操作）")

    def check_component_mapping(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            for section in self.page_sections(page):
                for field_key in ("tableFields", "formFields", "cardFields", "fields"):
                    for i, field in enumerate(section.get(field_key) or []):
                        if isinstance(field, dict):
                            has_component = any(k in field for k in ("iduxComponent", "component", "render"))
                            if not has_component:
                                self.add_error(pid, "COMPONENT_MAPPING_MISSING", "error",
                                               f"$.pages[{self._idx(page)}].sections.{field_key}[{i}]",
                                               f"字段 {field.get('name', i)} 未声明组件映射",
                                               "iduxComponent/component/render 之一", "缺失",
                                               fix="为字段声明 iduxComponent 或 component 映射")

    def check_legacy_wireframe(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if isinstance(wf, str):
                msg = ("页面使用旧版自由文本线框，未完成模板契约校验" if self.strict
                       else "页面使用旧版自由文本线框，仅兼容读取，未完成模板契约校验")
                self.add_error(pid, "LEGACY_WIREFRAME",
                               "error" if self.strict else "warning",
                               f"$.pages[{self._idx(page)}].wireframe",
                               msg, "结构化 wireframe", "自由文本字符串",
                               fix="将 wireframe 重构为结构化对象（templateId/regions/variants）")

    # ---- 设计闭环：页面清单（RULE-28）----
    def _infer_container_type(self, page):
        """推断页面容器类型：显式 containerType > templateId 关键词 > page。"""
        ct = page.get("containerType")
        if ct in ("page", "modal", "drawer"):
            return ct
        tid = self.page_template(page) or ""
        if "modal" in tid:
            return "modal"
        if "drawer" in tid:
            return "drawer"
        return "page"

    def _container_has_entry(self, container, all_pages):
        """容器是否被其他页面的操作 targetPageId 或交互文本引用。"""
        cid = str(container.get("id", ""))
        cname = container.get("name") or ""
        for page in all_pages:
            if page is container:
                continue
            for op in page.get("operations") or []:
                if str(op.get("targetPageId") or "") == cid:
                    return True
            p = {k: v for k, v in page.items() if k != "children"}
            text = json.dumps(p, ensure_ascii=False)
            if cid and cid in text:
                return True
            if cname and len(cname) >= 2 and cname in text:
                return True
        return False

    def check_manifest_closure(self):
        """页面清单闭环：总览确认的页面/容器必须完整出现在 pages（含 children）。"""
        overview = (self.data.get("overview") or {}).get("pageOverview") or []
        all_pages = [p for p, _ in self.all_pages]
        page_ids = {str(p.get("id", "")) for p in all_pages if p.get("id")}
        by_id = {str(p.get("id", "")): p for p in all_pages if p.get("id")}
        # 1) 总览重复 id
        seen = set()
        for i, item in enumerate(overview):
            oid = str(item.get("id", ""))
            if not oid:
                continue
            if oid in seen:
                self.add_error(oid, "MANIFEST_DUPLICATE", "error",
                               f"$.overview.pageOverview[{i}].id",
                               f"页面总览存在重复页面 ID: {oid}",
                               "页面 ID 唯一", f"{oid} 重复出现",
                               fix="删除重复的总览条目或修改为唯一 ID")
            seen.add(oid)
        overview_ids = {str(i.get("id", "")) for i in overview if i.get("id")}
        # 2) 已确认但 pages 缺失（生成 HTML 将遗漏）
        for oid in sorted(overview_ids - page_ids):
            self.add_error(oid, "MANIFEST_PAGE_MISSING", "error", "$.overview.pageOverview",
                           f"页面总览已确认页面/容器 {oid} 未出现在 pages（含 children），生成 HTML 将遗漏该页面",
                           "总览确认的页面必须存在于 pages", f"pages 中缺失 {oid}",
                           fix=f"在 pages（或对应父页面 children）中补充 {oid} 页面对象及完整设计")
        # 3) 额外页面（总览未覆盖）
        for pid in sorted(page_ids - overview_ids):
            p = by_id.get(pid)
            self.add_error(pid, "MANIFEST_EXTRA_PAGE", "error",
                           self.page_path.get(id(p), "$.pages"),
                           f"页面 {pid} 未出现在页面总览 pageOverview",
                           "pages 与页面总览一致", "总览缺失该页面",
                           fix="在 overview.pageOverview 中补充该页面条目（含名称、类型、用途、入口）")
        # 4) 元数据不一致（名称/类型/容器类型）
        for item in overview:
            oid = str(item.get("id", ""))
            p = by_id.get(oid)
            if not p:
                continue
            if item.get("name") and p.get("name") and item["name"] != p["name"]:
                self.add_error(oid, "MANIFEST_METADATA_MISMATCH", "error", "$.overview.pageOverview",
                               f"页面 {oid} 名称在页面总览与 pages 不一致",
                               f"总览名称={item['name']}", f"pages 名称={p['name']}",
                               fix="统一页面名称")
            if item.get("type") and p.get("type") and item["type"] != p["type"]:
                self.add_error(oid, "MANIFEST_METADATA_MISMATCH", "error", "$.overview.pageOverview",
                               f"页面 {oid} 页面类型在页面总览与 pages 不一致",
                               f"总览类型={item['type']}", f"pages 类型={p['type']}",
                               fix="统一页面类型（使用 Common Design 中文页面类型名）")
            ov_ct = item.get("containerType")
            if ov_ct and ov_ct != self._infer_container_type(p):
                self.add_error(oid, "MANIFEST_CONTAINER_TYPE_MISMATCH", "error", "$.overview.pageOverview",
                               f"页面 {oid} 容器类型在页面总览与 pages 不一致",
                               f"总览容器类型={ov_ct}", f"pages 容器类型={self._infer_container_type(p)}",
                               fix="统一容器类型（page/modal/drawer）")
        # 5) 孤立容器：弹窗/抽屉没有任何入口引用（已确认容器升级为 error）
        for p in all_pages:
            if self._infer_container_type(p) in ("modal", "drawer") \
                    and not self._container_has_entry(p, all_pages):
                cid = str(p.get("id", ""))
                sev = "error" if cid in overview_ids else "warning"
                self.add_error(cid, "ORPHAN_CONTAINER", sev,
                               self.page_path.get(id(p), "$.pages"),
                               f"容器 {p.get('name') or cid} 没有任何页面操作或交互入口指向它",
                               "弹窗/抽屉应有明确的触发入口", "无入口引用",
                               fix="在主页面 operations.targetPageId 或关键交互说明中声明该容器入口")

    # ---- 设计闭环：操作目标（RULE-29）----
    def check_operation_closure(self):
        """操作目标闭环：结构化操作的目标页面/容器必须存在且类型正确，高影响操作必须二次确认。"""
        by_id = {str(p.get("id", "")): p for p, _ in self.all_pages if p.get("id")}
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            for i, op in enumerate(page.get("operations") or []):
                opath = f"{path}.operations[{i}]"
                action = op.get("action") or ""
                opid = op.get("id") or ""
                if not opid:
                    self.add_error(pid, "OPERATION_ID_MISSING", "warning", f"{opath}.id",
                                   "操作缺少 id，无法稳定追踪到 Coding 项",
                                   "非空操作 id", "空",
                                   fix="为操作补充唯一 id（如 OP01）")
                if action not in KNOWN_ACTIONS:
                    self.add_error(pid, "OPERATION_ACTION_UNKNOWN", "warning", f"{opath}.action",
                                   f"未知操作类型: {action or '空'}",
                                   f"已知类型之一: {sorted(KNOWN_ACTIONS)}", action or "空",
                                   fix="使用已知操作类型，无法归类时用 other")
                if action == "other":
                    self.add_error(pid, "OPERATION_ACTION_OTHER", "info", f"{opath}.action",
                                   "操作类型为 other，需人工核验其实现语义",
                                   "明确的操作类型", "other",
                                   fix="如可归类请改为具体操作类型")
                if action == "open-container":
                    target = str(op.get("targetPageId") or "")
                    if not target:
                        self.add_error(pid, "OPERATION_TARGET_MISSING", "error", f"{opath}.targetPageId",
                                       "open-container 操作缺少 targetPageId",
                                       "目标页面/容器 ID", "空",
                                       fix="补充 targetPageId 指向目标页面")
                    elif target not in by_id:
                        self.add_error(pid, "OPERATION_TARGET_MISSING", "error", f"{opath}.targetPageId",
                                       f"操作目标页面/容器 {target} 不存在于 pages（含 children）",
                                       "目标页面存在于 pages", f"{target} 缺失",
                                       fix=f"在 pages 中补充目标页面 {target}，或修正 targetPageId")
                    else:
                        want = op.get("targetContainerType") or ""
                        got = self._infer_container_type(by_id[target])
                        if want and want != got:
                            self.add_error(pid, "OPERATION_CONTAINER_TYPE_MISMATCH", "error",
                                           f"{opath}.targetContainerType",
                                           f"操作目标容器类型不匹配: {target} 实际为 {got}",
                                           want, got,
                                           fix="修正 targetContainerType 或选择正确的容器页面")
                if action in HIGH_RISK_ACTIONS and not op.get("confirm"):
                    self.add_error(pid, "OPERATION_CONFIRM_MISSING", "error", f"{opath}.confirm",
                                   f"高影响操作 {action} 缺少二次确认配置 confirm=true",
                                   "confirm=true（建议补充 confirmConfig.title/level）", "未配置二次确认",
                                   fix="设置 confirm=true 并补充 confirmConfig")

    # ---- 设计闭环：Tab 变体（RULE-30，条件式）----
    def _is_shell_region(self, region):
        r = str(region).lower()
        return any(k in r for k in SHELL_REGION_KEYS)

    def check_tab_variants(self):
        """Tab 变体闭环：仅当页面显式声明两个及以上内容 Tab 时强制完整变体线框。"""
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            tabs = page.get("tabs") or []
            if len(tabs) < 2:
                continue  # 条件式：普通详情页/单内容页仍可使用单张 wireframe
            tab_ids = [str(t.get("tabId") or "") for t in tabs]
            valid_tab_ids = {tid for tid in tab_ids if tid}
            for i, t in enumerate(tabs):
                if not t.get("tabId"):
                    self.add_error(pid, "TABS_ID_MISSING", "error", f"{path}.tabs[{i}].tabId",
                                   f"内容 Tab 缺少唯一 tabId（共 {len(tabs)} 个 Tab）",
                                   "每个 Tab 有唯一 tabId", "tabId 为空",
                                   fix="为每个 Tab 补充唯一 tabId（如 tab-overview）")
            dup = {tid for tid in tab_ids if tid and tab_ids.count(tid) > 1}
            if dup:
                self.add_error(pid, "TABS_ID_DUPLICATE", "error", f"{path}.tabs",
                               f"内容 Tab tabId 重复: {sorted(dup)}",
                               "tabId 唯一", f"重复 {sorted(dup)}",
                               fix="修改重复的 tabId")
            variants = wf.get("variants") or []
            if len(variants) != len(tabs):
                self.add_error(pid, "TABS_VARIANT_COUNT_MISMATCH", "error",
                               f"{path}.wireframe.variants",
                               f"多内容 Tab 页面（{len(tabs)} 个 Tab）必须为每个 Tab 提供完整变体线框，当前 variants 数量为 {len(variants)}",
                               f"{len(tabs)} 个 variant（每个 Tab 一个）", f"{len(variants)} 个 variant",
                               fix="为每个 Tab 分别绘制一张完整变体线框（公共外壳 + 当前 Tab 内容区）")
            variant_tab_ids = [str(v.get("tabId") or "") for v in variants]
            for tid in sorted(valid_tab_ids - set(variant_tab_ids)):
                self.add_error(pid, "TABS_VARIANT_MISSING", "error", f"{path}.wireframe.variants",
                               f"内容 Tab {tid} 缺少对应变体线框",
                               f"存在 tabId={tid} 的 variant", "缺失",
                               fix=f"为 Tab {tid} 补充 variant（tabId={tid}，含公共外壳与内容区）")
            for v in variants:
                vtid = str(v.get("tabId") or "")
                if vtid and vtid not in valid_tab_ids:
                    self.add_error(pid, "TABS_ORPHAN_VARIANT", "error", f"{path}.wireframe.variants",
                                   f"变体 tabId={vtid} 在页面 tabs 中不存在",
                                   "variant.tabId 属于页面 tabs", vtid,
                                   fix="删除孤立变体或将 tabId 修正为已声明 Tab")
                preserve = v.get("preserveRegions") or []
                if not any(self._is_shell_region(r) for r in preserve):
                    self.add_error(pid, "TABS_VARIANT_NO_SHELL", "error", f"{path}.wireframe.variants",
                                   f"变体 {vtid or '(无 tabId)'} 未保留公共页面外壳（如抽屉外壳/标题栏/对象摘要/Tab 行/底部操作区）",
                                   "preserveRegions 包含公共外壳区域", f"preserveRegions={preserve}",
                                   fix="变体保留公共外壳区域（如 drawer-shell/title-bar/object-summary/tab-bar/footer），仅替换当前 Tab 内容区")
                changed = v.get("changedRegions") or []
                ascii_txt = (v.get("ascii") or "").strip()
                if not changed or len(ascii_txt) < 10:
                    self.add_error(pid, "TABS_VARIANT_NO_CONTENT", "error", f"{path}.wireframe.variants",
                                   f"变体 {vtid or '(无 tabId)'} 缺少当前 Tab 内容区（changedRegions 为空或 ascii 内容为空/过短）",
                                   "非空 changedRegions 与完整内容区线框图",
                                   f"changedRegions={changed}, ascii 长度={len(ascii_txt)}",
                                   fix="在变体中绘制当前 Tab 内容区（表格/表单/描述列表等），并声明 changedRegions")
            for i, sec in enumerate(page.get("sections") or []):
                stid = sec.get("tabId")
                if stid and str(stid) not in valid_tab_ids:
                    self.add_error(pid, "TABS_SECTION_INVALID", "error", f"{path}.sections[{i}].tabId",
                                   f"内容区块绑定的 tabId={stid} 不存在于页面 tabs",
                                   "tabId 属于页面 tabs", stid,
                                   fix="修正 section.tabId 或补充对应 Tab")
            unbound = [s for s in page.get("sections") or [] if not s.get("tabId")]
            if unbound:
                self.add_error(pid, "TABS_SECTION_UNBOUND", "warning", f"{path}.sections",
                               f"多内容 Tab 页面存在未绑定 tabId 的内容区块（{len(unbound)} 个）",
                               "每个内容区块绑定所属 tabId", "未绑定",
                               fix="为内容区块补充 tabId，确保 sections 与 tabs/variants 可互相追踪")

    # ---- 设计闭环：页面级 Coding（RULE-31）----
    def check_coding_closure(self):
        """页面级 Coding 闭环：pageContext 一致、每页至少一个开发项、无孤立开发项。"""
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            cg = page.get("codingGuide") or {}
            pc = cg.get("pageContext") or {}
            if pc.get("pageId") and str(pc["pageId"]) != pid:
                self.add_error(pid, "CODING_PAGE_CONTEXT_MISMATCH", "error",
                               f"{path}.codingGuide.pageContext.pageId",
                               f"页面级 Coding 指导 pageContext.pageId={pc['pageId']} 与页面 id={pid} 不一致",
                               f"pageContext.pageId={pid}", str(pc["pageId"]),
                               fix="将 pageContext.pageId 修正为页面 id")
            items = cg.get("pageItems") or []
            if not items:
                self.add_error(pid, "CODING_NO_ITEMS", "error", f"{path}.codingGuide.pageItems",
                               f"页面 {page.get('name') or pid} 没有页面级 Coding 开发项（pageItems 为空），HTML 与 Coding 指导将缺失该页面",
                               "每个页面至少一个稳定 Coding item", "pageItems 为空",
                               fix="为页面补充页面级 Coding 指导（至少一个开发项）")
            ids = [str(i.get("id") or "") for i in items]
            dup = {x for x in ids if x and ids.count(x) > 1}
            if dup:
                self.add_error(pid, "CODING_ITEM_DUPLICATE", "error", f"{path}.codingGuide.pageItems",
                               f"页面级 Coding 开发项 id 重复: {sorted(dup)}",
                               "开发项 id 唯一", f"重复 {sorted(dup)}",
                               fix="修改重复的开发项 id")
            for i, item in enumerate(items):
                if item.get("pageId") and str(item["pageId"]) != pid:
                    self.add_error(pid, "CODING_ITEM_ORPHAN", "error",
                                   f"{path}.codingGuide.pageItems[{i}].pageId",
                                   f"Coding 开发项 {item.get('id')} 声明的 pageId={item['pageId']} 与所属页面 {pid} 不一致",
                                   f"pageId={pid}", str(item["pageId"]),
                                   fix="修正开发项 pageId 或移动到对应页面")

    # ---- 执行 ----
    def _idx(self, page):
        for i, p in enumerate(self.data.get("pages", [])):
            if p is page:
                return i
        return -1

    def run(self):
        if not isinstance(self.data, dict):
            self.check_schema()
            return
        self._legacy_page_ids = {p.get("id") for p in self.data.get("pages", [])
                                 if isinstance(self.page_wireframe(p), str)}
        self.all_pages = list(_walk_pages(self.data.get("pages") or []))
        self.page_path = {id(page): path for page, path in self.all_pages}
        self.check_schema()
        self.check_unique_page_ids()
        self.check_overview_consistency()
        self.check_template_registered()
        self.check_type_template_match()
        self.check_unregistered_type()
        self.check_navigation_type()
        self.check_skeleton_regions()
        self.check_region_order()
        self.check_required_components()
        self.check_section_wireframe_consistency()
        self.check_table_semantics()
        self.check_modal_semantics()
        self.check_drawer_semantics()
        self.check_stepper_semantics()
        self.check_step_variants()
        self.check_variant_shell_preserved()
        self.check_footer_alignment()
        self.check_footer_button_order()
        self.check_wireframe_content_consistency()
        self.check_coding_item_ids()
        self.check_path_without_verify()
        self.check_vue3_syntax()
        self.check_component_mapping()
        self.check_legacy_wireframe()
        # ---- 设计闭环（页面清单 / 操作目标 / Tab 变体 / 页面级 Coding）----
        self.check_manifest_closure()
        self.check_operation_closure()
        self.check_tab_variants()
        self.check_coding_closure()
        # ---- 线框图绘制质量与双向一致性（RULE-32 / RULE-33）----
        self.check_wireframe_drawing_quality()
        self.check_wireframe_region_drawn()

    def result(self):
        errors = [e for e in self.errors if e["severity"] == "error"]
        warnings = [e for e in self.errors if e["severity"] == "warning"]
        infos = [e for e in self.errors if e["severity"] == "info"]
        passed = not errors
        return {
            "valid": passed,
            "validationStatus": "passed" if passed else "failed",
            "errorCount": len(errors),
            "warningCount": len(warnings),
            "infoCount": len(infos),
            "strict": self.strict,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
        }


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(json.dumps({
            "valid": False, "validationStatus": "failed",
            "errorCount": 1, "message": f"无法读取输入文件: {e}",
        }, ensure_ascii=False, indent=2) + "\n")
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Demo 设计说明书模板契约校验器")
    parser.add_argument("--input", required=True, help="Demo JSON 路径")
    parser.add_argument("--template-registry", required=True,
                        help="Common Design 模板注册表 JSON 路径")
    parser.add_argument("--strict", action="store_true",
                        help="严格模式：legacy wireframe 直接报错；默认关闭时仅警告")
    args = parser.parse_args()

    data = load_json(args.input)
    registry = load_json(args.template_registry)

    validator = Validator(data, registry, strict=args.strict)
    validator.run()
    result = validator.result()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""validate_demo_spec.py 的自动化测试。

运行方式:
  python3 -m unittest discover -s tests -v

覆盖 15 个场景:
  1. 合法基础表格页通过
  2. 缺少分页失败
  3. 缺少标题栏失败
  4. 基础表格页误画成普通卡片失败
  5. 列表弹窗缺少关闭入口失败
  6. 列表抽屉 footer 对齐错误失败
  7. 配置表单页 footer 右对齐失败
  8. 步骤条页面使用 IxTabs 而不是 IxStepper 失败
  9. 多步骤页面缺少步骤变体失败
  10. 自定义模板没有 overrideJustification 失败
  11. 页面 type 使用未注册名称失败
  12. sections 与 wireframe.regions 不一致失败
  13. partial 状态下 target.path 非空失败
  14. 合法业务覆盖模板规则时通过
  15. legacy wireframe 在非严格模式下产生警告
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "validate_demo_spec.py"
REGISTRY = BASE / "references" / "02-template-contracts" / "common-design-template-registry.json"


def run_validator(payload, strict=True):
    """以子进程方式运行校验脚本，与真实使用方式一致。"""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
        tmp_path = f.name
    cmd = [sys.executable, str(SCRIPT), "--input", tmp_path, "--template-registry", str(REGISTRY)]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    os.unlink(tmp_path)
    report = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, report


def error_codes(report):
    return {e.get("errorCode") for e in report.get("errors", [])}


def warning_codes(report):
    return {w.get("errorCode") for w in report.get("warnings", [])}


def base_regions():
    return [
        {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
        {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "页面标题"},
        {"id": "filter", "templateRegion": "filter", "position": "content-top", "required": True, "content": "筛选区"},
        {"id": "toolbar", "templateRegion": "toolbar", "position": "content", "required": True, "content": "工具栏"},
        {"id": "table", "templateRegion": "table", "position": "content", "required": True, "content": "表格主体"},
        {"id": "pagination", "templateRegion": "pagination", "position": "bottom", "required": True, "content": "分页"},
    ]


def base_page(**overrides):
    page = {
        "id": "P01",
        "name": "策略列表",
        "type": "基础表格页",
        "codeAvailability": "verified",
        "templateContract": {
            "templateId": "page-table-basic",
            "baseTemplateId": "",
            "navigationType": "left-shaped",
            "templateSource": "common-design/references/02-template/01-page-types.md#page-table-basic",
            "requiredRegions": ["global-navigation", "title-bar", "filter", "toolbar", "table", "pagination"],
            "optionalRegions": [],
            "regionOrder": ["global-navigation", "title-bar", "filter", "toolbar", "table", "pagination"],
            "footerContract": {},
            "componentContract": {"table": ["IxTable"], "pagination": ["IxPagination"], "toolbar": ["IxButton"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        },
        "wireframe": {
            "templateId": "page-table-basic",
            "navigationType": "left-shaped",
            "layoutSource": "Common Design page-table-basic",
            "shell": {
                "globalNavigation": True,
                "titleBar": {"required": True, "type": "plain", "component": ""},
                "contentContainer": {"required": True, "type": "page-content"},
                "footer": {"required": False, "alignment": "", "height": "56px"},
            },
            "regions": base_regions(),
            "variants": [],
            "ascii": "标题栏/筛选/工具栏/表格/分页",
        },
        "sections": [
            {"title": "筛选区", "type": "filter", "filterFields": [{"name": "策略名称", "iduxComponent": "IxInput"}]},
            {"title": "工具栏", "type": "toolbar"},
            {"title": "表格主体", "type": "table", "tableFields": [{"name": "策略名称", "iduxComponent": "IxText"}]},
        ],
        "footerActions": [],
        "codingGuide": {
            "pageItems": [
                {
                    "id": "P01-C01", "scope": "page-shell", "name": "页面外壳", "mode": "reuse-framework",
                    "mappingRef": "M01", "mappingStatus": "verified",
                    "target": {"path": "src/pages/policy/index.vue", "export": "PolicyPage"},
                    "requirements": ["保留标题栏、筛选区、表格、分页结构"],
                    "acceptanceCriteria": ["页面结构一致"],
                }
            ]
        },
    }
    page.update(overrides)
    return page


def make_spec(pages, design_context=None):
    spec = {
        "title": "测试需求设计说明书",
        "overview": {
            "summary": "测试",
            "pageOverview": [
                {"id": p.get("id", ""), "name": p.get("name", ""), "type": p.get("type", "")} for p in pages
            ],
        },
        "pages": pages,
    }
    if design_context is not None:
        spec["designContext"] = design_context
    return spec


def modal_regions():
    return [
        {"id": "modal-shell", "templateRegion": "modal-shell", "position": "top", "required": True, "content": "弹窗外壳"},
        {"id": "modal-header", "templateRegion": "modal-header", "position": "top", "required": True, "content": "弹窗标题与关闭入口"},
        {"id": "form-content", "templateRegion": "form-content", "position": "content", "required": True, "content": "表单主体"},
        {"id": "modal-footer", "templateRegion": "modal-footer", "position": "bottom", "required": True, "content": "底部操作：确定/取消"},
    ]


def modal_page(**overrides):
    """合法表单弹窗（form-modal），用于操作目标闭环与孤儿容器测试。"""
    page = base_page()
    page.update({
        "id": "P02",
        "name": "批量编辑主机资产",
        "type": "表单弹窗",
        "templateContract": {
            "templateId": "form-modal",
            "baseTemplateId": "",
            "navigationType": "left-shaped",
            "templateSource": "common-design/references/02-template/01-page-types.md#form-modal",
            "requiredRegions": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "optionalRegions": [],
            "regionOrder": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "footerContract": {},
            "componentContract": {"shell": ["IxModal"], "form": ["IxForm", "IxFormItem"], "footer": ["IxButton"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        },
        "wireframe": {
            "templateId": "form-modal",
            "navigationType": "left-shaped",
            "layoutSource": "Common Design form-modal",
            "shell": {
                "globalNavigation": False,
                "titleBar": {"required": True, "type": "modal", "component": ""},
                "contentContainer": {"required": True, "type": "modal-content"},
                "footer": {"required": True, "alignment": "left", "height": "56px"},
            },
            "regions": modal_regions(),
            "variants": [],
            "ascii": "弹窗标题/表单主体/确定/取消",
        },
        "sections": [
            {"title": "表单主体", "type": "form", "fields": [{"name": "主机名", "iduxComponent": "IxInput"}]},
        ],
        "footerActions": [],
        "codingGuide": {
            "pageItems": [
                {
                    "id": "P02-C01", "scope": "modal-form", "name": "批量编辑表单", "mode": "reuse-framework",
                    "mappingRef": "M02", "mappingStatus": "verified",
                    "target": {"path": "src/pages/policy/batch-edit-modal.vue", "export": "BatchEditModal"},
                    "requirements": ["保留弹窗外壳、表单、底部操作结构"],
                    "acceptanceCriteria": ["弹窗结构一致"],
                }
            ]
        },
    })
    page.update(overrides)
    return page


def valid_tab_variants(tab_ids):
    """为每个 tabId 生成合法变体：保留公共外壳、changedRegions 与 ascii 内容区。"""
    return [
        {
            "tabId": tid,
            "preserveRegions": ["title-bar", "tab-bar", "footer"],
            "changedRegions": ["tab-content"],
            "ascii": "标题栏/Tab行/" + tid + "内容区/底部操作",
        }
        for tid in tab_ids
    ]


def tabbed_page(tabs, variants, section_tab_ids=None, **overrides):
    """多内容 Tab 页面：tabs + wireframe.variants + sections.tabId 绑定。"""
    page = base_page()
    page["tabs"] = tabs
    page["wireframe"]["variants"] = variants
    if section_tab_ids:
        for i, tid in enumerate(section_tab_ids):
            if i < len(page["sections"]):
                page["sections"][i]["tabId"] = tid
    page.update(overrides)
    return page


def drawer_detail_page(**overrides):
    """合法详情抽屉（detail-drawer），用于表格与详情字段一致性（RULE-38）测试。"""
    page = base_page()
    page.update({
        "id": "D01",
        "name": "策略详情",
        "type": "详情抽屉",
        "templateContract": {
            "templateId": "detail-drawer",
            "baseTemplateId": "",
            "navigationType": "",
            "templateSource": "common-design/references/02-template/01-page-types.md#detail-drawer",
            "requiredRegions": ["drawer-shell", "drawer-header", "object-summary", "detail-content", "drawer-footer"],
            "optionalRegions": [],
            "regionOrder": ["drawer-shell", "drawer-header", "object-summary", "detail-content", "drawer-footer"],
            "footerContract": {"required": True, "alignment": "left", "buttonOrder": ["close"]},
            "componentContract": {"shell": ["IxDrawer"], "object-summary": ["IxDescriptions"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        },
        "wireframe": {
            "templateId": "detail-drawer",
            "navigationType": "",
            "layoutSource": "Common Design detail-drawer",
            "shell": {
                "globalNavigation": False,
                "titleBar": {"required": True, "type": "drawer", "component": ""},
                "contentContainer": {"required": True, "type": "drawer-content"},
                "footer": {"required": True, "alignment": "left", "height": "56px"},
            },
            "regions": [
                {"id": "drawer-shell", "templateRegion": "drawer-shell", "position": "top", "required": True, "content": "抽屉外壳"},
                {"id": "drawer-header", "templateRegion": "drawer-header", "position": "top", "required": True, "content": "抽屉标题与关闭入口"},
                {"id": "object-summary", "templateRegion": "object-summary", "position": "content-top", "required": True, "content": "对象摘要"},
                {"id": "detail-content", "templateRegion": "detail-content", "position": "content", "required": True, "content": "详情描述列表"},
                {"id": "drawer-footer", "templateRegion": "drawer-footer", "position": "bottom", "required": True, "content": "底部操作：关闭"},
            ],
            "variants": [],
            "ascii": "抽屉标题/对象摘要/详情描述列表/底部关闭",
        },
        "sections": [
            {"title": "基本信息", "type": "detail",
             "detailFields": [{"name": "策略名称", "iduxComponent": "IxText"},
                              {"name": "描述", "iduxComponent": "IxText"}]},
        ],
        "footerActions": [],
        "codingGuide": {
            "pageItems": [
                {
                    "id": "D01-C01", "scope": "drawer-detail", "name": "详情抽屉", "mode": "reuse-framework",
                    "mappingRef": "M03", "mappingStatus": "verified",
                    "target": {"path": "src/pages/policy/detail-drawer.vue", "export": "PolicyDetailDrawer"},
                    "requirements": ["保留抽屉外壳、对象摘要、详情描述列表结构"],
                    "acceptanceCriteria": ["抽屉结构一致"],
                }
            ]
        },
    })
    page.update(overrides)
    return page


def tag_page(table_fields, **overrides):
    """基础表格页，表格主体区块使用指定标签字段（RULE-39 测试）。"""
    page = base_page()
    page["sections"] = [
        {"title": "筛选区", "type": "filter", "filterFields": [{"name": "策略名称", "iduxComponent": "IxInput"}]},
        {"title": "工具栏", "type": "toolbar"},
        {"title": "表格主体", "type": "table", "tableFields": table_fields},
    ]
    page.update(overrides)
    return page


class TestValidateDemoSpec(unittest.TestCase):

    def test_valid_table_basic_passes(self):
        """1. 合法基础表格页通过。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))

    def test_card_list_template_registered(self):
        """Common Design 新增模板 page-card-list（卡片列表页）已入注册表：类型/模板识别通过、
        骨架按 requiredRegions（无 filter/pagination）校验通过。"""
        page = base_page()
        page["name"] = "连接器列表"
        page["type"] = "卡片列表页"
        page["templateContract"]["templateId"] = "page-card-list"
        page["templateContract"]["templateSource"] = "common-design/references/02-template/01-page-types.md#page-card-list"
        page["templateContract"]["requiredRegions"] = ["global-navigation", "title-bar", "toolbar", "card-list"]
        page["templateContract"]["regionOrder"] = ["global-navigation", "title-bar", "toolbar", "card-list"]
        page["templateContract"]["componentContract"] = {"toolbar": ["IxButton", "IxSearch"], "card-list": ["IxCard"]}
        page["wireframe"]["templateId"] = "page-card-list"
        page["wireframe"]["layoutSource"] = "Common Design page-card-list"
        page["wireframe"]["regions"] = [
            {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
            {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "页面标题"},
            {"id": "toolbar", "templateRegion": "toolbar", "position": "content", "required": True, "content": "工具栏（新增按钮 + 搜索）"},
            {"id": "card-list", "templateRegion": "card-list", "position": "content", "required": True, "content": "卡片列表（一行一个长条卡片）"},
        ]
        page["wireframe"]["ascii"] = (
            "标题栏/工具栏/卡片列表\n"
            "工具栏  [新增连接器]        搜索  [________]\n"
            "卡片列表：\n"
            "卡片  [图标]  条目A标题  [编辑] [删除]  连接状态：正常\n"
            "卡片  [图标]  条目B标题  [编辑] [删除]  连接状态：异常"
        )
        page["sections"] = [
            {"title": "工具栏", "type": "toolbar"},
            {"title": "卡片列表", "type": "content"},
        ]
        code, report = run_validator(make_spec([page]), strict=True)
        errs = error_codes(report)
        self.assertNotIn("TEMPLATE_NOT_REGISTERED", errs, f"report={report}")
        self.assertNotIn("TYPE_TEMPLATE_MISMATCH", errs, f"report={report}")
        self.assertNotIn("REQUIRED_REGION_MISSING", errs, f"report={report}")
        self.assertNotIn("SKELETON_REGION_MISSING", errs, f"report={report}")


    def test_missing_pagination_fails(self):
        """2. 缺少分页失败。"""
        page = base_page()
        page["wireframe"]["regions"] = [r for r in page["wireframe"]["regions"] if r["templateRegion"] != "pagination"]
        page["templateContract"]["componentContract"] = {
            "table": ["IxTable"], "toolbar": ["IxButton"]
        }
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertFalse(report.get("valid"))
        self.assertTrue(
            {"REQUIRED_REGION_MISSING", "TABLE_SEMANTIC_MISSING"} & error_codes(report),
            f"expected region/semantic error, got {error_codes(report)}",
        )

    def test_missing_title_bar_fails(self):
        """3. 缺少标题栏失败。"""
        page = base_page()
        page["wireframe"]["regions"] = [r for r in page["wireframe"]["regions"] if r["templateRegion"] != "title-bar"]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("REQUIRED_REGION_MISSING", error_codes(report))

    def test_table_page_as_card_fails(self):
        """4. 基础表格页误画成普通卡片失败（无表格语义）。"""
        page = base_page()
        page["wireframe"]["regions"] = [
            {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
            {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "页面标题"},
            {"id": "overview", "templateRegion": "overview", "position": "content", "required": True, "content": "概览卡片"},
            {"id": "chart", "templateRegion": "chart", "position": "content", "required": True, "content": "图表"},
        ]
        page["wireframe"]["ascii"] = "标题栏/概览卡片/图表"
        page["sections"] = [
            {"title": "概览卡片", "type": "overview"},
            {"title": "图表", "type": "chart", "tableFields": [{"name": "指标", "iduxComponent": "IxText"}]},
        ]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(
            {"TABLE_SEMANTIC_MISSING", "REQUIRED_REGION_MISSING"} & error_codes(report),
            f"expected table semantic error, got {error_codes(report)}",
        )

    def test_modal_missing_close_fails(self):
        """5. 列表弹窗缺少关闭入口失败。"""
        page = base_page(
            id="P02", name="选择策略弹窗", type="列表弹窗",
            templateContract={
                "templateId": "list-modal", "baseTemplateId": "", "navigationType": "",
                "templateSource": "common-design/references/02-template/01-page-types.md#list-modal",
                "requiredRegions": ["modal-shell", "modal-header", "filter", "table", "pagination", "modal-footer"],
                "optionalRegions": [], "regionOrder": ["modal-shell", "modal-header", "filter", "table", "pagination", "modal-footer"],
                "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]},
                "componentContract": {"shell": ["IxModal"], "table": ["IxTable"], "pagination": ["IxPagination"], "footer": ["IxButton"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "list-modal", "navigationType": "",
            "layoutSource": "Common Design list-modal",
            "shell": {"globalNavigation": False, "titleBar": {"required": False, "type": "", "component": ""},
                      "contentContainer": {"required": True, "type": "modal"}, "footer": {"required": True, "alignment": "right", "height": "56px"}},
            "regions": [
                {"id": "modal-shell", "templateRegion": "modal-shell", "position": "full", "required": True, "content": "弹窗外壳"},
                {"id": "modal-header", "templateRegion": "modal-header", "position": "top", "required": True, "content": "弹窗标题"},
                {"id": "filter", "templateRegion": "filter", "position": "content-top", "required": True, "content": "筛选区"},
                {"id": "table", "templateRegion": "table", "position": "content", "required": True, "content": "列表主体"},
                {"id": "pagination", "templateRegion": "pagination", "position": "bottom", "required": True, "content": "分页"},
                {"id": "modal-footer", "templateRegion": "modal-footer", "position": "bottom", "required": True, "content": "底部操作区"},
            ],
            "variants": [], "ascii": "弹窗外壳/标题/筛选/列表/分页/底部操作区",
        }
        page["footerActions"] = []
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(
            {"MODAL_CLOSE_MISSING", "MODAL_REGION_MISSING"} & error_codes(report),
            f"expected modal close error, got {error_codes(report)}",
        )

    def test_drawer_footer_alignment_fails(self):
        """6. 列表抽屉 footer 对齐错误失败（模板要求左对齐，声明 right 即错）。"""
        page = base_page(
            id="P02", name="选择策略抽屉", type="列表抽屉",
            templateContract={
                "templateId": "list-drawer", "baseTemplateId": "", "navigationType": "",
                "templateSource": "common-design/references/02-template/01-page-types.md#list-drawer",
                "requiredRegions": ["drawer-shell", "drawer-header", "object-context", "filter", "table", "pagination", "drawer-footer"],
                "optionalRegions": [], "regionOrder": ["drawer-shell", "drawer-header", "object-context", "filter", "table", "pagination", "drawer-footer"],
                "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]},
                "componentContract": {"shell": ["IxDrawer"], "table": ["IxTable"], "pagination": ["IxPagination"], "footer": ["IxButton"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "list-drawer", "navigationType": "",
            "layoutSource": "Common Design list-drawer",
            "shell": {"globalNavigation": False, "titleBar": {"required": False, "type": "", "component": ""},
                      "contentContainer": {"required": True, "type": "drawer"}, "footer": {"required": True, "alignment": "right", "height": "56px"}},
            "regions": [
                {"id": "drawer-shell", "templateRegion": "drawer-shell", "position": "full", "required": True, "content": "抽屉外壳"},
                {"id": "drawer-header", "templateRegion": "drawer-header", "position": "top", "required": True, "content": "抽屉标题和关闭入口"},
                {"id": "object-context", "templateRegion": "object-context", "position": "content-top", "required": True, "content": "对象上下文"},
                {"id": "filter", "templateRegion": "filter", "position": "content", "required": True, "content": "筛选区"},
                {"id": "table", "templateRegion": "table", "position": "content", "required": True, "content": "列表主体"},
                {"id": "pagination", "templateRegion": "pagination", "position": "bottom", "required": True, "content": "分页"},
                {"id": "drawer-footer", "templateRegion": "drawer-footer", "position": "bottom", "required": True, "content": "确认/取消"},
            ],
            "variants": [], "ascii": "抽屉外壳/标题/上下文/筛选/列表/分页/底部按钮",
        }
        page["footerActions"] = [{"label": "确定", "kind": "confirm"}, {"label": "取消", "kind": "cancel"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("FOOTER_ALIGNMENT_MISMATCH", error_codes(report))

    def test_form_config_footer_right_fails(self):
        """7. 配置表单页 footer 右对齐失败（模板要求左对齐）。"""
        page = base_page(
            id="P02", name="策略配置表单", type="配置表单页",
            templateContract={
                "templateId": "page-form-config", "baseTemplateId": "", "navigationType": "left-shaped",
                "templateSource": "common-design/references/02-template/01-page-types.md#page-form-config",
                "requiredRegions": ["global-navigation", "title-bar", "form-content", "footer"],
                "optionalRegions": [], "regionOrder": ["global-navigation", "title-bar", "form-content", "footer"],
                "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]},
                "componentContract": {"form": ["IxForm", "IxFormItem"], "footer": ["IxButton"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "page-form-config", "navigationType": "left-shaped",
            "layoutSource": "Common Design page-form-config",
            "shell": {"globalNavigation": True, "titleBar": {"required": True, "type": "plain", "component": ""},
                      "contentContainer": {"required": True, "type": "page-content"}, "footer": {"required": True, "alignment": "left", "height": "56px"}},
            "regions": [
                {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
                {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "页面标题"},
                {"id": "form-content", "templateRegion": "form-content", "position": "content", "required": True, "content": "表单内容"},
                {"id": "footer", "templateRegion": "footer", "position": "bottom", "required": True, "content": "保存/取消"},
            ],
            "variants": [], "ascii": "标题栏/表单内容/底部按钮",
        }
        page["sections"] = [
            {"title": "表单内容", "type": "form", "formFields": [{"name": "策略名称", "iduxComponent": "IxInput"}]},
        ]
        page["footerActions"] = [{"label": "保存", "kind": "confirm"}, {"label": "取消", "kind": "cancel"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("FOOTER_ALIGNMENT_MISMATCH", error_codes(report))

    def test_stepper_uses_tabs_fails(self):
        """8. 步骤条页面使用 IxTabs 而不是 IxStepper 失败。"""
        page = base_page(
            id="P02", name="策略配置向导", type="下钻步骤条配置页",
            templateContract={
                "templateId": "page-form-stepper", "baseTemplateId": "", "navigationType": "left-shaped",
                "templateSource": "common-design/references/02-template/01-page-types.md#page-form-stepper",
                "requiredRegions": ["global-navigation", "title-bar", "stepper", "step-content", "footer"],
                "optionalRegions": [], "regionOrder": ["global-navigation", "title-bar", "stepper", "step-content", "footer"],
                "footerContract": {"required": True, "alignment": "left", "buttonOrder": ["previous", "next-or-complete", "cancel"]},
                "componentContract": {"stepper": ["IxTabs"], "footer": ["IxButton"], "title-bar": ["IxHeader-prefix"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "page-form-stepper", "navigationType": "left-shaped",
            "layoutSource": "Common Design page-form-stepper",
            "shell": {"globalNavigation": True, "titleBar": {"required": True, "type": "drilldown", "component": "IxHeader-prefix"},
                      "contentContainer": {"required": True, "type": "page-content"}, "footer": {"required": True, "alignment": "left", "height": "56px"}},
            "regions": [
                {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
                {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "返回入口 + 页面标题"},
                {"id": "stepper", "templateRegion": "stepper", "position": "content-top", "required": True, "component": "IxTabs", "content": "步骤一/步骤二/步骤三"},
                {"id": "step-content", "templateRegion": "step-content", "position": "content", "required": True, "content": "当前步骤配置内容"},
                {"id": "footer", "templateRegion": "footer", "position": "bottom", "required": True, "content": "上一步/下一步/取消"},
            ],
            "variants": [
                {"id": "step-1", "preserveRegions": ["global-nav", "title-bar", "stepper", "footer"], "changedRegions": ["step-content"], "ascii": "步骤一内容"},
                {"id": "step-2", "preserveRegions": ["global-nav", "title-bar", "stepper", "footer"], "changedRegions": ["step-content"], "ascii": "步骤二内容"},
                {"id": "step-3", "preserveRegions": ["global-nav", "title-bar", "stepper", "footer"], "changedRegions": ["step-content"], "ascii": "步骤三内容"},
            ],
            "ascii": "返回入口/步骤条/步骤内容/底部按钮",
        }
        page["footerActions"] = [{"label": "上一步", "kind": "previous"}, {"label": "下一步", "kind": "next-or-complete"}, {"label": "取消", "kind": "cancel"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("REQUIRED_COMPONENT_MISSING", error_codes(report))

    def test_multi_step_missing_variants_fails(self):
        """9. 多步骤页面缺少步骤变体失败。"""
        page = base_page(
            id="P02", name="策略配置向导", type="下钻步骤条配置页",
            templateContract={
                "templateId": "page-form-stepper", "baseTemplateId": "", "navigationType": "left-shaped",
                "templateSource": "common-design/references/02-template/01-page-types.md#page-form-stepper",
                "requiredRegions": ["global-navigation", "title-bar", "stepper", "step-content", "footer"],
                "optionalRegions": [], "regionOrder": ["global-navigation", "title-bar", "stepper", "step-content", "footer"],
                "footerContract": {"required": True, "alignment": "left", "buttonOrder": ["previous", "next-or-complete", "cancel"]},
                "componentContract": {"stepper": ["IxStepper", "IxProFormStepper"], "footer": ["IxButton"], "title-bar": ["IxHeader-prefix"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "page-form-stepper", "navigationType": "left-shaped",
            "layoutSource": "Common Design page-form-stepper",
            "shell": {"globalNavigation": True, "titleBar": {"required": True, "type": "drilldown", "component": "IxHeader-prefix"},
                      "contentContainer": {"required": True, "type": "page-content"}, "footer": {"required": True, "alignment": "left", "height": "56px"}},
            "regions": [
                {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
                {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "返回入口 + 页面标题"},
                {"id": "stepper", "templateRegion": "stepper", "position": "content-top", "required": True, "component": "IxStepper", "content": "步骤一/步骤二/步骤三"},
                {"id": "step-content", "templateRegion": "step-content", "position": "content", "required": True, "content": "当前步骤配置内容"},
                {"id": "footer", "templateRegion": "footer", "position": "bottom", "required": True, "content": "上一步/下一步/取消"},
            ],
            "variants": [],
            "ascii": "返回入口/步骤条/步骤内容/底部按钮",
        }
        page["footerActions"] = [{"label": "上一步", "kind": "previous"}, {"label": "下一步", "kind": "next-or-complete"}, {"label": "取消", "kind": "cancel"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("STEP_VARIANT_MISSING", error_codes(report))

    def test_custom_without_override_fails(self):
        """10. 自定义模板没有 overrideJustification 失败。"""
        page = base_page()
        page["templateContract"]["templateId"] = "custom"
        page["templateContract"]["baseTemplateId"] = "page-table-basic"
        page["templateContract"]["override"] = {"enabled": False, "source": "", "reason": "", "affectedRules": []}
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(
            {"CUSTOM_OVERRIDE_MISSING", "CUSTOM_OVERRIDE_INCOMPLETE"} & error_codes(report),
            f"expected custom override error, got {error_codes(report)}",
        )

    def test_unregistered_type_fails(self):
        """11. 页面 type 使用未注册名称失败。"""
        page = base_page(type="下钻配置表单页")
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("UNREGISTERED_TYPE", error_codes(report))

    def test_section_wireframe_mismatch_fails(self):
        """12. sections 与 wireframe.regions 不一致失败。"""
        page = base_page()
        page["sections"].append(
            {"title": "事件列表", "type": "table", "tableFields": [{"name": "事件名称", "iduxComponent": "IxText"}]}
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("SECTION_MISSING_IN_WIREFRAME", error_codes(report))

    def test_partial_path_not_empty_fails(self):
        """13. partial 状态下 target.path 非空失败。"""
        page = base_page(codeAvailability="partial")
        page["codingGuide"]["pageItems"][0]["mappingStatus"] = "pending"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("PATH_WITHOUT_VERIFY", error_codes(report))

    def test_valid_override_passes(self):
        """14. 合法业务覆盖模板规则时通过（custom + 完整 override）。"""
        page = base_page(
            id="P02", name="自定义策略页面", type="自定义策略页",
            templateContract={
                "templateId": "custom", "baseTemplateId": "page-table-basic", "navigationType": "left-shaped",
                "templateSource": "common-design/references/02-template/01-page-types.md#page-table-basic",
                "requiredRegions": ["global-navigation", "title-bar", "filter", "toolbar", "table", "pagination"],
                "optionalRegions": ["overview"], "regionOrder": ["global-navigation", "title-bar", "filter", "toolbar", "table", "pagination"],
                "footerContract": {}, "componentContract": {"table": ["IxTable"], "pagination": ["IxPagination"], "toolbar": ["IxButton"]},
                "wireframeContract": {},
                "override": {"enabled": True, "source": "用户确认", "reason": "需求要求增加概览卡片区",
                             "affectedRules": ["requiredRegions", "regionOrder"]},
                "customReason": "在基础表格页上叠加概览卡片区",
                "overrideJustification": "用户确认需要概览统计区，覆盖模板 requiredRegions 顺序约束",
            },
        )
        page["wireframe"] = {
            "templateId": "custom", "navigationType": "left-shaped",
            "layoutSource": "Common Design page-table-basic + 用户确认覆盖",
            "shell": {"globalNavigation": True, "titleBar": {"required": True, "type": "plain", "component": ""},
                      "contentContainer": {"required": True, "type": "page-content"}, "footer": {"required": False, "alignment": "", "height": "56px"}},
            "regions": base_regions(),
            "variants": [],
            "ascii": "标题栏/筛选/工具栏/表格/分页",
        }
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertTrue(report.get("valid"))

    def test_override_relaxes_required_region(self):
        """override 生效时模板必需区域约束放宽（以 Product Design / 用户确认为准）-> 不报 REQUIRED_REGION_MISSING。"""
        page = base_page()
        page["templateContract"]["override"] = {
            "enabled": True, "source": "用户确认",
            "reason": "产品级区域结构差异（步骤条与标题栏同行）",
            "affectedRules": ["requiredRegions", "regionOrder", "requiredComponents"],
        }
        page["wireframe"]["regions"] = [r for r in page["wireframe"]["regions"] if r["templateRegion"] != "pagination"]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertTrue(report.get("valid"))

    def test_required_region_missing_without_override_fails(self):
        """未声明 override 时，模板必需区域（pagination）缺失仍被阻断。"""
        page = base_page()
        page["wireframe"]["regions"] = [r for r in page["wireframe"]["regions"] if r["templateRegion"] != "pagination"]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("REQUIRED_REGION_MISSING", error_codes(report))

    def test_legacy_wireframe_warning_non_strict(self):
        """15. legacy wireframe 在非严格模式下产生警告，严格模式下失败。"""
        page = base_page()
        page["wireframe"] = "标题栏/筛选区/工具栏/表格/分页"
        code_strict, report_strict = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code_strict, 0)
        self.assertIn("LEGACY_WIREFRAME", error_codes(report_strict))

        code_lenient, report_lenient = run_validator(make_spec([page]), strict=False)
        self.assertEqual(code_lenient, 0)
        self.assertTrue(report_lenient.get("valid"))
        self.assertIn("LEGACY_WIREFRAME", warning_codes(report_lenient))

    # ---- 页面清单闭环（RULE-28）----
    def test_manifest_page_missing_fails(self):
        """页面总览确认了批量编辑弹窗，但 pages 缺失 -> MANIFEST_PAGE_MISSING。"""
        spec = {
            "title": "测试需求设计说明书",
            "overview": {
                "summary": "测试",
                "pageOverview": [
                    {"id": "P01", "name": "策略列表", "type": "基础表格页"},
                    {"id": "P02", "name": "批量编辑主机资产", "type": "表单弹窗", "containerType": "modal"},
                ],
            },
            "pages": [base_page()],
        }
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("MANIFEST_PAGE_MISSING", error_codes(report))

    def test_manifest_metadata_mismatch_fails(self):
        """页面总览与 pages 的页面名称不一致 -> MANIFEST_METADATA_MISMATCH。"""
        spec = make_spec([base_page()])
        spec["overview"]["pageOverview"][0]["name"] = "策略列表（改）"
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("MANIFEST_METADATA_MISMATCH", error_codes(report))

    # ---- 操作目标闭环（RULE-29）----
    def test_operation_target_missing_fails(self):
        """批量编辑操作 targetPageId 不存在 -> OPERATION_TARGET_MISSING。"""
        page = base_page(operations=[
            {"id": "OP01", "action": "open-container", "label": "批量编辑主机资产", "trigger": "工具栏按钮",
             "targetPageId": "P99", "targetContainerType": "modal", "confirm": False},
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("OPERATION_TARGET_MISSING", error_codes(report))

    def test_operation_confirm_missing_fails(self):
        """删除操作缺少二次确认 -> OPERATION_CONFIRM_MISSING。"""
        page = base_page(operations=[
            {"id": "OP02", "action": "delete", "label": "删除策略", "trigger": "行内操作", "confirm": False},
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("OPERATION_CONFIRM_MISSING", error_codes(report))

    def test_operation_closure_passes(self):
        """合法操作闭环：open-container 指向存在的弹窗 + 删除带二次确认 -> 通过。"""
        modal = modal_page()
        page = base_page(operations=[
            {"id": "OP01", "action": "open-container", "label": "批量编辑主机资产", "trigger": "工具栏按钮",
             "targetPageId": "P02", "targetContainerType": "modal", "confirm": False,
             "note": "打开批量编辑弹窗"},
            {"id": "OP02", "action": "delete", "label": "删除", "trigger": "行内操作", "confirm": True,
             "confirmConfig": {"title": "确认删除该策略？", "level": "danger"}},
            {"id": "OP03", "action": "refresh", "label": "刷新", "trigger": "页头"},
        ])
        code, report = run_validator(make_spec([page, modal]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertTrue(report.get("valid"))

    def test_operation_other_info(self):
        """action=other 输出 info 提示，不阻断生成。"""
        page = base_page(operations=[
            {"id": "OP04", "action": "other", "label": "自定义操作", "trigger": "页头"},
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(e.get("errorCode") == "OPERATION_ACTION_OTHER" for e in report.get("infos", [])))

    # ---- Tab 变体闭环（RULE-30，条件式）----
    TABS = [
        {"tabId": "tab-overview", "name": "概览"},
        {"tabId": "tab-source", "name": "来源与识别依据"},
        {"tabId": "tab-log", "name": "操作记录"},
    ]

    def test_tabs_missing_variants_fails(self):
        """声明三个内容 Tab 但没有 variants -> TABS_VARIANT_COUNT_MISMATCH + TABS_VARIANT_MISSING。"""
        page = tabbed_page(tabs=self.TABS, variants=[])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue({"TABS_VARIANT_COUNT_MISMATCH", "TABS_VARIANT_MISSING"} & error_codes(report))

    def test_tabs_variant_count_mismatch_fails(self):
        """三个 Tab 只有两个 variants -> TABS_VARIANT_COUNT_MISMATCH。"""
        page = tabbed_page(tabs=self.TABS, variants=valid_tab_variants(["tab-overview", "tab-source"]),
                           section_tab_ids=["tab-overview", "tab-source"])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TABS_VARIANT_COUNT_MISMATCH", error_codes(report))

    def test_tabs_orphan_variant_fails(self):
        """variant.tabId 不存在于 tabs -> TABS_ORPHAN_VARIANT。"""
        variants = valid_tab_variants(["tab-overview", "tab-source"]) + [{
            "tabId": "tab-ghost",
            "preserveRegions": ["title-bar", "tab-bar", "footer"],
            "changedRegions": ["tab-content"],
            "ascii": "标题栏/Tab行/幽灵内容区/底部操作",
        }]
        page = tabbed_page(tabs=self.TABS[:2], variants=variants, section_tab_ids=["tab-overview", "tab-source"])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TABS_ORPHAN_VARIANT", error_codes(report))

    def test_tabs_variant_no_shell_fails(self):
        """variant 缺少公共页面外壳 -> TABS_VARIANT_NO_SHELL。"""
        variants = [
            {"tabId": "tab-overview", "preserveRegions": ["content-body"],
             "changedRegions": ["tab-content"], "ascii": "内容区/概览内容"},
            {"tabId": "tab-source", "preserveRegions": ["content-body"],
             "changedRegions": ["tab-content"], "ascii": "内容区/来源内容"},
        ]
        page = tabbed_page(tabs=self.TABS[:2], variants=variants, section_tab_ids=["tab-overview", "tab-source"])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TABS_VARIANT_NO_SHELL", error_codes(report))

    def test_tabs_variant_no_content_fails(self):
        """variant 缺少当前 Tab 内容区（changedRegions 为空且 ascii 过短）-> TABS_VARIANT_NO_CONTENT。"""
        variants = [
            {"tabId": "tab-overview", "preserveRegions": ["title-bar", "tab-bar", "footer"],
             "changedRegions": [], "ascii": "标题栏"},
            {"tabId": "tab-source", "preserveRegions": ["title-bar", "tab-bar", "footer"],
             "changedRegions": ["tab-content"], "ascii": "标题栏/Tab行/来源内容/底部操作"},
        ]
        page = tabbed_page(tabs=self.TABS[:2], variants=variants, section_tab_ids=["tab-overview", "tab-source"])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TABS_VARIANT_NO_CONTENT", error_codes(report))

    def test_tabs_section_invalid_fails(self):
        """section 绑定不存在的 tabId -> TABS_SECTION_INVALID。"""
        page = tabbed_page(tabs=self.TABS[:2], variants=valid_tab_variants(["tab-overview", "tab-source"]),
                           section_tab_ids=["tab-ghost", "tab-source"])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TABS_SECTION_INVALID", error_codes(report))

    def test_multitab_closure_passes(self):
        """合法多 Tab 闭环：tabs + 对应 variants + sections.tabId 绑定 -> 通过。"""
        tabs = [
            {"tabId": "tab-overview", "name": "概览"},
            {"tabId": "tab-source", "name": "来源与识别依据"},
            {"tabId": "tab-log", "name": "操作记录"},
        ]
        page = tabbed_page(tabs=tabs, variants=valid_tab_variants([t["tabId"] for t in tabs]),
                           section_tab_ids=["tab-overview", "tab-source", "tab-log"])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertTrue(report.get("valid"))

    # ---- 孤儿容器 ----
    def test_orphan_container_fails(self):
        """已确认弹窗没有任何入口 -> ORPHAN_CONTAINER（error）。"""
        modal = modal_page()
        code, report = run_validator(make_spec([base_page(), modal]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("ORPHAN_CONTAINER", error_codes(report))

    # ---- 页面级 Coding 闭环（RULE-31）----
    def test_coding_page_context_mismatch_fails(self):
        """codingGuide.pageContext.pageId 与页面 ID 不一致 -> CODING_PAGE_CONTEXT_MISMATCH。"""
        page = base_page()
        page["codingGuide"]["pageContext"] = {"pageId": "P99", "summary": "错误上下文"}
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("CODING_PAGE_CONTEXT_MISMATCH", error_codes(report))

    def test_coding_no_items_fails(self):
        """页面存在但没有页面级 Coding item -> CODING_NO_ITEMS。"""
        page = base_page()
        page["codingGuide"]["pageItems"] = []
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("CODING_NO_ITEMS", error_codes(report))

    # ---- wireframe 绘制完整性（RULE-32 / RULE-33）----
    def test_wireframe_ascii_too_short_fails(self):
        """线框图只有几个字（过短）-> WIREFRAME_ASCII_TOO_SHORT（error）。"""
        page = base_page()
        page["wireframe"]["ascii"] = "这是一个表格页"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("WIREFRAME_ASCII_TOO_SHORT", error_codes(report))

    def test_wireframe_ascii_not_drawn_fails(self):
        """线框图未按模板绘制任何区域 -> WIREFRAME_ASCII_NOT_DRAWN（error）。"""
        page = base_page()
        page["wireframe"]["ascii"] = "页面整体布局说明"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("WIREFRAME_ASCII_NOT_DRAWN", error_codes(report))

    def test_wireframe_ascii_region_not_drawn_warns(self):
        """regions 声明了表格但 ascii 未绘制 -> WIREFRAME_REGION_NOT_DRAWN（warning）。"""
        page = base_page()
        page["wireframe"]["ascii"] = "标题栏/筛选/工具栏/分页区"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("WIREFRAME_REGION_NOT_DRAWN", {e.get("errorCode") for e in report.get("warnings", [])})

    def test_wireframe_ascii_full_drawing_passes(self):
        """完整字符画线框图 -> 通过。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "┌ 标题栏 ─────────────────┐\n"
            "│ [筛选] [工具栏]        │\n"
            "├──────────┬─────────────┤\n"
            "│ 表格列1   │ 表格列2      │\n"
            "├──────────┴─────────────┤\n"
            "│ [分页] 上一页 1 2 下一页 │\n"
            "└────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))

    def test_wireframe_region_order_mismatch_warns(self):
        """regions 顺序与 ascii 绘制顺序矛盾 -> WIREFRAME_REGION_ORDER_MISMATCH（warning）。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "┌ 标题栏 ─────────────────┐\n"
            "│ [筛选] [工具栏]        │\n"
            "│ [分页] 上一页 1 2 下一页 │\n"
            "├──────────┬─────────────┤\n"
            "│ 表格列1   │ 表格列2      │\n"
            "└────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("WIREFRAME_REGION_ORDER_MISMATCH", {e.get("errorCode") for e in report.get("warnings", [])})

    def test_wireframe_duplicate_singular_control_warns(self):
        """页面级单例控件（如导出）被重复绘制 -> WIREFRAME_DUPLICATE_CONTROL（warning）。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "┌ 标题栏 ─────────────────┐\n"
            "│ [导出] [刷新]          │\n"
            "│ [筛选] [导出]          │\n"
            "│ 表格                   │\n"
            "└────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("WIREFRAME_DUPLICATE_CONTROL", {e.get("errorCode") for e in report.get("warnings", [])})

    def test_wireframe_row_action_not_flagged(self):
        """行内重复的操作按钮（非单例控件）不应误报重复控件。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "┌ 标题栏 ─────────────────┐\n"
            "│ 表格列1   │ 表格列2      │\n"
            "│ 主机A   │ [详情]        │\n"
            "│ 主机B   │ [详情]        │\n"
            "└────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertNotIn("WIREFRAME_DUPLICATE_CONTROL", {e.get("errorCode") for e in report.get("warnings", [])})

    def test_wireframe_label_list_fails(self):
        """区域标签罗列式线框图（每行一个'区域名：内容' + 横线分隔）-> RULE-34 error 阻断。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "+----------------------------------------------------------+\n"
            "| 全局导航：数据资产管理 / 主机资产\n"
            "+----------------------------------------------------------+\n"
            "| 页面标题栏：主机资产 [返回] [刷新]\n"
            "+----------------------------------------------------------+\n"
            "| 筛选工具栏：高级搜索框 / 关键词\n"
            "+----------------------------------------------------------+\n"
            "| 表格列表：主机名 | IP | 状态 | 操作\n"
            "+----------------------------------------------------------+\n"
            "| 分页区：上一页 1 2 3 下一页\n"
            "+----------------------------------------------------------+"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertFalse(report.get("valid"))
        self.assertTrue(any(e.get("errorCode") == "WIREFRAME_ASCII_LABEL_LIST" for e in report.get("errors", [])))

    def test_wireframe_full_layout_passes(self):
        """完整页面布局字符画（内容行左右竖线闭合、含容器嵌套）-> RULE-34 通过。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "┌──────────────────────────────────┐\n"
            "│ 主机资产                [刷新] [导出] │\n"
            "├──────────────────────────────────┤\n"
            "│ [筛选：主机名 关键词]      [查询]  │\n"
            "│ [新增] [批量编辑] [删除]          │\n"
            "│ ┌──────────────────────────────┐ │\n"
            "│ │ 主机名 | IP | 状态 | 操作    │ │\n"
            "│ │ 主机A   | 1.1.1.1 | 在线 | … │ │\n"
            "│ └──────────────────────────────┘ │\n"
            "│ 上一页 1 2 3 下一页               │\n"
            "└──────────────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode") == "WIREFRAME_ASCII_LABEL_LIST" for e in report.get("errors", [])))

    def test_child_page_not_flattened_fails(self):
        """子容器以完整页面对象内嵌在父页面 children 中 -> RULE-35 CHILD_PAGE_NOT_FLATTENED 阻断。"""
        page = base_page()
        modal = modal_page()
        page["children"] = [modal]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertFalse(report.get("valid"))
        self.assertTrue(any(e.get("errorCode") == "CHILD_PAGE_NOT_FLATTENED" for e in report.get("errors", [])))

    def test_child_string_ref_passes(self):
        """children 使用字符串 ID 引用（子容器为 pages 独立元素）-> RULE-35 通过且不崩溃。"""
        page = base_page()
        modal = modal_page()
        page["children"] = ["P02"]
        if not page.get("operations"):
            page["operations"] = []
        page["operations"].append({"name": "批量编辑", "action": "open-container", "targetPageId": "P02", "description": "打开弹窗"})
        code, report = run_validator(make_spec([page, modal]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode") == "CHILD_PAGE_NOT_FLATTENED" for e in report.get("errors", [])))

    def test_requirement_field_missing_fails(self):
        """需求明确字段未落入任何字段数组 -> RULE-36 REQUIRED_FIELD_MISSING 阻断。"""
        page = base_page()
        page["requirementFieldNames"] = ["主机名", "IP地址", "操作系统"]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQUIRED_FIELD_MISSING" for e in report.get("errors", [])))

    def test_requirement_field_all_covered_passes(self):
        """需求明确字段全部落入字段数组 -> RULE-36 通过。"""
        page = base_page()
        names = []
        for s in page.get("sections", []):
            for k in ("tableFields", "formFields", "cardFields", "fields"):
                for f in s.get(k) or []:
                    if f.get("name"):
                        names.append(f["name"])
        page["requirementFieldNames"] = names
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertFalse(any(e.get("errorCode") == "REQUIRED_FIELD_MISSING" for e in report.get("errors", [])))

    def test_requirement_field_excluded_passes(self):
        """需求字段未落位但 excludedFields 声明排除原因 -> RULE-36 通过。"""
        page = base_page()
        page["requirementFieldNames"] = ["主机名"]
        page["excludedFields"] = {"主机名": "仅在详情页展示，列表不展示"}
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertFalse(any(e.get("errorCode") == "REQUIRED_FIELD_MISSING" for e in report.get("errors", [])))

    def test_footer_ascii_order_mismatch_fails(self):
        """线框图中按钮顺序错误（取消在左、确定在右）-> RULE-37 FOOTER_ASCII_ORDER_MISMATCH 阻断。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/取消/确定"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "FOOTER_ASCII_ORDER_MISMATCH" for e in report.get("errors", [])))

    def test_footer_ascii_order_passes(self):
        """线框图中按钮顺序正确（确定在左、取消在右）-> RULE-37 通过。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/确定/取消"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertFalse(any(e.get("errorCode") == "FOOTER_ASCII_ORDER_MISMATCH" for e in report.get("errors", [])))

    def test_footer_ascii_button_missing_fails(self):
        """底部只画关闭、一个模板按钮都没画（P09/P10 静默通过场景）-> RULE-37 FOOTER_ASCII_BUTTON_MISSING 阻断。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/关闭"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("FOOTER_ASCII_BUTTON_MISSING", error_codes(report))

    def test_footer_ascii_custom_button_without_override_fails(self):
        """底部操作区出现模板允许集合外的自定义按钮（保存并关闭）且未 override -> RULE-37 FOOTER_ASCII_CUSTOM_BUTTON 阻断。"""
        page = modal_page()
        page["wireframe"]["ascii"] = (
            "┌──────────────────────┐\n"
            "│ 弹窗标题             │\n"
            "├──────────────────────┤\n"
            "│ 表单主体             │\n"
            "├──────────────────────┤\n"
            "│ 取消 [保存并关闭]     │\n"
            "└──────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("FOOTER_ASCII_CUSTOM_BUTTON", error_codes(report))

    def test_footer_ascii_custom_button_with_override_passes(self):
        """自定义底部按钮经 templateContract.override 声明后不再判为模板外按钮 -> RULE-37 不报 CUSTOM_BUTTON。"""
        page = modal_page()
        page["wireframe"]["ascii"] = (
            "┌──────────────────────┐\n"
            "│ 弹窗标题             │\n"
            "├──────────────────────┤\n"
            "│ 表单主体             │\n"
            "├──────────────────────┤\n"
            "│ 确定 取消 [保存并关闭] │\n"
            "└──────────────────────┘"
        )
        page["templateContract"]["override"] = {
            "enabled": True, "source": "产品业务规范 v1", "reason": "业务需要保存并关闭", "affectedRules": ["RULE-37"],
        }
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("FOOTER_ASCII_CUSTOM_BUTTON", error_codes(report))
        self.assertNotIn("FOOTER_ASCII_BUTTON_MISSING", error_codes(report))

    def test_wireframe_duplicate_region_warns(self):
        """同一区域（步骤条）在 ascii 中被绘制多次 -> RULE-46 WIREFRAME_DUPLICATE_REGION（warning）。"""
        page = base_page()
        page["wireframe"]["ascii"] = "标题栏/筛选/工具栏/步骤条\n步骤条：第1步\n表格/分页"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("WIREFRAME_DUPLICATE_REGION", warning_codes(report))

    def _prosearch_page(self, flat_row=None):
        """构造声明高级搜索（IxProSearch）的表格页。flat_row 为额外的平铺筛选行文本。"""
        page = base_page()
        page["wireframe"]["ascii"] = "\n".join([
            "标题栏：主机资产",
            "高级搜索框：关键词/状态/时间范围（IxProSearch）",
            "表格列表：主机名 | IP | 状态 | 操作",
            "分页区：上一页 1 2 3 下一页",
        ] + ([flat_row] if flat_row else []))
        item = {"id": "P01-C03", "scope": "filter", "name": "高级搜索组件（IxProSearch）",
                "mode": "component-reuse", "mappingRef": "M03", "mappingStatus": "verified",
                "target": {"path": "common-design", "component": "IxProSearch"},
                "requirements": ["关键词/状态/时间范围搜索"], "acceptanceCriteria": ["筛选搜索收敛在高级搜索组件内"]}
        page.setdefault("codingGuide", {})["pageItems"] = [item]
        return page

    def test_prosearch_filter_duplicate_warns(self):
        """声明高级搜索（IxProSearch）却单独绘制筛选区行 -> RULE-46 WIREFRAME_PROSEARCH_FILTER_DUPLICATE（warning）。"""
        page = self._prosearch_page(flat_row="筛选区：状态 [全部] 级别 [全部]")
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("WIREFRAME_PROSEARCH_FILTER_DUPLICATE", warning_codes(report))

    def test_prosearch_filter_converged_passes(self):
        """声明高级搜索且线框图只画高级搜索组件 -> 不告警。"""
        page = self._prosearch_page()
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("WIREFRAME_PROSEARCH_FILTER_DUPLICATE",
                         [e.get("errorCode") for e in report.get("warnings", []) + report.get("errors", [])])

    def test_prosearch_absent_skips(self):
        """未声明高级搜索、使用平铺筛选 -> 平铺筛选行合法，不出该码。"""
        page = base_page()
        page["wireframe"]["ascii"] = "\n".join([
            "标题栏：主机资产",
            "筛选区：状态 [全部] 级别 [全部] [查询] [重置]",
            "表格列表：主机名 | IP | 状态 | 操作",
            "分页区：上一页 1 2 3 下一页",
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("WIREFRAME_PROSEARCH_FILTER_DUPLICATE",
                         [e.get("errorCode") for e in report.get("warnings", []) + report.get("errors", [])])

    def test_wireframe_column_alignment_warns(self):
        """内容行右边界错位（两列结构断裂）-> RULE-47 WIREFRAME_COLUMN_ALIGNMENT（warning）。"""
        page = base_page()
        page["wireframe"]["ascii"] = "\n".join([
            "┌" + "─" * 24 + "┐",
            "│ 标题栏" + " " * 18 + "│",
            "├" + "─" * 24 + "┤",
            "│ 表格" + " " * 18 + "│",
            "│ 分页" + " " * 22 + "│",
            "│ 底部" + " " * 18 + "│",
            "└" + "─" * 26 + "┘",
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("WIREFRAME_COLUMN_ALIGNMENT", warning_codes(report))

    # ---- 表格与详情字段一致性（RULE-38）----
    def test_table_detail_field_mismatch_fails(self):
        """表格字段在详情容器中缺失 -> RULE-38 TABLE_DETAIL_FIELD_MISMATCH 阻断。"""
        table = base_page()
        table["operations"] = [
            {"id": "OP01", "action": "open-container", "label": "查看详情", "trigger": "行内操作",
             "targetPageId": "D01", "targetContainerType": "drawer", "confirm": False},
        ]
        detail = drawer_detail_page()
        detail["sections"] = [
            {"title": "基本信息", "type": "detail",
             "detailFields": [{"name": "描述", "iduxComponent": "IxText"}]},
        ]  # 详情缺少表格字段“策略名称”
        code, report = run_validator(make_spec([table, detail]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "TABLE_DETAIL_FIELD_MISMATCH" for e in report.get("errors", [])))

    def test_table_detail_field_consistent_passes(self):
        """表格字段全部能在详情容器中找到 -> RULE-38 通过。"""
        table = base_page()
        table["operations"] = [
            {"id": "OP01", "action": "open-container", "label": "查看详情", "trigger": "行内操作",
             "targetPageId": "D01", "targetContainerType": "drawer", "confirm": False},
        ]
        detail = drawer_detail_page()  # 详情包含表格字段“策略名称”
        code, report = run_validator(make_spec([table, detail]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode") == "TABLE_DETAIL_FIELD_MISMATCH" for e in report.get("errors", [])))

    def test_table_detail_without_detail_skips(self):
        """表格页没有关联详情容器（非“表格有详情”场景）-> RULE-38 不校验。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode") == "TABLE_DETAIL_FIELD_MISMATCH" for e in report.get("errors", [])))

    def test_table_detail_via_children_fails(self):
        """详情容器通过 children 字符串 ID 挂载时同样校验 -> 字段缺失阻断。"""
        table = base_page()
        table["children"] = ["D01"]
        detail = drawer_detail_page()
        detail["sections"] = [
            {"title": "基本信息", "type": "detail",
             "detailFields": [{"name": "描述", "iduxComponent": "IxText"}]},
        ]  # 详情缺少表格字段“策略名称”
        code, report = run_validator(make_spec([table, detail]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "TABLE_DETAIL_FIELD_MISMATCH" for e in report.get("errors", [])))

    # ---- 字段形态键契约（RULE-41）：内容必须写在渲染器实际渲染的键上 ----
    def test_form_field_options_not_rendered_fails(self):
        """表单字段把选项/说明写在 options/description -> FORM_FIELD_KEY_MISMATCH 阻断（HTML 会静默空列）。"""
        page = modal_page()
        page["sections"] = [
            {"title": "表单主体", "type": "form", "formFields": [
                {"name": "策略名称", "iduxComponent": "IxInput", "options": ["A", "B"], "description": "长度不超过64字符"},
            ]},
        ]
        code, report = run_validator(make_spec([base_page(), page]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "FORM_FIELD_KEY_MISMATCH" for e in report.get("errors", [])))

    def test_form_field_key_placed_wrong_warns(self):
        """表单字段同时有异态键与渲染键 -> FORM_FIELD_KEY_PLACED_WRONG warning（内容已渲染，不升为 error）。"""
        page = modal_page()
        page["sections"] = [
            {"title": "表单主体", "type": "form", "formFields": [
                {"name": "策略名称", "iduxComponent": "IxInput", "options": ["A", "B"], "rules": "长度不超过64字符"},
            ]},
        ]
        code, report = run_validator(make_spec([base_page(), page]), strict=True)
        self.assertTrue(any(w.get("errorCode") == "FORM_FIELD_KEY_PLACED_WRONG" for w in report.get("warnings", [])))
        self.assertFalse(any(e.get("errorCode") == "FORM_FIELD_KEY_MISMATCH" for e in report.get("errors", [])))

    def test_form_legacy_fields_options_not_rendered_fails(self):
        """表单区块用自由 fields 数组写字典且键为 options/description -> 按表单键契约阻断。"""
        page = modal_page()
        page["sections"] = [
            {"title": "表单主体", "type": "form", "fields": [
                {"name": "策略名称", "iduxComponent": "IxInput", "options": ["A", "B"], "description": "长度不超过64字符"},
            ]},
        ]
        code, report = run_validator(make_spec([base_page(), page]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "FORM_FIELD_KEY_MISMATCH" for e in report.get("errors", [])))

    def test_filter_field_rules_not_rendered_fails(self):
        """筛选项字段写 rules/tips -> FILTER_FIELD_KEY_MISMATCH 阻断。"""
        page = base_page()
        for s in page["sections"]:
            if s.get("type") == "filter":
                s["filterFields"] = [{"name": "策略名称", "iduxComponent": "IxInput", "rules": "模糊匹配", "tips": "支持回车搜索"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "FILTER_FIELD_KEY_MISMATCH" for e in report.get("errors", [])))

    def test_table_field_rules_not_rendered_fails(self):
        """表格字段写 rules/tips -> TABLE_FIELD_KEY_MISMATCH 阻断。"""
        page = base_page()
        for s in page["sections"]:
            if s.get("type") == "table":
                s["tableFields"] = [{"name": "策略名称", "iduxComponent": "IxText", "rules": "必填", "tips": "支持排序"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "TABLE_FIELD_KEY_MISMATCH" for e in report.get("errors", [])))

    def test_field_key_contract_passes(self):
        """字段内容写在渲染键上（含合法空栏）-> RULE-41 不误报；base_page 单页全链路通过。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        self.assertEqual(code, 0)
        page = modal_page()
        page["sections"] = [
            {"title": "表单主体", "type": "form", "formFields": [
                {"name": "策略名称", "iduxComponent": "IxInput", "required": "是", "default": "-", "rules": "必填；长度不超过64字符", "tips": "名称在同终端组内唯一"},
            ]},
        ]
        code, report = run_validator(make_spec([base_page(), page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(e.get("errorCode", "").startswith(("FORM_FIELD_KEY", "FILTER_FIELD_KEY", "TABLE_FIELD_KEY")) for e in all_issues))

    # ---- 下拉选项完整性（RULE-48）：固定选项须完整枚举，禁止举例代替枚举 ----
    def _filter_page_with_options(self, page, field):
        for s in page["sections"]:
            if s.get("type") == "filter":
                s["filterFields"] = [field]
        return page

    def test_requirement_option_missing_fails(self):
        """声明 requirementOptionSets 但选项单元格未列全 -> REQUIRED_OPTION_MISSING 阻断。"""
        page = base_page()
        page["requirementOptionSets"] = [{"field": "生效范围", "options": ["全部终端", "指定终端组", "指定终端"]}]
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect",
            "options": "全部终端/指定终端组",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("REQUIRED_OPTION_MISSING", error_codes(report))

    def test_requirement_option_all_present_passes(self):
        """声明 requirementOptionSets 且选项单元格完整列出 -> RULE-48 不误报。"""
        page = base_page()
        page["requirementOptionSets"] = [{"field": "生效范围", "options": ["全部终端", "指定终端组", "指定终端"]}]
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect",
            "options": "全部终端/指定终端组/指定终端",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")).startswith(("REQUIRED_OPTION", "OPTION_")) for i in all_issues))

    def test_option_set_field_not_found_fails(self):
        """requirementOptionSets 声明的字段不存在于任何字段数组 -> OPTION_FIELD_NOT_FOUND 阻断。"""
        page = base_page()
        page["requirementOptionSets"] = [{"field": "不存在的下拉字段", "options": ["A", "B"]}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("OPTION_FIELD_NOT_FOUND", error_codes(report))

    def test_option_truncation_marker_warns(self):
        """选择类字段选项写截断表达（如 '高/中/低等'）-> OPTION_TRUNCATION_MARKER warning。"""
        page = base_page()
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉多选", "iduxComponent": "IxSelect",
            "options": "全部终端/指定终端组/自定义等",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("OPTION_TRUNCATION_MARKER", warning_codes(report))

    def test_option_dimension_lost_warns(self):
        """声明 dimension=group 但选项单元格被压成单层列表 -> OPTION_DIMENSION_LOST warning。"""
        page = base_page()
        page["requirementOptionSets"] = [{
            "field": "生效范围", "dimension": "group",
            "options": ["全部终端", "指定终端组", "指定终端"],
        }]
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect",
            "options": "全部终端/指定终端组/指定终端",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("OPTION_DIMENSION_LOST", warning_codes(report))

    def test_option_dimension_kept_passes(self):
        """声明 dimension=group 且选项单元格保留“组名：选项”结构 -> 不误报。"""
        page = base_page()
        page["requirementOptionSets"] = [{
            "field": "生效范围", "dimension": "group",
            "options": ["终端组A", "终端1", "终端2", "终端组B", "终端3"],
        }]
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉多选", "iduxComponent": "IxSelect",
            "options": "终端组A：终端1/终端2；终端组B：终端3",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(i.get("errorCode") == "OPTION_DIMENSION_LOST" for i in all_issues))

    def test_option_dimension_inferred_from_columns_warns(self):
        """未写 dimension 但 sourceColumns 声明 >=2 列（分组列+值列）-> 视为 group 并校验。"""
        page = base_page()
        page["requirementOptionSets"] = [{
            "field": "生效范围", "sourceColumns": ["终端组", "终端"],
            "options": ["终端组A", "终端1", "终端组B", "终端2"],
        }]
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect",
            "options": "终端组A/终端1/终端组B/终端2",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("OPTION_DIMENSION_LOST", warning_codes(report))

    def test_option_dimension_flat_skips(self):
        """dimension 缺省（flat）时不做维度校验 -> 单层列表不误报。"""
        page = base_page()
        page["requirementOptionSets"] = [{
            "field": "生效范围",
            "options": ["全部终端", "指定终端组", "指定终端"],
        }]
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect",
            "options": "全部终端/指定终端组/指定终端",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(i.get("errorCode") == "OPTION_DIMENSION_LOST" for i in all_issues))

    def test_option_completeness_skips_without_declaration(self):
        """未声明 requirementOptionSets 且选项单元格无截断标记 -> RULE-48 不误报。"""
        page = base_page()
        page = self._filter_page_with_options(page, {
            "name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect",
            "options": "全部终端/指定终端组",
        })
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")).startswith(("REQUIRED_OPTION", "OPTION_")) for i in all_issues))

    # ---- 详情页字段去重（RULE-49）：概览卡片/对象摘要字段不在描述列表重复 ----
    @staticmethod
    def _table_with_detail(detail):
        table = base_page()
        table["operations"] = [
            {"id": "OP01", "action": "open-container", "label": "查看详情", "trigger": "行内操作",
             "targetPageId": "D01", "targetContainerType": "drawer", "confirm": False},
        ]
        return [table, detail]

    def test_detail_field_duplicate_warns(self):
        """概览卡片(cardFields)字段又出现在详情描述列表 -> RULE-49 DETAIL_FIELD_DUPLICATE 告警。"""
        detail = drawer_detail_page()
        detail["cardFields"] = [{"name": "策略名称"}, {"name": "状态"}]
        code, report = run_validator(make_spec(self._table_with_detail(detail)), strict=True)
        self.assertIn("DETAIL_FIELD_DUPLICATE", warning_codes(report))

    def test_detail_summary_fields_declared_warns(self):
        """声明 detailSummaryFields 且该字段在描述列表重复 -> RULE-49 告警。"""
        detail = drawer_detail_page()
        detail["detailSummaryFields"] = ["策略名称"]
        code, report = run_validator(make_spec(self._table_with_detail(detail)), strict=True)
        self.assertIn("DETAIL_FIELD_DUPLICATE", warning_codes(report))

    def test_detail_field_dedup_exempt_passes(self):
        """detailDedupExempt 豁免的字段不触发去重告警。"""
        detail = drawer_detail_page()
        detail["detailSummaryFields"] = ["策略名称"]
        detail["detailDedupExempt"] = {"策略名称": "需在详情中可编辑，属有意重复"}
        code, report = run_validator(make_spec(self._table_with_detail(detail)), strict=True)
        self.assertNotIn("DETAIL_FIELD_DUPLICATE", warning_codes(report))
        self.assertEqual(code, 0)

    def test_detail_field_duplicated_in_list_fails(self):
        """同一详情描述列表内字段重复 -> RULE-49 DETAIL_FIELD_DUPLICATED_IN_LIST 阻断。"""
        detail = drawer_detail_page()
        detail["sections"] = [
            {"title": "基本信息", "type": "detail",
             "detailFields": [{"name": "策略名称"}, {"name": "策略名称"}]},
        ]
        code, report = run_validator(make_spec(self._table_with_detail(detail)), strict=True)
        self.assertIn("DETAIL_FIELD_DUPLICATED_IN_LIST", error_codes(report))
        self.assertEqual(code, 1)

    def test_detail_field_dedup_skips_non_detail_page(self):
        """非详情类页面不触发 RULE-49 去重。"""
        page = base_page()
        page["cardFields"] = [{"name": "策略名称"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("DETAIL_FIELD_DUPLICATE", warning_codes(report))

    def test_detail_summary_card_section_duplicate_warns(self):
        """未声明 detailSummaryFields 时，摘要卡片型区块与描述列表同字段 -> DETAIL_FIELD_DUPLICATE。"""
        page = drawer_detail_page()
        page["sections"] = [
            {"title": "对象摘要", "type": "object-summary", "fields": ["策略名称", "启用状态"]},
            {"title": "基本信息", "type": "detail", "detailFields": [{"name": "策略名称"}, {"name": "描述"}]},
        ]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("DETAIL_FIELD_DUPLICATE", warning_codes(report))

    # ---- 按钮/可点击操作表（RULE-50）----
    @staticmethod
    def _page_with_actions(actions, rules=None):
        page = base_page()
        page["sections"][-1]["actions"] = actions
        if rules is not None:
            page["actionRules"] = rules
        return page

    def test_action_high_impact_missing_text_fails(self):
        """高影响操作（删除）缺二次确认文案 -> ACTION_CONFIRM_TEXT_MISSING 阻断。"""
        page = self._page_with_actions([
            {"name": "删除", "trigger": "标准确认弹窗", "component": "IxModal.confirm",
             "source": "common-design", "sourceRef": "common-design/references/05-components/idux-component-map.md#modal"}
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("ACTION_CONFIRM_TEXT_MISSING", error_codes(report))

    def test_action_high_impact_complete_passes(self):
        """高影响操作写全组件、文案与来源 -> 无 ACTION_ 问题。"""
        page = self._page_with_actions([
            {"name": "删除", "trigger": "标准确认弹窗", "component": "IxModal.confirm",
             "text": "确认删除吗？\n删除后，数据不可恢复，请谨慎操作。", "feedback": "删除成功后从列表移除",
             "source": "common-design", "sourceRef": "common-design/references/05-components/idux-component-map.md#modal"}
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        allc = error_codes(report) | warning_codes(report)
        self.assertFalse(any(c and c.startswith("ACTION_") for c in allc))

    def test_action_source_ai_fill_warns(self):
        """组件/文案来源标为 ai-fill（AI 自拟）-> ACTION_SOURCE_NOT_TRACED 告警。"""
        page = self._page_with_actions([
            {"name": "移动", "trigger": "局部面板", "component": "下拉面板",
             "fields": ["目标类型选择框", "之前/之后 下拉框"], "source": "ai-fill"}
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("ACTION_SOURCE_NOT_TRACED", warning_codes(report))

    def test_action_component_missing_warns(self):
        """操作涉及二次确认/局部面板但未写组件 -> ACTION_COMPONENT_MISSING 告警。"""
        page = self._page_with_actions([
            {"name": "移动", "trigger": "局部面板", "text": "确认移动吗？",
             "source": "common-design", "sourceRef": "common-design/references/x.md#y"}
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("ACTION_COMPONENT_MISSING", warning_codes(report))

    def test_action_legacy_string_skipped(self):
        """旧字符串写法（actions 为字符串列表）兼容，不触发 RULE-50。"""
        page = self._page_with_actions(["查询：按条件刷新表格", "重置：清空条件并恢复默认列表"])
        code, report = run_validator(make_spec([page]), strict=True)
        allc = error_codes(report) | warning_codes(report)
        self.assertFalse(any(c and c.startswith("ACTION_") for c in allc))

    def test_action_rules_configurable(self):
        """actionRules 可扩展高影响操作名并支持豁免。"""
        page = self._page_with_actions(
            [{"name": "灰度放量", "trigger": "标准确认弹窗", "component": "IxModal.confirm"}],
            rules={"highImpactActions": ["灰度放量"]},
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("ACTION_CONFIRM_TEXT_MISSING", error_codes(report))
        page2 = self._page_with_actions(
            [{"name": "灰度放量", "trigger": "标准确认弹窗", "component": "IxModal.confirm"}],
            rules={"highImpactActions": ["灰度放量"], "exempt": ["灰度放量"]},
        )
        code2, report2 = run_validator(make_spec([page2]), strict=True)
        self.assertNotIn("ACTION_CONFIRM_TEXT_MISSING", error_codes(report2))

    # ---- 表格区按钮位置（RULE-51，线框图）----
    @staticmethod
    def _page_with_ascii(ascii_text):
        page = base_page()
        page["wireframe"]["ascii"] = ascii_text
        return page

    def test_table_button_below_table_warns(self):
        """表格关联按钮绘制在表格框下方 -> RULE-51 TABLE_BUTTON_MISPLACED 告警。"""
        page = self._page_with_ascii(
            "┌──────────────────┐\n"
            "│ 页面标题          │\n"
            "├──────────────────┤\n"
            "│ ┌──────────────┐ │\n"
            "│ │ 名称 | 状态   │ │\n"
            "│ │ A | 高        │ │\n"
            "│ └──────────────┘ │\n"
            "│ [批量操作] [新增] │\n"
            "│ 上一页 1 2 下一页 │\n"
            "└──────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("TABLE_BUTTON_MISPLACED", warning_codes(report))

    def test_table_button_in_toolbar_passes(self):
        """表格按钮置于表格框上方工具栏 -> 不产生 RULE-51 提示。"""
        page = self._page_with_ascii(
            "┌──────────────────┐\n"
            "│ 页面标题          │\n"
            "├──────────────────┤\n"
            "│ [批量操作] [新增] │\n"
            "│ ┌──────────────┐ │\n"
            "│ │ 名称 | 状态   │ │\n"
            "│ │ A | 高        │ │\n"
            "│ └──────────────┘ │\n"
            "│ 上一页 1 2 下一页 │\n"
            "└──────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")) in ("TABLE_BUTTON_MISPLACED", "TABLE_ACTION_NOT_IN_TOOLBAR") for i in all_issues))

    def test_table_pagination_not_flagged(self):
        """表格框下方仅分页/边框 -> 不误报。"""
        page = self._page_with_ascii(
            "┌──────────────────┐\n"
            "│ 页面标题          │\n"
            "├──────────────────┤\n"
            "│ ┌──────────────┐ │\n"
            "│ │ 名称 | 状态   │ │\n"
            "│ └──────────────┘ │\n"
            "│ 上一页 1 2 下一页 共 20 条 │\n"
            "└──────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")) in ("TABLE_BUTTON_MISPLACED", "TABLE_ACTION_NOT_IN_TOOLBAR") for i in all_issues))

    def test_table_batch_action_outside_warns(self):
        """批量操作按钮绘制在表格工具栏之外（如概览区）-> TABLE_ACTION_NOT_IN_TOOLBAR 告警。"""
        page = self._page_with_ascii(
            "┌──────────────────┐\n"
            "│ ┌──────────────┐ │\n"
            "│ │ [批量删除]     │ │\n"
            "│ └──────────────┘ │\n"
            "│ ┌──────────────┐ │\n"
            "│ │ 名称 | 状态   │ │\n"
            "│ └──────────────┘ │\n"
            "└──────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("TABLE_ACTION_NOT_IN_TOOLBAR", warning_codes(report))

    def test_table_button_check_skips_without_table(self):
        """ascii 中无表格框 -> RULE-51 跳过，不误报。"""
        page = self._page_with_ascii(
            "┌──────────────────┐\n"
            "│ 页面标题          │\n"
            "│ [批量操作]        │\n"
            "└──────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")) in ("TABLE_BUTTON_MISPLACED", "TABLE_ACTION_NOT_IN_TOOLBAR") for i in all_issues))

    # ---- 列设置为表格组件自带功能（RULE-51 扩展）----
    def test_column_setting_drawn_warns(self):
        """线框图工具栏画列设置按钮 -> WIREFRAME_COLUMN_SETTING_DRAWN 告警。"""
        page = self._page_with_ascii(
            "┌──────────────────────────┐\n"
            "│ [新增] [批量删除] [列设置]  │\n"
            "│ ┌──────────────────────┐ │\n"
            "│ │ 名称 | 状态           │ │\n"
            "│ └──────────────────────┘ │\n"
            "└──────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("WIREFRAME_COLUMN_SETTING_DRAWN", warning_codes(report))

    def test_column_setting_absent_passes(self):
        """未绘制列设置按钮 -> 不告警。"""
        page = self._page_with_ascii(
            "┌──────────────────────────┐\n"
            "│ [新增] [批量删除]           │\n"
            "│ ┌──────────────────────┐ │\n"
            "│ │ 名称 | 状态           │ │\n"
            "│ └──────────────────────┘ │\n"
            "└──────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("WIREFRAME_COLUMN_SETTING_DRAWN", warning_codes(report))

    def test_column_setting_below_table_no_misplaced(self):
        """列设置画在表格下方 -> 仅报 WIREFRAME_COLUMN_SETTING_DRAWN，不再叠加 TABLE_BUTTON_MISPLACED。"""
        page = self._page_with_ascii(
            "┌──────────────────────────┐\n"
            "│ ┌──────────────────────┐ │\n"
            "│ │ 名称 | 状态           │ │\n"
            "│ └──────────────────────┘ │\n"
            "│ [列设置]                  │\n"
            "└──────────────────────────┘"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("WIREFRAME_COLUMN_SETTING_DRAWN", warning_codes(report))
        self.assertNotIn("TABLE_BUTTON_MISPLACED", warning_codes(report))

    # ---- 表格标签使用约束（RULE-39）----
    def test_table_tag_count_exceeded_fails(self):
        """同一表格内标签数量超过 5 -> RULE-39 TABLE_TAG_COUNT_EXCEEDED 阻断。"""
        fields = [{"name": f"状态字段{i}", "display": "浅色标签", "iduxComponent": "IxTag"} for i in range(6)]
        code, report = run_validator(make_spec([tag_page(fields)]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "TABLE_TAG_COUNT_EXCEEDED" for e in report.get("errors", [])))

    def test_table_tag_style_overused_fails(self):
        """深色标签出现 2 次 -> RULE-39 TABLE_TAG_STYLE_OVERUSED 阻断。"""
        fields = [
            {"name": "风险等级", "display": "深色标签", "iduxComponent": "IxTag", "description": "高/中/低"},
            {"name": "处置状态", "display": "深色标签", "iduxComponent": "IxTag", "description": "待处置/已处置"},
        ]
        code, report = run_validator(make_spec([tag_page(fields)]), strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "TABLE_TAG_STYLE_OVERUSED" for e in report.get("errors", [])))

    def test_table_tag_style_unspecified_warns(self):
        """多个标签字段样式未标注 -> RULE-39 TABLE_TAG_STYLE_UNSPECIFIED warning（不阻断）。"""
        fields = [
            {"name": "风险等级", "display": "单标签", "iduxComponent": "IxTag"},
            {"name": "处置状态", "display": "单标签", "iduxComponent": "IxTag"},
        ]
        code, report = run_validator(make_spec([tag_page(fields)]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "TABLE_TAG_STYLE_UNSPECIFIED" for w in report.get("warnings", [])))

    def test_table_tag_neutral_field_warns(self):
        """中性描述字段使用标签 -> RULE-39 TABLE_TAG_NEUTRAL_FIELD warning（不阻断）。"""
        fields = [
            {"name": "资产类型", "display": "单标签", "iduxComponent": "IxTag"},
            {"name": "风险等级", "display": "浅色标签", "iduxComponent": "IxTag", "description": "高/中/低"},
        ]
        code, report = run_validator(make_spec([tag_page(fields)]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "TABLE_TAG_NEUTRAL_FIELD" for w in report.get("warnings", [])))

    def test_table_tag_usage_passes(self):
        """标签总数与样式均符合配额 -> RULE-39 通过，无 TABLE_TAG_* 错误或警告。"""
        fields = [
            {"name": "风险等级", "display": "深色标签", "iduxComponent": "IxTag", "description": "高/中/低"},
            {"name": "处置状态", "display": "状态点+文字", "iduxComponent": "IxBadge/IxTag", "description": "待处置/处理中/已处置"},
            {"name": "标签", "display": "浅色标签", "iduxComponent": "IxTag", "description": "自定义标签"},
            {"name": "启用状态", "display": "浅色标签", "iduxComponent": "IxTag", "description": "启用/禁用"},
        ]
        code, report = run_validator(make_spec([tag_page(fields)]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode", "").startswith("TABLE_TAG_") for e in report.get("errors", [])))
        self.assertFalse(any(w.get("errorCode", "").startswith("TABLE_TAG_") for w in report.get("warnings", [])))

    # ---- 设计依据可追溯（RULE-40）----
    def _page_claiming_design(self, refs=None, claimed_source="Product Design: 策略配置主题框架"):
        """构造声称引用 Product Design 的页面；refs 为 None 表示不写 designReferences。"""
        tc = base_page()["templateContract"]
        tc["override"] = {"enabled": True, "source": claimed_source, "reason": "业务覆盖", "affectedRules": []}
        page = base_page(templateContract=tc)
        if refs is not None:
            page["codingGuide"]["designReferences"] = refs
        return page

    def test_design_ref_missing_fails(self):
        """页面声称引用 Product Design 但无 designReferences -> RULE-40 DESIGN_REF_MISSING error（阻断）。"""
        page = self._page_claiming_design(refs=None)
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("DESIGN_REF_MISSING", error_codes(report))

    def test_design_ref_invalid_source_warns(self):
        """designReferences 的 source 非法 -> RULE-40 DESIGN_REF_SOURCE warning。"""
        page = self._page_claiming_design(refs=[{"source": "common", "ref": "Common Design 页面模板: 概览表格页"}])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "DESIGN_REF_SOURCE" for w in report.get("warnings", [])))

    def test_design_ref_empty_ref_warns(self):
        """designReferences 的 ref 为空 -> RULE-40 DESIGN_REF_REF warning。"""
        page = self._page_claiming_design(refs=[{"source": "product-design", "ref": ""}])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "DESIGN_REF_REF" for w in report.get("warnings", [])))

    def test_design_ref_passes(self):
        """声称引用 Design Skill 且 designReferences 登记完整 -> RULE-40 通过，无 DESIGN_REF_* 警告。"""
        page = self._page_claiming_design(refs=[
            {"source": "product-design", "ref": "Product Design: 策略配置主题框架"},
            {"source": "common-design", "ref": "Common Design 页面模板: 概览表格页"},
            {"source": "ai-fill", "ref": "AI 补齐: 自动补齐筛选项"},
        ])
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(w.get("errorCode", "").startswith("DESIGN_REF_") for w in report.get("warnings", [])))

    def test_design_ref_absent_no_claim_passes(self):
        """页面未声称引用 Design Skill 且无 designReferences -> RULE-40 通过（不强制登记）。"""
        page = base_page()
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(w.get("errorCode", "").startswith("DESIGN_REF_") for w in report.get("warnings", [])))

    # ---- RULE-42 需求理解与页面设计追溯 ----

    def _trace_model(self, tasks=None, status="resolved", **extra):
        model = {
            "status": status,
            "inputType": "narrative",
            "tasks": tasks or [],
            "businessObjects": ["事件"],
            "confirmedFacts": ["用户需要处置事件"],
            "designInferences": [],
            "aiFillItems": [],
            "gaps": [],
        }
        model.update(extra)
        return model

    def _bound_page(self, task_ids=("T01",)):
        page = base_page(taskRefs=list(task_ids))
        return page

    def test_requirement_status_not_resolved_fails(self):
        """需求理解 status=needs_confirmation -> RULE-42 REQ_TRACE_STATUS_NOT_RESOLVED error 阻断。"""
        spec = make_spec([self._bound_page()])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"}],
            status="needs_confirmation")
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQ_TRACE_STATUS_NOT_RESOLVED" for e in report.get("errors", [])))

    def test_model_missing_but_task_ref_fails(self):
        """页面带 taskRefs 但顶层缺 requirementUnderstanding -> RULE-42 REQ_TRACE_MODEL_MISSING error。"""
        spec = make_spec([self._bound_page()])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQ_TRACE_MODEL_MISSING" for e in report.get("errors", [])))

    def test_page_without_task_ref_fails(self):
        """模型 resolved 但页面无 taskRefs -> RULE-42 REQ_TRACE_NO_TASK_REF error。"""
        spec = make_spec([base_page()])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQ_TRACE_NO_TASK_REF" for e in report.get("errors", [])))

    def test_task_not_bound_to_page_fails(self):
        """任务 T02 未被任何页面 taskRefs 引用 -> RULE-42 REQ_TRACE_TASK_UNBOUND error。"""
        spec = make_spec([self._bound_page(["T01"])])
        spec["requirementUnderstanding"] = self._trace_model(tasks=[
            {"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"},
            {"id": "T02", "actor": "审核员", "action": "审核事件", "outcome": "审核通过"},
        ])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQ_TRACE_TASK_UNBOUND" for e in report.get("errors", [])))

    def test_task_without_outcome_fails(self):
        """任务有 action 但无 outcome -> RULE-42 REQ_TRACE_ACTION_NO_OUTCOME error。"""
        spec = make_spec([self._bound_page()])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQ_TRACE_ACTION_NO_OUTCOME" for e in report.get("errors", [])))

    def test_task_without_action_fails(self):
        """任务缺核心动作定义 -> RULE-42 REQ_TRACE_TASK_INCOMPLETE error。"""
        spec = make_spec([self._bound_page()])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "outcome": "处置成功"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.get("errorCode") == "REQ_TRACE_TASK_INCOMPLETE" for e in report.get("errors", [])))

    def test_judge_block_field_no_purpose_warns(self):
        """区块声明 decisionPoint 但字段缺 fieldRole -> RULE-42 REQ_TRACE_FIELD_NO_PURPOSE warning。"""
        page = self._bound_page()
        page["sections"][2]["decisionPoint"] = "是否需要立即处置"
        spec = make_spec([page])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "REQ_TRACE_FIELD_NO_PURPOSE" for w in report.get("warnings", [])))

    def test_invalid_source_marker_warns(self):
        """区块 source 值非法 -> RULE-42 REQ_TRACE_SOURCE_INVALID warning。"""
        page = self._bound_page()
        page["sections"][2]["source"] = "user-guess"
        spec = make_spec([page])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "REQ_TRACE_SOURCE_INVALID" for w in report.get("warnings", [])))

    def test_invalid_field_role_warns(self):
        """判断区块字段 fieldRole 值非法 -> RULE-42 REQ_TRACE_FIELD_ROLE_INVALID warning。"""
        page = self._bound_page()
        page["sections"][2]["decisionPoint"] = "是否需要立即处置"
        page["sections"][2]["tableFields"][0]["fieldRole"] = "input"
        spec = make_spec([page])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "REQ_TRACE_FIELD_ROLE_INVALID" for w in report.get("warnings", [])))

    def test_requirement_trace_passes(self):
        """模型 resolved、任务均有页面承载与结果反馈、无判断区块缺失 -> RULE-42 通过。"""
        spec = make_spec([self._bound_page(["T01"])])
        spec["requirementUnderstanding"] = self._trace_model(
            tasks=[{"id": "T01", "actor": "处置员", "action": "处置事件", "outcome": "处置成功"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode", "").startswith("REQ_TRACE_") for e in report.get("errors", [])))
        self.assertFalse(any(w.get("errorCode", "").startswith("REQ_TRACE_") for w in report.get("warnings", [])))

    def test_requirement_trace_skipped_without_model(self):
        """历史格式：无 requirementUnderstanding 且页面无 taskRefs -> RULE-42 不启用，不产生 REQ_TRACE_*。"""
        page = base_page()
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode", "").startswith("REQ_TRACE_") for e in report.get("errors", [])))
        self.assertFalse(any(w.get("errorCode", "").startswith("REQ_TRACE_") for w in report.get("warnings", [])))


    # ---- 设计依据一致性（RULE-43，条件式：声明 designContext 时启用）----
    def _design_context(self, **overrides):
        dc = {
            "commonDesign": {"skillId": "common-design", "read": True},
            "productDesign": {"matched": False, "skillId": "", "coverage": []},
            "readLedger": [],
        }
        dc.update(overrides)
        return dc

    def _page_with_design_ref(self, refs):
        page = base_page()
        page["codingGuide"]["designReferences"] = refs
        return page

    def test_design_context_absent_skips(self):
        """未声明 designContext -> RULE-43 不启用（历史格式不误伤）。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(report.get("valid"))
        self.assertFalse(any(e.get("errorCode", "").startswith(("DESIGN_REF_UNREAD", "TEMPLATE_"))
                             for e in report.get("errors", [])))

    def test_design_context_unread_ref_fails(self):
        """designReferences 引用的 product-design 文档在 readLedger 中仅 index-only -> DESIGN_REF_UNREAD error。"""
        page = self._page_with_design_ref(
            [{"source": "product-design", "ref": "product-design/references/<sample-doc>.md#主题框架"}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            readLedger=[{"doc": "product-design/references/<sample-doc>.md", "status": "index-only"}])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("DESIGN_REF_UNREAD", error_codes(report))

    def test_design_context_consistent_passes(self):
        """product 模板覆盖 + readLedger 命中 + 反向登记 product-design -> RULE-43 通过。"""
        tc = base_page()["templateContract"]
        tc["templateBase"] = "product"
        tc["productTemplateRef"] = "product-design/references/<sample-doc>.md#policy-theme"
        tc["override"] = {"enabled": True, "source": "Product Design: 策略主题框架",
                          "reason": "业务覆盖", "affectedRules": []}
        page = base_page(templateContract=tc)
        page["codingGuide"]["designReferences"] = [
            {"source": "product-design", "ref": "product-design/references/<sample-doc>.md#policy-theme"},
            {"source": "common-design",
             "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"},
        ]
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design", "coverage": []},
            readLedger=[
                {"doc": "product-design/references/<sample-doc>.md", "status": "read"},
                {"doc": "common-design/references/02-template/01-page-types.md", "status": "read"},
            ])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertTrue(report.get("valid"))

    def test_design_context_template_override_not_applied_fails(self):
        """Product Design 声明模板覆盖，但页面仍落 common 模板 -> TEMPLATE_OVERRIDE_NOT_APPLIED error。"""
        page = self._page_with_design_ref(
            [{"source": "common-design",
              "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "template", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}]},
            readLedger=[{"doc": "common-design/references/02-template/01-page-types.md",
                         "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_OVERRIDE_NOT_APPLIED", error_codes(report))

    def test_design_context_template_source_unregistered_fails(self):
        """采用 product 模板但未登记 product-design 依据 -> TEMPLATE_SOURCE_UNREGISTERED error。"""
        tc = base_page()["templateContract"]
        tc["templateBase"] = "product"
        tc["productTemplateRef"] = "product-design/references/<sample-doc>.md#policy-theme"
        page = base_page(templateContract=tc)
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design", "coverage": []},
            readLedger=[{"doc": "product-design/references/<sample-doc>.md", "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_SOURCE_UNREGISTERED", error_codes(report))

    def test_design_context_anchor_unread_fails(self):
        """台账只精读了某文档的 A 小节，页面却引用同文档 B 小节 -> DESIGN_REF_UNREAD error（锚点级）。"""
        page = self._page_with_design_ref(
            [{"source": "product-design", "ref": "product-design/references/<sample-doc>.md#筛选区形态"}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design", "coverage": []},
            readLedger=[{"ref": "product-design/references/<sample-doc>.md#主题框架", "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("DESIGN_REF_UNREAD", error_codes(report))

    def test_design_context_whole_doc_read_passes(self):
        """台账以 <文档路径>#* 声明整篇已读 -> 任意小节引用通过。"""
        page = self._page_with_design_ref(
            [{"source": "product-design", "ref": "product-design/references/<sample-doc>.md#筛选区形态"}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design", "coverage": []},
            readLedger=[{"ref": "product-design/references/<sample-doc>.md#*", "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")

    def test_ability_source_not_registered_fails(self):
        """coverage 声明 filtering override 且页面命中，但页面未登记同 ability 的 product-design 依据 -> ABILITY_SOURCE_NOT_REGISTERED。"""
        page = self._page_with_design_ref(
            [{"source": "common-design",
              "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "filtering", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}]},
            readLedger=[{"ref": "common-design/references/02-template/01-page-types.md#page-table-basic",
                         "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("ABILITY_SOURCE_NOT_REGISTERED", error_codes(report))

    def test_ability_source_registered_passes(self):
        """页面按能力登记 product-design 依据且台账已精读 -> 通过。"""
        page = self._page_with_design_ref([
            {"source": "product-design", "ref": "product-design/references/<sample-doc>.md#筛选三态",
             "ability": "filtering"},
            {"source": "common-design",
             "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"},
        ])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "filtering", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}]},
            readLedger=[
                {"ref": "product-design/references/<sample-doc>.md#筛选三态", "status": "read"},
                {"ref": "common-design/references/02-template/01-page-types.md#page-table-basic",
                 "status": "read"},
            ])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")

    # ---- 未核验实现细节隔离（RULE-44）----
    def test_unverified_export_fails(self):
        """partial 状态编码项 target.export 非空 -> EXPORT_WITHOUT_VERIFY error。"""
        page = base_page(codeAvailability="partial")
        page["codingGuide"]["pageItems"][0]["target"] = {"export": "PolicyPage"}
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("EXPORT_WITHOUT_VERIFY", error_codes(report))

    def test_unverified_component_name_fails(self):
        """partial 状态表格字段写入未核验产品专有组件名 -> COMPONENT_WITHOUT_VERIFY error。"""
        page = base_page(codeAvailability="partial")
        page["sections"][2]["tableFields"] = [{"name": "策略名称", "iduxComponent": "AESPolicyTable"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("COMPONENT_WITHOUT_VERIFY", error_codes(report))

    def test_unverified_ix_component_passes(self):
        """partial 状态仅使用 Ix 标准组件（语义级）-> RULE-44 不误伤。"""
        page = base_page(codeAvailability="partial")
        page["codingGuide"]["pageItems"][0]["target"] = {}
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertFalse(any(e.get("errorCode") == "COMPONENT_WITHOUT_VERIFY" for e in report.get("errors", [])))

    def test_unverified_visual_baseline_fails(self):
        """partial 状态引用真实可视化基线页面 -> VISUAL_BASELINE_WITHOUT_VERIFY error。"""
        page = base_page(codeAvailability="partial")
        page["visualBaselineRef"] = "src/pages/policy/index.vue"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("VISUAL_BASELINE_WITHOUT_VERIFY", error_codes(report))

    def test_code_status_undeclared_warns(self):
        """未声明 codeAvailability -> CODE_STATUS_UNDECLARED warning，并已按 unavailable 保守处理。"""
        page = base_page()
        page.pop("codeAvailability")
        page["codingGuide"]["pageItems"][0]["target"] = {}
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(w.get("errorCode") == "CODE_STATUS_UNDECLARED" for w in report.get("warnings", [])))

    def test_code_status_in_page_context_fails(self):
        """codeAvailability 写在 codingGuide.pageContext 时也应生效（修复读取位置）-> PATH_WITHOUT_VERIFY error。"""
        page = base_page()
        page.pop("codeAvailability")
        page["codingGuide"].setdefault("pageContext", {})["codeAvailability"] = "partial"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("PATH_WITHOUT_VERIFY", error_codes(report))

    # ---- 需求入口落位闭环（RULE-52，条件式）：PRD 点名入口必须有落点 ----
    @staticmethod
    def _entry(scope="in-scope", host="P01", container="P02", evidence=None):
        entry = {"id": "EP01", "host": host, "hostScope": scope, "location": "操作列",
                 "trigger": "加入行为白名单", "container": container, "source": "PRD F1"}
        if evidence is not None:
            entry["hostEvidence"] = evidence
        return entry

    @staticmethod
    def _entry_host_with_op(ascii_text=None):
        """宿主页 P01 带"加入行为白名单"入口（open-container 指向 P02）。"""
        host = base_page()
        host["children"] = ["P02"]
        host["operations"] = [
            {"id": "OP01", "action": "open-container", "label": "加入行为白名单",
             "trigger": "行内操作", "targetPageId": "P02", "targetContainerType": "modal",
             "confirm": False},
        ]
        if ascii_text is not None:
            host["wireframe"]["ascii"] = ascii_text
        return host

    @staticmethod
    def _entry_host_ascii():
        return (
            "┌ 标题栏 ─────────────────┐\n"
            "│ [筛选] [工具栏]        │\n"
            "├──────────┬─────────────┤\n"
            "│ 表格列1   │ 加入行为白名单入口│\n"
            "├──────────┴─────────────┤\n"
            "│ [分页] 上一页 1 2 下一页 │\n"
            "└────────────────────────┘"
        )

    def test_entry_point_in_scope_placed_passes(self):
        """in-scope 宿主页面已落位入口且线框图已绘制 -> RULE-52 通过。"""
        host = self._entry_host_with_op(ascii_text=self._entry_host_ascii())
        spec = make_spec([host, modal_page()])
        spec["requirementEntryPoints"] = [self._entry()]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("ENTRY_") for e in report.get("errors", [])))
        self.assertFalse(any(w.get("errorCode") == "ENTRY_NOT_DRAWN" for w in report.get("warnings", [])))

    def test_entry_point_not_placed_fails(self):
        """in-scope 宿主页面未落位入口 -> ENTRY_POINT_NOT_PLACED 阻断。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry()]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("ENTRY_POINT_NOT_PLACED", error_codes(report))

    def test_entry_point_not_drawn_warns(self):
        """in-scope 入口已落位但线框图未绘制入口 -> ENTRY_NOT_DRAWN warning，不阻断。"""
        host = self._entry_host_with_op()  # 默认 ascii 无入口痕迹
        spec = make_spec([host, modal_page()])
        spec["requirementEntryPoints"] = [self._entry()]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("ENTRY_NOT_DRAWN", warning_codes(report))

    def test_entry_point_out_of_scope_unregistered_fails(self):
        """out-of-scope 宿主未在 entryHosts 登记 -> ENTRY_HOST_UNREGISTERED 阻断。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal")]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("ENTRY_HOST_UNREGISTERED", error_codes(report))

    def test_entry_point_out_of_scope_registered_passes(self):
        """out-of-scope 宿主已登记（Tier1 精读 + 开发项 + 线框图）-> RULE-52 通过。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal",
                                                      evidence=self._evidence())]
        spec["entryHosts"] = [
            {"id": "安全事件页", "name": "安全事件页/告警列表", "scope": "out-of-scope",
             "read": True, "readTier": "tier1", "wireframe": "【告警列表操作列：加入行为白名单入口】",
             "devItem": "P01-C01"},
        ]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("ENTRY_") for e in report.get("errors", [])))
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("HOST_") for e in report.get("errors", [])))
        self.assertFalse(any(w.get("errorCode") == "ENTRY_NOT_DRAWN" for w in report.get("warnings", [])))

    def test_entry_point_out_of_scope_missing_dev_item_fails(self):
        """out-of-scope 宿主已登记但缺对应开发项 -> ENTRY_HOST_UNREGISTERED 阻断。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal")]
        spec["entryHosts"] = [
            {"id": "安全事件页", "read": True, "readTier": "tier1", "wireframe": "x", "devItem": ""},
        ]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("ENTRY_HOST_UNREGISTERED", error_codes(report))

    def test_entry_point_out_of_scope_dangling_dev_item_fails(self):
        """out-of-scope 宿主登记了不存在的开发项 -> ENTRY_HOST_UNREGISTERED 阻断。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal")]
        spec["entryHosts"] = [
            {"id": "安全事件页", "read": True, "readTier": "tier1", "wireframe": "x", "devItem": "P99-E01"},
        ]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("ENTRY_HOST_UNREGISTERED", error_codes(report))

    def test_entry_point_incomplete_fails(self):
        """入口挂载点缺必需字段 -> ENTRY_POINT_INCOMPLETE 阻断。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [{"id": "EP01", "host": "P01", "hostScope": "in-scope"}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("ENTRY_POINT_INCOMPLETE", error_codes(report))

    def test_entry_point_skips_without_declaration(self):
        """未声明 requirementEntryPoints -> RULE-52 不启用、不误报。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")).startswith("ENTRY_") for i in all_issues))

    def test_entry_host_wireframe_placeholder_passes(self):
        """out-of-scope 宿主落位说明为一行文字（含位置与触发元素）-> 合规，不再要求绘制宿主完整线框图。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal",
                                                      evidence=self._evidence())]
        spec["entryHosts"] = [
            {"id": "安全事件页", "name": "安全事件页/告警列表", "scope": "out-of-scope",
             "read": True, "readTier": "tier1",
             "wireframe": "告警列表操作列新增【加入行为白名单】按钮，点击打开行为白名单表单抽屉，编码要求见 P01-C01",
             "devItem": "P01-C01"},
        ]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertFalse(any(w.get("errorCode") == "ENTRY_NOT_DRAWN" for w in report.get("warnings", [])))

    def test_entry_host_wireframe_vague_warns(self):
        """out-of-scope 宿主落位说明非空但未写清位置/触发元素 -> ENTRY_NOT_DRAWN warning。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal",
                                                      evidence=self._evidence())]
        spec["entryHosts"] = [
            {"id": "安全事件页", "scope": "out-of-scope",
             "read": True, "readTier": "tier1", "wireframe": "稍后补充", "devItem": "P01-C01"},
        ]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("ENTRY_NOT_DRAWN", warning_codes(report))

    # ---- 共用线框差异描述闭环（RULE-62，条件式）：相同 UI 页面共用主页面线框，只描述差异 ----
    def _shared_pages(self, host=None, shared=None):
        host = host or modal_page()
        host["operations"] = [{"id": "OP01", "name": "编辑主机资产", "action": "open-container",
                               "trigger": "行内操作", "targetPageId": "P03",
                               "targetContainerType": "modal", "confirm": False}]
        return [base_page(), host, shared or shared_modal_page()]

    def test_wireframe_shared_passes(self):
        """从页面声明共用主页面线框且 wireframeDiff 非空 -> RULE-62 通过，不重复绘制不报结构错误。"""
        code, report = run_validator(make_spec(self._shared_pages()), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        all_codes = list(error_codes(report)) + list(warning_codes(report))
        self.assertFalse(any(str(c).startswith("WIREFRAME_SHARED_") for c in all_codes))
        error_list = report.get("errors", [])
        self.assertFalse(any(e.get("errorCode") in ("REQUIRED_REGION_MISSING", "REGION_ORDER_MISMATCH",
                                                    "WIREFRAME_ASCII_TOO_SHORT") for e in error_list))

    def test_wireframe_shared_diff_missing_warns(self):
        """共用线框但 wireframeDiff 为空 -> WIREFRAME_SHARED_DIFF_MISSING warning。"""
        page = shared_modal_page()
        page["wireframeDiff"] = ""
        code, report = run_validator(make_spec(self._shared_pages(shared=page)), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("WIREFRAME_SHARED_DIFF_MISSING", warning_codes(report))

    def test_wireframe_shared_target_missing_fails(self):
        """wireframeSharedWith 指向不存在的主页面 -> WIREFRAME_SHARED_TARGET_MISSING 阻断。"""
        page = shared_modal_page()
        page["wireframeSharedWith"] = "P99"
        code, report = run_validator(make_spec(self._shared_pages(shared=page)), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("WIREFRAME_SHARED_TARGET_MISSING", error_codes(report))

    def test_wireframe_shared_target_mismatch_fails(self):
        """主页面与从页面模板/类型不一致（UI 不同，如编辑对象不一样）-> WIREFRAME_SHARED_TARGET_MISMATCH 阻断。"""
        page = shared_modal_page()
        page["type"] = "表单抽屉"
        tc = dict(page["templateContract"])
        tc["templateId"] = "form-drawer"
        page["templateContract"] = tc
        code, report = run_validator(make_spec(self._shared_pages(shared=page)), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("WIREFRAME_SHARED_TARGET_MISMATCH", error_codes(report))

    def test_wireframe_shared_chain_blocked(self):
        """主页面自身也声明共用（链式共享）-> WIREFRAME_SHARED_HOST_NOT_DRAWN 阻断。"""
        host = modal_page()
        host["wireframeSharedWith"] = "P01"
        code, report = run_validator(make_spec(self._shared_pages(host=host)), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("WIREFRAME_SHARED_HOST_NOT_DRAWN", error_codes(report))

    # ---- 设计规范补齐落位闭环（RULE-63，条件式）：designContext.designCompleteness ----
    def _page_with_delete_trace(self):
        page = base_page()
        page["operations"] = [
            {"id": "OP01", "name": "手动删除", "action": "confirm", "trigger": "行内操作", "confirm": True},
        ]
        return page

    def _completeness_item(self, **over):
        item = {
            "capability": "手动删除",
            "appliesTo": "策略对象",
            "ref": "common-design/crud-pairing.md#手动新增删除成对",
            "source": "common-design",
            "decision": "included",
            "landingRef": "P01#手动删除",
        }
        item.update(over)
        return item

    def _completeness_spec(self, items, read_status="read"):
        page = self._page_with_delete_trace()
        spec = make_spec([page])
        ledger = [{"doc": "common-design/crud-pairing.md", "status": read_status}]
        spec["designContext"] = {
            "commonDesign": {"skillId": "common-design", "read": True},
            "productDesign": {"matched": False, "skillId": "", "coverage": []},
            "readLedger": ledger,
            "designCompleteness": items,
        }
        return spec

    def test_design_completeness_passes(self):
        """补齐项落点 landingRef 指向页面操作且页面可检索到能力痕迹 -> RULE-63 通过。"""
        spec = self._completeness_spec([self._completeness_item()])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        all_codes = list(error_codes(report)) + list(warning_codes(report))
        self.assertFalse(any(str(c).startswith("COMPLETENESS_") for c in all_codes))

    def test_design_completeness_not_landed_fails(self):
        """landingRef 指向页面存在但落点处检索不到补齐能力痕迹 -> COMPLETENESS_ITEM_NOT_LANDED 阻断。"""
        item = self._completeness_item(landingRef="P01#批量删除", capability="批量删除")
        code, report = run_validator(self._completeness_spec([item]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("COMPLETENESS_ITEM_NOT_LANDED", error_codes(report))

    def test_design_completeness_missing_landing_ref_fails(self):
        """included 条目缺 landingRef -> COMPLETENESS_ITEM_NOT_LANDED 阻断。"""
        item = self._completeness_item(landingRef="")
        code, report = run_validator(self._completeness_spec([item]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("COMPLETENESS_ITEM_NOT_LANDED", error_codes(report))

    def test_design_completeness_dev_item_landing_passes(self):
        """landingRef 为开发项 ID（codingGuide.pageItems[].id）-> 合法落点，通过。"""
        spec = self._completeness_spec([self._completeness_item(landingRef="P01-C01")])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertFalse(any(e.get("errorCode") == "COMPLETENESS_ITEM_NOT_LANDED"
                             for e in report.get("errors", [])))

    def test_design_completeness_excluded_reason_missing_fails(self):
        """excluded 条目缺 reason -> COMPLETENESS_EXCLUSION_REASON_MISSING 阻断。"""
        item = self._completeness_item(decision="excluded")
        item.pop("landingRef", None)
        code, report = run_validator(self._completeness_spec([item]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("COMPLETENESS_EXCLUSION_REASON_MISSING", error_codes(report))

    def test_design_completeness_entry_invalid_fails(self):
        """source 非法且 ref 无 # 锚点 -> COMPLETENESS_ENTRY_INVALID 阻断。"""
        item = self._completeness_item(source="pd", ref="common-design/crud-pairing.md")
        code, report = run_validator(self._completeness_spec([item]), strict=True)
        self.assertEqual(code, 1)
        self.assertIn("COMPLETENESS_ENTRY_INVALID", error_codes(report))

    def test_design_completeness_basis_unread_warns(self):
        """ref 未在 readLedger 精读命中 -> COMPLETENESS_BASIS_UNREAD warning（不阻断）。"""
        spec = self._completeness_spec([self._completeness_item()], read_status="index-only")
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0)
        self.assertIn("COMPLETENESS_BASIS_UNREAD", warning_codes(report))

    def test_design_completeness_absent_skips(self):
        """未声明 designCompleteness -> RULE-63 不启用、不误报。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")).startswith("COMPLETENESS_") for i in all_issues))

    # ---- 模板契约差异同步闭环（RULE-64，条件式）：快照与 Common Design 不一致时登记 templateSync ----
    @staticmethod
    def _sync_entry(**over):
        entry = {
            "templateId": "form-modal",
            "field": "footer.buttonOrder",
            "registryValue": ["confirm", "cancel"],
            "commonDesignValue": ["close"],
            "ref": "common-design/references/02-template/01-page-types.md#form-modal",
        }
        entry.update(over)
        return entry

    @staticmethod
    def _sync_dc(entries):
        return {
            "commonDesign": {"skillId": "common-design", "read": True},
            "productDesign": {"matched": False, "skillId": "", "coverage": []},
            "readLedger": [{"doc": "common-design/references/02-template/01-page-types.md", "status": "read"}],
            "templateSync": entries,
        }

    def test_template_sync_passes(self):
        """登记 footer.buttonOrder 差异（close）并按 Common Design 画「关闭」-> 覆盖生效，RULE-37 通过。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/关闭"
        page["footerActions"] = [{"label": "关闭", "kind": "close"}]
        code, report = run_validator(make_spec([page], design_context=self._sync_dc([self._sync_entry()])), strict=True)
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("TEMPLATE_SYNC_") for e in report.get("errors", []) + report.get("warnings", [])))
        self.assertFalse(any(e.get("errorCode") in ("FOOTER_ASCII_BUTTON_MISSING", "FOOTER_ASCII_ORDER_MISMATCH") for e in report.get("errors", [])))

    def test_template_sync_override_conflict_fails(self):
        """登记差异为 close 但线框仍画「确定/取消」-> 覆盖后与 Common Design 期望不符，RULE-37 阻断。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/确定/取消"
        code, report = run_validator(make_spec([page], design_context=self._sync_dc([self._sync_entry()])), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(
            {"FOOTER_ASCII_ORDER_MISMATCH", "FOOTER_ASCII_BUTTON_MISSING"} & error_codes(report),
            f"expected footer ascii deviation error, got {error_codes(report)}",
        )

    def test_template_sync_entry_invalid_fails(self):
        """field 非法（不在支持集合）-> TEMPLATE_SYNC_ENTRY_INVALID 阻断。"""
        page = modal_page()
        code, report = run_validator(make_spec([page], design_context=self._sync_dc([self._sync_entry(field="footer.title")])), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(any(e.get("errorCode") == "TEMPLATE_SYNC_ENTRY_INVALID" for e in report.get("errors", [])))

    def test_template_sync_target_missing_fails(self):
        """templateId 不在注册表 -> TEMPLATE_SYNC_TARGET_MISSING 阻断。"""
        page = modal_page()
        entry = self._sync_entry(templateId="ghost-modal")
        code, report = run_validator(make_spec([page], design_context=self._sync_dc([entry])), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(any(e.get("errorCode") == "TEMPLATE_SYNC_TARGET_MISSING" for e in report.get("errors", [])))

    def test_template_sync_basis_unread_warns(self):
        """ref 未在 readLedger 精读命中 -> TEMPLATE_SYNC_BASIS_UNREAD 告警，不阻断。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/关闭"
        dc = self._sync_dc([self._sync_entry()])
        dc["readLedger"] = [{"doc": "common-design/references/02-template/01-page-types.md", "status": "index-only"}]
        code, report = run_validator(make_spec([page], design_context=dc), strict=True)
        self.assertIn("TEMPLATE_SYNC_BASIS_UNREAD", warning_codes(report))
        self.assertNotIn("TEMPLATE_SYNC_BASIS_UNREAD", error_codes(report))

    def test_template_sync_alignment_override_passes(self):
        """登记 footer.alignment 差异（left -> right）并按 Common Design 声明 right -> JSON 层对账通过。"""
        page = modal_page()
        page["templateContract"]["footerContract"] = {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]}
        page["wireframe"]["shell"]["footer"]["alignment"] = "right"
        entry = self._sync_entry(field="footer.alignment", registryValue="left", commonDesignValue="right")
        code, report = run_validator(make_spec([page], design_context=self._sync_dc([entry])), strict=True)
        self.assertNotIn("FOOTER_ALIGNMENT_MISMATCH", error_codes(report))

    def test_template_sync_absent_skips(self):
        """未声明 templateSync -> RULE-64 不启用、不误报。"""
        code, report = run_validator(make_spec([modal_page()]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")).startswith("TEMPLATE_SYNC_") for i in all_issues))

    def test_template_sync_deviation_blocked_without_sync(self):
        """未登记差异却画「关闭」-> 无豁免，RULE-37 仍按注册表快照阻断（保护不弱化）。"""
        page = modal_page()
        page["wireframe"]["ascii"] = "弹窗标题/表单主体/关闭"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertTrue(any(e.get("errorCode") == "FOOTER_ASCII_BUTTON_MISSING" for e in report.get("errors", [])))
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("TEMPLATE_SYNC_") for e in report.get("errors", []) + report.get("warnings", [])))

    # ---- 承载形式分流闭环（RULE-65）：CD 分流决策链逐页留痕对账 + 可疑信号复核 ----
    @staticmethod
    def _card_list_page(**overrides):
        """卡片列表页（page-card-list），registry 标记 carrierTraceRequired=true。"""
        page = base_page()
        page["name"] = "连接器列表"
        page["type"] = "卡片列表页"
        page["templateContract"]["templateId"] = "page-card-list"
        page["templateContract"]["templateSource"] = "common-design/references/02-template/01-page-types.md#page-card-list"
        page["templateContract"]["requiredRegions"] = ["global-navigation", "title-bar", "toolbar", "card-list"]
        page["templateContract"]["regionOrder"] = ["global-navigation", "title-bar", "toolbar", "card-list"]
        page["templateContract"]["componentContract"] = {"toolbar": ["IxButton", "IxSearch"], "card-list": ["IxCard"]}
        page["wireframe"]["templateId"] = "page-card-list"
        page["wireframe"]["layoutSource"] = "Common Design page-card-list"
        page["wireframe"]["regions"] = [
            {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": True, "content": "全局导航"},
            {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": True, "content": "页面标题"},
            {"id": "toolbar", "templateRegion": "toolbar", "position": "content", "required": True, "content": "工具栏（新增按钮 + 搜索）"},
            {"id": "card-list", "templateRegion": "card-list", "position": "content", "required": True, "content": "卡片列表（一行一个长条卡片）"},
        ]
        page["wireframe"]["ascii"] = (
            "标题栏/工具栏/卡片列表\n"
            "工具栏  [新增连接器]        搜索  [________]\n"
            "卡片列表：\n"
            "卡片  [图标]  条目A标题  [编辑] [删除]  连接状态：正常\n"
            "卡片  [图标]  条目B标题  [编辑] [删除]  连接状态：异常"
        )
        page["sections"] = [
            {"title": "工具栏", "type": "toolbar"},
            {"title": "卡片列表", "type": "content"},
        ]
        page.update(overrides)
        return page

    @staticmethod
    def _sweep_entry(**over):
        entry = {
            "pageId": "P01",
            "contextRef": "common-design/references/02-template/01-page-types.md#多卡片承载",
            "dataTraits": {"字段数": "少（仅连接名称/状态/操作）", "视觉丰富度": "含连接状态与平台图标"},
            "decision": "多卡片承载",
            "templateRef": "page-card-list",
            "reason": "字段少且需展示连接状态视觉，按 CD 分流章节判为多卡片承载",
        }
        entry.update(over)
        return entry

    @staticmethod
    def _sweep_dc(entries, **over):
        dc = {
            "commonDesign": {"skillId": "common-design", "read": True},
            "productDesign": {"matched": False, "skillId": "", "coverage": []},
            "readLedger": [{"doc": "common-design/references/02-template/01-page-types.md", "status": "read"}],
            "carrierSweep": entries,
        }
        dc.update(over)
        return dc

    def test_carrier_sweep_passes(self):
        """卡片列表页 + 完整 carrierSweep 条目 + 依据精读 -> 无 CARRIER_SWEEP_* 且整体通过。"""
        page = self._card_list_page()
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([self._sweep_entry()])), strict=True)
        self.assertEqual(code, 0)
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("CARRIER_SWEEP_") for e in report.get("errors", []) + report.get("warnings", [])))

    def test_carrier_sweep_mismatch_fails(self):
        """条目判定卡片承载（page-card-list）但页面实际画了基础表格页 -> CARRIER_SWEEP_MISMATCH 阻断。"""
        page = base_page()
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([self._sweep_entry()])), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("CARRIER_SWEEP_MISMATCH", error_codes(report))

    def test_carrier_sweep_target_missing_fails(self):
        """条目 pageId 指向不存在页面 -> CARRIER_SWEEP_TARGET_MISSING。"""
        page = self._card_list_page()
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([self._sweep_entry(pageId="P99")])), strict=True)
        self.assertIn("CARRIER_SWEEP_TARGET_MISSING", error_codes(report))

    def test_carrier_sweep_card_trace_missing_fails(self):
        """声明 carrierSweep=[] 却使用了 carrierTraceRequired=true 的卡片列表页 -> CARD_TRACE_MISSING（用卡必留痕）。"""
        page = self._card_list_page()
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([])), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("CARRIER_SWEEP_CARD_TRACE_MISSING", error_codes(report))

    def test_carrier_sweep_entry_invalid_fails(self):
        """条目缺 dataTraits/decision -> CARRIER_SWEEP_ENTRY_INVALID。"""
        page = self._card_list_page()
        entry = self._sweep_entry()
        del entry["dataTraits"]
        entry["decision"] = ""
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([entry])), strict=True)
        self.assertIn("CARRIER_SWEEP_ENTRY_INVALID", error_codes(report))

    def test_carrier_sweep_basis_unread_warns(self):
        """contextRef 依据未精读（readLedger 无命中）-> CARRIER_SWEEP_BASIS_UNREAD warning，不阻断。"""
        page = self._card_list_page()
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([self._sweep_entry()], readLedger=[])), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("CARRIER_SWEEP_BASIS_UNREAD", warning_codes(report))

    def test_carrier_sweep_signal_review_warns(self):
        """未声明 carrierSweep 且页面文本含承载分流特征词（第三方对接）-> SIGNAL_REVIEW warning，不阻断。"""
        page = base_page()
        page["name"] = "第三方厂商存储列表"
        page["sections"][2]["tableFields"] = [{"name": "对接进度", "iduxComponent": "IxText"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("CARRIER_SWEEP_SIGNAL_REVIEW", warning_codes(report))

    def test_carrier_sweep_absent_skips(self):
        """未声明 carrierSweep 且页面无分流特征词 -> RULE-65 不产生任何 CARRIER_SWEEP_*。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        all_issues = report.get("errors", []) + report.get("warnings", [])
        self.assertFalse(any(str(i.get("errorCode", "")).startswith("CARRIER_SWEEP_") for i in all_issues))

    def test_carrier_sweep_table_with_trace_passes(self):
        """表格承载判定 + page-table-basic 页面 -> 账实一致通过（分流是双向对账而非单向禁表格）。"""
        page = base_page()
        entry = self._sweep_entry(templateRef="page-table-basic", decision="表格承载",
                                  dataTraits={"字段数": "多（12 列）", "数据量": "大，需筛选排序分页"},
                                  reason="字段结构一致且数据量大，按 CD 分流章节判为表格承载")
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([entry])), strict=True)
        self.assertEqual(code, 0)
        self.assertFalse(any(str(e.get("errorCode", "")).startswith("CARRIER_SWEEP_") for e in report.get("errors", []) + report.get("warnings", [])))

    def test_carrier_sweep_mismatch_reverse_fails(self):
        """条目判定表格承载但页面实际画了卡片列表页 -> CARRIER_SWEEP_MISMATCH（反向同样阻断）。"""
        page = self._card_list_page()
        entry = self._sweep_entry(templateRef="page-table-basic", decision="表格承载",
                                  dataTraits={"字段数": "多"}, reason="判为表格承载")
        code, report = run_validator(make_spec([page], design_context=self._sweep_dc([entry])), strict=True)
        self.assertIn("CARRIER_SWEEP_MISMATCH", error_codes(report))

    # ---- 页面定位证据闭环（RULE-53，条件式）：禁止文件名定位、防张冠李戴 ----
    @staticmethod
    def _evidence(**over):
        ev = {
            "navPath": ["安全事件", "事件详情", "告警列表"],
            "prdNavPath": ["安全事件", "事件详情", "告警列表"],
            "route": "/security/events/:id?tab=alarm-list",
            "title": "告警列表",
            "tabs": ["事件详情", "告警列表", "告警链"],
            "codeRefs": ["src/pages/security/alarm-list/index.tsx"],
            "matchedBy": ["route", "tab", "title"],
            "identitySource": "code",
            "candidates": ["alarm-list", "alert-list"],
            "rejected": [{"candidate": "alert-list", "reason": "该页面为告警链，非告警列表"}],
        }
        ev.update(over)
        return ev

    def test_page_identity_ref_valid_passes(self):
        """pageIdentityRefs 携带合规身份证据 -> RULE-53 通过。"""
        spec = make_spec([base_page()])
        spec["pageIdentityRefs"] = [{"id": "REF01", "name": "告警列表", "evidence": self._evidence()}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")

    def test_page_identity_missing_evidence_fails(self):
        """pageIdentityRefs 缺身份证据 -> HOST_IDENTITY_UNVERIFIED 阻断。"""
        spec = make_spec([base_page()])
        spec["pageIdentityRefs"] = [{"id": "REF01", "name": "告警列表"}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("HOST_IDENTITY_UNVERIFIED", error_codes(report))

    def test_host_identity_filename_only_fails(self):
        """命中依据含文件名 -> HOST_IDENTITY_FILENAME_ONLY 阻断。"""
        spec = make_spec([base_page()])
        spec["pageIdentityRefs"] = [{"id": "REF01", "name": "告警列表",
                                     "evidence": self._evidence(matchedBy=["filename", "title"])}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("HOST_IDENTITY_FILENAME_ONLY", error_codes(report))

    def test_host_identity_navpath_mismatch_fails(self):
        """代码路径末级与 PRD 声明不符（告警链 vs 告警列表）-> HOST_NAVPATH_MISMATCH 阻断。"""
        spec = make_spec([base_page()])
        spec["pageIdentityRefs"] = [{"id": "REF01", "name": "告警列表",
                                     "evidence": self._evidence(navPath=["安全事件", "事件详情", "告警链"])}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("HOST_NAVPATH_MISMATCH", error_codes(report))

    def test_host_identity_ambiguous_warns(self):
        """存在多个形近候选但未记录排除 -> HOST_IDENTITY_AMBIGUOUS warning，不阻断。"""
        spec = make_spec([base_page()])
        spec["pageIdentityRefs"] = [{"id": "REF01", "name": "告警列表",
                                     "evidence": self._evidence(rejected=[])}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("HOST_IDENTITY_AMBIGUOUS", warning_codes(report))

    def test_host_identity_degraded_mode_passes(self):
        """环境无代码时退化模式：以 title + tabs 对证即可通过。"""
        spec = make_spec([base_page()])
        spec["pageIdentityRefs"] = [{"id": "REF01", "name": "告警列表",
                                     "evidence": {"navPath": ["安全事件", "事件详情", "告警列表"],
                                                  "title": "告警列表", "tabs": ["告警列表"],
                                                  "matchedBy": ["title", "tab"],
                                                  "identitySource": "degraded"}}]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")

    def test_entry_point_out_of_scope_missing_evidence_fails(self):
        """out-of-scope 入口宿主已登记但缺身份证据 -> HOST_IDENTITY_UNVERIFIED 阻断。"""
        spec = make_spec([base_page()])
        spec["requirementEntryPoints"] = [self._entry(scope="out-of-scope", host="安全事件页", container="bw-alert-modal")]
        spec["entryHosts"] = [
            {"id": "安全事件页", "name": "安全事件页/告警列表", "scope": "out-of-scope",
             "read": True, "readTier": "tier1", "wireframe": "【告警列表操作列：加入行为白名单入口】",
             "devItem": "P01-C01"},
        ]
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("HOST_IDENTITY_UNVERIFIED", error_codes(report))

    # ---- 组件形态描述闭环（RULE-54，条件式）：多形态组件须写明选用形态 ----
    def test_component_form_missing_warns(self):
        """声明 >1 形态候选但未写 iduxComponentForm -> COMPONENT_FORM_MISSING warning，不阻断。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签", "状态标签"]},
        ])])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("COMPONENT_FORM_MISSING", warning_codes(report))

    def test_component_form_unknown_warns(self):
        """选用形态不在候选内 -> COMPONENT_FORM_UNKNOWN warning，不阻断。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "彩色卡片"},
        ])])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("COMPONENT_FORM_UNKNOWN", warning_codes(report))

    def test_component_form_two_part_form_passes(self):
        """两段式写法“深色标签（支持新增）”主值在候选内 -> 无 UNKNOWN/DECISION 告警。"""
        spec = make_spec([tag_page([
            {"name": "身份标签", "display": "标签", "iduxComponent": "IxTag", "description": "主机身份",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "深色标签（支持新增）",
             "formDecision": "按 Common Design 标签样式判定小节，身份标签采用深色标签（支持新增）形态"},
        ])])
        code, report = run_validator(spec, strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        for c in ("COMPONENT_FORM_UNKNOWN", "FORM_DECISION_MISSING", "FORM_DECISION_MISMATCH"):
            self.assertNotIn(c, codes, f"report={report}")

    def test_component_form_primary_substring_passes(self):
        """“平铺+搜索”主值“平铺”命中候选 -> 两段式兼容，不误报 UNKNOWN。"""
        spec = make_spec([tag_page([
            {"name": "办公地址", "display": "选择器", "iduxComponent": "IxCascader", "description": "省/市/区",
             "formCandidates": ["平铺", "级联"], "iduxComponentForm": "平铺+搜索",
             "formDecision": "省市区层级选择按判定小节采用级联形态更优，但 PRD 明确要求平铺+搜索，按 PRD 执行"},
        ])])
        code, report = run_validator(spec, strict=True)
        self.assertNotIn("COMPONENT_FORM_UNKNOWN", warning_codes(report), f"report={report}")

    def test_component_form_decision_missing_warns(self):
        """已选形态但未写 formDecision -> FORM_DECISION_MISSING warning（判定链读了未留痕）。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "深色标签"},
        ])])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("FORM_DECISION_MISSING", warning_codes(report))

    def test_component_form_decision_mismatch_warns(self):
        """formDecision 未引用所选形态 -> FORM_DECISION_MISMATCH warning。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "深色标签",
             "formDecision": "按判定小节采用描边标签形态"},
        ])])
        code, report = run_validator(spec, strict=True)
        self.assertIn("FORM_DECISION_MISMATCH", warning_codes(report), f"report={report}")

    def test_component_form_decision_complete_passes(self):
        """formDecision 含所选形态 -> 无 DECISION 告警。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "深色标签",
             "formDecision": "按 Common Design 标签样式判定小节，风险等级语义醒目采用深色标签"},
        ])])
        code, report = run_validator(spec, strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertNotIn("FORM_DECISION_MISSING", codes, f"report={report}")
        self.assertNotIn("FORM_DECISION_MISMATCH", codes, f"report={report}")

    def test_component_form_valid_passes(self):
        """选用形态在候选内 -> 无 COMPONENT_FORM_* 告警。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "深色标签"},
        ])])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertNotIn("COMPONENT_FORM_MISSING", warning_codes(report))
        self.assertNotIn("COMPONENT_FORM_UNKNOWN", warning_codes(report))

    def test_component_form_single_candidate_passes(self):
        """仅一个候选（非多形态）-> RULE-54 不启用、不误报。"""
        spec = make_spec([tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["深色标签"]},
        ])])
        code, report = run_validator(spec, strict=True)
        all_codes = set(warning_codes(report)) | set(error_codes(report))
        self.assertEqual(code, 0, f"report={report}")
        self.assertNotIn("COMPONENT_FORM_MISSING", all_codes)
        self.assertNotIn("COMPONENT_FORM_UNKNOWN", all_codes)

    # ---- 组件形态溯源（RULE-54 扩展）：命名真值=组件映射，选择依据真值=widget patterns ----
    COMP_MAP_REF = "common-design/references/05-components/idux-component-map.md#IxTag"
    PATTERN_REF = "common-design/references/03-patterns/03-widget-patterns/tag-pattern.md#标签样式选择"

    def _form_spec(self, refs, ledger):
        page = tag_page([
            {"name": "风险等级", "display": "标签", "iduxComponent": "IxTag", "description": "高/中/低",
             "formCandidates": ["描边标签", "深色标签"], "iduxComponentForm": "深色标签"},
        ])
        page["codingGuide"]["designReferences"] = refs
        spec = make_spec([page])
        spec["designContext"] = self._design_context(readLedger=ledger)
        return spec

    def test_component_form_source_unread_warns(self):
        """>1 形态候选但缺 Common Design 组件映射依据 -> COMPONENT_FORM_SOURCE_UNREAD warning。"""
        spec = self._form_spec(
            [{"source": "common-design", "ref": self.PATTERN_REF}],
            [{"ref": self.PATTERN_REF, "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("COMPONENT_FORM_SOURCE_UNREAD", warning_codes(report))

    def test_component_form_rule_unread_warns(self):
        """>1 形态候选但缺 widget pattern 选择依据 -> COMPONENT_FORM_RULE_UNREAD warning。"""
        spec = self._form_spec(
            [{"source": "common-design", "ref": self.COMP_MAP_REF}],
            [{"ref": self.COMP_MAP_REF, "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("COMPONENT_FORM_RULE_UNREAD", warning_codes(report))

    def test_component_form_evidence_index_only_warns(self):
        """依据仅目录级索引（index-only）-> 两层依据均判为未精读命中（并要求补读为 read）。"""
        refs = [{"source": "common-design", "ref": self.COMP_MAP_REF},
                {"source": "common-design", "ref": self.PATTERN_REF}]
        ledger = [{"ref": "common-design/references/03-patterns/03-widget-patterns/#*", "status": "index-only"},
                  {"ref": self.COMP_MAP_REF, "status": "index-only"},
                  {"ref": self.PATTERN_REF, "status": "index-only"}]
        code, report = run_validator(self._form_spec(refs, ledger), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("DESIGN_REF_UNREAD", error_codes(report))
        codes = warning_codes(report)
        self.assertIn("COMPONENT_FORM_SOURCE_UNREAD", codes)
        self.assertIn("COMPONENT_FORM_RULE_UNREAD", codes)

    def test_component_form_evidence_complete_passes(self):
        """两层依据均已锚点级精读 -> 无形态溯源类告警。"""
        refs = [{"source": "common-design", "ref": self.COMP_MAP_REF},
                {"source": "common-design", "ref": self.PATTERN_REF}]
        ledger = [{"ref": self.COMP_MAP_REF, "status": "read"},
                  {"ref": self.PATTERN_REF, "status": "read"}]
        code, report = run_validator(self._form_spec(refs, ledger), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        codes = warning_codes(report)
        self.assertNotIn("COMPONENT_FORM_SOURCE_UNREAD", codes)
        self.assertNotIn("COMPONENT_FORM_RULE_UNREAD", codes)

    def test_component_form_single_candidate_skips_evidence(self):
        """单形态字段不触发形态溯源检查（零负担）。"""
        page = tag_page([{"name": "风险等级", "display": "标签", "iduxComponent": "IxTag",
                          "description": "高/中/低", "formCandidates": ["深色标签"]}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(readLedger=[])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        codes = warning_codes(report)
        self.assertNotIn("COMPONENT_FORM_SOURCE_UNREAD", codes)
        self.assertNotIn("COMPONENT_FORM_RULE_UNREAD", codes)

    # ---- 抽屉 footer 对齐与注册表防漂移（RULE-20 / 注册表）----
    def test_drawer_footer_alignment_left_passes(self):
        """抽屉模板 footer 声明左对齐（与注册表一致）-> 无 FOOTER_ALIGNMENT_MISMATCH。"""
        code, report = run_validator(make_spec([drawer_detail_page()]), strict=True)
        self.assertNotIn("FOOTER_ALIGNMENT_MISMATCH", error_codes(report))

    # ---- 线框图底部按钮水平位置闭环（RULE-60）----
    BOX_TOP = "+" + "-" * 46 + "+"
    ALIGN_ASCII_HEADER = (
        "表单弹窗（form-modal）\n"
        "弹窗标题  新建策略\n"
        "表单配置项（单列）：\n"
        "策略名称          [________________]\n"
        "生效范围          [请选择]\n"
    )
    ALIGN_LEFT_DRAW_ASCII = (
        BOX_TOP + "\n" + ALIGN_ASCII_HEADER + BOX_TOP + "\n"
        "| [确定] [取消]                          |\n" + BOX_TOP
    )
    ALIGN_RIGHT_ASCII = (
        BOX_TOP + "\n" + ALIGN_ASCII_HEADER + BOX_TOP + "\n"
        "|                        [确定] [取消]  |\n" + BOX_TOP
    )
    ALIGN_CENTER_ASCII = (
        BOX_TOP + "\n" + ALIGN_ASCII_HEADER + BOX_TOP + "\n"
        "|                [确定] [取消]          |\n" + BOX_TOP
    )
    ALIGN_NO_STRUCT_ASCII = ALIGN_ASCII_HEADER + "底部按钮区 [确定] [取消]"

    def _align_spec(self, ascii_text):
        """form-modal 弹窗页 + 带框线 ascii（复用 _form_modal_spec 契约，覆盖其 ascii）。"""
        spec = self._form_modal_spec(ascii_text)
        spec["pages"][1]["wireframe"]["ascii"] = ascii_text
        return spec

    def test_footer_ascii_alignment_right_template_left_drawing_fails(self):
        """form-modal（right）按钮画在左侧 -> FOOTER_ASCII_ALIGNMENT_MISMATCH（error）。"""
        code, report = run_validator(self._align_spec(self.ALIGN_LEFT_DRAW_ASCII), strict=True)
        self.assertIn("FOOTER_ASCII_ALIGNMENT_MISMATCH", error_codes(report), f"report={report}")

    def test_footer_ascii_alignment_right_template_correct_passes(self):
        """form-modal（right）按钮贴右画 -> 无对齐告警。"""
        code, report = run_validator(self._align_spec(self.ALIGN_RIGHT_ASCII), strict=True)
        self.assertNotIn("FOOTER_ASCII_ALIGNMENT_MISMATCH", error_codes(report), f"report={report}")

    def test_footer_ascii_alignment_left_template_right_drawing_fails(self):
        """form-drawer（left，registry footer.alignment=left）按钮画在右侧 -> FOOTER_ASCII_ALIGNMENT_MISMATCH（error）。
        detail-drawer 的 footer 在 Common Design 中无按钮契约（buttonOrder 空），由本用例与
        test_registry_drawer_left_modal_right 共同保证 left 口径取自真实有对齐契约的模板。"""
        page = drawer_detail_page()
        page["type"] = "表单抽屉"
        page["templateContract"]["templateId"] = "form-drawer"
        page["templateContract"]["templateSource"] = "common-design/references/02-template/01-page-types.md#form-drawer"
        page["templateContract"]["footerContract"] = {"required": True, "alignment": "left",
                                                      "buttonOrder": ["confirm", "cancel"]}
        page["templateContract"]["requiredRegions"] = ["drawer-shell", "drawer-header", "form-content", "drawer-footer"]
        page["templateContract"]["regionOrder"] = ["drawer-shell", "drawer-header", "form-content", "drawer-footer"]
        page["wireframe"]["templateId"] = "form-drawer"
        page["wireframe"]["layoutSource"] = "Common Design form-drawer"
        page["wireframe"]["regions"] = [
            {"id": "drawer-shell", "templateRegion": "drawer-shell", "position": "top", "required": True, "content": "抽屉外壳"},
            {"id": "drawer-header", "templateRegion": "drawer-header", "position": "top", "required": True, "content": "抽屉标题"},
            {"id": "form-content", "templateRegion": "form-content", "position": "content", "required": True, "content": "表单配置"},
            {"id": "drawer-footer", "templateRegion": "drawer-footer", "position": "bottom", "required": True, "content": "底部确定/取消"},
        ]
        page["wireframe"]["ascii"] = (
            "+" + "-" * 40 + "+\n"
            "抽屉标题  新建策略\n"
            "策略名称          [________________]\n"
            "+" + "-" * 40 + "+\n"
            "|                         [确定] [取消]  |\n"
            "+" + "-" * 40 + "+"
        )
        page["footerActions"] = [{"label": "确定", "kind": "confirm"}, {"label": "取消", "kind": "cancel"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("FOOTER_ASCII_ALIGNMENT_MISMATCH", error_codes(report), f"report={report}")

    def test_footer_ascii_alignment_unresolvable_skips(self):
        """无结构框线或按钮居中（容差内）-> 无法可靠判定，静默跳过不告警。"""
        for ascii_text in (self.ALIGN_NO_STRUCT_ASCII, self.ALIGN_CENTER_ASCII):
            code, report = run_validator(self._align_spec(ascii_text), strict=True)
            self.assertNotIn("FOOTER_ASCII_ALIGNMENT_MISMATCH", error_codes(report), f"ascii={ascii_text[:20]} report={report}")

    def test_flat_filter_search_first_warns(self):
        """平铺筛选行搜索框排在时间范围/选择框之前 -> WIREFRAME_FLAT_FILTER_ORDER_MISMATCH（warning）。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "标题栏/筛选/工具栏/表格/分页\n"
            "筛选条件：  关键字 [________]    状态  [请选择]    时间范围  [____ ~ ____]\n"
            "表格主体"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("WIREFRAME_FLAT_FILTER_ORDER_MISMATCH", warning_codes(report), f"report={report}")

    def test_flat_filter_search_last_passes(self):
        """平铺筛选行顺序正确（时间范围 -> 选择框 -> 搜索框最右）-> 无该告警。"""
        page = base_page()
        page["wireframe"]["ascii"] = (
            "标题栏/筛选/工具栏/表格/分页\n"
            "筛选条件：  时间范围  [____ ~ ____]    状态  [请选择]    关键字 [________]\n"
            "表格主体"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("WIREFRAME_FLAT_FILTER_ORDER_MISMATCH", warning_codes(report), f"report={report}")

    def test_flat_filter_prosearch_page_skips(self):
        """高级搜索页（IxProSearch 承载筛选）不适用本规则 -> 无该告警（互斥由 RULE-46 管）。"""
        page = base_page()
        page["codingGuide"]["pageItems"].append(
            {"id": "P01-C02", "scope": "filter", "name": "高级搜索", "description": "筛选与搜索全部收敛在高级搜索组件（IxProSearch）", "mode": "reuse-component",
             "mappingRef": "M02", "mappingStatus": "verified",
             "target": {"component": "IxProSearch", "path": "src/components/pro-search/index.vue"},
             "requirements": ["筛选与搜索收敛在高级搜索组件"],
             "acceptanceCriteria": ["高级搜索承载全部筛选"]}
        )
        page["wireframe"]["ascii"] = (
            "标题栏/筛选/工具栏/表格/分页\n"
            "筛选条件：  关键字 [________]    状态  [请选择]    时间范围  [____ ~ ____]\n"
            "表格主体"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("WIREFRAME_FLAT_FILTER_ORDER_MISMATCH", warning_codes(report), f"report={report}")

    def test_flat_filter_override_skips(self):
        """页面声明 filterOrderOverride（PD/PRD 指定其他顺序）-> 跳过检查。"""
        page = base_page()
        page["filterOrderOverride"] = "PRD 明确要求搜索框置首：先输入关键字再按状态/时间缩小范围"
        page["wireframe"]["ascii"] = (
            "标题栏/筛选/工具栏/表格/分页\n"
            "筛选条件：  关键字 [________]    状态  [请选择]    时间范围  [____ ~ ____]\n"
            "表格主体"
        )
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotIn("WIREFRAME_FLAT_FILTER_ORDER_MISMATCH", warning_codes(report), f"report={report}")


    def test_registry_drawer_left_modal_right(self):
        """注册表防漂移：抽屉模板 footer 一律 left，弹窗模板一律 right。"""
        import json
        import pathlib
        root = pathlib.Path(__file__).resolve().parent.parent
        reg_path = root / "references/02-template-contracts/common-design-template-registry.json"
        with open(reg_path, encoding="utf-8") as f:
            reg = json.load(f)
        for tid, tpl in reg["templates"].items():
            al = (tpl.get("footer") or {}).get("alignment", "")
            if "drawer" in tid:
                self.assertEqual(al, "left", f"{tid} 抽屉模板必须左对齐，实际={al}")
            if "modal" in tid:
                self.assertEqual(al, "right", f"{tid} 弹窗模板必须保持右对齐，实际={al}")

    # ---- 能力发现完整性（RULE-55）----
    def test_capability_sweep_complete_passes(self):
        """能力全扫：coverage 每项均有判定且命中项有已精读证据 -> 通过。"""
        page = self._page_with_design_ref([
            {"source": "product-design", "ref": "product-design/references/<sample-doc>.md#资产信息",
             "ability": "component"},
            {"source": "common-design",
             "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"},
        ])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "component", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}],
                           "capabilitySweep": [{"capability": "component", "decision": "hit",
                                                "reason": "使用资产信息业务封装组件",
                                                "evidenceRef": "product-design/references/<sample-doc>.md#资产信息"}]},
            readLedger=[
                {"ref": "product-design/references/<sample-doc>.md#资产信息", "status": "read"},
                {"ref": "common-design/references/02-template/01-page-types.md#page-table-basic",
                 "status": "read"},
            ])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        all_codes = set(warning_codes(report)) | set(error_codes(report))
        self.assertNotIn("ABILITY_NOT_SWEPT", all_codes)
        self.assertNotIn("ABILITY_HIT_NOT_READ", all_codes)

    def test_capability_not_swept_warns(self):
        """coverage 有 capability 但 capabilitySweep 漏扫 -> ABILITY_NOT_SWEPT warning。"""
        page = self._page_with_design_ref([
            {"source": "product-design", "ref": "product-design/references/<sample-doc>.md#筛选",
             "ability": "filtering"},
            {"source": "common-design",
             "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"},
        ])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "filtering", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}],
                           "capabilitySweep": []},
            readLedger=[{"ref": "product-design/references/<sample-doc>.md#筛选", "status": "read"},
                        {"ref": "common-design/references/02-template/01-page-types.md#page-table-basic",
                         "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertIn("ABILITY_NOT_SWEPT", warning_codes(report))

    def test_capability_hit_not_read_warns(self):
        """命中能力但 evidenceRef 未在 readLedger 精读 -> ABILITY_HIT_NOT_READ warning。"""
        page = self._page_with_design_ref([
            {"source": "product-design", "ref": "product-design/references/<sample-doc>.md#筛选",
             "ability": "filtering"},
            {"source": "common-design",
             "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"},
        ])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "filtering", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}],
                           "capabilitySweep": [{"capability": "filtering", "decision": "hit",
                                                "reason": "筛选三态",
                                                "evidenceRef": "product-design/references/<sample-doc>.md#筛选三态"}]},
            readLedger=[{"ref": "product-design/references/<sample-doc>.md#筛选", "status": "read"},
                        {"ref": "common-design/references/02-template/01-page-types.md#page-table-basic",
                         "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertIn("ABILITY_HIT_NOT_READ", warning_codes(report))

    def test_capability_sweep_absent_warns(self):
        """声明 coverage 但完全没有 capabilitySweep -> 每个能力 ABILITY_NOT_SWEPT warning。"""
        page = self._page_with_design_ref([
            {"source": "product-design", "ref": "product-design/references/<sample-doc>.md#筛选",
             "ability": "filtering"},
            {"source": "common-design",
             "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"},
        ])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "filtering", "relation": "override",
                                         "appliesTo": ["page-table-basic"]}]},
            readLedger=[{"ref": "product-design/references/<sample-doc>.md#筛选", "status": "read"},
                        {"ref": "common-design/references/02-template/01-page-types.md#page-table-basic",
                         "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertIn("ABILITY_NOT_SWEPT", warning_codes(report))

    # ---- 模板 ID 一致性与覆盖兜底（RULE-56）----
    def test_template_coverage_unapplied_warns(self):
        """coverage 声明了 appliesTo 但无页面命中 -> TEMPLATE_COVERAGE_UNAPPLIED warning（不阻断）。"""
        page = self._page_with_design_ref(
            [{"source": "common-design",
              "ref": "common-design/references/02-template/01-page-types.md#page-table-basic"}])
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "template", "relation": "override",
                                         "appliesTo": ["detail-drawer"]}]},
            readLedger=[{"doc": "common-design/references/02-template/01-page-types.md",
                         "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("TEMPLATE_COVERAGE_UNAPPLIED", warning_codes(report))

    def test_template_coverage_legacy_id_applied_passes(self):
        """appliesTo 用旧 ID（page-detail-drawer）时归一为 detail-drawer 后命中：不报未命中，且模板覆盖仍被强制。"""
        page = drawer_detail_page()
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "template", "relation": "override",
                                         "appliesTo": ["page-detail-drawer"]}]},
            readLedger=[])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_OVERRIDE_NOT_APPLIED", error_codes(report))
        self.assertNotIn("TEMPLATE_COVERAGE_UNAPPLIED", warning_codes(report))

    def test_sweep_appliesTo_unapplied_warns(self):
        """capabilitySweep 声明了 appliesTo 但无页面命中 -> TEMPLATE_COVERAGE_UNAPPLIED warning。"""
        spec = make_spec([base_page()])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design", "coverage": [],
                           "capabilitySweep": [{"capability": "component", "decision": "not-hit",
                                                "appliesTo": ["no-such-template"]}]})
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("TEMPLATE_COVERAGE_UNAPPLIED", warning_codes(report))

    def test_legacy_template_id_ref_warns(self):
        """templateSource / layoutSource 引用已废弃旧模板 ID -> LEGACY_TEMPLATE_ID_REF warning。"""
        page = base_page()
        page["templateContract"]["templateSource"] = \
            "common-design/references/02-template/01-page-types.md#page-list-drawer"
        page["wireframe"]["layoutSource"] = "Common Design page-list-drawer"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        hits = [e for e in report.get("warnings", []) if e.get("errorCode") == "LEGACY_TEMPLATE_ID_REF"]
        self.assertGreaterEqual(len(hits), 2, f"应在 templateSource 与 layoutSource 各告警一次, report={report}")

    def test_template_id_consistency_absent_skips(self):
        """未声明 designContext、页面也未携带模板引用文本 -> RULE-56 不启用。"""
        code, report = run_validator(make_spec([base_page()]), strict=True)
        self.assertEqual(code, 0)

    def test_pd_override_template_direct_adoption_passes(self):
        """PD 声明模板 override 且页面直接采用 PD 模板 ID/类型名 -> 视为注册表新增模板，放行。"""
        page = base_page()
        page["type"] = "策略详情页"
        page["templateContract"] = {
            "templateId": "pd-policy-detail", "baseTemplateId": "",
            "templateBase": "product",
            "productTemplateRef": "product-design/references/templates.md#策略详情页模板",
            "templateSource": "Product Design 策略详情页模板",
            "requiredRegions": [], "optionalRegions": [], "regionOrder": [],
            "footerContract": {}, "componentContract": {}, "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        }
        page["codingGuide"]["designReferences"] = [
            {"source": "product-design",
             "ref": "product-design/references/templates.md#策略详情页模板"}]
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "页面模板", "relation": "override",
                                         "templateId": "pd-policy-detail", "name": "策略详情页",
                                         "appliesTo": ["list-table"]}]},
            readLedger=[{"doc": "product-design/references/templates.md", "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertNotIn("TEMPLATE_NOT_REGISTERED", error_codes(report))
        self.assertNotIn("UNREGISTERED_TYPE", error_codes(report))

    def test_pd_override_still_common_template_fails(self):
        """命中 PD 模板 override 却仍写 Common Design 模板 ID -> TEMPLATE_OVERRIDE_NOT_APPLIED error。"""
        page = base_page()  # tid=page-table-basic（CD 模板）
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "页面模板", "relation": "override",
                                         "templateId": "pd-table-basic", "name": "新版表格页",
                                         "appliesTo": ["page-table-basic"]}]},
            readLedger=[])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_OVERRIDE_NOT_APPLIED", error_codes(report))

    def test_pd_template_id_without_coverage_still_fails(self):
        """PD 未声明任何模板 override 时，自造 PD 模板 ID 仍被 TEMPLATE_NOT_REGISTERED 拦截。"""
        page = base_page()
        page["type"] = "策略详情页"
        page["templateContract"] = dict(base_page()["templateContract"],
                                        templateId="pd-policy-detail",
                                        templateBase="product",
                                        productTemplateRef="product-design/references/templates.md#x")
        page["codingGuide"]["designReferences"] = [
            {"source": "product-design", "ref": "product-design/references/templates.md#x"}]
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design", "coverage": []},
            readLedger=[{"doc": "product-design/references/templates.md", "status": "read"}])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_NOT_REGISTERED", error_codes(report))

    def test_pd_template_basis_unread_warns(self):
        """采用 PD 模板但模板文档依据未精读 -> PD_TEMPLATE_BASIS_UNREAD warning。"""
        page = base_page()
        page["type"] = "策略详情页"
        page["templateContract"] = dict(base_page()["templateContract"],
                                        templateId="pd-policy-detail",
                                        templateBase="product",
                                        productTemplateRef="product-design/references/templates.md#策略详情页模板")
        page["codingGuide"]["designReferences"] = [
            {"source": "product-design",
             "ref": "product-design/references/templates.md#策略详情页模板"}]
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "页面模板", "relation": "override",
                                         "templateId": "pd-policy-detail", "name": "策略详情页",
                                         "appliesTo": ["list-table"]}]},
            readLedger=[{"ref": "product-design/references/templates.md#策略详情页模板",
                         "status": "index-only"}])
        code, report = run_validator(spec, strict=True)
        self.assertIn("PD_TEMPLATE_BASIS_UNREAD", warning_codes(report))

    def test_pd_template_type_name_by_chinese_applies_passes(self):
        """coverage.appliesTo 用页面类型中文名（含旧名）三口径命中 -> 模板覆盖仍被强制。"""
        page = base_page()  # 仍用 CD 模板
        spec = make_spec([page])
        spec["designContext"] = self._design_context(
            productDesign={"matched": True, "skillId": "product-design",
                           "coverage": [{"capability": "template", "relation": "override",
                                         "templateId": "pd-table-basic", "name": "新版表格页",
                                         "appliesTo": ["基础表格页"]}]},
            readLedger=[])
        code, report = run_validator(spec, strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_OVERRIDE_NOT_APPLIED", error_codes(report))
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertNotIn("TEMPLATE_COVERAGE_UNAPPLIED", codes)
        self.assertNotIn("LEGACY_TEMPLATE_ID_REF", codes)

    # ---- 表单单列布局闭环（RULE-57）----
    FORM_LAYOUT_CODES = ("FORM_LAYOUT_MULTI_COLUMN", "FORM_LAYOUT_LABEL_NOT_INLINE",
                         "FORM_LAYOUT_BASIS_UNREAD")
    FORM_FIELDS = [
        {"name": "策略名称", "iduxComponent": "IxInput", "rules": "必填"},
        {"name": "生效范围", "iduxComponent": "IxSelect", "rules": "单选"},
        {"name": "优先级", "iduxComponent": "IxInputNumber", "rules": "1-100"},
    ]
    FORM_ONE_COLUMN_ASCII = (
        "表单弹窗（form-modal）\n"
        "弹窗标题  新建策略\n"
        "表单配置项（单列）：\n"
        "策略名称          [________________]\n"
        "生效范围          [请选择]\n"
        "优先级            [___]\n"
        "底部按钮区  [确定] [取消]"
    )
    FORM_MULTI_COLUMN_ASCII = FORM_ONE_COLUMN_ASCII.replace(
        "策略名称          [________________]",
        "策略名称  [________________]    生效范围  [请选择]")
    FORM_LABEL_SPLIT_ASCII = FORM_ONE_COLUMN_ASCII.replace(
        "策略名称          [________________]", "策略名称\n[________________]")
    FORM_BASIS_REF = "common-design/references/04-forms/01-form-spec.md#表单布局"
    FORM_BASIS_LEDGER = [{"ref": FORM_BASIS_REF, "status": "read"}]

    def _form_modal_spec(self, ascii_text, refs=None, ledger=None, fields=None):
        """表单弹窗页面：ascii 可定制；默认登记表单布局依据并精读。"""
        page = base_page()
        page["id"] = "F01"
        page["name"] = "新建策略"
        page["type"] = "表单弹窗"
        page["templateContract"] = {
            "templateId": "form-modal", "baseTemplateId": "",
            "templateSource": "common-design/references/02-template/01-page-types.md#form-modal",
            "requiredRegions": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "optionalRegions": [], "regionOrder": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]},
            "componentContract": {"shell": ["IxModal"], "form-content": ["IxForm", "IxFormItem"], "footer": ["IxButton"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        }
        page["wireframe"] = {
            "templateId": "form-modal", "navigationType": "",
            "layoutSource": "Common Design form-modal",
            "shell": {"globalNavigation": False,
                      "titleBar": {"required": True, "type": "modal", "component": "IxModal"},
                      "contentContainer": {"required": True, "type": "modal-content"},
                      "footer": {"required": True, "alignment": "right", "height": "56px"}},
            "regions": [
                {"id": "modal-shell", "templateRegion": "modal-shell", "position": "top", "required": True, "content": "弹窗外壳"},
                {"id": "modal-header", "templateRegion": "modal-header", "position": "top", "required": True, "content": "弹窗标题与关闭入口"},
                {"id": "form-content", "templateRegion": "form-content", "position": "content", "required": True, "content": "表单配置项单列绘制"},
                {"id": "modal-footer", "templateRegion": "modal-footer", "position": "bottom", "required": True, "content": "底部取消与确定"},
            ],
            "variants": [],
            "ascii": ascii_text,
        }
        page["sections"] = [{"title": "表单配置", "type": "form",
                             "formFields": list(fields if fields is not None else self.FORM_FIELDS)}]
        page["footerActions"] = [{"label": "确定", "kind": "confirm"}, {"label": "取消", "kind": "cancel"}]
        page["codingGuide"]["pageItems"] = [{
            "id": "F01-C01", "scope": "modal-form", "name": "表单弹窗", "mode": "reuse-framework",
            "mappingRef": "M02", "mappingStatus": "verified",
            "target": {"path": "src/pages/strategy/modal-form.vue", "export": "StrategyFormModal"},
            "requirements": ["表单配置项按单列绘制，label 与控件同一行"],
            "acceptanceCriteria": ["表单单列布局"],
        }]
        page["codingGuide"]["designReferences"] = (
            list(refs) if refs is not None else [{"source": "common-design", "ref": self.FORM_BASIS_REF}])
        host = base_page()
        host["operations"] = [{"id": "OP01", "name": "新建策略", "action": "open-container",
                               "targetPageId": "F01", "targetContainerType": "modal"}]
        spec = make_spec([host, page])
        spec["designContext"] = self._design_context(
            readLedger=list(ledger) if ledger is not None else list(self.FORM_BASIS_LEDGER))
        return spec

    def test_form_layout_single_column_passes(self):
        """表单单列 + label 与控件同行 + 表单布局依据已精读 -> 不告警。"""
        code, report = run_validator(self._form_modal_spec(self.FORM_ONE_COLUMN_ASCII), strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertFalse(codes & set(self.FORM_LAYOUT_CODES), f"report={report}")

    def test_form_layout_multi_column_warns(self):
        """同一行出现 >=2 个表单配置项 -> FORM_LAYOUT_MULTI_COLUMN（warning，不阻断）。"""
        code, report = run_validator(self._form_modal_spec(self.FORM_MULTI_COLUMN_ASCII), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("FORM_LAYOUT_MULTI_COLUMN", warning_codes(report))

    def test_form_layout_label_not_inline_warns(self):
        """label 独占一行、控件在下一行 -> FORM_LAYOUT_LABEL_NOT_INLINE（warning）。"""
        code, report = run_validator(self._form_modal_spec(self.FORM_LABEL_SPLIT_ASCII), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        self.assertIn("FORM_LAYOUT_LABEL_NOT_INLINE", warning_codes(report))

    FORM_LIST_FIELDS = [
        {"name": "绑定字段", "iduxComponent": "IxSelect", "rules": "必选"},
        {"name": "取值", "iduxComponent": "IxInput", "rules": "必填"},
        {"name": "匹配方式", "iduxComponent": "IxSelect", "rules": "单选"},
    ]

    def _form_list_section_spec(self, ascii_text, section_extra=None, page_extra=None):
        """表单弹窗含动态列表区块（formList 声明），用于 RULE-57 分流豁免测试（自包含 form-modal 契约）。"""
        page = base_page()
        page["id"] = "F02"
        page["name"] = "绑定条件配置"
        page["type"] = "表单弹窗"
        page["templateContract"] = {
            "templateId": "form-modal", "baseTemplateId": "",
            "navigationType": "left-shaped",
            "templateSource": "common-design/references/02-template/01-page-types.md#form-modal",
            "requiredRegions": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "optionalRegions": [], "regionOrder": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]},
            "componentContract": {"shell": ["IxModal"], "form-content": ["IxForm", "IxFormItem"], "footer": ["IxButton"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        }
        page["wireframe"] = {
            "templateId": "form-modal", "navigationType": "",
            "layoutSource": "Common Design form-modal",
            "shell": {"globalNavigation": False,
                      "titleBar": {"required": True, "type": "modal", "component": "IxModal"},
                      "contentContainer": {"required": True, "type": "modal-content"},
                      "footer": {"required": True, "alignment": "right", "height": "56px"}},
            "regions": modal_regions(),
            "variants": [],
            "ascii": ascii_text,
        }
        section = {"title": "绑定条件", "type": "form", "formFields": list(self.FORM_LIST_FIELDS)}
        section.update(section_extra or {})
        page["sections"] = [
            {"title": "基本信息", "type": "form",
             "formFields": [{"name": "策略名称", "iduxComponent": "IxInput", "rules": "必填"},
                            {"name": "生效范围", "iduxComponent": "IxSelect", "rules": "单选"}]},
            section,
        ]
        page.update(page_extra or {})
        page["footerActions"] = [{"label": "确定", "kind": "confirm"}, {"label": "取消", "kind": "cancel"}]
        page["codingGuide"] = {
            "pageItems": [{"id": "F02-C01", "scope": "modal-form", "name": "绑定条件弹窗", "mode": "reuse-framework",
                           "mappingRef": "M02", "mappingStatus": "verified",
                           "target": {"path": "src/pages/policy/bind-modal.vue", "export": "BindModal"},
                           "requirements": ["表单配置项按单列绘制，绑定条件为动态列表"],
                           "acceptanceCriteria": ["动态列表一行一个对象"]}],
            "designReferences": [{"source": "common-design", "ref": self.FORM_BASIS_REF}],
        }
        host = base_page()
        host["operations"] = [{"id": "OP01", "name": "配置绑定条件", "action": "open-container",
                               "targetPageId": "F02", "targetContainerType": "modal"}]
        spec = make_spec([host, page])
        spec["designContext"] = self._design_context(readLedger=list(self.FORM_BASIS_LEDGER))
        return spec

    def test_form_layout_form_list_section_skips(self):
        """动态列表区块声明 formList: true -> 一行多列（列头行）不报 FORM_LAYOUT_MULTI_COLUMN。"""
        ascii_text = (
            "表单弹窗（form-modal）\n"
            "弹窗标题  绑定条件配置\n"
            "基本信息：\n"
            "策略名称          [________________]\n"
            "绑定条件（动态列表，一行一个对象）：\n"
            "绑定字段      取值          匹配方式\n"
            "[请选择]      [________]    [等于]\n"
            "底部按钮区  [确定] [取消]"
        )
        code, report = run_validator(
            self._form_list_section_spec(ascii_text, section_extra={"formList": True}), strict=True)
        self.assertNotIn("FORM_LAYOUT_MULTI_COLUMN", warning_codes(report), f"report={report}")

    def test_form_layout_form_list_page_blocks_skip(self):
        """页面 formListBlocks 登记区块名 -> 同样豁免动态列表区块。"""
        ascii_text = (
            "表单弹窗（form-modal）\n"
            "弹窗标题  绑定条件配置\n"
            "绑定条件（动态列表）：\n"
            "绑定字段      取值          匹配方式\n"
            "[请选择]      [________]    [等于]\n"
            "底部按钮区  [确定] [取消]"
        )
        code, report = run_validator(
            self._form_list_section_spec(ascii_text, page_extra={"formListBlocks": ["绑定条件"]}), strict=True)
        self.assertNotIn("FORM_LAYOUT_MULTI_COLUMN", warning_codes(report), f"report={report}")

    def test_form_layout_inline_delete_row_skips(self):
        """未声明 formList，但同行多字段且带行内删除标记 -> 视为动态列表行自动豁免。"""
        ascii_text = (
            "表单弹窗（form-modal）\n"
            "绑定条件（动态列表，一行一个对象）：\n"
            "绑定字段  [请选择]    取值  [________]    匹配方式  [等于]    [删除]\n"
            "底部按钮区  [确定] [取消]"
        )
        code, report = run_validator(self._form_list_section_spec(ascii_text), strict=True)
        self.assertNotIn("FORM_LAYOUT_MULTI_COLUMN", warning_codes(report), f"report={report}")

    def test_form_layout_multi_column_still_warns_without_exemption(self):
        """无 formList 声明、无行内删除标记的同行多配置项 -> 仍报 FORM_LAYOUT_MULTI_COLUMN。"""
        ascii_text = (
            "表单弹窗（form-modal）\n"
            "弹窗标题  绑定条件配置\n"
            "基本信息：\n"
            "策略名称  [________________]    生效范围  [请选择]\n"
            "底部按钮区  [确定] [取消]"
        )
        code, report = run_validator(self._form_list_section_spec(ascii_text), strict=True)
        self.assertIn("FORM_LAYOUT_MULTI_COLUMN", warning_codes(report), f"report={report}")

    def test_form_layout_basis_unread_warns(self):
        """表单布局依据未登记或仅索引（index-only）-> FORM_LAYOUT_BASIS_UNREAD（warning）。"""
        for refs, ledger in (
            ([], list(self.FORM_BASIS_LEDGER)),
            ([{"source": "common-design", "ref": self.FORM_BASIS_REF}],
             [{"ref": self.FORM_BASIS_REF, "status": "index-only"}]),
        ):
            code, report = run_validator(
                self._form_modal_spec(self.FORM_ONE_COLUMN_ASCII, refs=refs, ledger=ledger), strict=True)
            self.assertIn("FORM_LAYOUT_BASIS_UNREAD", warning_codes(report), f"report={report}")

    def test_form_layout_basis_read_passes(self):
        """表单布局依据锚点级登记且精读 -> 无 FORM_LAYOUT_BASIS_UNREAD。"""
        code, report = run_validator(self._form_modal_spec(self.FORM_ONE_COLUMN_ASCII), strict=True)
        self.assertNotIn("FORM_LAYOUT_BASIS_UNREAD", set(error_codes(report)) | set(warning_codes(report)))

    def test_form_layout_non_form_page_skips(self):
        """非表单承载页（表格页）不做表单单列检查。"""
        page = base_page()
        page["wireframe"]["ascii"] = "基础表格页\n筛选区 [关键字]  [查询] [重置]\n表格区 事件名称 | 风险等级 | 操作"
        code, report = run_validator(make_spec([page]), strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertFalse(codes & set(self.FORM_LAYOUT_CODES), f"report={report}")

    # ---- 详情页操作去重（RULE-58）----
    def _detail_action_page(self, summary_actions, footer_actions, exempt=None):
        """详情抽屉：顶部概览卡片（summary-card）声明操作 + 底部按钮栏，用于 RULE-58 测试。"""
        page = drawer_detail_page()
        summary = {"title": "对象摘要", "type": "summary-card",
                   "cardFields": [{"name": "策略名称", "iduxComponent": "IxText"}],
                   "actions": list(summary_actions)}
        page["sections"] = [summary] + list(page["sections"])
        page["footerActions"] = list(footer_actions)
        if exempt is not None:
            page["detailActionDedupExempt"] = list(exempt)
        return make_spec([page])

    def test_detail_summary_action_duplicate_warns(self):
        """概览卡片操作（重启）重复出现在底部按钮栏 -> DETAIL_SUMMARY_ACTION_DUPLICATE（warning）。"""
        spec = self._detail_action_page(
            [{"name": "编辑", "kind": "normal"}, {"name": "重启", "kind": "high-impact"}],
            [{"label": "关闭", "kind": "close"}, {"label": "重启", "kind": "normal"}])
        code, report = run_validator(spec, strict=True)
        self.assertIn("DETAIL_SUMMARY_ACTION_DUPLICATE", warning_codes(report), f"report={report}")

    def test_detail_summary_action_alias_duplicate_warns(self):
        """同义操作名（概览卡片 编辑 vs 底部 修改）也判为重复。"""
        spec = self._detail_action_page([{"name": "编辑", "kind": "normal"}],
                                        [{"label": "修改", "kind": "normal"}])
        code, report = run_validator(spec, strict=True)
        self.assertIn("DETAIL_SUMMARY_ACTION_DUPLICATE", warning_codes(report), f"report={report}")

    def test_detail_summary_action_no_overlap_passes(self):
        """概览卡片承载对象级操作、底部只保留页面级动作 -> 不告警。"""
        spec = self._detail_action_page(
            [{"name": "编辑", "kind": "normal"}, {"name": "重启", "kind": "high-impact"}],
            [{"label": "关闭", "kind": "close"}])
        code, report = run_validator(spec, strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertNotIn("DETAIL_SUMMARY_ACTION_DUPLICATE", codes, f"report={report}")

    def test_detail_action_dedup_exempt_passes(self):
        """detailActionDedupExempt 显式声明的操作豁免去重。"""
        spec = self._detail_action_page(
            [{"name": "重启", "kind": "high-impact"}],
            [{"label": "关闭", "kind": "close"}, {"label": "重启", "kind": "normal"}],
            exempt=["重启"])
        code, report = run_validator(spec, strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertNotIn("DETAIL_SUMMARY_ACTION_DUPLICATE", codes, f"report={report}")

    def test_detail_action_dedup_skips_without_summary_actions(self):
        """概览卡片未声明操作时跳过（条件式启用）。"""
        spec = self._detail_action_page([], [{"label": "关闭", "kind": "close"},
                                             {"label": "重启", "kind": "normal"}])
        code, report = run_validator(spec, strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertNotIn("DETAIL_SUMMARY_ACTION_DUPLICATE", codes, f"report={report}")

    def test_detail_action_dedup_skips_without_footer(self):
        """无底部按钮栏（footerActions 为空）时跳过。"""
        spec = self._detail_action_page([{"name": "编辑", "kind": "normal"}], [])
        code, report = run_validator(spec, strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertNotIn("DETAIL_SUMMARY_ACTION_DUPLICATE", codes, f"report={report}")

    # ---- 复用业务组件容器闭环（RULE-59，条件式：声明 reuseBusinessComponent 时启用）----
    REUSE_REF = "product-design/references/<sample-doc>.md#资产适用规则检测组件"

    def _reuse_host_page(self, note=True):
        """宿主页面：基础表格页 + 打开复用容器的操作；note=False 时不在页面上交代复用。"""
        page = base_page()
        extra = ("点击[资产适用规则检测]打开弹窗，复用 Product Design 组件，不单独绘制"
                 if note else "点击[资产适用规则检测]打开弹窗查看规则命中结果")
        page["wireframe"]["ascii"] = "标题栏/筛选/工具栏/表格/分页\n" + extra
        page["operations"] = [{"id": "P01-OP01", "name": "资产适用规则检测",
                               "action": "open-container", "targetPageId": "B04",
                               "targetContainerType": "modal"}]
        return page

    def _reuse_container_page(self, decl=True, over=False, refs=True, with_entry=True,
                              trigger="按钮点击", basis="product-design", code_evidence="",
                              **decl_overrides):
        """复用业务组件容器（form-modal）：默认不画线框、不写区块与底部按钮，只保留复用开发项。"""
        page = modal_page()
        page.update({"id": "B04", "name": "资产适用规则检测"})
        if not with_entry:
            page.pop("__unused", None)
        page["wireframe"]["regions"] = []
        page["wireframe"]["ascii"] = "弹窗标题/确定" if over else ""
        if over:
            page["sections"] = [{"title": "规则表单", "type": "form",
                                 "formFields": [{"name": "规则名称", "iduxComponent": "IxInput"}]}]
            page["footerActions"] = [{"label": "确定", "kind": "confirm"}]
        else:
            page["sections"] = []
            page["footerActions"] = []
        page["codingGuide"]["pageItems"] = [{
            "id": "B04-C01", "scope": "reuse-business-component", "name": "资产适用规则检测",
            "mode": "reuse", "mappingRef": "M09", "mappingStatus": "verified",
            "target": {"path": "product-design", "export": "AssetRuleCheckModal"},
            "requirements": ["复用业务封装组件，不单独实现"],
            "acceptanceCriteria": ["样式以业务实现为准"],
        }]
        page["codingGuide"]["designReferences"] = [{"source": "product-design", "ref": self.REUSE_REF}] if refs else []
        if decl:
            decl_obj = {"decision": "reuse", "componentRef": self.REUSE_REF,
                        "hostPageId": "P01", "trigger": trigger, "basis": basis}
            if code_evidence:
                decl_obj["codeEvidence"] = code_evidence
            decl_obj.update(decl_overrides)
            page["reuseBusinessComponent"] = decl_obj
        return page

    def _reuse_spec(self, container_kw=None, host_note=True, ledger=None, with_entry=True):
        host = self._reuse_host_page(host_note)
        if not with_entry:
            host.pop("operations", None)
            host["wireframe"]["ascii"] = "标题栏/筛选/工具栏/表格/分页"
        container = self._reuse_container_page(with_entry=with_entry, **(container_kw or {}))
        kw = container_kw or {}
        if ledger is None:
            ledger = [{"ref": self.REUSE_REF, "status": "read"}] if kw.get("refs", True) else []
        spec = make_spec([host, container])
        spec["designContext"] = self._design_context(readLedger=ledger)
        return spec

    def test_reuse_container_minimal_passes(self):
        """复用容器最小合法：声明 reuse + PD 依据实读 + 宿主交代 -> 无 RULE-59 码。"""
        code, report = run_validator(self._reuse_spec(), strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertEqual(code, 0, f"report={report}")
        self.assertFalse([c for c in codes if c.startswith("REUSE_")], f"report={report}")

    def test_reuse_container_over_described_fails(self):
        """声明复用却仍自绘线框/区块/底部按钮 -> REUSE_CONTAINER_OVER_DESCRIBED error。"""
        code, report = run_validator(self._reuse_spec({"over": True}), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("REUSE_CONTAINER_OVER_DESCRIBED", error_codes(report), f"report={report}")

    def test_reuse_basis_unread_warns(self):
        """basis=product-design 但依据未精读（readLedger 未 read）-> REUSE_BASIS_UNREAD warning。"""
        code, report = run_validator(self._reuse_spec(ledger=[]), strict=True)
        self.assertIn("REUSE_BASIS_UNREAD", warning_codes(report), f"report={report}")

    def test_reuse_basis_code_without_evidence_warns(self):
        """basis=code 但未填 codeEvidence -> REUSE_BASIS_UNREAD warning。"""
        code, report = run_validator(
            self._reuse_spec({"basis": "code", "refs": False}), strict=True)
        self.assertIn("REUSE_BASIS_UNREAD", warning_codes(report), f"report={report}")

    def test_reuse_host_note_missing_warns(self):
        """宿主页面未交代复用（无线框说明/无复用标记）-> REUSE_HOST_NOTE_MISSING warning。"""
        code, report = run_validator(self._reuse_spec(host_note=False), strict=True)
        self.assertIn("REUSE_HOST_NOTE_MISSING", warning_codes(report), f"report={report}")

    def test_reuse_scope_invalid_warns(self):
        """trigger 非法；且容器无宿主入口（独立页面）-> REUSE_SCOPE_INVALID warning。"""
        code, report = run_validator(self._reuse_spec({"trigger": "随便看看"}), strict=True)
        self.assertIn("REUSE_SCOPE_INVALID", warning_codes(report), f"report={report}")
        code2, report2 = run_validator(
            self._reuse_spec(with_entry=False, container_kw={"refs": False}), strict=True)
        self.assertIn("REUSE_SCOPE_INVALID", warning_codes(report2), f"report={report2}")

    def test_reuse_candidate_unmarked_warns(self):
        """容器已引用 PD 业务组件依据且有宿主入口，但未声明复用 -> REUSE_CANDIDATE_UNMARKED warning。"""
        code, report = run_validator(self._reuse_spec({"decl": False}), strict=True)
        self.assertIn("REUSE_CANDIDATE_UNMARKED", warning_codes(report), f"report={report}")

    def test_reuse_absent_skips(self):
        """无复用声明且无 PD 业务组件依据 -> RULE-59 不启用（历史格式不误伤）。"""
        code, report = run_validator(
            self._reuse_spec({"decl": False, "refs": False}, ledger=[]), strict=True)
        codes = set(error_codes(report)) | set(warning_codes(report))
        self.assertFalse([c for c in codes if c.startswith("REUSE_")], f"report={report}")


def load_registry():
    """读取模板注册表（页面类型更名回归测试用）。"""
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def shared_modal_page(**overrides):
    """从页面（RULE-62）：与主页面 P02 共用线框，不重复绘制，只描述差异。"""
    page = modal_page()
    page["id"] = "P03"
    page["name"] = "编辑主机资产"
    page.pop("wireframe", None)
    page["wireframeSharedWith"] = "P02"
    page["wireframeDiff"] = "标题改为「编辑主机资产」，表单回填既有数据"
    page.update(overrides)
    return page


def log_detail_drawer_page(**overrides):
    """合法日志详情抽屉（log-detail-drawer），用于页面类型更名（2026）回归测试。"""
    page = base_page()
    page.update({
        "id": "L01",
        "name": "操作日志详情",
        "type": "日志详情抽屉",
        "templateContract": {
            "templateId": "log-detail-drawer",
            "baseTemplateId": "",
            "navigationType": "",
            "templateSource": "common-design/references/02-template/01-page-types.md#log-detail-drawer",
            "requiredRegions": ["drawer-shell", "drawer-header", "detail-content", "drawer-footer"],
            "optionalRegions": [],
            "regionOrder": ["drawer-shell", "drawer-header", "detail-content", "drawer-footer"],
            "footerContract": {"required": True, "alignment": "left",
                               "buttonOrder": ["previous", "next-or-complete"]},
            "componentContract": {"shell": ["IxDrawer"], "detail-content": ["IxProDesc"], "footer": ["IxButton"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        },
        "wireframe": {
            "templateId": "log-detail-drawer",
            "navigationType": "",
            "layoutSource": "Common Design log-detail-drawer",
            "shell": {
                "globalNavigation": False,
                "titleBar": {"required": True, "type": "drawer", "component": ""},
                "contentContainer": {"required": True, "type": "drawer-content"},
                "footer": {"required": True, "alignment": "left", "height": "56px"},
            },
            "regions": [
                {"id": "drawer-shell", "templateRegion": "drawer-shell", "position": "top", "required": True, "content": "抽屉外壳"},
                {"id": "drawer-header", "templateRegion": "drawer-header", "position": "top", "required": True, "content": "抽屉标题与关闭入口"},
                {"id": "detail-content", "templateRegion": "detail-content", "position": "content", "required": True, "content": "分组标题与描述列表"},
                {"id": "drawer-footer", "templateRegion": "drawer-footer", "position": "bottom", "required": True, "content": "底部操作区：上一个/下一个/完成"},
            ],
            "variants": [],
            "ascii": "抽屉标题/分组标题/详情描述列表/底部上一个下一个完成",
        },
        "sections": [
            {"title": "基础信息", "type": "detail",
             "detailFields": [{"name": "时间", "iduxComponent": "IxText"},
                              {"name": "操作人", "iduxComponent": "IxText"}]},
        ],
        "footerActions": [
            {"label": "上一个", "kind": "previous"},
            {"label": "下一个", "kind": "next-or-complete"},
        ],
        "codingGuide": {
            "pageItems": [
                {
                    "id": "L01-C01", "scope": "drawer-detail", "name": "日志详情抽屉", "mode": "reuse-framework",
                    "mappingRef": "M07", "mappingStatus": "verified",
                    "target": {"path": "src/pages/log/detail-drawer.vue", "export": "LogDetailDrawer"},
                    "requirements": ["保留抽屉外壳、标题栏、描述列表与底部按钮结构"],
                    "acceptanceCriteria": ["抽屉结构一致"],
                }
            ]
        },
    })
    page.update(overrides)
    return page


def log_entry_host_page(**overrides):
    """日志列表（宿主页面），通过 open-container 操作指向日志详情抽屉。"""
    page = base_page()
    page["sections"] = [
        {"title": "筛选区", "type": "filter", "filterFields": [{"name": "操作人", "iduxComponent": "IxInput"}]},
        {"title": "工具栏", "type": "toolbar"},
        {"title": "表格主体", "type": "table",
         "tableFields": [{"name": "时间", "iduxComponent": "IxText"},
                         {"name": "操作人", "iduxComponent": "IxText"}]},
    ]
    page["operations"] = [
        {"id": "OP01", "name": "查看日志详情", "action": "open-container",
         "targetPageId": "L01", "targetContainerType": "drawer", "confirm": False},
    ]
    page.update(overrides)
    return page


class TestPageTypeRename(unittest.TestCase):
    """页面类型更名（2026）：弹窗/抽屉不再称“页”，中文名与 templateId 唯一来源为模板注册表。"""

    NEW_TYPES = {
        "列表弹窗": "list-modal",
        "列表抽屉": "list-drawer",
        "详情抽屉": "detail-drawer",
        "日志详情抽屉": "log-detail-drawer",
        "表单弹窗": "form-modal",
        "表单抽屉": "form-drawer",
    }

    def test_registry_keys_renamed(self):
        """注册表仅含 15 个 templateId（14 更名存量 + 新增 page-card-list），旧 page-list-* / page-detail-* / page-form-* 全部清除。"""
        keys = set(load_registry()["templates"])
        self.assertEqual(keys, {
            "page-table-basic", "page-table-tree", "page-table-overview", "page-table-overview-tree",
            "list-modal", "list-drawer", "page-detail-drilldown", "detail-drawer", "log-detail-drawer",
            "page-form-config", "page-form-stepper", "form-modal", "form-drawer", "page-dashboard",
            "page-card-list",
        })
        for old in ("page-list-modal", "page-list-drawer", "page-detail-drawer",
                    "page-detail-log", "page-form-modal", "page-form-drawer"):
            self.assertNotIn(old, keys, f"旧 templateId 未清理: {old}")

    def test_registry_names_present_and_updated(self):
        """每个模板都有中文 name；6 个更名模板用新名，旧中文名不得残留。"""
        templates = load_registry()["templates"]
        for tid, tpl in templates.items():
            self.assertTrue(str(tpl.get("name", "")).strip(), f"{tid} 缺少 name 字段")
        for tid, name in {v: k for k, v in self.NEW_TYPES.items()}.items():
            self.assertEqual(templates[tid]["name"], name, f"{tid} 中文名应为 {name}")
        old_names = {"弹窗列表页", "抽屉列表页", "抽屉详情页", "日志详情页", "弹窗表单页", "抽屉表单页"}
        all_names = {t.get("name", "") for t in templates.values()}
        self.assertFalse(old_names & all_names, f"注册表残留旧中文名: {sorted(old_names & all_names)}")

    def test_registry_footer_button_order_canonical(self):
        """注册表 buttonOrder 只能使用规范槽位，避免与校验器槽位词表失配。"""
        allowed = {"previous", "next-or-complete", "cancel", "confirm", "close"}
        for tid, tpl in load_registry()["templates"].items():
            order = set((tpl.get("footer") or {}).get("buttonOrder") or [])
            self.assertTrue(order <= allowed, f"{tid} buttonOrder 使用了非规范槽位 {sorted(order - allowed)}")

    def test_new_type_name_derives_template_id(self):
        """中文页面类型名 -> templateId 由注册表 name 派生（TYPE_TEMPLATE_MAP 不再硬编码）。"""
        for cn, tid in self.NEW_TYPES.items():
            page = base_page(type=cn)
            code, report = run_validator(make_spec([page]), strict=True)
            self.assertNotIn("UNREGISTERED_TYPE", error_codes(report), f"{cn} 应为已注册类型")
            mismatches = [e for e in report.get("errors", []) if e.get("errorCode") == "TYPE_TEMPLATE_MISMATCH"]
            self.assertEqual(len(mismatches), 1, f"{cn} 应触发一次 TYPE_TEMPLATE_MISMATCH, report={report}")
            self.assertEqual(mismatches[0].get("expected"), tid, f"{cn} 应映射到 {tid}")

    def test_old_type_name_unregistered(self):
        """旧中文页面类型名（抽屉列表页）已废弃 -> UNREGISTERED_TYPE。"""
        code, report = run_validator(make_spec([base_page(type="抽屉列表页")]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("UNREGISTERED_TYPE", error_codes(report))

    def test_old_template_id_not_registered(self):
        """旧 templateId（page-list-drawer）已废弃 -> TEMPLATE_NOT_REGISTERED。"""
        page = base_page()
        page["templateContract"]["templateId"] = "page-list-drawer"
        page["templateContract"]["templateSource"] = "common-design/references/02-template/01-page-types.md#page-list-drawer"
        page["wireframe"]["templateId"] = "page-list-drawer"
        page["wireframe"]["layoutSource"] = "Common Design page-list-drawer"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("TEMPLATE_NOT_REGISTERED", error_codes(report))

    def test_legacy_type_names_unregistered(self):
        """旧中文类型名（步骤条配置页/仪表盘页）已废弃 -> UNREGISTERED_TYPE；最新名（下钻步骤条配置页/Dashboard）通过。"""
        for cn in ("步骤条配置页", "仪表盘页"):
            _code, report = run_validator(make_spec([base_page(type=cn)]), strict=True)
            self.assertIn("UNREGISTERED_TYPE", error_codes(report), f"{cn} 应判为未注册页面类型名")
        for cn in ("下钻步骤条配置页", "Dashboard"):
            _code, report = run_validator(make_spec([base_page(type=cn)]), strict=True)
            self.assertNotIn("UNREGISTERED_TYPE", error_codes(report), f"{cn} 应为已注册页面类型名")

    def test_detail_page_detected_via_template_contract(self):
        """详情类页面判定读取 templateContract.templateId：类型名为 PD 自定义（不含“详情”）时仍按详情处理。"""
        page = drawer_detail_page()
        page["type"] = "策略信息抽屉"
        page["sections"] = [
            {"title": "对象摘要", "type": "object-summary", "fields": ["策略名称", "启用状态"]},
            {"title": "基本信息", "type": "detail", "detailFields": [{"name": "策略名称"}, {"name": "描述"}]},
        ]
        _code, report = run_validator(make_spec([page]), strict=True)
        self.assertIn("DETAIL_FIELD_DUPLICATE", warning_codes(report))

    def test_log_detail_drawer_page_passes(self):
        """日志详情抽屉使用新 ID 与左对齐 footer -> 通过，且不被当作整页。"""
        code, report = run_validator(make_spec([log_entry_host_page(), log_detail_drawer_page()]), strict=True)
        self.assertEqual(code, 0, f"report={report}")
        codes = set(error_codes(report)) | set(warning_codes(report))
        for c in ("UNREGISTERED_TYPE", "TEMPLATE_NOT_REGISTERED", "TYPE_TEMPLATE_MISMATCH",
                  "FOOTER_ALIGNMENT_MISMATCH", "FOOTER_BUTTON_ORDER_MISMATCH"):
            self.assertNotIn(c, codes, f"不应出现 {c}")

    def test_log_detail_drawer_right_footer_fails(self):
        """日志详情抽屉属抽屉类，footer 声明右对齐 -> FOOTER_ALIGNMENT_MISMATCH。"""
        page = log_detail_drawer_page()
        page["templateContract"]["footerContract"]["alignment"] = "right"
        page["wireframe"]["shell"]["footer"]["alignment"] = "right"
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("FOOTER_ALIGNMENT_MISMATCH", error_codes(report))


if __name__ == "__main__":
    unittest.main(verbosity=2)

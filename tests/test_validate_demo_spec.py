#!/usr/bin/env python3
"""validate_demo_spec.py 的自动化测试。

运行方式:
  python3 -m unittest discover -s tests -v

覆盖 15 个场景:
  1. 合法基础表格页通过
  2. 缺少分页失败
  3. 缺少标题栏失败
  4. 基础表格页误画成普通卡片失败
  5. 弹窗列表页缺少关闭入口失败
  6. 抽屉列表页 footer 对齐错误失败
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


def make_spec(pages):
    return {
        "title": "测试需求设计说明书",
        "overview": {
            "summary": "测试",
            "pageOverview": [
                {"id": p.get("id", ""), "name": p.get("name", ""), "type": p.get("type", "")} for p in pages
            ],
        },
        "pages": pages,
    }


def modal_regions():
    return [
        {"id": "modal-shell", "templateRegion": "modal-shell", "position": "top", "required": True, "content": "弹窗外壳"},
        {"id": "modal-header", "templateRegion": "modal-header", "position": "top", "required": True, "content": "弹窗标题与关闭入口"},
        {"id": "form-content", "templateRegion": "form-content", "position": "content", "required": True, "content": "表单主体"},
        {"id": "modal-footer", "templateRegion": "modal-footer", "position": "bottom", "required": True, "content": "底部操作：确定/取消"},
    ]


def modal_page(**overrides):
    """合法弹窗表单页（page-form-modal），用于操作目标闭环与孤儿容器测试。"""
    page = base_page()
    page.update({
        "id": "P02",
        "name": "批量编辑主机资产",
        "type": "弹窗表单页",
        "templateContract": {
            "templateId": "page-form-modal",
            "baseTemplateId": "",
            "navigationType": "left-shaped",
            "templateSource": "common-design/references/02-template/01-page-types.md#page-form-modal",
            "requiredRegions": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "optionalRegions": [],
            "regionOrder": ["modal-shell", "modal-header", "form-content", "modal-footer"],
            "footerContract": {},
            "componentContract": {"shell": ["IxModal"], "form": ["IxForm", "IxFormItem"], "footer": ["IxButton"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        },
        "wireframe": {
            "templateId": "page-form-modal",
            "navigationType": "left-shaped",
            "layoutSource": "Common Design page-form-modal",
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
    """合法抽屉详情页（page-detail-drawer），用于表格与详情字段一致性（RULE-38）测试。"""
    page = base_page()
    page.update({
        "id": "D01",
        "name": "策略详情",
        "type": "抽屉详情页",
        "templateContract": {
            "templateId": "page-detail-drawer",
            "baseTemplateId": "",
            "navigationType": "",
            "templateSource": "common-design/references/02-template/01-page-types.md#page-detail-drawer",
            "requiredRegions": ["drawer-shell", "drawer-header", "object-summary", "detail-content", "drawer-footer"],
            "optionalRegions": [],
            "regionOrder": ["drawer-shell", "drawer-header", "object-summary", "detail-content", "drawer-footer"],
            "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["close"]},
            "componentContract": {"shell": ["IxDrawer"], "object-summary": ["IxDescriptions"]},
            "wireframeContract": {},
            "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
        },
        "wireframe": {
            "templateId": "page-detail-drawer",
            "navigationType": "",
            "layoutSource": "Common Design page-detail-drawer",
            "shell": {
                "globalNavigation": False,
                "titleBar": {"required": True, "type": "drawer", "component": ""},
                "contentContainer": {"required": True, "type": "drawer-content"},
                "footer": {"required": True, "alignment": "right", "height": "56px"},
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
        """5. 弹窗列表页缺少关闭入口失败。"""
        page = base_page(
            id="P02", name="选择策略弹窗", type="弹窗列表页",
            templateContract={
                "templateId": "page-list-modal", "baseTemplateId": "", "navigationType": "",
                "templateSource": "common-design/references/02-template/01-page-types.md#page-list-modal",
                "requiredRegions": ["modal-shell", "modal-header", "filter", "table", "pagination", "modal-footer"],
                "optionalRegions": [], "regionOrder": ["modal-shell", "modal-header", "filter", "table", "pagination", "modal-footer"],
                "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["confirm", "cancel"]},
                "componentContract": {"shell": ["IxModal"], "table": ["IxTable"], "pagination": ["IxPagination"], "footer": ["IxButton"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "page-list-modal", "navigationType": "",
            "layoutSource": "Common Design page-list-modal",
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
        """6. 抽屉列表页 footer 对齐错误失败（模板要求右对齐）。"""
        page = base_page(
            id="P02", name="选择策略抽屉", type="抽屉列表页",
            templateContract={
                "templateId": "page-list-drawer", "baseTemplateId": "", "navigationType": "",
                "templateSource": "common-design/references/02-template/01-page-types.md#page-list-drawer",
                "requiredRegions": ["drawer-shell", "drawer-header", "object-context", "filter", "table", "pagination", "drawer-footer"],
                "optionalRegions": [], "regionOrder": ["drawer-shell", "drawer-header", "object-context", "filter", "table", "pagination", "drawer-footer"],
                "footerContract": {"required": True, "alignment": "left", "buttonOrder": ["confirm", "cancel"]},
                "componentContract": {"shell": ["IxDrawer"], "table": ["IxTable"], "pagination": ["IxPagination"], "footer": ["IxButton"]},
                "wireframeContract": {}, "override": {"enabled": False, "source": "", "reason": "", "affectedRules": []},
            },
        )
        page["wireframe"] = {
            "templateId": "page-list-drawer", "navigationType": "",
            "layoutSource": "Common Design page-list-drawer",
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
            id="P02", name="策略配置向导", type="步骤条配置页",
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
            id="P02", name="策略配置向导", type="步骤条配置页",
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
                    {"id": "P02", "name": "批量编辑主机资产", "type": "弹窗表单页", "containerType": "modal"},
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

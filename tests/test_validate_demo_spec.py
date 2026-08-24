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
            "templateSource": "common-design/references/03-design-template/01-page-types.md#page-table-basic",
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
        {"id": "modal-footer", "templateRegion": "modal-footer", "position": "bottom", "required": True, "content": "底部操作：取消/确定"},
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
            "templateSource": "common-design/references/03-design-template/01-page-types.md#page-form-modal",
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
            "ascii": "弹窗标题/表单主体/取消/确定",
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
                "templateSource": "common-design/references/03-design-template/01-page-types.md#page-list-modal",
                "requiredRegions": ["modal-shell", "modal-header", "filter", "table", "pagination", "modal-footer"],
                "optionalRegions": [], "regionOrder": ["modal-shell", "modal-header", "filter", "table", "pagination", "modal-footer"],
                "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["cancel", "confirm"]},
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
                "templateSource": "common-design/references/03-design-template/01-page-types.md#page-list-drawer",
                "requiredRegions": ["drawer-shell", "drawer-header", "object-context", "filter", "table", "pagination", "drawer-footer"],
                "optionalRegions": [], "regionOrder": ["drawer-shell", "drawer-header", "object-context", "filter", "table", "pagination", "drawer-footer"],
                "footerContract": {"required": True, "alignment": "left", "buttonOrder": ["cancel", "confirm"]},
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
                "templateSource": "common-design/references/03-design-template/01-page-types.md#page-form-config",
                "requiredRegions": ["global-navigation", "title-bar", "form-content", "footer"],
                "optionalRegions": [], "regionOrder": ["global-navigation", "title-bar", "form-content", "footer"],
                "footerContract": {"required": True, "alignment": "right", "buttonOrder": ["cancel", "confirm"]},
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
                {"id": "footer", "templateRegion": "footer", "position": "bottom", "required": True, "content": "取消/保存"},
            ],
            "variants": [], "ascii": "标题栏/表单内容/底部按钮",
        }
        page["sections"] = [
            {"title": "表单内容", "type": "form", "formFields": [{"name": "策略名称", "iduxComponent": "IxInput"}]},
        ]
        page["footerActions"] = [{"label": "取消", "kind": "cancel"}, {"label": "保存", "kind": "confirm"}]
        code, report = run_validator(make_spec([page]), strict=True)
        self.assertNotEqual(code, 0)
        self.assertIn("FOOTER_ALIGNMENT_MISMATCH", error_codes(report))

    def test_stepper_uses_tabs_fails(self):
        """8. 步骤条页面使用 IxTabs 而不是 IxStepper 失败。"""
        page = base_page(
            id="P02", name="策略配置向导", type="步骤条配置页",
            templateContract={
                "templateId": "page-form-stepper", "baseTemplateId": "", "navigationType": "left-shaped",
                "templateSource": "common-design/references/03-design-template/01-page-types.md#page-form-stepper",
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
                "templateSource": "common-design/references/03-design-template/01-page-types.md#page-form-stepper",
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
                "templateSource": "common-design/references/03-design-template/01-page-types.md#page-table-basic",
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

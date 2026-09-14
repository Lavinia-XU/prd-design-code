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
#   5. 在 references/01-workflow/06-quality-and-rules.md 登记表中同步一条。
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
    {"ruleId": "RULE-10", "errorCode": "WIREFRAME_REGION_MISSING", "name": "requiredRegions 全部出现在 wireframe.regions", "check": "check_skeleton_regions", "source": "references/01-workflow/04-demo-output-spec.md 结构化线框契约", "tests": "test_missing_pagination_fails"},
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
    {"ruleId": "RULE-23", "errorCode": "CODING_ITEM_ID_MISSING", "name": "codingGuide 含稳定开发项 ID", "check": "check_coding_item_ids", "source": "references/01-workflow/05-interaction-coding-guidelines.md", "tests": ""},
    {"ruleId": "RULE-24", "errorCode": "PATH_WITHOUT_VERIFY / CODE_STATUS_UNDECLARED", "name": "代码可用状态：codeAvailability 必填（page/templateContract/codingGuide.pageContext 三处读取，缺省按 unavailable 保守处理，不再静默跳过）；partial/unavailable 时 target.path 必须为空", "check": "check_path_without_verify", "source": "SKILL.md 代码可用状态 / references/01-workflow/04-demo-output-spec.md 代码可用状态与设计依据分离", "tests": "test_partial_path_not_empty_fails, test_code_status_undeclared_warns"},
    {"ruleId": "RULE-25", "errorCode": "VUE3_SYNTAX", "name": "禁止 Vue3 专属绑定语法作为实现要求", "check": "check_vue3_syntax", "source": "references/01-workflow/05-interaction-coding-guidelines.md", "tests": ""},
    {"ruleId": "RULE-26", "errorCode": "COMPONENT_MAPPING_MISSING", "name": "非普通文本字段声明组件映射", "check": "check_component_mapping", "source": "references/01-workflow/04-demo-output-spec.md", "tests": ""},
    {"ruleId": "RULE-27", "errorCode": "LEGACY_WIREFRAME", "name": "legacy 自由文本线框兼容模式", "check": "check_legacy_wireframe", "source": "SKILL.md 强制模板契约与线框校验（兼容模式）", "tests": "test_legacy_wireframe_warning_non_strict"},
    {"ruleId": "RULE-28", "errorCode": "MANIFEST_* / ORPHAN_CONTAINER", "name": "页面清单闭环：总览确认页面/容器与 pages（含 children）完整一致", "check": "check_manifest_closure", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_manifest_page_missing_fails, test_orphan_container_warns"},
    {"ruleId": "RULE-29", "errorCode": "OPERATION_*", "name": "操作目标闭环：open-container 目标存在、容器类型正确、高影响操作二次确认", "check": "check_operation_closure", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_operation_target_missing_fails, test_operation_confirm_missing_fails"},
    {"ruleId": "RULE-30", "errorCode": "TABS_*", "name": "Tab 变体闭环：多内容 Tab 页面强制完整变体、公共外壳与内容区、sections 绑定 tabId", "check": "check_tab_variants", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_tabs_missing_variants_fails, test_tabs_variant_count_mismatch_fails, test_tabs_orphan_variant_fails, test_tabs_variant_no_shell_fails, test_tabs_variant_no_content_fails"},
    {"ruleId": "RULE-31", "errorCode": "CODING_CLOSURE_*", "name": "页面级 Coding 闭环：pageContext 一致、每页至少一个开发项、无孤立开发项", "check": "check_coding_closure", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_coding_page_context_mismatch_fails, test_coding_no_items_fails"},
    {"ruleId": "RULE-32", "errorCode": "WIREFRAME_ASCII_TOO_SHORT / WIREFRAME_ASCII_NOT_DRAWN", "name": "线框图绘制质量：ascii 必须按模板绘制，禁止只有几个字或一句话", "check": "check_wireframe_drawing_quality", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_ascii_too_short_fails, test_ascii_not_drawn_fails"},
    {"ruleId": "RULE-33", "errorCode": "WIREFRAME_REGION_NOT_DRAWN", "name": "线框图双向一致性：regions 声明的内容性区块必须在 ascii 中有绘制痕迹", "check": "check_wireframe_region_drawn", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_ascii_region_not_drawn_warns"},
    {"ruleId": "RULE-34", "errorCode": "WIREFRAME_ASCII_LABEL_LIST", "name": "线框图布局完整性：ascii 禁止区域标签罗列，必须绘制为完整页面布局字符画", "check": "check_wireframe_label_list", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_wireframe_label_list_fails, test_wireframe_full_layout_passes"},
    {"ruleId": "RULE-35", "errorCode": "CHILD_PAGE_NOT_FLATTENED", "name": "页面平铺闭环：children 只允许子容器 ID 引用，禁止内嵌完整页面设计对象；子容器必须作为 pages 数组独立元素", "check": "check_child_page_flattened", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_child_page_not_flattened_fails, test_child_id_reference_passes"},
    {"ruleId": "RULE-36", "errorCode": "REQUIRED_FIELD_MISSING", "name": "字段完整性闭环：需求/规范明确要求的字段（表格列、表单项、筛选项、详情描述字段等）必须落入对应字段数组或 excludedFields 排除声明", "check": "check_requirement_fields", "source": "references/01-workflow/01-output-templates.md 字段完整性", "tests": "test_requirement_field_missing_fails, test_requirement_field_all_covered_passes, test_requirement_field_excluded_passes"},
    {"ruleId": "RULE-37", "errorCode": "FOOTER_ASCII_BUTTON_MISSING / FOOTER_ASCII_ORDER_MISMATCH / FOOTER_ASCII_CUSTOM_BUTTON", "name": "线框图底部按钮：必须按模板 buttonOrder 绘制（缺主操作/顺序错=error，缺次要按钮=warning）；按钮文案须落在模板允许集合，底部操作区出现模板外自定义按钮需 override 声明（业务自定义以业务为准）", "check": "check_footer_ascii_order", "source": "references/01-workflow/04-demo-output-spec.md 11.6 底部操作区 / Common Design 模板 footer.buttonOrder", "tests": "test_footer_ascii_button_missing_fails, test_footer_ascii_order_mismatch_fails, test_footer_ascii_order_passes, test_footer_ascii_custom_button_without_override_fails, test_footer_ascii_custom_button_with_override_passes"},
    {"ruleId": "RULE-38", "errorCode": "TABLE_DETAIL_FIELD_MISMATCH", "name": "表格与详情字段一致性：表格页展示的每个字段必须在对应详情容器中存在（Common Design 表格与详情字段一致规则兜底）", "check": "check_table_detail_field_consistency", "source": "Common Design 表格与详情字段一致规则 / references/01-workflow/06-quality-and-rules.md", "tests": "test_table_detail_field_mismatch_fails, test_table_detail_field_consistent_passes, test_table_detail_without_detail_skips, test_table_detail_via_children_fails"},
    {"ruleId": "RULE-39", "errorCode": "TABLE_TAG_*", "name": "表格标签使用约束：同一表格内标签总数 <= 5，深色/icon/点状标签各仅允许 1 次、浅色标签最多 2 次，样式未标注或中性描述字段占用标签配额时 warning 提示（Common Design 标签（IxTag）样式使用约束兜底）", "check": "check_table_tag_usage", "source": "Common Design 标签（IxTag）样式使用约束", "tests": "test_table_tag_count_exceeded_fails, test_table_tag_style_overused_fails, test_table_tag_style_unspecified_warns, test_table_tag_neutral_field_warns, test_table_tag_usage_passes"},
    {"ruleId": "RULE-40", "errorCode": "DESIGN_REF_*", "name": "设计依据可追溯：声称引用 Design Skill 的决策必须在页面 codingGuide.designReferences 登记来源（source 为 common-design/product-design/code/ai-fill，ref 非空）；声称有依据却无登记为 error（阻断），来源/字段格式类为 warning", "check": "check_design_references", "source": "references/01-workflow/00-design-skill-resolver.md 能力识别参考框架 / SKILL.md 输出可追溯", "tests": "test_design_ref_missing_fails, test_design_ref_invalid_source_warns, test_design_ref_empty_ref_warns, test_design_ref_passes, test_design_ref_absent_no_claim_passes"},
    {"ruleId": "RULE-41", "errorCode": "FORM_FIELD_KEY_MISMATCH / FILTER_FIELD_KEY_MISMATCH / TABLE_FIELD_KEY_MISMATCH / FORM_FIELD_KEY_PLACED_WRONG / FILTER_FIELD_KEY_PLACED_WRONG / TABLE_FIELD_KEY_PLACED_WRONG", "name": "字段形态键契约：字段内容必须写在渲染器实际渲染的键上（表单字段 formFields 用 rules/tips；筛选字段 filterFields 用 options/description；表格字段 tableFields/columns 用 display/description）；内容写在异态键导致 HTML 对应列静默空白时阻断（error），内容已渲染但键写错位置时 warning（RULE-41）", "check": "check_field_key_contract", "source": "references/01-workflow/04-demo-output-spec.md 字段形态键对照（RULE-41）/ 01-output-templates.md AI Coding指导输出格式", "tests": "test_form_field_options_not_rendered_fails, test_form_field_key_placed_wrong_warns, test_form_legacy_fields_options_not_rendered_fails, test_filter_field_rules_not_rendered_fails, test_table_field_rules_not_rendered_fails, test_field_key_contract_passes"},
    {"ruleId": "RULE-42", "errorCode": "REQ_TRACE_STATUS_NOT_RESOLVED / REQ_TRACE_MODEL_MISSING / REQ_TRACE_NO_TASK_REF / REQ_TRACE_TASK_UNBOUND / REQ_TRACE_TASK_INCOMPLETE / REQ_TRACE_ACTION_NO_OUTCOME / REQ_TRACE_FIELD_NO_PURPOSE / REQ_TRACE_SOURCE_INVALID / REQ_TRACE_FIELD_ROLE_INVALID", "name": "需求理解与页面设计追溯（条件式）：顶层声明 requirementUnderstanding 或页面带 taskRefs 时启用——需求理解未解决（status!=resolved）阻断 HTML 生成；每个页面必须关联至少一个业务任务；每个已建模业务任务必须有页面承载；核心动作必须有结果反馈；判断区块内字段须说明用途（fieldRole）；source/fieldRole 显式声明时值必须合法（RULE-42）", "check": "check_requirement_trace", "source": "references/01-workflow/04-demo-output-spec.md 11.9 需求理解与页面设计追溯（RULE-42）/ 01-output-templates.md 任务锚定字段", "tests": "test_requirement_status_not_resolved_fails, test_model_missing_but_task_ref_fails, test_page_without_task_ref_fails, test_task_not_bound_to_page_fails, test_task_without_outcome_fails, test_judge_block_field_no_purpose_warns, test_invalid_source_marker_warns, test_requirement_trace_passes, test_requirement_trace_skipped_without_model"},
    {"ruleId": "RULE-43", "errorCode": "DESIGN_REF_UNREAD / DESIGN_REF_UNANCHORED / TEMPLATE_OVERRIDE_NOT_APPLIED / TEMPLATE_SOURCE_UNREGISTERED / ABILITY_SOURCE_NOT_REGISTERED / DESIGN_CONTEXT_INCOMPLETE", "name": "设计依据一致性（条件式，顶层声明 designContext 时启用）：common/product-design 依据必须锚点级命中 readLedger 且 status=read（引用未读章节阻断，整篇已读用 #* 声明）；Product Design 声明模板覆盖时被覆盖页面必须真正采用 product 模板（禁止落到 Common Design）；coverage 声明 extend/override 的任意能力，适用页面必须登记同 ability 的 product-design 依据；采用 product 模板必须反向登记 product-design 依据并声明 productDesign.matched", "check": "check_design_basis_consistency", "source": "references/01-workflow/00-design-skill-resolver.md 设计依据登记与读取 / references/01-workflow/04-demo-output-spec.md designContext（RULE-43）", "tests": "test_design_context_unread_ref_fails, test_design_context_anchor_unread_fails, test_design_context_whole_doc_read_passes, test_design_context_template_override_not_applied_fails, test_design_context_template_source_unregistered_fails, test_ability_source_not_registered_fails, test_ability_source_registered_passes, test_design_context_consistent_passes, test_design_context_absent_skips"},
    {"ruleId": "RULE-44", "errorCode": "EXPORT_WITHOUT_VERIFY / COMPONENT_WITHOUT_VERIFY / VISUAL_BASELINE_WITHOUT_VERIFY / MAPPINGREF_WITHOUT_VERIFY / COMPONENT_PATH_WITHOUT_VERIFY", "name": "未核验实现细节隔离：partial/unavailable 时禁止把未核验的真实代码对象（target.export、产品专有组件名、真实组件路径、可视化基线页面、路径式 mappingRef）当作设计结论写进字段/编码指导，只能做语义级描述，真实导出名/Props/Events 留待 Coding Gate 核验", "check": "check_unverified_implementation", "source": "references/01-workflow/05-interaction-coding-guidelines.md 代码可用状态与设计依据分离 / references/01-workflow/04-demo-output-spec.md 未核验对象约束（RULE-44）", "tests": "test_unverified_export_fails, test_unverified_component_name_fails, test_unverified_ix_component_passes, test_unverified_visual_baseline_fails"},
    {"ruleId": "RULE-45", "errorCode": "WIREFRAME_REGION_ORDER_MISMATCH", "name": "线框图区域顺序一致性（warning）：regions 声明顺序应与 ascii 自上而下的绘制顺序一致，出现逆序（后面的区域绘制在更靠上的位置）时提示", "check": "check_wireframe_region_ascii_order", "source": "references/01-workflow/04-demo-output-spec.md 线框图绘制规范 / references/01-workflow/03-demo-page-decomposition.md 区域结构", "tests": "test_wireframe_region_order_mismatch_warns, test_wireframe_region_order_ok_passes"},
    {"ruleId": "RULE-46", "errorCode": "WIREFRAME_DUPLICATE_CONTROL / WIREFRAME_DUPLICATE_REGION", "name": "线框图重复绘制检测（warning）：带标记的控件标签（【】/[]）重复出现时提示；同一内容区域（步骤条/Tab/工具栏/筛选区/分页）在 ascii 中被绘制多次时提示", "check": "check_wireframe_duplicate_control", "source": "references/01-workflow/04-demo-output-spec.md 线框图绘制规范", "tests": "test_wireframe_duplicate_control_warns, test_wireframe_duplicate_region_warns"},
    {"ruleId": "RULE-47", "errorCode": "WIREFRAME_COLUMN_ALIGNMENT", "name": "线框图列对齐一致性（warning）：内容行右边界（右竖线）应在同一列，出现明显错位（两列结构断裂）时提示", "check": "check_wireframe_column_alignment", "source": "references/01-workflow/04-demo-output-spec.md 线框图绘制规范", "tests": "test_wireframe_column_alignment_warns, test_wireframe_full_layout_passes"},
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

# 表格标签使用约束（Common Design 标签（IxTag）样式使用约束）
# 同一个表格内：标签总数 <= 5；深色/icon/点状标签各自仅允许 1 次；浅色标签最多 2 次。
TAG_MAX_COUNT = 5
TAG_STYLE_LIMITS = {"dark": 1, "icon": 1, "dot": 1, "light": 2}
TAG_STYLE_KEYS = {
    "dark": ["深色", "dark"],
    "icon": ["icon", "图标", "带图标"],
    "dot": ["点状", "状态点", "dot"],
    "light": ["浅色", "light"],
}
TAG_STYLE_NAMES = {"dark": "深色", "icon": "icon", "dot": "点状", "light": "浅色"}
# 中性描述字段：标签配额不足时应改用普通文本或等宽文本，不占用标签配额
TAG_NEUTRAL_FIELD_KEYS = (
    "资产类型", "资产", "ip", "域名", "端口", "路径", "url",
    "地址", "主机", "mac", "序列号", "编号", "创建时间", "更新时间",
)

# 字段形态键契约（RULE-41）：HTML 生成器对各字段形态实际渲染的键。
# rendered 为该形态渲染的键；aliens 为其他形态的语义键（写了不会被渲染，
# 导致 HTML 对应列静默空白）。
FIELD_KEY_CONTRACT = {
    "formFields":   {"rendered": ("rules", "tips"),          "aliens": ("options", "description")},
    "filterFields": {"rendered": ("options", "description"), "aliens": ("rules", "tips")},
    "tableFields":  {"rendered": ("display", "description"), "aliens": ("rules", "tips", "options")},
    "columns":      {"rendered": ("display", "description"), "aliens": ("rules", "tips", "options")},
}

# RULE-42 需求理解与页面设计追溯：合法来源标记与字段用途取值
SOURCE_LABELS = ("requirement", "product-design", "common-design", "code", "ai-fill")
FIELD_ROLE_LABELS = {
    "identify": "识别信息",
    "judge": "判断信息",
    "precondition": "操作前置",
    "result": "结果反馈",
}


def _has_text_value(value):
    """字段值是否承载实际内容（None/空串/空容器视为空）。"""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


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
    """递归展开 pages 及其 children，产出 (page, json_path) 序列（设计闭环用）。
    children 支持字符串 ID 引用（跳过）与 dict 页面对象（兼容旧数据，递归展开）。"""
    for i, page in enumerate(pages or []):
        path = f"{base_path}[{i}]"
        if not isinstance(page, dict):
            continue
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
# 页面级单例控件：同一页 ascii 中重复绘制即提示（RULE-46）。行内重复动作（详情/编辑/删除）不在其列。
SINGULAR_CONTROLS = {
    "导出", "刷新", "查询", "重置", "确定", "取消", "提交", "保存", "关闭",
    "返回", "新增", "新建", "全选", "清空", "更多", "批量操作", "批量删除",
    "展开", "收起", "下载", "上传", "同步", "启用", "禁用",
}
# 底部操作按钮语义槽位 -> 允许文案（RULE-21 / RULE-37 单一来源）。
# 文案落在模板允许集合内即为合法；业务自定义按钮（文案不在集合内）必须通过 templateContract.override 声明。
FOOTER_KIND_LABELS = {
    "previous": ["上一步"],
    "next-or-complete": ["下一步", "完成", "提交"],
    "cancel": ["取消"],
    "confirm": ["确定", "确认", "保存"],
    "close": ["关闭"],
}
# 语义槽位英文别名（结构化 footerActions 的 kind 判定用）
FOOTER_KIND_ALIASES = {
    "previous": ["previous"],
    "next-or-complete": ["next"],
    "cancel": ["cancel"],
    "confirm": ["confirm", "ok"],
    "close": ["close"],
}
# ascii 底部按钮常见描述性前缀（归一化时剥离，如"底部关闭" -> "关闭"）
FOOTER_LABEL_PREFIXES = ("底部操作区", "底部操作", "底部按钮", "抽屉底部", "弹窗底部", "底部", "footer")
# 区域级单例（RULE-46 扩展）：同一 ascii 中同一内容区域重复绘制（>=2 行命中）即 warning
REGION_SINGLETON_KEYS = {
    "stepper": ["步骤条", "stepper"],
    "toolbar": ["工具栏", "操作栏"],
    "filter": ["筛选区", "查询区", "筛选栏"],
    "tab-bar": ["标签页", "页签"],
    "pagination": ["分页"],
}
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

    def _page_override_enabled(self, page):
        """Product Design / 用户确认的页面模板 override 是否生效。
        生效时以 Product Design 原文为准，放宽注册表结构约束（区域/顺序/必需组件），
        与 check_footer_alignment 对 footer 的处理保持一致。"""
        tc = page.get("templateContract") or {}
        ov = tc.get("override") or {}
        return bool(ov.get("enabled"))

    def check_skeleton_regions(self):
        """必需页面骨架区块是否存在（wireframe.regions 或 templateContract 声明）。override 生效时以 Product Design 为准，放宽。"""
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._page_override_enabled(page):
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
        """区域顺序与模板一致。override 生效时以 Product Design 为准，放宽。"""
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._page_override_enabled(page):
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
        """模板必需组件是否声明。override 生效时以 Product Design 为准，放宽。"""
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._page_override_enabled(page):
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

    def check_wireframe_region_ascii_order(self):
        """RULE-45 线框图区域顺序一致性（warning）：regions 声明顺序应与 ascii 中首次绘制位置自上而下一致。"""
        for page, ppath in self.all_pages:
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "")
            if len(ascii_text.strip()) < 8:
                continue
            regions = wf.get("regions") or []
            if not isinstance(regions, list) or len(regions) < 2:
                continue
            lines = ascii_text.splitlines()
            order = []
            for r in regions:
                if not isinstance(r, dict):
                    continue
                name = str(r.get("templateRegion") or r.get("id") or "")
                keys = REGION_ASCII_KEYS.get(name, [])
                if not keys:
                    continue
                idx = None
                for i, line in enumerate(lines):
                    if any(k in line for k in keys):
                        idx = i
                        break
                if idx is not None:
                    order.append((name, idx))
            mismatch = None
            for a in range(len(order)):
                for b in range(a + 1, len(order)):
                    if order[b][1] < order[a][1] - 1:
                        mismatch = (order[a], order[b])
                        break
                if mismatch:
                    break
            if mismatch:
                a, b = mismatch
                self.add_error(pid, "WIREFRAME_REGION_ORDER_MISMATCH", "warning",
                               f"{ppath}.wireframe",
                               f"regions 声明顺序与 ascii 绘制顺序矛盾：{b[0]} 绘制在 {a[0]} 之上",
                               f"{a[0]} 应位于 {b[0]} 之上",
                               f"{a[0]} 在第 {a[1] + 1} 行、{b[0]} 在第 {b[1] + 1} 行",
                               fix="调整 ascii 绘制顺序或 regions 顺序，使二者自上而下一致")

    def check_wireframe_duplicate_control(self):
        """RULE-46 线框图重复控件（warning）：页面级单例控件（导出/查询/确定/保存等）在同一页 ascii 中重复绘制时提示。
        仅针对页面级单例动作，行内重复动作（详情/编辑/删除）不计入，避免误报。"""
        singular = SINGULAR_CONTROLS
        for page, ppath in self.all_pages:
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "")
            if len(ascii_text.strip()) < 8:
                continue
            counts = {}
            for lb in re.findall(r"[【\[]([^】\]\n]{1,20})[】\]]", ascii_text):
                lb = lb.strip()
                if lb in singular:
                    counts[lb] = counts.get(lb, 0) + 1
            for lb, n in counts.items():
                if n >= 2:
                    self.add_error(pid, "WIREFRAME_DUPLICATE_CONTROL", "warning",
                                   f"{ppath}.wireframe.ascii",
                                   f"页面级控件在 ascii 中被重复绘制 {n} 次：{lb}",
                                   f"{lb} 仅绘制一次", f"出现 {n} 次",
                                   fix="删除重复绘制的控件，或区分其标签文本")
            # 区域级单例：同一内容区域（步骤条/Tab/工具栏/筛选区/分页）不应重复绘制
            lines = [l for l in ascii_text.splitlines() if l.strip()]
            for region, keys in REGION_SINGLETON_KEYS.items():
                hit_lines = [l for l in lines if any(k in l for k in keys)]
                if len(hit_lines) >= 2:
                    self.add_error(pid, "WIREFRAME_DUPLICATE_REGION", "warning",
                                   f"{ppath}.wireframe.ascii",
                                   f"区域 {region} 在 ascii 中被重复绘制（{len(hit_lines)} 处）",
                                   f"{region} 区域仅绘制一次",
                                   f"命中 {len(hit_lines)} 行：{' / '.join(k for k in keys if any(k in l for l in hit_lines))}",
                                   fix="合并重复绘制的区域，避免同一区域（步骤条/Tab/工具栏/筛选区/分页）在页面中出现两次")

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
            if self._page_override_enabled(page):
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
        for kind, keys in FOOTER_KIND_LABELS.items():
            if any(k.lower() in text for k in keys):
                return kind
        for kind, keys in FOOTER_KIND_ALIASES.items():
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

    @staticmethod
    def _ascii_region_drawn(ascii_text, keys):
        """判断 ascii 是否真正绘制了某区域：结构化字符画要求关键词出现在带框线的一行内（避免整段文本偶发命中），
        纯文本（简单字符串线框）退化为按分隔符分段匹配（避免整句包含即命中）。"""
        if not keys:
            return False
        lines = [l for l in ascii_text.splitlines() if l.strip()]
        if any(re.search(r"[│|]", l) for l in lines):
            for l in lines:
                if re.search(r"[│|─┌┐└┘├┤┬┴┼]", l) and any(k in l for k in keys):
                    return True
            return False
        segs = [s for s in re.split(r"[/、,，;；|]+", ascii_text) if s.strip()]
        return any(any(k in s for k in keys) for s in segs)

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
                if not self._ascii_region_drawn(ascii_text, keys):
                    self.add_error(pid, "WIREFRAME_REGION_NOT_DRAWN", "warning",
                                   f"$.pages[{self._idx(page)}].wireframe.ascii",
                                   f"regions 声明了 {region_name} 区块，但 ascii 线框图中未绘制对应区域",
                                   f"regions 含 {region_name}", f"ascii 未出现 {region_name} 相关绘制痕迹",
                                   fix=f"在 ascii 线框图中补画 {region_name} 区域（或补充对应文字标签）")

    def check_wireframe_label_list(self):
        """RULE-34 线框图布局完整性：ascii 禁止区域标签罗列（每行一个"区域名：内容"），必须绘制为完整页面布局字符画。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "").strip()
            if len(ascii_text) < 8:
                continue
            lines = [l.rstrip() for l in ascii_text.splitlines() if l.strip()]
            if len(lines) < 6:
                continue
            # 分隔线行：ASCII 风格 +----+ 或 box-drawing 风格 ┌─┐/├─┤/└─┘（纯横线，兼容现代字符画）
            rule_re = r"[+┌├└][─\-]+[+┐┤┘]?"
            sep_lines = [l for l in lines if re.fullmatch(rule_re, l.strip())]
            # 内容行：非边框线、非分隔线的行
            content_lines = [l for l in lines
                             if not re.match(r"^[+┌└├]", l.strip())
                             and not re.fullmatch(rule_re, l.strip())]
            if not content_lines:
                continue
            # 无右竖线闭合的内容行：以 | 或 │ 开头但不以 | 或 │ 结尾（区域标签罗列特征）
            unclosed = [l for l in content_lines
                        if l.strip().startswith(("|", "│")) and not l.strip().endswith(("|", "│"))]
            if len(unclosed) >= 3 and len(sep_lines) >= 3 and len(unclosed) >= len(content_lines) * 0.4:
                self.add_error(pid, "WIREFRAME_ASCII_LABEL_LIST", "error",
                               f"$.pages[{self._idx(page)}].wireframe.ascii",
                               "线框图是区域标签罗列，未绘制为页面布局图",
                               "从 Common Design 页面模板文档继承模板布局样式并填入业务内容的完整页面布局字符画",
                               f"{len(unclosed)} 个内容行无右竖线闭合、{len(sep_lines)} 个分隔行，形似每行一个'区域名：内容'",
                               fix="读取 Common Design 页面模板文档中该页面类型的模板结构与线框样式，继承模板样式并填入业务内容，禁止逐区域罗列标签")

    def check_child_page_flattened(self):
        """RULE-35 页面平铺闭环：children 只允许子容器 ID 引用（字符串），禁止内嵌任何页面对象；
        子容器（弹窗/抽屉等）必须作为 pages 数组的独立元素，否则生成器不会渲染导致漏页。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            children = page.get("children")
            if not children:
                continue
            path = f"$.pages[{self._idx(page)}].children"
            if isinstance(children, dict):
                self.add_error(pid, "CHILD_PAGE_NOT_FLATTENED", "error", path,
                               "children 内嵌了完整页面设计对象，子容器必须在 pages 数组平铺",
                               "children 只允许子容器 ID 引用（字符串）或空数组",
                               "children 为对象，包含页面设计字段",
                               fix="将该子容器提升为 pages 数组的独立页面对象（含 templateContract/wireframe/sections/codingGuide），父页面 children 只保留其 ID 引用")
                continue
            for child in children:
                if isinstance(child, dict):
                    self.add_error(pid, "CHILD_PAGE_NOT_FLATTENED", "error", path,
                                   "children 内嵌了页面对象，子容器必须在 pages 数组平铺，children 只允许字符串 ID 引用",
                                   "children 只允许子容器 ID 引用（字符串）或空数组",
                                   f"children 元素为对象（{child.get('id') or '无id'}）",
                                   fix="将该子容器提升为 pages 数组的独立页面对象（含 templateContract/wireframe/sections/codingGuide），父页面 children 只保留其 ID 引用（字符串）")

    def check_requirement_fields(self):
        """RULE-36 字段完整性闭环：需求/规范明确要求的字段必须逐项落入对应字段数组（表格列/表单项/筛选项/详情描述字段）或 excludedFields 排除声明。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            required = page.get("requirementFieldNames") or []
            if not required:
                continue
            excluded = page.get("excludedFields") or {}
            covered = set()
            for section in self.page_sections(page):
                for key in ("tableFields", "formFields", "cardFields", "fields", "filterFields", "detailFields"):
                    for field in section.get(key) or []:
                        if isinstance(field, dict) and field.get("name"):
                            covered.add(str(field["name"]).strip())
            for key in ("tableFields", "formFields", "filterFields"):
                for field in page.get(key) or []:
                    if isinstance(field, dict) and field.get("name"):
                        covered.add(str(field["name"]).strip())
            missing = []
            for name in required:
                n = str(name).strip()
                if not n:
                    continue
                if n in covered or n in excluded:
                    continue
                if any(n in c or c in n for c in covered if len(c) >= 2 and len(n) >= 2):
                    continue
                missing.append(n)
            if missing:
                self.add_error(pid, "REQUIRED_FIELD_MISSING", "error",
                               f"$.pages[{self._idx(page)}].requirementFieldNames",
                               f"需求明确要求的字段未落入设计说明书：{'、'.join(missing)}",
                               "需求/规范明确列出的每个字段都出现在对应区块的字段数组（表格列/表单项/筛选项/详情字段）中，或写入 excludedFields 并说明排除原因",
                               f"缺失字段：{'、'.join(missing)}",
                               fix="将缺失字段补充到对应区块的字段数组（tableFields/formFields/filterFields/cardFields/fields等），若该页面确实不展示则写入 excludedFields 并说明原因")

    def _table_field_names(self, page):
        """表格页展示的字段名（sections 中 tableFields + 页面级 tableFields）。"""
        names = []
        for section in self.page_sections(page):
            for field in section.get("tableFields") or []:
                if isinstance(field, dict) and field.get("name"):
                    names.append(str(field["name"]).strip())
        for field in page.get("tableFields") or []:
            if isinstance(field, dict) and field.get("name"):
                names.append(str(field["name"]).strip())
        return names

    def _detail_field_names(self, page):
        """详情容器页展示的字段名（sections 与页面级各字段数组：详情描述字段/卡片/表格/表单等）。"""
        names = set()
        keys = ("tableFields", "formFields", "cardFields", "fields", "filterFields", "detailFields")
        for section in self.page_sections(page):
            for key in keys:
                for field in section.get(key) or []:
                    if isinstance(field, dict) and field.get("name"):
                        names.add(str(field["name"]).strip())
        for key in keys:
            for field in page.get(key) or []:
                if isinstance(field, dict) and field.get("name"):
                    names.add(str(field["name"]).strip())
        return names

    def _linked_detail_ids(self, page, by_id):
        """表格页关联的详情容器 ID：open-container 操作指向详情类容器 + children 挂载的详情容器。"""
        candidates = []
        for op in page.get("operations") or []:
            if op.get("action") == "open-container" and op.get("targetPageId"):
                candidates.append(str(op["targetPageId"]))
        for child in page.get("children") or []:
            if isinstance(child, str):
                candidates.append(child)
            elif isinstance(child, dict) and child.get("id"):
                candidates.append(str(child["id"]))
        ids = []
        for cid in candidates:
            target = by_id.get(cid)
            if target is None or cid in ids:
                continue
            tid = self.page_template(target)
            ptype = str(target.get("type", ""))
            if (tid and tid.startswith("page-detail")) or "详情" in ptype:
                ids.append(cid)
        return ids

    def check_table_detail_field_consistency(self):
        """RULE-38 表格与详情字段一致性：表格页展示的字段必须在对应详情容器中存在。

        场景：表格展示部分字段、详情抽屉展示完整字段。Common Design 已明确
        “表格展示的字段与详情抽屉字段保持一致”规则，本校验兜底：表格页 tableFields
        中每个字段都必须在关联详情容器（open-container 目标或 children 挂载的详情类容器）
        的字段数组（detailFields/cardFields/fields/tableFields 等）中找到对应项。
        表格无详情容器时不校验（非“表格有详情”场景）。
        """
        by_id = {str(p.get("id", "")): p for p, _ in self.all_pages if p.get("id")}
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            table_fields = self._table_field_names(page)
            if not table_fields:
                continue
            detail_ids = self._linked_detail_ids(page, by_id)
            if not detail_ids:
                continue
            detail_names = set()
            for did in detail_ids:
                detail_names |= self._detail_field_names(by_id[did])
            norm_detail = {norm(n) for n in detail_names if norm(n)}
            missing = []
            for name in table_fields:
                n = norm(name)
                if not n:
                    continue
                if n in norm_detail:
                    continue
                if any(len(n) >= 2 and len(nd) >= 2 and (n in nd or nd in n) for nd in norm_detail):
                    continue
                missing.append(name)
            if missing:
                self.add_error(pid, "TABLE_DETAIL_FIELD_MISMATCH", "error",
                               f"{path}.sections.tableFields",
                               f"表格展示的字段与详情不一致，以下表格字段在详情容器（{'、'.join(detail_ids)}）中不存在：{'、'.join(missing)}",
                               "表格展示的每个字段都能在对应详情容器中找到（Common Design 表格与详情字段一致规则）",
                               f"缺失字段：{'、'.join(missing)}",
                               source_ref="Common Design 表格与详情字段一致规则",
                               fix="将表格中展示的字段补充到对应详情容器的字段数组（detailFields/cardFields/fields/tableFields），或从表格移除该字段")

    def _collect_table_blocks(self, page):
        """收集页面内每个表格区块的字段列表（sections 中带 tableFields 的区块 + 页面级 tableFields）。"""
        blocks = []
        for section in self.page_sections(page):
            fields = section.get("tableFields") or []
            if fields:
                blocks.append((section.get("title") or "表格区", fields))
        page_fields = page.get("tableFields") or []
        if page_fields:
            blocks.append(("页面级表格", page_fields))
        return blocks

    def _is_tag_field(self, field):
        """字段是否为标签组件（IxTag / 标签）。"""
        if not isinstance(field, dict):
            return False
        comp = str(field.get("iduxComponent") or "").lower()
        if "ixtag" in comp:
            return True
        if "tag" in comp and "select" not in comp:
            return True
        text = " ".join(str(field.get(k) or "") for k in ("component", "display"))
        return "标签" in text

    def _tag_style(self, field):
        """识别标签字段样式：dark/icon/dot/light，未标注返回 None。"""
        if not isinstance(field, dict):
            return None
        texts = [str(field.get(k) or "") for k in ("display", "description", "style", "tagType", "tagStyle")]
        joined = " ".join(texts).lower()
        for style, keys in TAG_STYLE_KEYS.items():
            if any(k.lower() in joined for k in keys):
                return style
        return None

    def check_table_tag_usage(self):
        """RULE-39 表格标签使用约束（Common Design 标签（IxTag）样式使用约束兜底）。

        同一个表格内：
          - 标签使用数量 <= 5（超出 -> error）
          - 深色/icon/点状标签各自仅允许 1 次、浅色标签最多 2 次（超出 -> error）
          - 存在 >= 2 个标签且样式未标注时 warning，提示无法自动校验“同一样式仅允许 1 次”
          - 中性描述字段（资产类型/IP/域名等）使用标签时 warning，提示配额优先留给重要业务字段
        """
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            for block_title, fields in self._collect_table_blocks(page):
                tag_fields = [(f, self._tag_style(f)) for f in fields if self._is_tag_field(f)]
                if not tag_fields:
                    continue
                path = f"$.pages[{self._idx(page)}].sections"
                source_ref = "Common Design 标签（IxTag）样式使用约束"
                # 1) 标签总数配额
                if len(tag_fields) > TAG_MAX_COUNT:
                    self.add_error(pid, "TABLE_TAG_COUNT_EXCEEDED", "error", path,
                                   f"表格区块「{block_title}」标签使用数量超过配额：{len(tag_fields)} 个（上限 {TAG_MAX_COUNT} 个）",
                                   f"同一表格内标签数量 <= {TAG_MAX_COUNT}", f"{len(tag_fields)} 个",
                                   source_ref=source_ref,
                                   fix=f"削减标签字段至 {TAG_MAX_COUNT} 个以内；标签配额优先留给风险等级、处置/启用禁用状态、本身命名为“标签”的重要业务字段，中性描述字段改用普通文本或等宽文本")
                # 2) 样式配额：深色/icon/点状各仅 1 次，浅色最多 2 次
                style_counts = {}
                for _f, style in tag_fields:
                    style_counts[style] = style_counts.get(style, 0) + 1
                for style, limit in TAG_STYLE_LIMITS.items():
                    cnt = style_counts.get(style, 0)
                    if cnt > limit:
                        self.add_error(pid, "TABLE_TAG_STYLE_OVERUSED", "error", path,
                                       f"表格区块「{block_title}」{TAG_STYLE_NAMES[style]}标签使用 {cnt} 次，超过同一样式配额（{limit} 次）",
                                       f"{TAG_STYLE_NAMES[style]}标签最多 {limit} 次", f"{cnt} 次",
                                       source_ref=source_ref,
                                       fix=f"同一表格内{TAG_STYLE_NAMES[style]}标签仅保留 {limit} 个，其余字段改用其他样式或普通文本，禁止多个字段同时使用同一样式")
                # 3) 样式未标注：无法自动校验“同一样式仅 1 次”的盲区提示（双重检查）
                unspecified = [f for f, s in tag_fields if s is None]
                if len(tag_fields) >= 2 and unspecified:
                    self.add_error(pid, "TABLE_TAG_STYLE_UNSPECIFIED", "warning", path,
                                   f"表格区块「{block_title}」存在 {len(unspecified)} 个标签字段未标注样式（深色/浅色/icon/点状），无法自动校验“同一样式仅允许出现 1 次”",
                                   "标签字段在 display/description 中标注样式", "样式未标注",
                                   source_ref=source_ref,
                                   fix="为标签字段标注样式（深色/浅色/icon/点状），确保深色/icon/点状各不超过 1 个、浅色不超过 2 个，禁止多个字段同时使用同一样式")
                # 4) 中性描述字段不占用标签配额
                for f, _style in tag_fields:
                    name = str(f.get("name") or "")
                    if any(k in name.lower() for k in TAG_NEUTRAL_FIELD_KEYS):
                        self.add_error(pid, "TABLE_TAG_NEUTRAL_FIELD", "warning", path,
                                       f"表格区块「{block_title}」中性描述字段「{name}」使用了标签组件，标签配额应优先留给风险等级、处置/启用禁用状态等重要业务字段",
                                       "中性描述字段使用普通文本或等宽文本", f"「{name}」使用标签组件",
                                       source_ref=source_ref,
                                       fix=f"将「{name}」改为普通文本或等宽文本，把标签配额留给需要凸显的重要业务状态字段")

    def check_field_key_contract(self):
        """RULE-41 字段形态键契约：字段内容必须写在渲染器实际渲染的键上。

        formFields 渲染 rules/tips；filterFields 渲染 options/description；
        tableFields/columns 渲染 display/description。内容写在异态键上会导致
        HTML 对应列静默空白：异态键有值且渲染键为空 -> error（阻断生成）；
        渲染键也有值 -> warning（内容已渲染但键写错位置）。
        区块级自由文本 fields 数组中的字典字段按区块类型推定形态
        （含“表单/form”按表单键、含“表格/列表/table/list”按表格键），
        与 HTML 生成器 normalize_legacy_fields 的推定规则一致。
        """
        for page, path in self.all_pages:
            pid = page.get("id", "")
            for key in ("formFields", "filterFields", "tableFields", "columns"):
                fields = page.get(key)
                if isinstance(fields, list):
                    self._audit_field_contract(pid, f"{path}.{key}", key, fields)
            sections = page.get("sections")
            if not isinstance(sections, list):
                continue
            for si, section in enumerate(sections):
                if not isinstance(section, dict):
                    continue
                spath = f"{path}.sections[{si}]"
                for key in ("formFields", "filterFields", "tableFields", "columns"):
                    fields = section.get(key)
                    if isinstance(fields, list):
                        self._audit_field_contract(pid, f"{spath}.{key}", key, fields)
                legacy = section.get("fields")
                if isinstance(legacy, list):
                    block_type = f"{section.get('type', '')} {section.get('title', '')}"
                    if "表单" in block_type or "form" in block_type:
                        self._audit_field_contract(pid, f"{spath}.fields", "formFields", legacy)
                    elif "表格" in block_type or "列表" in block_type or "table" in block_type or "list" in block_type:
                        self._audit_field_contract(pid, f"{spath}.fields", "tableFields", legacy)

    def _audit_field_contract(self, pid, base_path, field_key, fields):
        """对一组字段执行键契约审计（RULE-41 单字段检查）。"""
        contract = FIELD_KEY_CONTRACT.get(field_key)
        if not contract:
            return
        rendered, aliens = contract["rendered"], contract["aliens"]
        prefix = "FORM" if field_key == "formFields" else "FILTER" if field_key == "filterFields" else "TABLE"
        for i, field in enumerate(fields):
            if not isinstance(field, dict):
                continue
            fpath = f"{base_path}[{i}]"
            alien_present = [k for k in aliens if _has_text_value(field.get(k))]
            if not alien_present:
                continue
            rendered_present = [k for k in rendered if _has_text_value(field.get(k))]
            if not rendered_present:
                self.add_error(
                    pid, f"{prefix}_FIELD_KEY_MISMATCH", "error", fpath,
                    f"字段内容写在了不渲染的键 {alien_present} 上，HTML 的对应列将静默空白",
                    f"内容写入渲染键 {list(rendered)}",
                    f"内容仅存在于不渲染键 {alien_present}",
                    fix=f"删除 {alien_present}，把内容改写进渲染键 {list(rendered)}",
                )
            else:
                self.add_error(
                    pid, f"{prefix}_FIELD_KEY_PLACED_WRONG", "warning", fpath,
                    f"字段内容同时出现在渲染键 {rendered_present} 与不渲染键 {alien_present}，键位置错误",
                    f"仅使用渲染键 {list(rendered)}",
                    f"同时使用了不渲染键 {alien_present}",
                    fix=f"删除 {alien_present}，内容统一写入渲染键 {list(rendered)}",
                )

    def check_design_references(self):
        """RULE-40 设计依据可追溯：声称引用 Design Skill 的决策必须在 codingGuide.designReferences 登记来源。

        声称有依据却无登记为 error（阻断）；来源/字段格式非法为 warning。
        是否真正读取、以及“声明来源 vs 实际落地”的一致性由 RULE-43 强制校验。
        """
        allowed_sources = ("common-design", "product-design", "code", "ai-fill")
        for page, path in self.all_pages:
            pid = page.get("id", "")
            cg = page.get("codingGuide") or {}
            refs = cg.get("designReferences")
            if refs is None:
                # 页面存在声称引用 Design Skill 的来源标注，但无 designReferences 登记
                claimed = self._claimed_design_sources(page)
                if claimed:
                    self.add_error(pid, "DESIGN_REF_MISSING", "error",
                                   f"{path}.codingGuide.designReferences",
                                   f"页面声称引用 {claimed}，但 codingGuide.designReferences 缺失",
                                   "designReferences 登记", "缺失",
                                   fix="在 codingGuide.designReferences 中登记对应来源")
                continue
            if not isinstance(refs, list):
                self.add_error(pid, "DESIGN_REF_TYPE", "warning",
                               f"{path}.codingGuide.designReferences",
                               "designReferences 必须是数组", "数组", type(refs).__name__,
                               fix="将 designReferences 改为数组")
                continue
            for i, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    self.add_error(pid, "DESIGN_REF_ITEM", "warning",
                                   f"{path}.codingGuide.designReferences[{i}]",
                                   "引用项必须是对象", "对象", type(ref).__name__,
                                   fix="将引用项改为对象")
                    continue
                src = str(ref.get("source", "")).strip()
                if src not in allowed_sources:
                    self.add_error(pid, "DESIGN_REF_SOURCE", "warning",
                                   f"{path}.codingGuide.designReferences[{i}].source",
                                   f"source 必须为 {allowed_sources} 之一",
                                   "合法 source", src or "空",
                                   fix="修正 source 取值")
                if not str(ref.get("ref", "")).strip():
                    self.add_error(pid, "DESIGN_REF_REF", "warning",
                                   f"{path}.codingGuide.designReferences[{i}].ref",
                                   "ref 来源标识不能为空", "非空 ref", "空",
                                   fix="补充 ref 来源标识")

    def _claimed_design_sources(self, page):
        """收集页面中显式声称引用 Design Skill 的来源标注。"""
        claimed = set()
        rr = page.get("restoreRequirement") or {}
        for comp in rr.get("components") or []:
            src = str(comp.get("source", ""))
            if "Product Design" in src:
                claimed.add("Product Design")
            if "Common Design" in src:
                claimed.add("Common Design")
        tc = page.get("templateContract") or {}
        ov = tc.get("override") or {}
        if "Product Design" in str(ov.get("source", "")):
            claimed.add("Product Design")
        return sorted(claimed)

    @staticmethod
    def _norm_label(text):
        return re.sub(r"[\s/、,，;；:：·\-_\[\]【】()（）]", "", str(text or "")).lower()

    def _strip_footer_prefix(self, text):
        t = str(text or "").strip()
        for p in FOOTER_LABEL_PREFIXES:
            if t.startswith(p):
                return t[len(p):].strip()
        return t

    def _footer_region_text(self, ascii_text):
        """定位 ascii 底部操作区文本（最后一个内部分隔线之后、底边线之前的区块）；
        无法定位结构化字符画时返回空串（此时不做自定义按钮检测，避免误伤整体描述文本）。"""
        lines = [l.rstrip() for l in ascii_text.splitlines() if l.strip()]
        if len(lines) < 2:
            return ""
        struct = [i for i, l in enumerate(lines)
                  if re.fullmatch(r"[+\-─│┌┐└┘├┤┬┴┼ ]+", l.strip()) and re.search(r"[─\-]", l)]
        internal = [i for i in struct if 0 < i < len(lines) - 1]
        if not internal:
            return ""
        start = max(internal) + 1
        end = len(lines)
        while end > start and re.fullmatch(r"[+\-─│┌┐└┘├┤┬┴┼ ]+", lines[end - 1].strip()):
            end -= 1
        return "\n".join(lines[start:end]).strip()

    def _check_footer_custom_buttons(self, page, pid, path, template, allowed, footer_text):
        """RULE-37：底部操作区出现的、模板允许集合外的按钮，需 override 声明（业务自定义按钮以业务为准）。"""
        tc = page.get("templateContract") or {}
        if bool((tc.get("override") or {}).get("enabled")):
            return
        allowed_norm = {self._norm_label(a) for a in allowed}
        global_norm = {self._norm_label(l) for labels in FOOTER_KIND_LABELS.values() for l in labels}
        seen = set()
        for raw in re.findall(r"[【\[]([^】\]\n]{1,24})[】\]]", footer_text):
            token = raw.strip()
            if not token or token in seen:
                continue
            seen.add(token)
            base = self._norm_label(self._strip_footer_prefix(token))
            if not base or base in allowed_norm:
                continue
            # 仅当该标签由底部按钮文案组合而成（如"保存并关闭"）或为其它模板的底部按钮时，判为自定义底部按钮
            if any(g and g in base for g in global_norm):
                self.add_error(pid, "FOOTER_ASCII_CUSTOM_BUTTON", "error",
                               path,
                               f"底部操作区出现模板允许集合外的自定义按钮：{token}",
                               f"模板允许按钮：{' / '.join(allowed)}（或启用 templateContract.override 并登记业务覆盖来源）",
                               token,
                               source_ref=template.get("source", ""),
                               fix="改用模板允许的按钮文案，或启用 templateContract.override 并在 source 登记业务覆盖来源")

    def check_footer_ascii_order(self):
        """RULE-37 线框图底部按钮：ascii 必须按模板 buttonOrder 绘制（主操作在左、次操作在右），
        按钮文案须落在模板允许集合（缺主操作/顺序错=error，缺次要按钮=warning），自定义按钮需 override 声明。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = (self.registry.get("templates") or {}).get(tid) or {}
            expected_order = (template.get("footer") or {}).get("buttonOrder") or []
            if not expected_order:
                continue
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "")
            if not ascii_text.strip():
                continue
            path = f"$.pages[{self._idx(page)}].wireframe.ascii"
            tpl = template.get("source", "")
            allowed = []
            for kind in expected_order:
                allowed.extend(FOOTER_KIND_LABELS.get(kind, []))
            pos = []
            for kind in expected_order:
                idx = -1
                for key in FOOTER_KIND_LABELS.get(kind, []):
                    i = ascii_text.find(key)
                    if i != -1 and (idx == -1 or i < idx):
                        idx = i
                if idx != -1:
                    pos.append((idx, kind))
            pos.sort()
            actual_order = [k for _, k in pos]
            expected_present = [k for k in expected_order if k in actual_order]
            if not pos:
                # 一个模板按钮都没画：修复"找不到按钮即静默通过"（P09/P10 只画 [关闭] 的场景）
                self.add_error(pid, "FOOTER_ASCII_BUTTON_MISSING", "error",
                               path,
                               "线框图底部操作区未按模板绘制任何按钮",
                               f"按 Common Design 模板 buttonOrder 绘制底部按钮：{' → '.join(expected_order)}",
                               "未找到任何模板按钮（确定/取消/上一步/下一步/关闭等）",
                               source_ref=tpl,
                               fix="按 Common Design 模板 buttonOrder 在底部操作区绘制按钮，禁止只画关闭或省略主操作")
            elif actual_order != expected_present:
                self.add_error(pid, "FOOTER_ASCII_ORDER_MISMATCH", "error",
                               path,
                               "线框图中底部按钮出现顺序与模板按钮顺序不一致",
                               f"按 Common Design 模板顺序绘制底部按钮：{' → '.join(expected_order)}（主操作在左、次操作在右）",
                               f"ascii 中出现顺序：{' → '.join(actual_order)}",
                               source_ref=tpl,
                               fix="调整 ascii 线框图中按钮的绘制顺序，使主操作（确定/保存）在左、次操作（取消/关闭）在右，与模板 buttonOrder 一致")
            elif len(actual_order) < len(expected_order):
                missing_kinds = [k for k in expected_order if k not in actual_order]
                self.add_error(pid, "FOOTER_ASCII_BUTTON_MISSING", "warning",
                               path,
                               "线框图底部操作区缺少模板要求的按钮",
                               f"模板按钮：{' → '.join(expected_order)}",
                               f"缺少：{' → '.join(missing_kinds)}",
                               source_ref=tpl,
                               fix="补齐模板 buttonOrder 中缺失的按钮文案")
            footer_text = self._footer_region_text(ascii_text)
            if footer_text:
                self._check_footer_custom_buttons(page, pid, path, template, allowed, footer_text)

    def check_wireframe_column_alignment(self):
        """RULE-47 线框图列对齐一致性（warning）：内容行右边界（右竖线）应在同一列，
        出现明显错位时提示，用于捕捉"两列结构断裂"。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "")
            lines = [l.rstrip() for l in ascii_text.splitlines() if l.strip()]
            if len(lines) < 4:
                continue
            right_cols = []
            for l in lines:
                s = l.strip()
                if re.fullmatch(r"[+\-─│┌┐└┘├┤┬┴┼ ]+", s):
                    continue
                if s and s[-1] in "│|":
                    right_cols.append(len(l) - 1)
            if len(right_cols) < 4:
                continue
            drift = max(right_cols) - min(right_cols)
            if drift >= 3:
                self.add_error(pid, "WIREFRAME_COLUMN_ALIGNMENT", "warning",
                               f"$.pages[{self._idx(page)}].wireframe.ascii",
                               "线框图内容行右边界未对齐，疑似两列结构断裂",
                               "各内容行右竖线对齐在同一列",
                               f"右边界列跨度 {drift}（{min(right_cols)}~{max(right_cols)}）",
                               fix="对齐各行右边界竖线，或检查是否把两列结构画断")

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

    def _declared_code_availability(self, page):
        """读取页面声明的代码可用状态：page / templateContract / codingGuide.pageContext 三处取首个非空。"""
        tc = page.get("templateContract") or {}
        ctx = (page.get("codingGuide") or {}).get("pageContext") or {}
        for value in (page.get("codeAvailability"),
                      tc.get("codeAvailability"),
                      ctx.get("codeAvailability")):
            text = str(value or "").strip().lower()
            if text:
                return text
        return ""

    @staticmethod
    def _looks_like_path(text):
        text = str(text or "").strip()
        return "/" in text and "." in text

    @staticmethod
    def _norm_doc(text):
        """归一化文档路径（取 # 前），统一分隔符与大小写。"""
        return str(text or "").split("#", 1)[0].strip().replace("\\", "/").lower()

    @staticmethod
    def _norm_ref(text):
        """归一化设计依据引用为 (文档路径, 章节锚点)。无 # 时锚点为空串。"""
        raw = str(text or "").strip().replace("\\", "/")
        doc, _, anchor = raw.partition("#")
        return doc.strip().lower(), anchor.strip().lower()

    def _build_ledger(self, entries):
        """构建 readLedger 索引 {(文档, 锚点): status}。

        约定：条目形如 {"ref": "<文档路径>#<章节锚点>", "status": "read|index-only"}；
        锚点用 "*" 表示整篇已读。兼容旧写法 {"doc": <文档路径>, "status": ...}（视为整篇，锚点 "*"）。
        """
        ledger = {}
        for ent in entries or []:
            if not isinstance(ent, dict):
                continue
            if "ref" in ent:
                doc, anchor = self._norm_ref(ent.get("ref", ""))
            else:
                doc, anchor = self._norm_doc(ent.get("doc", "")), "*"
            if doc:
                ledger[(doc, anchor)] = str(ent.get("status", "")).strip().lower()
        return ledger

    @staticmethod
    def _split_component_tokens(value):
        return [t.strip() for t in re.split(r"[/,，、|;；\s]+", str(value or "")) if t.strip()]

    @staticmethod
    def _is_unverified_component_token(token):
        """真实/产品专有组件名令牌：以字母开头、非 iDux 标准组件（非 Ix 前缀）且含至少两个大写字母。"""
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", token):
            return False
        if token.startswith("Ix"):
            return False
        return sum(1 for c in token if c.isupper()) >= 2

    def _pd_registered_component_names(self, page):
        """收集页面已登记的 Product Design 组件/能力名（小写），用于区分“PD 已登记但代码未核验”与“凭空断言组件名”。"""
        names = set()

        def _add(v):
            s = str(v).strip()
            if s:
                names.add(s.lower())

        refs = (page.get("codingGuide") or {}).get("designReferences") or []
        for r in refs:
            if isinstance(r, dict) and str(r.get("source", "")).strip() == "product-design":
                for key in ("ability", "component", "name"):
                    _add(r.get(key, ""))
                for v in (r.get("components") or []):
                    _add(v)
        cc = (page.get("templateContract") or {}).get("componentContract") or {}
        for pc in (cc.get("patternComponents") or []):
            if isinstance(pc, dict):
                _add(pc.get("ability", ""))
                for v in (pc.get("components") or []):
                    _add(v)
        return names

    def _flag_unverified_components(self, pid, json_path, value, code_avail, seen, pd_registered=None):
        pd_registered = pd_registered or set()
        for token in self._split_component_tokens(value):
            if self._is_unverified_component_token(token) and token not in seen:
                seen.add(token)
                if token.lower() in pd_registered:
                    self.add_error(pid, "COMPONENT_WITHOUT_VERIFY", "warning",
                                   json_path,
                                   f"组件名（{token}）为 Product Design 已登记的业务封装，但代码状态为 {code_avail} 尚未核验",
                                   "保留业务组件名并标注“待 Coding 阶段核验”，或改为语义级能力描述",
                                   token,
                                   fix="保留业务组件名并标注“待 Coding 阶段核验”；不得因此退回 iDux 通用组件")
                    continue
                self.add_error(pid, "COMPONENT_WITHOUT_VERIFY", "error",
                               json_path,
                               f"代码状态为 {code_avail} 时不得把未核验的产品专有组件名（{token}）作为设计结论",
                               "语义级能力描述或 Ix 标准组件；真实组件名留待 Coding Gate 核验",
                               token,
                               fix="将产品专有组件名替换为语义级能力描述，或标记为 Coding 阶段待核验")

    def check_path_without_verify(self):
        """RULE-24：codeAvailability 必填（缺省按 unavailable 处理，不再静默跳过）；partial/unavailable 时禁止真实 target.path。"""
        for page, path in self.all_pages:
            pid = page.get("id", "")
            declared = self._declared_code_availability(page)
            code_avail = declared or "unavailable"
            if not declared:
                self.add_error(pid, "CODE_STATUS_UNDECLARED", "warning",
                               f"{path}.codeAvailability",
                               "未声明代码可用状态，已按 unavailable 保守处理",
                               "verified/partial/unavailable", "缺失",
                               fix="在 codingGuide.pageContext.codeAvailability 声明代码可用状态")
            if code_avail not in ("partial", "unavailable"):
                continue
            cg = page.get("codingGuide") or {}
            for i, item in enumerate(cg.get("pageItems") or []):
                if not isinstance(item, dict):
                    continue
                target = item.get("target") or {}
                path_val = target.get("path")
                if str(path_val or "").strip():
                    self.add_error(pid, "PATH_WITHOUT_VERIFY", "error",
                                   f"{path}.codingGuide.pageItems[{i}].target.path",
                                   f"代码状态为 {code_avail} 时 target.path 必须为空",
                                   "空 path（待映射阶段核验）", path_val,
                                   fix="清空 target.path，标记 mappingStatus=pending 或 blocked")

    def check_unverified_implementation(self):
        """RULE-44：partial/unavailable 时禁止把未核验的真实代码对象当作设计结论（只允许语义级描述）。"""
        for page, path in self.all_pages:
            pid = page.get("id", "")
            code_avail = self._declared_code_availability(page) or "unavailable"
            if code_avail not in ("partial", "unavailable"):
                continue
            seen = set()
            pd_registered = self._pd_registered_component_names(page)
            cg = page.get("codingGuide") or {}
            for i, item in enumerate(cg.get("pageItems") or []):
                if not isinstance(item, dict):
                    continue
                target = item.get("target") or {}
                if str(target.get("export", "")).strip():
                    self.add_error(pid, "EXPORT_WITHOUT_VERIFY", "error",
                                   f"{path}.codingGuide.pageItems[{i}].target.export",
                                   f"代码状态为 {code_avail} 时 target.export（真实导出名）必须为空",
                                   "空 export（Coding Gate 核验）", target.get("export"),
                                   fix="清空 target.export，真实导出名留待 Coding 阶段核验")
                self._flag_unverified_components(
                    pid, f"{path}.codingGuide.pageItems[{i}].target.component",
                    target.get("component", ""), code_avail, seen, pd_registered)
                self._flag_unverified_components(
                    pid, f"{path}.codingGuide.pageItems[{i}].target.components",
                    "/".join(str(c) for c in (target.get("components") or [])), code_avail, seen, pd_registered)
                mapping_ref = str(item.get("mappingRef", "")).strip()
                if self._looks_like_path(mapping_ref):
                    self.add_error(pid, "MAPPINGREF_WITHOUT_VERIFY", "error",
                                   f"{path}.codingGuide.pageItems[{i}].mappingRef",
                                   f"代码状态为 {code_avail} 时 mappingRef 不得是真实文件路径",
                                   "映射编号（如 M01）", mapping_ref,
                                   fix="改用映射编号，真实路径留待 Coding 阶段核验")
            if str(page.get("visualBaselineRef", "")).strip():
                self.add_error(pid, "VISUAL_BASELINE_WITHOUT_VERIFY", "error",
                               f"{path}.visualBaselineRef",
                               f"代码状态为 {code_avail} 时不得引用真实可视化基线页面",
                               "空 visualBaselineRef（待核验）", page.get("visualBaselineRef"),
                               fix="清空 visualBaselineRef，待页面代码核验可用后再引用")
            rr = page.get("restoreRequirement") or {}
            for k, comp in enumerate(rr.get("components") or []):
                if not isinstance(comp, dict):
                    continue
                if str(comp.get("path", "")).strip():
                    self.add_error(pid, "COMPONENT_PATH_WITHOUT_VERIFY", "error",
                                   f"{path}.restoreRequirement.components[{k}].path",
                                   f"代码状态为 {code_avail} 时不得声明真实组件路径",
                                   "空 path（待核验）", comp.get("path"),
                                   fix="清空组件 path，改用语义级能力描述")
                self._flag_unverified_components(
                    pid, f"{path}.restoreRequirement.components[{k}].name",
                    comp.get("name", ""), code_avail, seen, pd_registered)
            for s_idx, section in enumerate(self.page_sections(page)):
                if not isinstance(section, dict):
                    continue
                for key in ("component", "filterComponent", "topComponent"):
                    self._flag_unverified_components(
                        pid, f"{path}.sections[{s_idx}].{key}", section.get(key, ""), code_avail, seen, pd_registered)
                for f_key in ("fields", "formFields", "filterFields", "tableFields", "detailFields", "columns"):
                    for f_idx, field in enumerate(section.get(f_key) or []):
                        if not isinstance(field, dict):
                            continue
                        for comp_key in ("iduxComponent", "component"):
                            self._flag_unverified_components(
                                pid, f"{path}.sections[{s_idx}].{f_key}[{f_idx}].{comp_key}",
                                field.get(comp_key, ""), code_avail, seen, pd_registered)

    def check_design_basis_consistency(self):
        """RULE-43：设计依据一致性（条件式，顶层声明 designContext 时启用）。

        1) common/product-design 依据必须命中 readLedger 且 status=read（引用未读文档阻断）；
        2) Product Design 声明模板覆盖时，被覆盖页面必须真正采用 product 模板（禁止落到 Common Design）；
        3) 采用 product 模板必须反向登记 product-design 依据并声明 productDesign.matched。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return  # 未声明 designContext：历史格式不启用（不误伤）
        ledger = self._build_ledger(dc.get("readLedger"))

        def _ledger_status(doc, anchor):
            for key in ((doc, anchor), (doc, "*")):
                if key in ledger:
                    return ledger[key]
            if not anchor and (doc, "") in ledger:
                return ledger[(doc, "")]
            return None
        pd = dc.get("productDesign") or {}
        pd_matched = bool(pd.get("matched"))
        if pd_matched and not str(pd.get("skillId", "")).strip():
            self.add_error("-", "DESIGN_CONTEXT_INCOMPLETE", "warning",
                           "$.designContext.productDesign.skillId",
                           "productDesign.matched=true 但未声明 skillId",
                           "非空 skillId", "缺失",
                           fix="补充 Product Design 的 skillId")
        # 1) 未读引用
        for page, path in self.all_pages:
            pid = page.get("id", "")
            refs = (page.get("codingGuide") or {}).get("designReferences")
            if not isinstance(refs, list):
                continue
            for i, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    continue
                src = str(ref.get("source", "")).strip()
                if src not in ("common-design", "product-design"):
                    continue
                rf = str(ref.get("ref", "")).strip()
                if "#" not in rf:
                    self.add_error(pid, "DESIGN_REF_UNANCHORED", "warning",
                                   f"{path}.codingGuide.designReferences[{i}].ref",
                                   f"{src} 依据必须是精确锚点（文档#条目），禁止仅凭索引/摘要下结论",
                                   "文档路径#章节/模板条目", rf or "空",
                                   fix="补充精确锚点，禁止仅凭索引/摘要下结论")
                doc, anchor = self._norm_ref(rf)
                status = _ledger_status(doc, anchor)
                ref_label = f"{doc}#{anchor or '*'}"
                if status is None:
                    self.add_error(pid, "DESIGN_REF_UNREAD", "error",
                                   f"{path}.codingGuide.designReferences[{i}].ref",
                                   f"引用的设计依据 {ref_label} 未在 readLedger 中登记为已精读"
                                   "（锚点级命中：文档与章节锚点均须一致，或该文档以 #* 声明整篇已读）",
                                   "readLedger 中 status=read 且锚点匹配的条目", rf or "空",
                                   fix="仅引用已实际精读的章节；整篇已读请在 readLedger 用 <文档路径>#* 声明，"
                                       "否则须将该章节精确登记为 read")
                elif status != "read":
                    self.add_error(pid, "DESIGN_REF_UNREAD", "error",
                                   f"{path}.codingGuide.designReferences[{i}].ref",
                                   f"引用的设计依据 {ref_label} 在 readLedger 中状态为 {status}，索引/摘要不得作为设计依据",
                                   "status=read", status or "空",
                                   fix="补读该文档该章节原文后将 readLedger 状态更新为 read")
        # 2) 模板覆盖落地（防止“应为 Product Design 效果却落到 Common Design”）
        if pd_matched:
            overrides = [c for c in (pd.get("coverage") or [])
                         if isinstance(c, dict)
                         and str(c.get("capability", "")).strip().lower() in ("template", "page-template", "模板", "页面模板")
                         and str(c.get("relation", "")).strip().lower() == "override"]
            if overrides:
                applies = set()
                for c in overrides:
                    for t in c.get("appliesTo") or []:
                        applies.add(str(t).strip())
                for page, path in self.all_pages:
                    pid = page.get("id", "")
                    tid = self.page_template(page)
                    if applies and tid not in applies:
                        continue
                    tc = page.get("templateContract") or {}
                    base = str(tc.get("templateBase", "")).strip().lower()
                    pref = str(tc.get("productTemplateRef", "")).strip()
                    if base != "product" or not pref:
                        self.add_error(pid, "TEMPLATE_OVERRIDE_NOT_APPLIED", "error",
                                       f"{path}.templateContract.templateBase",
                                       "Product Design 声明模板覆盖，但页面未采用 Product Design 模板（落到 Common Design）",
                                       "templateBase=product 且 productTemplateRef 非空",
                                       f"templateBase={base or '空'}",
                                       fix="按 Product Design 覆盖定义采用 product 模板并登记 productTemplateRef")
        # 2b) 能力覆盖落地：coverage 声明 extend/override 的（非模板）能力，适用页面必须登记同 ability 的 product-design 依据
        if pd_matched:
            for cov in (pd.get("coverage") or []):
                if not isinstance(cov, dict):
                    continue
                cap = str(cov.get("capability", "")).strip()
                capk = cap.lower()
                relation = str(cov.get("relation", "")).strip().lower()
                if not capk or capk in ("template", "page-template", "模板", "页面模板"):
                    continue
                if relation not in ("override", "extend"):
                    continue
                applies = {str(t).strip() for t in (cov.get("appliesTo") or [])}
                for page, path in self.all_pages:
                    pid = page.get("id", "")
                    tid = self.page_template(page)
                    if applies and pid not in applies and tid not in applies:
                        continue
                    refs = (page.get("codingGuide") or {}).get("designReferences") or []
                    registered = any(isinstance(r, dict)
                                     and str(r.get("source", "")).strip() == "product-design"
                                     and str(r.get("ability", "")).strip().lower() == capk
                                     for r in refs)
                    if not registered:
                        self.add_error(pid, "ABILITY_SOURCE_NOT_REGISTERED", "error",
                                       f"{path}.codingGuide.designReferences",
                                       f"Product Design 声明能力 {cap} 的 {relation} 覆盖，但页面未登记该能力的 product-design 依据",
                                       f"designReferences 中含 source=product-design 且 ability={cap} 的条目", "缺失",
                                       fix=f"在 codingGuide.designReferences 登记 ability={cap} 的 Product Design 依据")
        # 3) 反向一致：采用 product 模板必须登记 product-design 依据
        for page, path in self.all_pages:
            pid = page.get("id", "")
            tc = page.get("templateContract") or {}
            base = str(tc.get("templateBase", "")).strip().lower()
            if base != "product":
                continue
            pref = str(tc.get("productTemplateRef", "")).strip()
            if not pref:
                self.add_error(pid, "TEMPLATE_SOURCE_UNREGISTERED", "error",
                               f"{path}.templateContract.productTemplateRef",
                               "采用 product 模板但未声明 productTemplateRef",
                               "非空 productTemplateRef", "空",
                               fix="补充 Product Design 模板锚点")
            if not pd_matched:
                self.add_error(pid, "TEMPLATE_SOURCE_UNREGISTERED", "error",
                               f"{path}.templateContract.templateBase",
                               "采用 product 模板但 designContext 未声明 productDesign.matched=true",
                               "productDesign.matched=true", "false/缺失",
                               fix="在 designContext.productDesign 中声明 matched 与 skillId")
            refs = (page.get("codingGuide") or {}).get("designReferences") or []
            has_pd = any(isinstance(r, dict) and str(r.get("source", "")).strip() == "product-design" for r in refs)
            if not has_pd:
                self.add_error(pid, "TEMPLATE_SOURCE_UNREGISTERED", "error",
                               f"{path}.codingGuide.designReferences",
                               "采用 product 模板但未登记 product-design 设计依据",
                               "source=product-design 的 designReferences 条目", "缺失",
                               fix="在 codingGuide.designReferences 中登记 Product Design 依据")

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

    # ---- 需求理解与页面设计追溯（RULE-42）----
    def check_requirement_trace(self):
        """RULE-42 需求理解与页面设计追溯（条件式启用）。

        顶层声明 requirementUnderstanding（需求理解模型）或任一页面带 taskRefs 时启用：
        - 模型 status != resolved 阻断 HTML 生成（未解决的业务事实不得作为确定设计写入 HTML）；
        - 页面带 taskRefs 但顶层无模型 -> 模型缺失阻断；
        - 每个页面必须关联至少一个业务任务（taskRefs 非空）；
        - 每个已建模业务任务必须有页面承载（taskRefs 引用）；
        - 核心动作必须有结果反馈（action 存在时 outcome 不得为空）；
        - 判断区块（带 informationPurpose/decisionPoint）内字段须说明用途（fieldRole）；
        - source/fieldRole 显式声明时值必须合法（requirement/product-design/common-design/code/ai-fill；
          identify/judge/precondition/result）。
        历史格式（无模型且无 taskRefs）不触发本规则，避免误伤存量数据。
        """
        model = self.data.get("requirementUnderstanding") if isinstance(self.data, dict) else None
        pages = list(self.all_pages)
        has_task_refs = any(isinstance(p.get("taskRefs"), list) and p.get("taskRefs") for p, _ in pages)
        if not isinstance(model, dict) and not has_task_refs:
            return
        if not isinstance(model, dict):
            for page, path in pages:
                if isinstance(page.get("taskRefs"), list) and page.get("taskRefs"):
                    self.add_error(page.get("id", ""), "REQ_TRACE_MODEL_MISSING", "error",
                                   f"{path}.taskRefs",
                                   "页面 taskRefs 引用了业务任务，但顶层缺少 requirementUnderstanding 需求理解模型",
                                   "顶层存在 requirementUnderstanding", "缺失",
                                   fix="先按 SKILL.md Step 1.5 完成需求理解与业务任务建模并输出 requirementUnderstanding")
            return
        status = model.get("status")
        if status != "resolved":
            self.add_error("", "REQ_TRACE_STATUS_NOT_RESOLVED", "error",
                           "$.requirementUnderstanding.status",
                           f"需求理解未解决（status={status or '缺失'}）：未解决的业务事实不得写入 HTML 作为确定设计",
                           "resolved", str(status or "缺失"),
                           fix="先确认阻塞性业务理解问题（页面拆解前提出）并更新 requirementUnderstanding.status=resolved")
        tasks = model.get("tasks")
        task_ids = []
        if isinstance(tasks, list):
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    continue
                tpath = f"$.requirementUnderstanding.tasks[{i}]"
                tid = str(task.get("id", "")).strip()
                task_ids.append(tid)
                if not _has_text_value(task.get("action")):
                    self.add_error("", "REQ_TRACE_TASK_INCOMPLETE", "error", f"{tpath}.action",
                                   f"业务任务 {tid or i} 缺少核心动作定义",
                                   "action 非空（处置/审核/分配/配置等）", "缺失/空",
                                   fix="补充任务执行动作与入口承载页面")
                elif not _has_text_value(task.get("outcome")):
                    self.add_error("", "REQ_TRACE_ACTION_NO_OUTCOME", "error", f"{tpath}.outcome",
                                   f"业务任务 {tid or i} 定义了核心动作却没有结果反馈（outcome）",
                                   "outcome 非空（成功/失败/部分成功及状态变化）", "缺失/空",
                                   fix="补充任务结果与状态反馈定义")
        bound = set()
        for page, path in pages:
            pid = page.get("id", "")
            refs = page.get("taskRefs")
            if not isinstance(refs, list) or not refs:
                self.add_error(pid, "REQ_TRACE_NO_TASK_REF", "error", f"{path}.taskRefs",
                               "页面没有关联任何业务任务（taskRefs 缺失或为空）",
                               "taskRefs 非空并引用已建模任务 id", "缺失/空",
                               fix="将该页面承载的业务任务 id 写入 taskRefs（见 01-output-templates.md 页面对象）")
            else:
                for r in refs:
                    if isinstance(r, str) and r.strip():
                        bound.add(r.strip())
        for tid in task_ids:
            if tid and tid not in bound:
                self.add_error("", "REQ_TRACE_TASK_UNBOUND", "error",
                               "$.requirementUnderstanding.tasks",
                               f"业务任务 {tid} 没有任何页面承载（taskRefs 未引用）",
                               "至少一个页面 taskRefs 引用该任务", "无页面承载",
                               fix="补充承载该任务的页面并在其 taskRefs 中登记，或确认该任务不在本次交付范围后从 tasks 移除")
        # 区块级追溯：判断区块（声明信息目的/决策点）字段用途 + 来源标记合法值
        for page, path in pages:
            pid = page.get("id", "")
            sections = page.get("sections")
            if not isinstance(sections, list):
                continue
            for si, section in enumerate(sections):
                if not isinstance(section, dict):
                    continue
                spath = f"{path}.sections[{si}]"
                self._audit_source_value(pid, f"{spath}.source", section.get("source"))
                is_judge_block = (_has_text_value(section.get("informationPurpose"))
                                  or _has_text_value(section.get("decisionPoint")))
                if not is_judge_block:
                    continue
                for key in ("fields", "formFields", "filterFields", "tableFields", "columns"):
                    fields = section.get(key)
                    if not isinstance(fields, list):
                        continue
                    for fi, field in enumerate(fields):
                        if not isinstance(field, dict):
                            continue
                        fpath = f"{spath}.{key}[{fi}]"
                        self._audit_source_value(pid, f"{fpath}.source", field.get("source"))
                        role = field.get("fieldRole")
                        if not _has_text_value(role):
                            self.add_error(pid, "REQ_TRACE_FIELD_NO_PURPOSE", "warning", f"{fpath}.fieldRole",
                                           "区块声明了信息目的/判断点，但字段未说明用途（识别/判断/操作前置/结果反馈）",
                                           "fieldRole 已标注", "缺失",
                                           fix="补充 fieldRole: identify（识别信息）/ judge（判断信息）/ precondition（操作前置）/ result（结果反馈）")
                        elif str(role).strip() not in FIELD_ROLE_LABELS:
                            self._audit_bad_role(pid, f"{fpath}.fieldRole", role)

    def _audit_source_value(self, pid, path, value):
        """来源标记合法性（RULE-42 warning 级）。"""
        if value is None:
            return
        s = str(value).strip()
        if s and s not in SOURCE_LABELS:
            self.add_error(pid, "REQ_TRACE_SOURCE_INVALID", "warning", path,
                           f"来源标记非法: {s}（合法值: requirement / product-design / common-design / code / ai-fill）",
                           "合法来源标记", s,
                           fix="使用 requirement / product-design / common-design / code / ai-fill 之一；AI 推导内容必须标 ai-fill")

    def _audit_bad_role(self, pid, path, role):
        """fieldRole 取值合法性（RULE-42 warning 级）。"""
        self.add_error(pid, "REQ_TRACE_FIELD_ROLE_INVALID", "warning", path,
                       f"fieldRole 值非法: {role}（合法值: identify / judge / precondition / result）",
                       "identify / judge / precondition / result", str(role),
                       fix="将 fieldRole 修正为 identify / judge / precondition / result 之一")

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
        # ---- 线框图绘制质量与双向一致性（RULE-32 / RULE-33 / RULE-34）----
        self.check_wireframe_drawing_quality()
        self.check_wireframe_region_drawn()
        self.check_wireframe_label_list()
        self.check_wireframe_region_ascii_order()
        self.check_wireframe_duplicate_control()
        # ---- 线框图列对齐一致性（RULE-47）：右边界错位/两列结构断裂提示 ----
        self.check_wireframe_column_alignment()
        # ---- 页面平铺闭环（RULE-35）：children 禁止内嵌完整页面设计对象 ----
        self.check_child_page_flattened()
        # ---- 字段完整性闭环（RULE-36）：需求明确字段必须落位或排除 ----
        self.check_requirement_fields()
        # ---- 字段形态键契约（RULE-41）：内容必须写在渲染器实际渲染的键上，跨形态套键阻断 ----
        self.check_field_key_contract()
        # ---- 表格与详情字段一致性闭环（RULE-38）：表格展示字段必须在对应详情容器中存在 ----
        self.check_table_detail_field_consistency()
        # ---- 表格标签使用约束（RULE-39）：同一表格内标签总数与样式配额（Common Design 标签样式约束兜底）----
        self.check_table_tag_usage()
        # ---- 设计依据可追溯（RULE-40）：声称引用 Design Skill 的决策须登记来源，无来源须标 ai-fill ----
        self.check_design_references()
        # ---- 需求理解与页面设计追溯（RULE-42）：任务绑定/结果反馈/判断区块字段用途/来源合法性 ----
        self.check_requirement_trace()
        # ---- 设计依据一致性（RULE-43）：读未读/模板覆盖落地/反向登记（条件式，声明 designContext 时启用）----
        self.check_design_basis_consistency()
        # ---- 未核验实现细节隔离（RULE-44）：partial/unavailable 时禁止未核验真实代码对象作设计结论 ----
        self.check_unverified_implementation()
        self.check_footer_ascii_order()

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import unicodedata
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
    {"ruleId": "RULE-28", "errorCode": "MANIFEST_* / ORPHAN_CONTAINER", "name": "页面清单闭环：总览确认页面/容器与 pages（含 children）完整一致", "check": "check_manifest_closure", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_manifest_page_missing_fails, test_orphan_container_fails"},
    {"ruleId": "RULE-29", "errorCode": "OPERATION_*", "name": "操作目标闭环：open-container 目标存在、容器类型正确、高影响操作二次确认", "check": "check_operation_closure", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_operation_target_missing_fails, test_operation_confirm_missing_fails"},
    {"ruleId": "RULE-30", "errorCode": "TABS_*", "name": "Tab 变体闭环：多内容 Tab 页面强制完整变体、公共外壳与内容区、sections 绑定 tabId", "check": "check_tab_variants", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_tabs_missing_variants_fails, test_tabs_variant_count_mismatch_fails, test_tabs_orphan_variant_fails, test_tabs_variant_no_shell_fails, test_tabs_variant_no_content_fails"},
    {"ruleId": "RULE-31", "errorCode": "CODING_CLOSURE_*", "name": "页面级 Coding 闭环：pageContext 一致、每页至少一个开发项、无孤立开发项", "check": "check_coding_closure", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_coding_page_context_mismatch_fails, test_coding_no_items_fails"},
    {"ruleId": "RULE-32", "errorCode": "WIREFRAME_ASCII_TOO_SHORT / WIREFRAME_ASCII_NOT_DRAWN", "name": "线框图绘制质量：ascii 必须按模板绘制，禁止只有几个字或一句话", "check": "check_wireframe_drawing_quality", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_wireframe_ascii_too_short_fails, test_wireframe_ascii_not_drawn_fails"},
    {"ruleId": "RULE-33", "errorCode": "WIREFRAME_REGION_NOT_DRAWN", "name": "线框图双向一致性：regions 声明的内容性区块必须在 ascii 中有绘制痕迹", "check": "check_wireframe_region_drawn", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_wireframe_ascii_region_not_drawn_warns"},
    {"ruleId": "RULE-34", "errorCode": "WIREFRAME_ASCII_LABEL_LIST", "name": "线框图布局完整性：ascii 禁止区域标签罗列，必须绘制为完整页面布局字符画", "check": "check_wireframe_label_list", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_wireframe_label_list_fails, test_wireframe_full_layout_passes"},
    {"ruleId": "RULE-35", "errorCode": "CHILD_PAGE_NOT_FLATTENED", "name": "页面平铺闭环：children 只允许子容器 ID 引用，禁止内嵌完整页面设计对象；子容器必须作为 pages 数组独立元素", "check": "check_child_page_flattened", "source": "references/01-workflow/04-demo-output-spec.md 设计闭环", "tests": "test_child_page_not_flattened_fails, test_child_string_ref_passes"},
    {"ruleId": "RULE-36", "errorCode": "REQUIRED_FIELD_MISSING", "name": "字段完整性闭环：需求/规范明确要求的字段（表格列、表单项、筛选项、详情描述字段等）必须落入对应字段数组或 excludedFields 排除声明", "check": "check_requirement_fields", "source": "references/01-workflow/01-output-templates.md 字段完整性", "tests": "test_requirement_field_missing_fails, test_requirement_field_all_covered_passes, test_requirement_field_excluded_passes"},
    {"ruleId": "RULE-37", "errorCode": "FOOTER_ASCII_BUTTON_MISSING / FOOTER_ASCII_ORDER_MISMATCH / FOOTER_ASCII_CUSTOM_BUTTON", "name": "线框图底部按钮：必须按模板 buttonOrder 绘制（缺主操作/顺序错=error，缺次要按钮=warning）；按钮文案须落在模板允许集合，底部操作区出现模板外自定义按钮需 override 声明（业务自定义以业务为准）", "check": "check_footer_ascii_order", "source": "references/01-workflow/04-demo-output-spec.md 11.6 底部操作区 / Common Design 模板 footer.buttonOrder", "tests": "test_footer_ascii_button_missing_fails, test_footer_ascii_order_mismatch_fails, test_footer_ascii_order_passes, test_footer_ascii_custom_button_without_override_fails, test_footer_ascii_custom_button_with_override_passes"},
    {"ruleId": "RULE-38", "errorCode": "TABLE_DETAIL_FIELD_MISMATCH", "name": "表格与详情字段一致性：表格页展示的每个字段必须在对应详情容器中存在（Common Design 表格与详情字段一致规则兜底）", "check": "check_table_detail_field_consistency", "source": "Common Design 表格与详情字段一致规则 / references/01-workflow/06-quality-and-rules.md", "tests": "test_table_detail_field_mismatch_fails, test_table_detail_field_consistent_passes, test_table_detail_without_detail_skips, test_table_detail_via_children_fails"},
    {"ruleId": "RULE-39", "errorCode": "TABLE_TAG_*", "name": "表格标签使用约束：同一表格内标签总数 <= 5，深色/icon/点状标签各仅允许 1 次、浅色标签最多 2 次，样式未标注或中性描述字段占用标签配额时 warning 提示（Common Design 标签（IxTag）样式使用约束兜底）", "check": "check_table_tag_usage", "source": "Common Design 标签（IxTag）样式使用约束", "tests": "test_table_tag_count_exceeded_fails, test_table_tag_style_overused_fails, test_table_tag_style_unspecified_warns, test_table_tag_neutral_field_warns, test_table_tag_usage_passes"},
    {"ruleId": "RULE-40", "errorCode": "DESIGN_REF_*", "name": "设计依据可追溯：声称引用 Design Skill 的决策必须在页面 codingGuide.designReferences 登记来源（source 为 common-design/product-design/code/ai-fill，ref 非空）；声称有依据却无登记为 error（阻断），来源/字段格式类为 warning", "check": "check_design_references", "source": "references/01-workflow/00-design-skill-resolver.md 能力识别参考框架 / SKILL.md 输出可追溯", "tests": "test_design_ref_missing_fails, test_design_ref_invalid_source_warns, test_design_ref_empty_ref_warns, test_design_ref_passes, test_design_ref_absent_no_claim_passes"},
    {"ruleId": "RULE-41", "errorCode": "FORM_FIELD_KEY_MISMATCH / FILTER_FIELD_KEY_MISMATCH / TABLE_FIELD_KEY_MISMATCH / FORM_FIELD_KEY_PLACED_WRONG / FILTER_FIELD_KEY_PLACED_WRONG / TABLE_FIELD_KEY_PLACED_WRONG", "name": "字段形态键契约：字段内容必须写在渲染器实际渲染的键上（表单字段 formFields 用 rules/tips；筛选字段 filterFields 用 options/description；表格字段 tableFields/columns 用 display/description）；内容写在异态键导致 HTML 对应列静默空白时阻断（error），内容已渲染但键写错位置时 warning（RULE-41）", "check": "check_field_key_contract", "source": "references/01-workflow/04-demo-output-spec.md 字段形态键对照（RULE-41）/ 01-output-templates.md AI Coding指导输出格式", "tests": "test_form_field_options_not_rendered_fails, test_form_field_key_placed_wrong_warns, test_form_legacy_fields_options_not_rendered_fails, test_filter_field_rules_not_rendered_fails, test_table_field_rules_not_rendered_fails, test_field_key_contract_passes"},
    {"ruleId": "RULE-42", "errorCode": "REQ_TRACE_STATUS_NOT_RESOLVED / REQ_TRACE_MODEL_MISSING / REQ_TRACE_NO_TASK_REF / REQ_TRACE_TASK_UNBOUND / REQ_TRACE_TASK_INCOMPLETE / REQ_TRACE_ACTION_NO_OUTCOME / REQ_TRACE_FIELD_NO_PURPOSE / REQ_TRACE_SOURCE_INVALID / REQ_TRACE_FIELD_ROLE_INVALID", "name": "需求理解与页面设计追溯（条件式）：顶层声明 requirementUnderstanding 或页面带 taskRefs 时启用——需求理解未解决（status!=resolved）阻断 HTML 生成；每个页面必须关联至少一个业务任务；每个已建模业务任务必须有页面承载；核心动作必须有结果反馈；判断区块内字段须说明用途（fieldRole）；source/fieldRole 显式声明时值必须合法（RULE-42）", "check": "check_requirement_trace", "source": "references/01-workflow/04-demo-output-spec.md 11.9 需求理解与页面设计追溯（RULE-42）/ 01-output-templates.md 任务锚定字段", "tests": "test_requirement_status_not_resolved_fails, test_model_missing_but_task_ref_fails, test_page_without_task_ref_fails, test_task_not_bound_to_page_fails, test_task_without_outcome_fails, test_judge_block_field_no_purpose_warns, test_invalid_source_marker_warns, test_requirement_trace_passes, test_requirement_trace_skipped_without_model"},
    {"ruleId": "RULE-43", "errorCode": "DESIGN_REF_UNREAD / DESIGN_REF_UNANCHORED / TEMPLATE_OVERRIDE_NOT_APPLIED / TEMPLATE_SOURCE_UNREGISTERED / ABILITY_SOURCE_NOT_REGISTERED / DESIGN_CONTEXT_INCOMPLETE", "name": "设计依据一致性（条件式，顶层声明 designContext 时启用）：common/product-design 依据必须锚点级命中 readLedger 且 status=read（引用未读章节阻断，整篇已读用 #* 声明）；Product Design 声明模板覆盖时被覆盖页面必须真正采用 product 模板（禁止落到 Common Design）；coverage 声明 extend/override 的任意能力，适用页面必须登记同 ability 的 product-design 依据；采用 product 模板必须反向登记 product-design 依据并声明 productDesign.matched", "check": "check_design_basis_consistency", "source": "references/01-workflow/00-design-skill-resolver.md 设计依据登记与读取 / references/01-workflow/04-demo-output-spec.md designContext（RULE-43）", "tests": "test_design_context_unread_ref_fails, test_design_context_anchor_unread_fails, test_design_context_whole_doc_read_passes, test_design_context_template_override_not_applied_fails, test_design_context_template_source_unregistered_fails, test_ability_source_not_registered_fails, test_ability_source_registered_passes, test_design_context_consistent_passes, test_design_context_absent_skips"},
    {"ruleId": "RULE-44", "errorCode": "EXPORT_WITHOUT_VERIFY / COMPONENT_WITHOUT_VERIFY / VISUAL_BASELINE_WITHOUT_VERIFY / MAPPINGREF_WITHOUT_VERIFY / COMPONENT_PATH_WITHOUT_VERIFY", "name": "未核验实现细节隔离：partial/unavailable 时禁止把未核验的真实代码对象（target.export、产品专有组件名、真实组件路径、可视化基线页面、路径式 mappingRef）当作设计结论写进字段/编码指导，只能做语义级描述，真实导出名/Props/Events 留待 Coding Gate 核验", "check": "check_unverified_implementation", "source": "references/01-workflow/05-interaction-coding-guidelines.md 代码可用状态与设计依据分离 / references/01-workflow/04-demo-output-spec.md 未核验对象约束（RULE-44）", "tests": "test_unverified_export_fails, test_unverified_component_name_fails, test_unverified_ix_component_passes, test_unverified_visual_baseline_fails"},
    {"ruleId": "RULE-45", "errorCode": "WIREFRAME_REGION_ORDER_MISMATCH", "name": "线框图区域顺序一致性（warning）：regions 声明顺序应与 ascii 自上而下的绘制顺序一致，出现逆序（后面的区域绘制在更靠上的位置）时提示", "check": "check_wireframe_region_ascii_order", "source": "references/01-workflow/04-demo-output-spec.md 线框图绘制规范 / references/01-workflow/03-demo-page-decomposition.md 区域结构", "tests": "test_wireframe_region_order_mismatch_warns"},
    {"ruleId": "RULE-46", "errorCode": "WIREFRAME_DUPLICATE_CONTROL / WIREFRAME_DUPLICATE_REGION / WIREFRAME_PROSEARCH_FILTER_DUPLICATE", "name": "线框图重复绘制检测（warning）：带标记的控件标签（【】/[]）重复出现时提示；同一内容区域（步骤条/Tab/工具栏/筛选区/分页）在 ascii 中被绘制多次时提示；页面筛选声明为高级搜索（IxProSearch/高级搜索）时线框图不得再单独绘制筛选区/查询区/过滤区行（筛选与搜索已收敛进高级搜索组件，重复绘制会导致 Coding 阶段重复实现）", "check": "check_wireframe_duplicate_control", "source": "references/01-workflow/04-demo-output-spec.md 线框图绘制规范 / 11.12 线框与区域结构双向一致性", "tests": "test_wireframe_duplicate_singular_control_warns, test_wireframe_duplicate_region_warns, test_prosearch_filter_duplicate_warns, test_prosearch_filter_converged_passes, test_prosearch_absent_skips"},
    {"ruleId": "RULE-47", "errorCode": "WIREFRAME_COLUMN_ALIGNMENT", "name": "线框图列对齐一致性（warning）：内容行右边界（右竖线）应在同一列，出现明显错位（两列结构断裂）时提示", "check": "check_wireframe_column_alignment", "source": "references/01-workflow/04-demo-output-spec.md 线框图绘制规范", "tests": "test_wireframe_column_alignment_warns, test_wireframe_full_layout_passes"},
    {"ruleId": "RULE-48", "errorCode": "REQUIRED_OPTION_MISSING / OPTION_FIELD_NOT_FOUND / OPTION_TRUNCATION_MARKER / OPTION_SET_INVALID / OPTION_SET_INCOMPLETE / OPTION_DIMENSION_LOST", "name": "下拉选项完整性与维度保留（条件式，页面声明 requirementOptionSets 时启用）：固定选项型下拉的完整选项必须逐项落入表单选项/规则(rules)或筛选选项范围(options)单元格，声明选项缺失阻断，声明字段不存在阻断；未声明选项集的选择类字段出现 等/例如/如：/… 截断指纹时告警；需求源枚举表含分组/层级列时（声明 dimension=group/hierarchy，或 sourceColumns 声明 >=2 列自动视为 group），选项单元格被压成单层列表、未保留该维度时告警（OPTION_DIMENSION_LOST），维度是否保留属本规则职责、承载该维度的控件形态由 RULE-54 依 widget patterns 判定", "check": "check_option_completeness", "source": "references/01-workflow/04-demo-output-spec.md 11.13 下拉选项完整性与维度保留（RULE-48）", "tests": "test_requirement_option_missing_fails, test_requirement_option_all_present_passes, test_option_set_field_not_found_fails, test_option_truncation_marker_warns, test_option_completeness_skips_without_declaration, test_option_dimension_lost_warns, test_option_dimension_kept_passes, test_option_dimension_inferred_from_columns_warns, test_option_dimension_flat_skips"},
    {"ruleId": "RULE-49", "errorCode": "DETAIL_FIELD_DUPLICATE / DETAIL_FIELD_DUPLICATED_IN_LIST", "name": "详情页字段去重（条件式，仅详情类页面）：概览卡片/对象摘要已展示字段在详情描述列表重复时告警（声明 detailSummaryFields 优先，未声明走 cardFields/摘要区块启发式；excludedFields/detailDedupExempt 豁免，历史/日志/记录类区块与表格字段不参与）；同一详情描述列表内字段重复阻断", "check": "check_detail_field_dedup", "source": "Common Design 详情概览卡片与描述列表字段去重规则 / references/01-workflow/04-demo-output-spec.md 11.14 详情页字段去重（RULE-49）", "tests": "test_detail_field_duplicate_warns, test_detail_summary_fields_declared_warns, test_detail_field_dedup_exempt_passes, test_detail_field_duplicated_in_list_fails, test_detail_field_dedup_skips_non_detail_page, test_detail_summary_card_section_duplicate_warns"},
    {"ruleId": "RULE-50", "errorCode": "ACTION_CONFIRM_TEXT_MISSING / ACTION_COMPONENT_MISSING / ACTION_CONTENT_MISSING / ACTION_SOURCE_NOT_TRACED / ACTION_NAME_MISSING", "name": "按钮/可点击操作表（条件式）：高影响操作/二次确认/局部面板须写清触发方式、组件与文案或字段；高影响缺文案阻断，缺组件/内容/来源告警；组件与文案须可溯源设计来源（Product Design 优先于 Common Design，禁止 AI 自拟），高影响操作与豁免支持 actionRules 配置，旧字符串写法兼容", "check": "check_action_table", "source": "references/01-workflow/04-demo-output-spec.md 11.15 按钮/可点击操作表（RULE-50）", "tests": "test_action_high_impact_missing_text_fails, test_action_high_impact_complete_passes, test_action_source_ai_fill_warns, test_action_component_missing_warns, test_action_legacy_string_skipped, test_action_rules_configurable"},
    {"ruleId": "RULE-51", "errorCode": "TABLE_BUTTON_MISPLACED / TABLE_ACTION_NOT_IN_TOOLBAR / WIREFRAME_COLUMN_SETTING_DRAWN", "name": "表格区按钮位置与组件自带功能（线框图，warning）：表格关联按钮（批量操作、子功能入口等）必须统一置于表格区左上角工具栏，出现在表格框下方或工具栏之外的区域时提示；列设置为表格组件自带功能，线框图不得绘制为独立按钮", "check": "check_table_button_placement", "source": "references/01-workflow/04-demo-output-spec.md 11.16 表格区按钮位置（RULE-51）", "tests": "test_table_button_below_table_warns, test_table_button_in_toolbar_passes, test_table_pagination_not_flagged, test_table_batch_action_outside_warns, test_table_button_check_skips_without_table, test_column_setting_drawn_warns, test_column_setting_absent_passes, test_column_setting_below_table_no_misplaced"},
    {"ruleId": "RULE-52", "errorCode": "ENTRY_POINT_INCOMPLETE / ENTRY_POINT_NOT_PLACED / ENTRY_HOST_UNREGISTERED / ENTRY_NOT_DRAWN", "name": "需求入口落位闭环（条件式，顶层声明 requirementEntryPoints 时启用）：PRD 点名的每个入口挂载点必须有落点——in-scope 宿主须在宿主页面 sections/actions 或 operations 中承载触发元素与打开容器并在宿主线框图中绘制入口（缺失阻断/告警）；out-of-scope 宿主须在 entryHosts 登记（含 Tier1 精读与对应开发项，缺失阻断），并写清宿主落位说明（entryHosts[].wireframe 一行文字：宿主内位置 + 触发元素 + 打开容器 + 编码要求；缺失或未含位置/触发元素告警——宿主仅加入口时不再要求绘制宿主完整线框图，落位信息写入 HTML 入口清单防止编码遗漏）；入口声明缺字段或 hostScope 非法阻断", "check": "check_requirement_entry_points", "source": "references/01-workflow/04-demo-output-spec.md 11.17 需求入口落位闭环（RULE-52）", "tests": "test_entry_point_in_scope_placed_passes, test_entry_point_not_placed_fails, test_entry_point_out_of_scope_unregistered_fails, test_entry_point_out_of_scope_registered_passes, test_entry_point_out_of_scope_missing_dev_item_fails, test_entry_point_out_of_scope_dangling_dev_item_fails, test_entry_point_not_drawn_warns, test_entry_point_incomplete_fails, test_entry_point_skips_without_declaration, test_entry_host_wireframe_placeholder_passes, test_entry_host_wireframe_vague_warns"},
    {"ruleId": "RULE-53", "errorCode": "HOST_IDENTITY_UNVERIFIED / HOST_IDENTITY_FILENAME_ONLY / HOST_IDENTITY_AMBIGUOUS / HOST_NAVPATH_MISMATCH", "name": "页面定位证据闭环（条件式，声明 requirementEntryPoints 或 pageIdentityRefs 时启用）：被定位的既有页面必须携带可核验身份证据（逐级导航路径 + 路由/菜单标识 + 标题 + 命中代码实体 + 命中依据），硬性禁止以文件名/目录名作为定位依据（matchedBy 含 filename/dir 即阻断）；out-of-scope 入口宿主缺失或薄弱证据阻断，in-scope 宿主仅在显式提供证据时校验；存在形近候选未记录排除告警；代码导航路径末级与 PRD 声明不符阻断（防张冠李戴，如 alert-list/告警链 误判为 alarm-list/告警列表）", "check": "check_page_identity", "source": "references/01-workflow/04-demo-output-spec.md 11.18 页面定位证据闭环（RULE-53）/ 01-output-templates.md 4.3", "tests": "test_page_identity_ref_valid_passes, test_page_identity_missing_evidence_fails, test_host_identity_filename_only_fails, test_host_identity_navpath_mismatch_fails, test_host_identity_ambiguous_warns, test_host_identity_degraded_mode_passes, test_entry_point_out_of_scope_missing_evidence_fails"},
    {"ruleId": "RULE-54", "errorCode": "COMPONENT_FORM_MISSING / COMPONENT_FORM_UNKNOWN / FORM_DECISION_MISSING / FORM_DECISION_MISMATCH / COMPONENT_FORM_SOURCE_UNREAD / COMPONENT_FORM_RULE_UNREAD / COMPONENT_VARIANT_WITHOUT_FORM / COMPONENT_VARIANT_MISSING / COMPONENT_VARIANT_MISMATCH", "name": "组件形态描述闭环（条件式，字段声明 >1 个形态候选 formCandidates 时启用）：组件在 Common Design 中登记多种形态（如 IxTag 多种标签样式、IxSelect 下拉面板的搜索/新增/树/分组、单选/多选的 radio/卡片）时，必须在 iduxComponentForm 写明选用的形态；声明多形态候选却未选形态给 COMPONENT_FORM_MISSING（warning），选用形态不在候选内给 COMPONENT_FORM_UNKNOWN（warning）；iduxComponentForm 支持 Common Design“形态 + 增强项”两段式写法（如“级联（可搜索）”“平铺+搜索”），按最长候选子串匹配形态主值，主值在候选内即通过；已选形态但 formDecision 未写判定结论给 FORM_DECISION_MISSING（warning），formDecision 未引用所选形态给 FORM_DECISION_MISMATCH（warning）——判定链读了必须留痕结论，倒逼判定被执行；形态来源分两层并各自要求已读证据——命名/枚举真值取 Common Design 组件映射（05-components/idux-component-map.md 的组件锚点，缺依据或依据未精读命中给 COMPONENT_FORM_SOURCE_UNREAD，warning），选择依据真值取 Common Design widget patterns（03-patterns/03-widget-patterns/ 的判定小节锚点，按目录级索引 + 命中文件精读读取，缺依据或依据未精读命中给 COMPONENT_FORM_RULE_UNREAD，warning）；仅校验声明候选的字段，单形态组件零负担；字段声明样式变体编号 iduxComponentVariantId（Common Design 组件表登记的变体编号，如 IxTag 深色标签 -> IxTag_Filled）时必须成对写 iduxComponentForm，只写编号不写形态名给 COMPONENT_VARIANT_WITHOUT_FORM（warning）；编号落位为条件必填——iduxComponentVariantId（条件必填，Common Design 组件映射表登记了变体编号的形态必须填写）与判定链联动对账：formDecision/形态中已出现本组件前缀的编号 token（如 IxTag_Filled）但字段未填给 COMPONENT_VARIANT_MISSING（warning，编号已产生却未落字段，防止静默跳过），已填但与判定说明引用的编号不一致给 COMPONENT_VARIANT_MISMATCH（warning）；映射表未登记编号的形态留空并在 formDecision 写明“该形态无变体编号登记”；形态清单与命名以 Common Design 组件映射为准，本 Skill 不内置形态目录", "check": "check_component_form", "source": "references/01-workflow/04-demo-output-spec.md 11.19 组件形态描述（RULE-54）/ 01-output-templates.md AI Coding指导输出格式", "tests": "test_component_variant_missing_warns, test_component_variant_mismatch_warns, test_component_variant_no_false_positive, test_component_form_missing_warns, test_component_form_unknown_warns, test_component_form_valid_passes, test_component_form_two_part_form_passes, test_component_form_primary_substring_passes, test_component_form_decision_missing_warns, test_component_form_decision_mismatch_warns, test_component_form_decision_complete_passes, test_component_form_single_candidate_passes, test_component_form_source_unread_warns, test_component_form_rule_unread_warns, test_component_form_evidence_index_only_warns, test_component_form_evidence_complete_passes, test_component_form_single_candidate_skips_evidence"},
    {"ruleId": "RULE-55", "errorCode": "ABILITY_NOT_SWEPT / ABILITY_HIT_NOT_READ", "name": "能力发现完整性（条件式，声明 designContext.productDesign.coverage 时启用）：以 Product Design 自身声明的 coverage 为真值，要求对每个能力在 capabilitySweep 显式判定 命中/未命中（未命中同样留痕），漏项或判定非法给 ABILITY_NOT_SWEPT（warning）；判定为命中的能力须附 evidenceRef 且锚点级命中 readLedger 的 status=read，否则给 ABILITY_HIT_NOT_READ（warning）；用于兜住“该读的没读、该用 Product Design 的组件退回 Common Design”，不硬编码任何产品/文档路径", "check": "check_capability_sweep", "source": "references/01-workflow/00-design-skill-resolver.md 能力识别参考框架（防漏清单）/ references/01-workflow/04-demo-output-spec.md 11.20 能力发现完整性（RULE-55）", "tests": "test_capability_sweep_complete_passes, test_capability_not_swept_warns, test_capability_hit_not_read_warns, test_capability_sweep_absent_warns"},
    {"ruleId": "RULE-56", "errorCode": "TEMPLATE_COVERAGE_UNAPPLIED / LEGACY_TEMPLATE_ID_REF", "name": "模板 ID 一致性与覆盖兜底（条件式，声明 designContext 或页面携带模板引用文本时启用）：coverage/capabilitySweep 声明了 appliesTo 却未命中任何页面时给 TEMPLATE_COVERAGE_UNAPPLIED（warning，兜住模板更名后 Product Design 侧仍用旧 ID 导致覆盖落地校验被静默旁路）；templateSource/layoutSource/组件来源等自由文本引用已废弃旧模板 ID 时给 LEGACY_TEMPLATE_ID_REF（warning）；appliesTo 匹配对旧 ID 自动归一为当前注册表 ID", "check": "check_template_id_consistency", "source": "references/01-workflow/04-demo-output-spec.md 11.21 模板 ID 一致性与覆盖兜底（RULE-56）/ 00-design-skill-resolver.md 3.1 同步规则", "tests": "test_template_coverage_unapplied_warns, test_template_coverage_legacy_id_applied_passes, test_legacy_template_id_ref_warns, test_template_id_consistency_absent_skips"},
    {"ruleId": "RULE-57", "errorCode": "FORM_LAYOUT_MULTI_COLUMN / FORM_LAYOUT_LABEL_NOT_INLINE / FORM_LAYOUT_BASIS_UNREAD", "name": "表单单列布局闭环（条件式，页面为表单承载页时启用）：表单配置必须单列——每行一个配置项、label 与控件水平同一行；ascii（含 variants）同一行出现 >=2 个已声明表单字段给 FORM_LAYOUT_MULTI_COLUMN（warning）；字段名与其控件不在同一行给 FORM_LAYOUT_LABEL_NOT_INLINE（warning）；动态表单列表分流豁免：区块声明 formList: true（或页面 formListBlocks 登记区块名）的动态列表/行内可编辑表格（IxProFormList，“一行一个对象、一行多列”）不适用单列口径，未声明时同行多字段且带行内删除/移除标记的行同样自动豁免；表单布局依据（Common Design 表单规范）未锚点级登记到 designReferences 或未在 readLedger 命中 status=read 给 FORM_LAYOUT_BASIS_UNREAD（warning）", "check": "check_form_layout", "source": "references/01-workflow/04-demo-output-spec.md 11.22 表单单列布局闭环（RULE-57）/ 03-demo-page-decomposition.md 4.3 配置类页面补齐要求", "tests": "test_form_layout_single_column_passes, test_form_layout_multi_column_warns, test_form_layout_label_not_inline_warns, test_form_layout_form_list_section_skips, test_form_layout_inline_delete_row_skips, test_form_layout_basis_unread_warns, test_form_layout_basis_read_passes, test_form_layout_non_form_page_skips"},
    {"ruleId": "RULE-58", "errorCode": "DETAIL_SUMMARY_ACTION_DUPLICATE", "name": "详情页操作去重（条件式，页面含概览卡片/对象摘要区块且该区块声明 actions 时启用）：概览卡片已承载的对象级操作（编辑/重启/删除等）不得在底部按钮栏（footerActions）重复出现；按操作名同义归一（编辑/修改、重启/重新启动等）比较，命中给 warning；页面级 detailActionDedupExempt 或区块级 excludedActions 可豁免；底部按钮栏只保留页面级动作（关闭/上一个/下一个/取消/确定）", "check": "check_detail_action_dedup", "source": "Common Design 详情概览卡片与底部按钮栏操作去重规则 / references/01-workflow/04-demo-output-spec.md 11.23 详情页操作去重（RULE-58）", "tests": "test_detail_summary_action_duplicate_warns, test_detail_summary_action_alias_duplicate_warns, test_detail_summary_action_no_overlap_passes, test_detail_action_dedup_exempt_passes, test_detail_action_dedup_skips_without_summary_actions, test_detail_action_dedup_skips_without_footer"},
    {"ruleId": "RULE-59", "errorCode": "REUSE_CONTAINER_OVER_DESCRIBED / REUSE_HOST_NOTE_MISSING / REUSE_BASIS_UNREAD / REUSE_SCOPE_INVALID / REUSE_CANDIDATE_UNMARKED", "name": "复用业务组件容器闭环（条件式，页面声明 reuseBusinessComponent.decision=reuse 时启用，并对 PD 业务组件候选做反向提示）：需求延伸容器（按钮点击/表格字段点击/详情字段点击/行操作/导入/导出）命中 Product Design 业务封装组件或代码识别已封装的组件时，不单独绘制线框与页面内容说明，只在宿主页面简要交代复用组件；声明复用却仍绘制线框/区块字段/底部按钮 -> REUSE_CONTAINER_OVER_DESCRIBED（error）；宿主页面未交代「打开 X，复用组件 Y、不单独绘制」-> REUSE_HOST_NOTE_MISSING（warning）；basis=product-design 依据未锚点级登记或未精读、basis=code 无 codeEvidence -> REUSE_BASIS_UNREAD（warning）；trigger 不在枚举内、hostPageId 缺失或不在本次范围、容器无宿主入口（独立页面）-> REUSE_SCOPE_INVALID（warning）；容器实例化 Product Design 业务组件且有宿主入口但未声明复用 -> REUSE_CANDIDATE_UNMARKED（warning）；声明复用的页面豁免 skeleton/组件契约/弹窗抽屉语义/线框绘制/表单单列/底部按钮栏等检查，但入口落位闭环与页面总览登记仍然生效", "check": "check_business_reuse", "source": "Common Design / Product Design 业务封装组件复用规则 / references/01-workflow/04-demo-output-spec.md 11.24 复用业务组件容器（RULE-59）", "tests": "test_reuse_container_minimal_passes, test_reuse_container_over_described_fails, test_reuse_basis_unread_warns, test_reuse_basis_code_without_evidence_warns, test_reuse_host_note_missing_warns, test_reuse_scope_invalid_warns, test_reuse_candidate_unmarked_warns, test_reuse_absent_skips"},
    {"ruleId": "RULE-60", "errorCode": "FOOTER_ASCII_ALIGNMENT_MISMATCH", "name": "线框图底部按钮水平位置闭环（条件式，模板 footer.alignment 为 left/right 时启用）：Common Design 模板声明底部按钮对齐（list-modal/form-modal=right，list-drawer/form-drawer/detail-drawer/log-detail-drawer/page-form-*=left）时，ascii 底部操作区按钮必须画在对应一侧——以底部操作区上边框线显示宽度为容器参照，按钮 span 整体距左/距右留白明显偏向另一侧（超出容差 max(4, W*12%)）给 FOOTER_ASCII_ALIGNMENT_MISMATCH（error）；RULE-20 只对账 JSON 层 alignment 声明、RULE-37 只查按钮出现顺序，本规则补齐水平位置维度；无法可靠判定时静默跳过（无结构框线、无按钮、顺序已错、override、PD 模板页），不引入误报", "check": "check_footer_ascii_alignment", "source": "references/01-workflow/04-demo-output-spec.md 11.23 线框图底部按钮水平位置（RULE-60）", "tests": "test_footer_ascii_alignment_right_template_left_drawing_fails, test_footer_ascii_alignment_right_template_correct_passes, test_footer_ascii_alignment_left_template_right_drawing_fails, test_footer_ascii_alignment_unresolvable_skips"},
    {"ruleId": "RULE-61", "errorCode": "WIREFRAME_FLAT_FILTER_ORDER_MISMATCH", "name": "平铺筛选组件横向顺序闭环（条件式，仅限平铺筛选项；高级搜索页不适用）：Common Design 页面模板对筛选区的定义为平铺筛选项从左到右固定「时间/日期范围 -> 下拉选择类（状态/类型等）-> 搜索框（关键字输入）」，搜索框固定最右、禁止放首位——平铺筛选行内同时出现搜索框与其他筛选控件且搜索框排在其前时给 WIREFRAME_FLAT_FILTER_ORDER_MISMATCH（warning）；时间范围与选择框的相对顺序不强判（避免臆造）；PRD/Product Design 明确指定其他顺序时页面声明 filterOrderOverride 豁免；高级搜索页（IxProSearch，RULE-46 互斥口径）与复用业务组件容器页跳过；无法可靠判定的行静默跳过不误报", "check": "check_wireframe_flat_filter_order", "source": "references/01-workflow/04-demo-output-spec.md 11.26 平铺筛选组件横向顺序（RULE-61）", "tests": "test_flat_filter_search_first_warns, test_flat_filter_search_last_passes, test_flat_filter_prosearch_page_skips, test_flat_filter_override_skips"},
    {"ruleId": "RULE-62", "errorCode": "WIREFRAME_SHARED_TARGET_MISSING / WIREFRAME_SHARED_TARGET_MISMATCH / WIREFRAME_SHARED_HOST_NOT_DRAWN / WIREFRAME_SHARED_DIFF_MISSING", "name": "共用线框差异描述闭环（条件式，页面声明 wireframeSharedWith 时启用）：相同 UI 的页面（如同一对象的新增/编辑共用同一弹窗布局、仅数据不同）以主页面完整绘制线框，从页面不重复绘制、只声明 wireframeSharedWith 指向主页面并用 wireframeDiff 描述差异——主页面不存在给 WIREFRAME_SHARED_TARGET_MISSING（error）；主页面模板 ID 或页面类型与从页面不一致（UI 不同/对象不同，如新增与编辑对象不一样）给 WIREFRAME_SHARED_TARGET_MISMATCH（error）；主页面链式共用或未完整绘制 ascii 给 WIREFRAME_SHARED_HOST_NOT_DRAWN（error）；wireframeDiff 缺失或为空给 WIREFRAME_SHARED_DIFF_MISSING（warning）；声明共用的页面跳过骨架/区域/绘制质量/footer/表格按钮/表单布局等全部线框结构类校验，差异在 HTML 中随页面渲染", "check": "check_wireframe_shared", "source": "references/01-workflow/04-demo-output-spec.md 11.27 共用线框差异描述闭环（RULE-62）", "tests": "test_wireframe_shared_passes, test_wireframe_shared_diff_missing_warns, test_wireframe_shared_target_missing_fails, test_wireframe_shared_target_mismatch_fails, test_wireframe_shared_chain_blocked"},
    {"ruleId": "RULE-63", "errorCode": "COMPLETENESS_ENTRY_INVALID / COMPLETENESS_ITEM_NOT_LANDED / COMPLETENESS_EXCLUSION_REASON_MISSING / COMPLETENESS_BASIS_UNREAD", "name": "设计规范补齐落位闭环（条件式，designContext 声明 designCompleteness 非空 list 时启用，兼容旧字段 productDesignCompleteness）：设计规范补齐项（Product Design / Common Design 声明为需求已建设对象/页面类型固有、必备、默认存在或成对约束能力，需求未提及但默认纳入）不能只在对话框说了，必须落进 demo-spec——每个条目 capability/appliesTo/ref（含 # 锚点）/source（product-design|common-design）/decision（included|excluded，缺省 included）非法给 COMPLETENESS_ENTRY_INVALID（error）；included 条目必须有本次设计落点 landingRef（开发项 ID 如 P01-C01，或 <页面ID>#<操作/区块名>），缺失/指向不存在的页面或开发项/落点处检索不到补齐能力痕迹给 COMPLETENESS_ITEM_NOT_LANDED（error）；excluded 条目缺排除原因给 COMPLETENESS_EXCLUSION_REASON_MISSING（error，仅限用户明确不做或与需求业务事实冲突时剔除）；ref 未在 readLedger 锚点级精读命中给 COMPLETENESS_BASIS_UNREAD（warning）；两个声明均缺失或为空时整条规则跳过，历史 JSON 不误伤", "check": "check_design_completeness", "source": "references/01-workflow/04-demo-output-spec.md 11.28 设计规范补齐落位闭环（RULE-63）/ SKILL.md 设计规范完备性补齐 / references/01-workflow/07-requirement-understanding.md 设计规范补齐项", "tests": "test_design_completeness_passes, test_design_completeness_not_landed_fails, test_design_completeness_missing_landing_ref_fails, test_design_completeness_dev_item_landing_passes, test_design_completeness_excluded_reason_missing_fails, test_design_completeness_entry_invalid_fails, test_design_completeness_basis_unread_warns, test_design_completeness_absent_skips"},
    {"ruleId": "RULE-64", "errorCode": "TEMPLATE_SYNC_ENTRY_INVALID / TEMPLATE_SYNC_TARGET_MISSING / TEMPLATE_SYNC_BASIS_UNREAD", "name": "模板契约差异同步闭环（条件式，designContext.templateSync 非空 list 时启用）：注册表快照与已读取的 Common Design 页面模板定义不一致时，以 Common Design 为准产出设计并逐条登记差异 {templateId, field(footer.buttonOrder|footer.alignment), registryValue, commonDesignValue, ref(含#锚点)}——条目字段缺失或 field/commonDesignValue 取值非法给 TEMPLATE_SYNC_ENTRY_INVALID（error）；templateId 不在注册表给 TEMPLATE_SYNC_TARGET_MISSING（error）；ref 未在 readLedger 锚点级精读命中给 TEMPLATE_SYNC_BASIS_UNREAD（warning）；已登记差异的字段在校验时以 commonDesignValue 覆盖注册表快照（RULE-20 对账与 RULE-37/60 线框判定生效），照 Common Design 原文绘制不再被快照误拦；未声明该字段时不启用，历史 JSON 不误伤", "check": "check_template_sync", "source": "references/01-workflow/04-demo-output-spec.md 11.29 模板契约差异同步闭环（RULE-64）/ references/01-workflow/00-design-skill-resolver.md 同步规则 / SKILL.md Design Context 字段", "tests": "test_template_sync_passes, test_template_sync_override_conflict_fails, test_template_sync_entry_invalid_fails, test_template_sync_target_missing_fails, test_template_sync_basis_unread_warns, test_template_sync_alignment_override_passes, test_template_sync_absent_skips, test_template_sync_deviation_blocked_without_sync"},
    {"ruleId": "RULE-65", "errorCode": "CARRIER_SWEEP_ENTRY_INVALID / CARRIER_SWEEP_TARGET_MISSING / CARRIER_SWEEP_MISMATCH / CARRIER_SWEEP_CARD_TRACE_MISSING / CARRIER_SWEEP_BASIS_UNREAD / CARRIER_SWEEP_SIGNAL_REVIEW", "name": "承载形式分流闭环（两部分）：其一，designContext.carrierSweep 键显式声明时启用条目对账——CD 存在承载形式分流决策链（如多实例配置内容的表格承载 vs 多卡片承载）时，逐页登记 { pageId, contextRef(分流章节锚点), dataTraits(逐特征判定), decision(CD 原文承载形式), templateRef(落地模板 ID), reason }；条目字段缺失或非法 CARRIER_SWEEP_ENTRY_INVALID（error）、pageId 不存在或 templateRef 不在注册表 CARRIER_SWEEP_TARGET_MISSING（error）、判定模板与页面实际 templateId 不一致 CARRIER_SWEEP_MISMATCH（error）、注册表标记 carrierTraceRequired=true 的特化承载模板（如卡片列表页，CD 明文仅判为对应承载时使用）被使用却无条目 CARRIER_SWEEP_CARD_TRACE_MISSING（error）、contextRef 未精读 CARRIER_SWEEP_BASIS_UNREAD（warning）；其二，可疑信号复核始终启用（warning）——页面文本含第三方对接类特征词（对接/厂商/第三方/平台/连接状态/进度等）却未留痕时告警复核，防止该选卡片承载却回落表格基线；判定语义始终以 CD 分流链原文为准，校验器只做账实一致与留痕完整性，不硬编码任何 CD 词汇与路径", "check": "check_carrier_sweep", "source": "references/01-workflow/04-demo-output-spec.md 11.30 承载形式分流闭环（RULE-65）/ references/01-workflow/00-design-skill-resolver.md 承载形式分流义务 / references/01-workflow/03-demo-page-decomposition.md 4.2.3", "tests": "test_carrier_sweep_passes, test_carrier_sweep_mismatch_fails, test_carrier_sweep_target_missing_fails, test_carrier_sweep_card_trace_missing_fails, test_carrier_sweep_entry_invalid_fails, test_carrier_sweep_basis_unread_warns, test_carrier_sweep_signal_review_warns, test_carrier_sweep_absent_skips, test_carrier_sweep_table_with_trace_passes, test_carrier_sweep_mismatch_reverse_fails"},
    {"ruleId": "RULE-66", "errorCode": "CHANGE_SYNC_ENTRY_INVALID / CHANGE_SYNC_TARGET_MISSING / CHANGE_SYNC_SOURCE_NOT_LANDED / CHANGE_SYNC_NOT_LANDED / CHANGE_SYNC_EXEMPTION_REASON_MISSING / CHANGE_SYNC_VIEW_UNCOVERED / CHANGE_SYNC_REVIEW", "name": "关联改动同步闭环（条件式，designContext.changeSync 声明时启用）：需求在已有功能上修改（如已有表单新增一个配置项）时，同一业务对象的关联视图（表格汇总列/筛选搜索项/详情展示/卡片）须同步呈现该字段或逐项写明豁免——条目字段缺失或 view 取值非法 CHANGE_SYNC_ENTRY_INVALID（error）；pageId 不存在 CHANGE_SYNC_TARGET_MISSING（error）；sourceField 不在该页 sections 任何字段数组中 CHANGE_SYNC_SOURCE_NOT_LANDED（error，触发字段未落位先按 RULE-36 落字段）；synced 落点指向不存在页面/开发项或落点处检索不到字段痕迹 CHANGE_SYNC_NOT_LANDED（error）；excluded 缺豁免理由 CHANGE_SYNC_EXEMPTION_REASON_MISSING（error，豁免是专业判断：如密码字段不进表格列、时间戳不值得做搜索项、超长描述不进筛选条件但可进关键词搜索）；views 枚举的关联视图未被 synced/excluded 覆盖 CHANGE_SYNC_VIEW_UNCOVERED（error）；反向复核始终对声明条目之外的页面生效（warning）——同页面表单字段均未出现在表格列与筛选项时告警人工复核（字段别名/派生列属正常差异故仅 warning，完整对账以 changeSync 条目为准）；只针对本次需求新增/修改的字段，存量字段历史差异不属本规则范围", "check": "check_change_sync", "source": "references/01-workflow/04-demo-output-spec.md 11.31 关联改动同步闭环（RULE-66）/ references/01-workflow/03-demo-page-decomposition.md 变更影响面识别 / SKILL.md Design Context 字段", "tests": "test_change_sync_passes, test_change_sync_source_not_landed_fails, test_change_sync_not_landed_fails, test_change_sync_exemption_reason_missing_fails, test_change_sync_view_uncovered_fails, test_change_sync_target_missing_fails, test_change_sync_entry_invalid_fails, test_change_sync_reverse_review_warns, test_change_sync_no_reverse_no_noise, test_change_sync_absent_skips"},
    {"ruleId": "RULE-67", "errorCode": "FORM_TIP_PLACEHOLDER / FORM_TIP_AMBIGUOUS", "name": "小i提示内容义务（条件式，字段 tips 显式声明小i痕迹时启用）：表单配置项有小i提示图标时，必须在小i提示（tips）中写明提示内容本身——具体说明该配置项的含义/影响/限制（如：用于实例鉴权，创建后不可修改），禁止只画图标不给内容或以占位空话（有/需要/待补充/见原型等）充数；tips 含小i痕迹词（小i/[i]/提示图标/tooltip 等）但去除痕迹词后无具体文案（<6字或纯空话）→ warning FORM_TIP_PLACEHOLDER，仅痕迹词与极短残留 → warning FORM_TIP_AMBIGUOUS 提示人工复核；有具体文案（≥6字且非空话）视为已履行义务；范围仅表单字段（formFields 与表单区块 fields），表格/筛选字段 description 列语义不同不适用（RULE-67）", "check": "check_tooltip_content", "source": "references/01-workflow/04-demo-output-spec.md 11.32 小i提示内容义务（RULE-67）/ 06-quality-and-rules.md 1.15 关联改动同步闭环之后", "tests": "test_tooltip_placeholder_warns / test_tooltip_specific_content_passes / test_tooltip_marker_only_warns / test_tooltip_absent_skips / test_tooltip_short_residue_ambiguous_warns / test_tooltip_filter_table_not_scanned"},
    {"ruleId": "RULE-68", "errorCode": "FEATURE_CONTRACT_ENTRY_INVALID / FEATURE_TARGET_MISSING / FEATURE_PRESERVE_MISSING / FEATURE_ADJUSTMENT_UNREASONED / FEATURE_FORBIDDEN_PATTERN / FEATURE_BASIS_UNREAD / FEATURE_UI_BLUEPRINT_INVALID / FEATURE_UI_BLUEPRINT_ELEMENT_MISSING / FEATURE_UI_BLUEPRINT_NOT_IN_WIREFRAME / FEATURE_UI_BLUEPRINT_NOT_DRAWN", "name": "Feature 契约落位闭环（条件式，designContext.featureContract 声明时启用）：CD Feature 业务功能层文档声明功能契约（哪些结构必须保留/哪些可按业务调整/哪些禁止出现）时，设计命中该功能则 CD 是约束而非参考，契约条款必须落进设计并逐项对账——按 source 文档分组登记 { source(Feature文档路径#契约章节锚点), appliedTo:[{pageId, item, landingRef}], adjustments:[{item, from, to, reason}], forbidden:[{pattern}], reason }；条目 source 缺失或不含 # 锚点、appliedTo 非非空数组、appliedTo 项缺 pageId/item/landingRef、adjustments 项缺 item/from/to、forbidden 项缺 pattern、reason 缺失 FEATURE_CONTRACT_ENTRY_INVALID（error）；appliedTo 的 pageId 不存在 FEATURE_TARGET_MISSING（error）；landingRef 指向不存在页面/开发项、与 pageId 不一致或落点处检索不到 item 痕迹 FEATURE_PRESERVE_MISSING（error，必须保留的契约结构未落位）；adjustments 项缺 reason FEATURE_ADJUSTMENT_UNREASONED（error，可按业务调整的部分调整须留痕：CD 原结构->本设计调整->业务理由，无理由调整视为静默偏离）；forbidden 声明的禁止模式词元出现在任一页面文本 FEATURE_FORBIDDEN_PATTERN（error，禁止模式由 AI 从契约原文声明为数据，校验器只做文本检索，不硬编码任何 CD 词汇）；source 未精读 FEATURE_BASIS_UNREAD（warning）；uiBlueprint 界面蓝图对账维度：Feature 文档含分步线框图时必须逐界面登记 { screen, pageId, structuralElements:[结构元素...] }（禁止选择性登记，resolver 层全量登记义务），条目缺 screen/pageId/structuralElements 非空数组 FEATURE_UI_BLUEPRINT_INVALID（error）、落点页不存在复用 FEATURE_TARGET_MISSING、页面无 wireframe.ascii 且无 wireframeSharedWith 共用声明 FEATURE_UI_BLUEPRINT_NOT_DRAWN（warning）、结构元素在页面全文（ascii+variants+区块字段）检索不到 FEATURE_UI_BLUEPRINT_ELEMENT_MISSING（error）、未在 ascii 命中但在页面其他文本命中 FEATURE_UI_BLUEPRINT_NOT_IN_WIREFRAME（warning，疑似只是文字提及未画进线框）；三层检索口径：ascii 命中通过/文本命中告警/全无阻断；结构形态对错机器不判定（诚实边界），由 resolver 义务与确认点对照兜底；机制通用不绑定功能词，CD 新增 Feature 文档零改动，历史 JSON 不误伤", "check": "check_feature_contract", "source": "references/01-workflow/04-demo-output-spec.md 11.33 Feature 契约落位闭环（RULE-68）/ references/01-workflow/00-design-skill-resolver.md Feature 契约遵守义务 / references/01-workflow/03-demo-page-decomposition.md 功能契约对账", "tests": "test_feature_contract_passes, test_feature_contract_entry_invalid_fails, test_feature_contract_target_missing_fails, test_feature_contract_preserve_missing_fails, test_feature_contract_adjustment_unreasoned_fails, test_feature_contract_forbidden_pattern_fails, test_feature_contract_basis_unread_warns, test_feature_contract_absent_skips, test_feature_ui_blueprint_passes, test_feature_ui_blueprint_invalid_fails, test_feature_ui_blueprint_element_missing_fails, test_feature_ui_blueprint_not_in_wireframe_warns, test_feature_ui_blueprint_not_drawn_warns, test_feature_ui_blueprint_variants_ascii_hit"},
    {"ruleId": "RULE-70", "errorCode": "REGION_BASIS_UNDECLARED / REGION_BASIS_UNREAD", "name": "区域规范精读闭环 v2（双轨制，条件式，页面 sections 或 wireframe.regions 命中区域识别枚举时启用）：本 Skill 不预置、不维护任何规范文档路径，「读什么」的权威在实际加载的 Common Design / Product Design 目录。区块命中区域（表格/概览/树/表单/筛选/步骤条/详情/导航）后：designContext 与页面级 regionBasisDeclarations 均未声明该区域依据给 REGION_BASIS_UNDECLARED（warning）；声明了依据但 ref 未在 readLedger 锚点级精读命中给 REGION_BASIS_UNREAD（warning）；防「页面明显有表格却没读表格规范也照常输出」导致规范真值（操作列收纳、列配置、空态、信息层级等）整体缺失；复用业务组件容器页（RULE-59）、PD override 页、wireframeSharedFrom 从页面跳过；regionBasisExempt（页面级，含 reason）豁免", "check": "check_region_basis_reading", "source": "references/01-workflow/04-demo-output-spec.md 11.35 区域规范精读闭环（RULE-70）/ references/02-template-contracts/common-design-template-registry.json regionReadingContract", "tests": "test_region_basis_undeclared_warns, test_region_basis_unread_warns, test_region_basis_read_passes, test_region_basis_doc_level_read_not_enough, test_region_basis_page_level_decl_passes, test_region_basis_non_design_context_skips, test_region_basis_exempt_skips, test_region_basis_pd_source_decl_passes"},
    {"ruleId": "RULE-71", "errorCode": "ACTION_COLUMN_OVERFLOW", "name": "表格行内操作收纳检验（条件式，页面含表格区块时启用）：表格区块行内操作数量超过收纳阈值（默认 3，区块/页面 actionColumnLimit 可覆盖）且未声明收纳时给 ACTION_COLUMN_OVERFLOW（warning，提醒按已读取的 Common Design 表格规范将超出部分收纳进「更多」，本 Skill 不内置规范真值数值，阈值仅为通用提醒口径）；行内操作来源优先 rowActions 数组，其次 actions[].scope=row 的项，两者均未声明时以区块 actions 总数启发判定并提示区分 scope；区块 actionOverflow=true 或 description/interactionNotes/ascii 已含「更多」收纳痕迹豁免", "check": "check_action_column_overflow", "source": "references/01-workflow/04-demo-output-spec.md 11.36 表格行内操作收纳检验（RULE-71）/ references/01-workflow/01-output-templates.md 行内操作契约", "tests": "test_action_overflow_warns, test_action_overflow_within_limit_passes, test_action_overflow_declared_passes, test_action_overflow_more_mark_passes, test_action_overflow_row_scope_counts, test_action_overflow_limit_override, test_action_overflow_ambiguous_actions_hint"},
    {"ruleId": "RULE-69", "errorCode": "OVERVIEW_STYLE_INVALID / OVERVIEW_STYLE_MISSING / OVERVIEW_CHART_STYLE_NOT_DRAWN / OVERVIEW_METRIC_COMPONENT_MISSING", "name": "概览区形态还原闭环（条件式，页面 templateId 命中注册表含 overviewVariants 的模板或 regions 含 overview 区域时启用）：概览表格页与概览左树表格页的概览区在 Common Design 中定义了多种形态（数字统计型/饼图/折线图/条形图等），概览区块必须声明 overviewStyle（形态值取注册表 overviewVariants.styles 的 id）与 overviewMetrics（指标数组 name/display/iduxComponent/description），线框图概览区按声明形态绘制可辨识痕迹（统计型=指标名+数字统计卡行，图表=图表占位框+形态标注）——声明非法形态值给 OVERVIEW_STYLE_INVALID（error，形态枚举以精读 CD 模板原文为准，禁止凭经验新增）；启用页面概览区块均未声明形态给 OVERVIEW_STYLE_MISSING（warning，形态信息缺失导致 AI Coding 只能自绘通用卡片）；声明图表形态但 ascii（含 variants）检索不到形态名痕迹给 OVERVIEW_CHART_STYLE_NOT_DRAWN（warning，疑似只写文字未画进线框）；overviewMetrics 项缺 name/iduxComponent/description 给 OVERVIEW_METRIC_COMPONENT_MISSING（warning）；复用业务组件容器页（RULE-59）、wireframeSharedWith 从页面（RULE-62）、PD override 页跳过；overviewStyleExempt（页面级，含 reason）豁免 MISSING", "check": "check_overview_style", "source": "references/01-workflow/04-demo-output-spec.md 11.34 概览区形态还原闭环（RULE-69）/ references/02-template-contracts/common-design-template-registry.json overviewVariants / references/01-workflow/01-output-templates.md 概览区块形态契约", "tests": "test_overview_style_stat_passes, test_overview_style_invalid_fails, test_overview_style_missing_warns, test_overview_style_chart_not_drawn_warns, test_overview_metric_component_missing_warns, test_overview_style_exempt_skips, test_overview_style_non_overview_page_skips, test_overview_style_region_trigger_enabled"},
]

# 页面 type（中文）与标准模板的映射：由模板注册表 templates[*].name 派生，
# 中文名与模板 ID 的唯一维护入口是 common-design-template-registry.json，避免硬编码漂移。
def build_type_template_map(registry):
    mapping = {}
    for tid, tpl in (registry.get("templates") or {}).items():
        name = str((tpl or {}).get("name", "")).strip()
        if name:
            mapping[name] = tid
    return mapping

# 页面模板 ID 更名别名表（RULE-56）：仅用于"兼容识别"旧 ID，不得作为新产出的 templateId。
# 键为 Common Design 更名前的已废弃旧 ID，值为当前注册表 ID。
TEMPLATE_CAPABILITY_KEYS = ("template", "page-template", "模板", "页面模板")


def is_template_capability(cap):
    """capability 是否属于页面模板层（关键词包含匹配，兼容 Product Design 侧用词变体）。"""
    capk = str(cap or "").strip().lower()
    return bool(capk) and (capk in TEMPLATE_CAPABILITY_KEYS
                           or "模板" in capk or "template" in capk)


LEGACY_TEMPLATE_ID_ALIASES = {
    "page-list-modal": "list-modal",
    "page-list-drawer": "list-drawer",
    "page-detail-drawer": "detail-drawer",
    "page-detail-log": "log-detail-drawer",
    "page-form-modal": "form-modal",
    "page-form-drawer": "form-drawer",
}


def normalize_template_id(tid):
    """把已废弃的旧模板 ID 归一为当前注册表 ID；非旧 ID 原样返回。"""
    t = str(tid or "").strip()
    return LEGACY_TEMPLATE_ID_ALIASES.get(t, t)


def legacy_template_id_in(text):
    """返回文本中出现的已废弃旧模板 ID（按 ID 边界精确匹配），无则返回 None。"""
    raw = str(text or "")
    for old in LEGACY_TEMPLATE_ID_ALIASES:
        if re.search(r"(?<![A-Za-z0-9-])" + re.escape(old) + r"(?![A-Za-z0-9-])", raw):
            return old
    return None


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

# 下拉选项完整性（RULE-48）：固定选项型控件与选项单元格渲染键。
# 选择类控件判定：字段 component / iduxComponent 命中任一关键词即视为固定选项型控件。
SELECT_COMPONENT_KEYS = (
    "下拉", "select", "选择器", "单选", "多选", "radio", "checkbox", "combobox",
)
# 选项单元格键：按字段形态取渲染器实际渲染的键（与 FIELD_KEY_CONTRACT 对齐）。
OPTION_CELL_KEYS = {
    "formFields":   ("rules", "tips"),
    "filterFields": ("options", "description"),
}
DEFAULT_OPTION_CELL_KEYS = ("rules", "options", "display", "description", "tips")
# 截断指纹：选项单元格出现这些标记说明"只举例未列全"。
OPTION_TRUNCATION_PATTERNS = (
    r"等等",
    r"例如",
    r"如[:：]",
    r"…",
    r"\.\.\.",
    r"共\s*\d+\s*[个项条]",
    r"等(?=$|[，,。、；;）)])",
)
RULE48_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.13 下拉选项完整性（RULE-48）"
RULE57_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.22 表单单列布局闭环（RULE-57）"
# 表单承载模板（RULE-57）：这些模板的页面主体是表单配置项，线框必须单列绘制
FORM_LAYOUT_TEMPLATE_IDS = ("page-form-config", "page-form-stepper", "form-modal", "form-drawer")
# 表单区块识别关键词（用于在非表单类模板页面中识别表单配置区块）
FORM_SECTION_KEYWORDS = ("表单", "配置项", "录入", "form")
# 表单布局依据（Common Design 表单规范）在 designReferences 中的识别关键词
FORM_LAYOUT_BASIS_HINTS = ("form", "表单", "录入")
# 详情页操作去重（RULE-58）：顶部概览卡片/对象摘要已承载的操作（如 编辑/重启）不应在底部按钮栏重复出现。
# 常用操作名同义归一：避免“编辑/修改”“重启/重新启动”这类同义重复被漏判。
RULE58_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.23 详情页操作去重（RULE-58）"
DETAIL_ACTION_ALIASES = {
    "编辑": "编辑", "修改": "编辑", "编辑信息": "编辑", "更改": "编辑", "维护": "编辑",
    "重启": "重启", "重新启动": "重启", "启动": "重启", "开机": "重启",
    "删除": "删除", "移除": "删除", "解绑": "删除",
    "禁用": "禁用", "停用": "禁用", "关闭策略": "禁用",
    "启用": "启用", "开启": "启用", "开启策略": "启用",
    "复制": "复制", "克隆": "复制", "另存为": "复制",
    "导出": "导出", "下载": "下载", "同步": "同步", "立即同步": "同步", "马上同步": "同步",
    "重置": "重置", "刷新": "刷新", "返回": "返回",
    "取消": "取消", "确定": "确定", "保存": "保存", "关闭": "关闭",
    "上一个": "上一个", "下一个": "下一个", "上一步": "上一个", "下一步": "下一个",
}


def normalize_action_name(name):
    """操作名归一：先去掉空白/装饰，再按同义词表归一到规范名；未知操作名原样返回。"""
    raw = str(name or "").strip()
    if not raw:
        return ""
    key = raw
    if key in DETAIL_ACTION_ALIASES:
        return DETAIL_ACTION_ALIASES[key]
    for k, v in DETAIL_ACTION_ALIASES.items():
        if k and k in key:
            return v
    return key

# 复用业务组件容器（RULE-59）：需求延伸容器命中 Product Design 业务封装组件（或代码识别已知封装）时，
# 不单独绘制线框与页面内容说明，只在宿主页面简要交代复用的组件。
RULE59_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.24 复用业务组件容器（RULE-59）"
REUSE_ALLOWED_TRIGGERS = ("按钮点击", "表格字段点击", "详情字段点击", "行操作", "导入", "导出")
REUSE_HOST_NOTE_MARKERS = ("复用", "不单独", "业务封装", "直接使用")
REUSE_BLOCKING_ASCII_KEYS = ("ascii",)
REUSE_SECTION_FIELD_KEYS = ("formFields", "tableFields", "detailFields", "cardFields", "filterFields")


def page_reuse_business(page):
    """取页面"复用业务组件"声明；非复用容器返回 None。"""
    if not isinstance(page, dict):
        return None
    decl = page.get("reuseBusinessComponent")
    if not isinstance(decl, dict):
        return None
    if str(decl.get("decision") or "").strip().lower() not in ("reuse", "复用"):
        return None
    return decl


def page_text_blob(page):
    """把页面里的文本（线框、区块、操作名等）拼成一份朴素文本，用于"宿主是否交代了复用"判断。"""
    if not isinstance(page, dict):
        return ""
    chunks = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str):
                    chunks.append(v)
                else:
                    walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                walk(v)

    walk(page.get("wireframe"))
    walk(page.get("sections"))
    walk(page.get("operations"))
    walk(page.get("footerActions"))
    walk(page.get("entryPoints"))
    return "\n".join(chunks)

# ascii 中的控件占位（如 [____]、[保存]、[••••]）
CONTROL_PLACEHOLDER_PATTERN = r"\[[^\[\]\n]{1,40}\]"

# 选项维度保留（RULE-48）：需求源枚举表含分组/层级列时必须保留该维度，禁止压平为单层列表。
# 声明方式：requirementOptionSets[] 增加可选 dimension（flat/group/hierarchy，缺省 flat）与可选 sourceColumns；
# sourceColumns 声明 >=2 列时自动视为 group（源表“分组列 + 值列”）。
# 承载该维度的控件形态不在此判定，仍由 RULE-54 依 Common Design widget patterns 判定并登记依据。
OPTION_DIMENSION_SYNONYMS = {
    "group": "group", "grouped": "group", "分组": "group", "分组下拉": "group",
    "hierarchy": "hierarchy", "tree": "hierarchy", "层级": "hierarchy", "树形": "hierarchy", "级联": "hierarchy",
    "flat": "flat", "平铺": "flat", "单层": "flat",
}
# 维度结构痕迹：显式分组/层级词，或“组名：选项A/选项B”结构，或箭头层级表达
OPTION_DIMENSION_MARKERS = (
    "分组", "层级", "级联", "父级", "子级", "上级", "下级", "一级", "二级", "三级", "树",
)
OPTION_DIMENSION_GROUP_PATTERN = (
    r"[\u4e00-\u9fffA-Za-z0-9（）()\-]{1,24}\s*[:：]\s*[^\n:：]+[/、,，;；|][^\n:：]+"
)
OPTION_DIMENSION_ARROW_PATTERN = r"[→＞>›⇒]"

# 详情页字段去重（RULE-49）：概览卡片/对象摘要已展示字段不应在详情描述列表重复（条件式，仅详情类页面）。
# 概览卡片字段（Zone A）来源：页面声明的 detailSummaryFields（推荐，声明优先）；未声明时取页面级/区块 cardFields 与摘要型区块字段。
# 详情描述列表型区块（Zone B）：承载“下方字段展示列表”的区块类型关键词
DETAIL_DESCRIPTION_SECTION_TYPES = (
    "overview", "descriptions", "description", "detail", "basic-info", "basic", "detail-content",
    "概览", "描述列表", "描述", "详情", "基本信息", "详情信息", "概要",
)
# 摘要卡片型区块（Zone A 兜底）：对象摘要/概览卡片以字段列表承载时使用；
# 不含 overview/概览（后者是概览内容列表，归 Zone B 详情描述列表）
DETAIL_SUMMARY_SECTION_TYPES = (
    "object-summary", "summary-card", "summary", "profile",
    "对象摘要", "摘要卡片", "摘要信息", "摘要", "概览卡片",
)
# 合法重复豁免区块：历史/日志/记录类不参与去重（无论 type，按关键词优先跳过）
DETAIL_DEDUP_SKIP_SECTION_TYPES = (
    "history", "timeline", "audit", "operation-log", "change-log", "changelog",
    "操作记录", "变更记录", "历史", "日志", "审计", "时间线",
)
DETAIL_FIELD_ARRAYS = ("detailFields", "fields", "cardFields")
RULE49_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.14 详情页字段去重（RULE-49）"

# RULE-50 按钮/可点击操作表：高影响操作/二次确认/局部面板须写清组件与文案或字段，组件与文案须可溯源设计来源
RULE50_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.15 按钮/可点击操作表（RULE-50）"
# 默认高影响操作名（可被 spec 级 / 页面级 actionRules.highImpactActions 扩展）
DEFAULT_HIGH_IMPACT_ACTIONS = ("删除", "禁用", "重启", "业务下线", "批量处置", "未保存离开")
# 默认高影响关键词（命中即视为高影响；可被 actionRules.highImpactKeywords 扩展）
DEFAULT_HIGH_IMPACT_KEYWORDS = (
    "删除", "禁用", "停用", "重启", "下线", "批量处置", "批量删除", "批量禁用",
    "未保存", "离开", "移除", "注销", "清空", "覆盖", "解绑", "提权", "强制", "处置", "销毁", "报废",
)
# 触发方式中表示"会弹窗/面板/二次确认"的关键词
ACTION_CONFIRM_TRIGGER_KEYWORDS = ("确认", "弹窗", "二次", "面板", "管理员密码", "抽屉", "对话框", "popconfirm")

# RULE-51 表格区按钮位置（线框图）：表格关联按钮统一置于表格区左上角工具栏，不得绘制在表格框下方或工具栏之外
RULE51_SOURCE = "references/01-workflow/04-demo-output-spec.md 11.16 表格区按钮位置（RULE-51）"
# 表格关联按钮关键词（批量操作、子功能入口等）；列设置/列配置为表格组件自带功能，不属于按钮（见 COLUMN_SETTING_DRAWN_KEYWORDS）
TABLE_TOOLBAR_BUTTON_KEYWORDS = (
    "批量", "导入", "导出", "刷新", "更多", "排序", "置顶", "移动",
    "新增", "新建", "设置", "删除", "编辑", "停用", "启用",
)
# 列设置/列配置：表格组件（IxTable）自带功能，线框图不得绘制为独立按钮
COLUMN_SETTING_DRAWN_KEYWORDS = ("列设置", "列配置")
# 表格下方区域的合法元素（不应误判为按钮）
TABLE_FOOTER_KEYWORDS = ("底部", "确定", "取消", "保存", "提交", "返回", "关闭")
TABLE_PAGINATION_KEYWORDS = ("上一页", "下一页", "分页", "页码", "共")
_ASCII_BORDER_CHARS = set("─│┌┐└┘├┤┬┴┼┏┓┗┛┃━═║╔╗╚╝╠╣╪╫ ")


def _find_ascii_table_box(lines):
    """定位 ascii 中的表格框：取"内部含 | 分隔数据行"的最小嵌套盒子，返回 (top_idx, bottom_idx)，找不到返回 None。"""
    stack = []
    boxes = []
    for i, line in enumerate(lines):
        if "┌" in line and "┐" in line:
            stack.append(i)
        if "└" in line and "┘" in line and stack:
            boxes.append((stack.pop(), i))
    candidates = []
    for top, bottom in boxes:
        if any("|" in line for line in lines[top + 1:bottom]):
            candidates.append((bottom - top, top, bottom))
    if not candidates:
        return None
    candidates.sort()
    return (candidates[0][1], candidates[0][2])


def _table_button_keywords_in(line):
    return [kw for kw in TABLE_TOOLBAR_BUTTON_KEYWORDS if kw in line]


def _ascii_line_is_border_only(line):
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= _ASCII_BORDER_CHARS


def _ascii_line_is_pagination_or_footer(line, has_button_keyword):
    if _ascii_line_is_border_only(line):
        return True
    if any(k in line for k in TABLE_FOOTER_KEYWORDS):
        return True
    if any(k in line for k in TABLE_PAGINATION_KEYWORDS) and not has_button_keyword:
        return True
    return False


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


_OPTION_SPLIT_RE = re.compile(r"[/、,，;；|｜·\n\r\t]+")
_OPTION_LABEL_RE = re.compile(r"^[^：:\n]{0,12}[：:]\s*")
_OPTION_PAREN_RE = re.compile(r"[（(][^）)]*[）)]")
_OPTION_TRAIL_RE = re.compile(r"(?:等等|等|…+|\.{3,})+$")


def option_tokens(text):
    """把选项单元格文本拆成选项令牌集合。

    逐项拆分后，去掉标签前缀（如"选项："）、括号补充（如"（默认）"）与尾部截断标记
    （如"低等"的"等"），再归一化，避免"指定终端"被"指定终端组"这类前缀造成误判。
    """
    tokens = set()
    for raw in _OPTION_SPLIT_RE.split(str(text)):
        seg = _OPTION_PAREN_RE.sub("", raw).strip()
        seg = _OPTION_LABEL_RE.sub("", seg).strip()
        seg = _OPTION_TRAIL_RE.sub("", seg).strip("。.；;，,、 ")
        if seg:
            tokens.add(norm(seg))
    return tokens


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


# 动态表单列表行内操作标记（RULE-57 豁免）：同一行出现多个字段且带行内删除/移除标记时，
# 该行是"一行一个对象、一行多列"的动态列表/行内可编辑表格，不按单列多配置项告警。
FORM_LIST_INLINE_DELETE_PATTERN = re.compile(r"删除|\[删\]|移除|×|✕")


def _disp_width(text):
    """显示宽度：东亚全角/宽字符记 2、其余记 1（ascii 线框对齐判定的统一口径）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in str(text))


def _form_primary_form(chosen, candidates):
    """RULE-54 两段式写法兼容：从 iduxComponentForm 取形态主值。

    Common Design 的组件形态常写作"形态 + 增强项"两段式（如"级联（可搜索）""平铺+搜索"），
    候选清单只登记形态主值。返回值：
    - ""      -> 未填写（MISSING）；
    - None    -> 完全不含任何候选（UNKNOWN）；
    - 否则    -> 匹配到的候选主值（两段式兼容通过）。
    """
    chosen = str(chosen or "").strip()
    if not chosen:
        return ""
    if chosen in candidates:
        return chosen
    for cand in sorted(candidates, key=len, reverse=True):
        if cand and cand in chosen:
            return cand
    return None


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
    "previous": ["上一步", "上一个"],
    "next-or-complete": ["下一步", "下一个", "完成", "提交"],
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
# 高级搜索组件识别标记（RULE-46 扩展）：页面筛选声明命中其一即视为「高级搜索承载整体筛选」
PROSEARCH_MARKERS = ("ixprosearch", "ix-pro-search", "高级搜索")
# 平铺筛选行识别关键词：ascii 中出现且该行不含高级搜索标记时，视为单独绘制的筛选区/查询区
FLAT_FILTER_LINE_KEYS = ("筛选", "查询", "过滤")
# 平铺筛选组件横向顺序（RULE-61）：Common Design 页面模板筛选区定义——平铺筛选项从左到右固定为
# 时间/日期范围 -> 下拉选择类（状态/类型等）-> 搜索框（关键字输入），搜索框固定最右、禁止放首位。
# 校验只强执可可靠判定的硬约束「搜索框不早于同行其他筛选控件」，时间范围与选择框的相对顺序不判（避免臆造）。
FLAT_FILTER_SEARCH_BOX_PATTERN = re.compile(
    r"(关键字|搜索词|查询关键字|模糊搜索|名称搜索|搜索框|关键字：|搜索：|关键字\s*\[)")
FLAT_FILTER_RANGE_PATTERN = re.compile(r"(时间范围|日期范围|起止时间|起止日期|开始.{0,6}截止|\[[^\]\n]{0,20}~[^\]\n]{0,20}\])")
FLAT_FILTER_SELECT_PATTERN = re.compile(r"(状态|类型|级别|等级|分类|类别|请选择|下拉)")
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
        self.type_template_map = build_type_template_map(registry)
        # 区域级规范精读契约（RULE-70）：优先取注册表 regionReadingContract.regions
        self._region_read_contract = (registry.get("regionReadingContract") or {}).get("regions") or {}
        # Product Design override 模板动态注册（视为注册表新增模板，可直接作为 templateId）
        self.pd_templates = {}
        self._collect_pd_templates()

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

    # ------------------------------------------------------------------
    # Product Design override 模板动态注册（PD 模板视为注册表新增模板）
    # ------------------------------------------------------------------
    def _pd_design_context(self):
        dc = self.data.get("designContext") or {}
        pd = dc.get("productDesign") if isinstance(dc, dict) else None
        return pd if isinstance(pd, dict) else {}

    def _pd_template_override_entries(self):
        """筛选 coverage 中页面模板层 override 条目（关键词匹配，兼容用词变体）。"""
        pd = self._pd_design_context()
        entries = []
        for c in (pd.get("coverage") or []):
            if not isinstance(c, dict):
                continue
            rel = str(c.get("relation", "")).strip().lower()
            if rel not in ("override", "覆盖") and "override" not in rel and "覆盖" not in rel:
                continue
            if is_template_capability(c.get("capability")):
                entries.append(c)
        return entries

    def _collect_pd_templates(self):
        """从 coverage 模板 override 条目显式声明 templateId/pdTemplateId 的，登记为动态模板。"""
        for c in self._pd_template_override_entries():
            tid = str(c.get("templateId") or c.get("pdTemplateId") or "").strip()
            if not tid or tid == "custom":
                continue
            name = str(c.get("name") or c.get("templateName") or "").strip()
            ref = str(c.get("sourceRef") or c.get("templateRef")
                      or c.get("productTemplateRef") or "").strip()
            applies = [str(t).strip() for t in (c.get("appliesTo") or []) if str(t).strip()]
            self.pd_templates[tid] = {"name": name, "ref": ref, "appliesTo": applies}

    def _pd_template_for_page(self, page, tid):
        """页面命中的 PD 模板 override 条目。

        匹配优先级：
        1) 页面 templateId 等于条目声明的 templateId/pdTemplateId（已直接采用 PD 模板的强关联）；
        2) appliesTo 三口径（templateId / 页面 id / 页面类型中文名）；appliesTo 为空 = 全部页面。
        """
        pid = str(page.get("id", "")).strip()
        ptype = str(page.get("type", "")).strip()
        for c in self._pd_template_override_entries():
            declared = str(c.get("templateId") or c.get("pdTemplateId") or "").strip()
            if declared and normalize_template_id(tid) == normalize_template_id(declared):
                return c
        for c in self._pd_template_override_entries():
            applies = [str(t).strip() for t in (c.get("appliesTo") or []) if str(t).strip()]
            if not applies:
                return c
            applies_norm = {normalize_template_id(t) for t in applies}
            if (normalize_template_id(tid) in applies_norm or pid in applies
                    or (ptype and ptype in applies)):
                return c
        return None

    def _pd_template_name(self, entry):
        return str((entry or {}).get("name", "")).strip()

    def _page_has_pd_template_basis(self, page):
        """页面是否登记了 product-design 依据（模板锚点）。"""
        refs = (page.get("codingGuide") or {}).get("designReferences") or []
        return any(isinstance(r, dict) and str(r.get("source", "")).strip() == "product-design"
                   for r in refs)

    def _page_has_pd_template_basis_read(self, page, entry):
        """PD 模板依据是否已精读（readLedger status=read，整篇 #* 或锚点命中）。"""
        if not self._page_has_pd_template_basis(page):
            return False
        ledger = {}
        dc = self.data.get("designContext") or {}
        for e in (dc.get("readLedger") or []) if isinstance(dc, dict) else []:
            if isinstance(e, dict) and str(e.get("ref", "")).strip():
                r = str(e.get("ref", "")).strip()
                ledger[(r.split("#", 1)[0], r.split("#", 1)[1] if "#" in r else "*")] = \
                    str(e.get("status", "")).strip()
        refs = (page.get("codingGuide") or {}).get("designReferences") or []
        for r in refs:
            if not isinstance(r, dict) or str(r.get("source", "")).strip() != "product-design":
                continue
            ref = str(r.get("ref", "")).strip()
            if not ref:
                continue
            doc = ref.split("#", 1)[0]
            anchor = ref.split("#", 1)[1] if "#" in ref else "*"
            if ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read":
                return True
        entry_ref = str((entry or {}).get("ref", "")).strip()
        if entry_ref:
            doc = entry_ref.split("#", 1)[0]
            anchor = entry_ref.split("#", 1)[1] if "#" in entry_ref else "*"
            if ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read":
                return True
        return False

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
            elif tid in self.pd_templates:
                continue
            elif (self._pd_template_override_entries()
                  and self._page_has_pd_template_basis(page)):
                # PD 声明了模板 override 且页面登记了 product-design 依据：
                # 页面 templateId 视为 Product Design 定义的页面模板 ID，动态注册放行
                self.pd_templates[tid] = {
                    "name": str(page.get("type", "")).strip(),
                    "ref": "", "appliesTo": [],
                }
                continue
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
            if self._pd_template_for_page(page, tid) or tid in self.pd_templates:
                continue
            expected = self.type_template_map.get(ptype)
            if ptype and expected and tid != "custom" and expected != tid:
                self.add_error(pid, "TYPE_TEMPLATE_MISMATCH", "error",
                               f"$.pages[{self._idx(page)}].type",
                               f"页面 type 与 templateId 不一致: {ptype}",
                               expected, tid,
                               source_ref=self.registry.get("sourceBase", ""),
                               fix=f"将 templateId 改为 {expected} 或将 type 与模板匹配")

    def check_unregistered_type(self):
        pd_type_names = {e["name"] for e in self.pd_templates.values() if e.get("name")}
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            ptype = str(page.get("type", ""))
            tid = self.page_template(page)
            if ptype in pd_type_names or self._pd_template_for_page(page, tid):
                continue
            if ptype and ptype not in self.type_template_map and tid != "custom" and tid:
                self.add_error(pid, "UNREGISTERED_TYPE", "error",
                               f"$.pages[{self._idx(page)}].type",
                               f"使用了未注册页面类型名称: {ptype}",
                               f"已注册类型 {sorted(self.type_template_map)}", ptype,
                               source_ref=self.registry.get("sourceBase", ""),
                               fix="改用已注册页面类型，或使用 custom 模板并填写 override")

    def check_navigation_type(self):
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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

    def _page_reuse_business(self, page):
        """页面是否声明为"复用业务组件容器"（RULE-59）；声明后豁免线框/区块/组件契约等检查。"""
        return page_reuse_business(page)

    def _page_override_enabled(self, page):
        """Product Design / 用户确认的页面模板 override 是否生效。
        生效时以 Product Design 原文为准，放宽注册表结构约束（区域/顺序/必需组件），
        与 check_footer_alignment 对 footer 的处理保持一致。"""
        tc = page.get("templateContract") or {}
        ov = tc.get("override") or {}
        return bool(ov.get("enabled"))

    @staticmethod
    def _wireframe_shared_with(page):
        """页面是否声明共用其他页面的线框（RULE-62）：返回主页面 ID（wireframeSharedWith）或空串。
        声明共用的页面不重复绘制线框图，跳过全部线框结构类校验（骨架/区域/绘制质量/footer/表格/表单布局等），
        由 check_wireframe_shared 专项校验共用关系与差异描述。"""
        value = page.get("wireframeSharedWith") if isinstance(page, dict) else None
        return str(value).strip() if value else ""

    def check_skeleton_regions(self):
        """必需页面骨架区块是否存在（wireframe.regions 或 templateContract 声明）。override 生效时以 Product Design 为准，放宽。"""
        for page in self.data.get("pages", []):
            if self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._page_override_enabled(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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
            if self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._page_override_enabled(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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
            if self._page_reuse_business(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._page_override_enabled(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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
            if self._wireframe_shared_with(page):
                continue
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
            if self._wireframe_shared_with(page):
                continue
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
            # 高级搜索与独立筛选区互斥（RULE-46 扩展）：筛选已收敛进 IxProSearch/高级搜索组件时，
            # 线框图不得再单独绘制筛选区/查询区/过滤区行（平铺筛选项），避免说明书重复表达导致 Coding 重复实现
            if self._page_prosearch_filter(page):
                flat_rows = []
                for line in lines:
                    text = line.strip()
                    if not text or any(m in text.lower() for m in PROSEARCH_MARKERS):
                        continue
                    if any(k in text for k in FLAT_FILTER_LINE_KEYS):
                        flat_rows.append(text)
                if flat_rows:
                    self.add_error(pid, "WIREFRAME_PROSEARCH_FILTER_DUPLICATE", "warning",
                                   f"{ppath}.wireframe.ascii",
                                   "筛选方式为高级搜索（IxProSearch）时，线框图又单独绘制了筛选区/查询区行",
                                   "线框图只绘制高级搜索组件及其位置，筛选/搜索全部收敛在该组件内",
                                   f"出现独立筛选行 {len(flat_rows)} 处：{' / '.join(t[:30] for t in flat_rows[:3])}",
                                   fix="删除线框图中单独绘制的筛选区/查询区行，筛选项与搜索框一并收敛进高级搜索组件（组件内部字段不展开绘制）")

    def check_wireframe_flat_filter_order(self):
        """RULE-61 平铺筛选组件横向顺序（warning，仅限平铺筛选项、高级搜索页不适用）：
        Common Design 页面模板对筛选区的定义为「时间/日期范围 -> 下拉选择类 -> 搜索框」，搜索框固定最右。
        平铺筛选行内同时出现搜索框与其他筛选控件（时间范围/选择框）且搜索框排在其前时告警；
        PRD/Product Design 明确指定其他顺序时在页面 filterOrderOverride 声明后豁免。"""
        for page, ppath in self.all_pages:
            pid = page.get("id", "")
            if page.get("filterOrderOverride"):
                continue
            if self._page_prosearch_filter(page) or self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "")
            if len(ascii_text.strip()) < 8:
                continue
            for line in ascii_text.splitlines():
                text = line.strip()
                if not text or any(m in text.lower() for m in PROSEARCH_MARKERS):
                    continue
                if not any(k in text for k in FLAT_FILTER_LINE_KEYS) and not FLAT_FILTER_SEARCH_BOX_PATTERN.search(text):
                    continue
                search_hits = [m.start() for m in FLAT_FILTER_SEARCH_BOX_PATTERN.finditer(text)]
                other_pos = []
                for m in FLAT_FILTER_RANGE_PATTERN.finditer(text):
                    other_pos.append(m.start())
                for m in FLAT_FILTER_SELECT_PATTERN.finditer(text):
                    other_pos.append(m.start())
                if not search_hits or not other_pos:
                    continue
                first_search = min(search_hits)
                if first_search < max(other_pos):
                    self.add_error(pid, "WIREFRAME_FLAT_FILTER_ORDER_MISMATCH", "warning",
                                   f"{ppath}.wireframe.ascii",
                                   "平铺筛选项中搜索框排在了时间范围/选择框之前",
                                   "平铺筛选组件从左到右按「时间范围/日期范围 -> 下拉选择类 -> 搜索框」排列，搜索框固定最右",
                                   f"行「{text[:36]}」中搜索框位于其他筛选控件之前",
                                   fix="调整平铺筛选行组件顺序：搜索框移至该行最右侧（时间范围/选择框之前不得出现搜索框）；"
                                       "若 PRD 或 Product Design 明确指定其他顺序，在页面 filterOrderOverride 声明说明后豁免本检查")

    # ------------------------------------------------------------------
    # RULE-70 区域规范精读闭环 / RULE-71 表格行内操作收纳检验
    # ------------------------------------------------------------------
    REGION_TYPE_MATCHERS = {
        "table": ("表格", "table"),
        "overview": ("概览", "overview"),
        "tree": ("树", "tree"),
        "form": ("表单", "form"),
        "filter": ("筛选", "filter"),
        "steps": ("步骤", "steps"),
        "detail": ("详情", "detail"),
        "nav": ("导航", "nav"),
    }
    ACTION_OVERFLOW_DEFAULT_LIMIT = 3

    def _block_region_key(self, block):
        """按区块 type/title 推定所属区域键（table/overview/tree），未命中返回 None。"""
        text = f"{block.get('type', '')} {block.get('title', '')}".strip().lower()
        for region_key, matchers in self.REGION_TYPE_MATCHERS.items():
            for m in matchers:
                if m in text:
                    return region_key
        return None

    def _page_region_hits(self, page, contract_keys):
        """收集页面命中区域识别枚举的内容区块 {region_key: 命中标签集合}。

        触发面只取 sections 内容区块——区块是 AI 拆解设计决策的载体，其规范依据
        才需要声明与精读。wireframe.regions 的 templateRegion 属于模板必需骨架
        （由模板契约与区域绘制规则管辖），不参与依据声明触发，避免每张表格页
        都强制声明筛选/分页等骨架规范造成噪音。
        """
        hits = {}
        sections = page.get("sections")
        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue
                key = self._block_region_key(section)
                if key in contract_keys:
                    label = str(section.get("title") or section.get("type") or key).strip()
                    hits.setdefault(key, set()).add(label)
        return hits

    def _page_basis_declarations(self, page):
        """合并 designContext 与页面级 regionBasisDeclarations，按 region 分组（列表）。"""
        groups = {}
        dc = self.data.get("designContext") or {}
        for src in (dc.get("regionBasisDeclarations"), page.get("regionBasisDeclarations")):
            if not isinstance(src, list):
                continue
            for item in src:
                if not isinstance(item, dict):
                    continue
                region = str(item.get("region", "")).strip().lower()
                ref = str(item.get("ref", "")).strip()
                if region and ref:
                    groups.setdefault(region, []).append(item)
        return groups

    def check_region_basis_reading(self):
        """RULE-70 区域规范精读闭环 v2（双轨制，warning）：

        本 Skill 不维护、不预置任何规范文档路径（规范分布在 Common Design / Product Design
        多个目录且随版本演进，「读什么」的权威在实际加载的 CD/PD 内容）。判定双轨：
        1. 权威轨：区块命中区域后，查声明池（designContext 与页面级 regionBasisDeclarations
           合并）。声明池无该区域依据 -> REGION_BASIS_UNDECLARED；声明了依据但 ref 未在
           readLedger 锚点级精读命中（#* 整篇可命中）-> REGION_BASIS_UNREAD。
        2. 兜底轨：注册表 regionReadingContract 仅登记「区域识别枚举」（label/desc），
           用于命中判定与提示文案，不参与路径判定。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return  # 历史 JSON 无 designContext，不启用（不误伤）
        contract = getattr(self, "_region_read_contract", None) or {}
        if not isinstance(contract, dict):
            contract = {}
        # 区域键 = 校验器内置识别枚举 ∪ 注册表登记枚举（registry 仅兜底，可扩展）
        region_keys = set(self.REGION_TYPE_MATCHERS.keys()) | set(contract.keys())
        ledger = self._build_ledger(dc.get("readLedger"))
        src_ref = ("references/01-workflow/04-demo-output-spec.md 11.35 区域规范精读闭环（RULE-70）/"
                   " references/02-template-contracts/common-design-template-registry.json regionReadingContract")
        for page, path in self.all_pages:
            pid = page.get("id", "")
            if self._page_reuse_business(page) or self._page_override_enabled(page):
                continue
            if str(page.get("wireframeSharedFrom") or "").strip():
                continue  # 与其他页面共用线框，从页面跳过（主页面承担）
            exempt = page.get("regionBasisExempt")
            if isinstance(exempt, dict) and str(exempt.get("reason", "")).strip():
                continue
            hits = self._page_region_hits(page, region_keys)
            declared = self._page_basis_declarations(page)
            for region_key in sorted(hits.keys()):
                region_label = "、".join(sorted(hits[region_key]))
                entry = contract.get(region_key) or {}
                region_name = str(entry.get("label") or region_key)
                desc = str(entry.get("desc", "")).strip()
                decls = declared.get(region_key) or []
                if not decls:
                    self.add_error(
                        pid, "REGION_BASIS_UNDECLARED", "warning",
                        f"{path}.designContext.regionBasisDeclarations",
                        f"页面存在{region_label}区块（区域 {region_key}），但 designContext 与页面级 regionBasisDeclarations "
                        f"均未声明该区域的规范依据。本 Skill 不预置规范文档路径，须按当前实际加载的 Common Design / "
                        f"Product Design 目录确认{region_name}相关规范（{desc}），登记依据声明并精读",
                        "designContext.regionBasisDeclarations 含该区域 {region, ref, source} 声明",
                        "无该区域任何依据声明",
                        source_ref=src_ref,
                        fix=f"在 designContext.regionBasisDeclarations 补 {{region: \"{region_key}\", ref: \"<实际加载的 CD/PD 规范文档路径>#<锚点>\", source: \"common-design|product-design\"}}；"
                            "并在 designContext.readLedger 对应锚点登记 status=read；"
                            "确无对应规范或确属豁免场景时，页面声明 regionBasisExempt: {reason: \"...\"}")
                    continue
                # 逐条声明校验锚点级精读命中（#* 整篇已读覆盖任意锚点，与 RULE-43 口径一致）
                for item in decls:
                    ref = str(item.get("ref", "")).strip()
                    doc, anchor = self._norm_ref(ref)
                    hit = ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"
                    if hit:
                        continue
                    where = "readLedger 无该条目" if ledger.get((doc, anchor)) is None else f"readLedger 状态为 {ledger.get((doc, anchor))}（仅读索引）"
                    self.add_error(
                        pid, "REGION_BASIS_UNREAD", "warning",
                        f"{path}.designContext.readLedger",
                        f"页面存在{region_label}区块（区域 {region_key}），声明的规范依据「{ref}」未在 readLedger "
                        f"锚点级精读命中（{where}）。该区域规范真值未进入设计依据，编码阶段会按 AI 经验自绘",
                        f"readLedger 含 {ref} 且 status=read（#* 整篇已读可命中）",
                        f"{where}",
                        source_ref=src_ref,
                        fix=f"精读 {ref} 指向的规范小节，在 designContext.readLedger 登记 status=read；"
                            "并按精读结论修正区块设计（如操作列收纳、列配置、空态、信息层级）；"
                            "声明路径有误时更正 regionBasisDeclarations 的 ref")
                    break  # 每区域报一条，避免刷屏

    def check_action_column_overflow(self):
        """RULE-71 表格行内操作收纳检验（条件式，warning）：

        表格区块行内操作超过收纳阈值（默认 3，actionColumnLimit 可覆盖）且未声明收纳
        时提醒收敛进「更多」。本 Skill 不内置规范真值数值，阈值仅为通用提醒口径，
        真值以已读取的 Common Design 表格规范为准。
        """
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.36 表格行内操作收纳检验（RULE-71）"
        for page, path in self.all_pages:
            pid = page.get("id", "")
            if self._page_reuse_business(page) or self._page_override_enabled(page):
                continue
            if str(page.get("wireframeSharedFrom") or "").strip():
                continue
            sections = page.get("sections")
            if not isinstance(sections, list):
                continue
            for si, block in enumerate(sections):
                if not isinstance(block, dict):
                    continue
                if self._block_region_key(block) != "table":
                    continue
                if block.get("actionOverflow"):
                    continue  # 已声明收纳
                limit_raw = block.get("actionColumnLimit") or page.get("actionColumnLimit")
                try:
                    limit = int(limit_raw) if str(limit_raw or "").strip() else self.ACTION_OVERFLOW_DEFAULT_LIMIT
                except (TypeError, ValueError):
                    limit = self.ACTION_OVERFLOW_DEFAULT_LIMIT
                row_actions = block.get("rowActions")
                actions = block.get("actions") if isinstance(block.get("actions"), list) else []
                ambiguous = False
                if not isinstance(row_actions, list):
                    scope_rows = [a for a in actions
                                  if isinstance(a, dict) and str(a.get("scope", "")).strip().lower() == "row"]
                    has_scope = any(isinstance(a, dict) and str(a.get("scope", "")).strip() for a in actions)
                    if has_scope:
                        row_actions = scope_rows  # 已显式区分：只统计行内操作
                    else:
                        row_actions = actions  # 启发式：未区分 scope 时以区块操作总数判定并提示
                        ambiguous = True
                count = len(row_actions or [])
                if count <= limit:
                    continue
                wireframe = page.get("wireframe") or {}
                haystack = " ".join([
                    str(wireframe.get("ascii", "") or ""),
                    str(block.get("description", "") or ""),
                    " ".join(str(x) for x in (block.get("interactionNotes") or []) if isinstance(x, str)),
                ])
                if "更多" in haystack:
                    continue  # 已有收纳痕迹
                # ambiguous 已在上方按声明情况判定
                scope_hint = ("当前区块未声明 rowActions 也未在 actions 上标记 scope，无法区分工具栏操作与行内操作，"
                              "请用 rowActions 数组或 actions[].scope=row/toolbar 显式区分；"
                              if ambiguous else "")
                self.add_error(
                    pid, "ACTION_COLUMN_OVERFLOW", "warning",
                    f"{path}.sections[{si}]",
                    f"表格区块「{block.get('title', '')}」行内操作数量为 {count}，超过收纳阈值 {limit}，"
                    "未发现收纳痕迹。按已读取的 Common Design 表格规范，超出阈值的行内操作应收纳进「更多」；"
                    "平铺过多行内操作会导致列宽挤压、操作溢出换行",
                    f"行内操作 <= {limit} 个，或声明 actionOverflow=true / 线框与说明含「更多」收纳",
                    f"行内操作 {count} 个且无收纳声明",
                    source_ref=src_ref,
                    fix=scope_hint +
                        "按已精读的 Common Design 表格规范收纳超出部分进「更多」（区块声明 actionOverflow: true 并在线框绘制「更多」）；"
                        "若业务确需全部平铺，将区块 actionColumnLimit 设为实际值并说明依据")

    # ------------------------------------------------------------------
    # RULE-69 概览区形态还原闭环
    # ------------------------------------------------------------------
    OVERVIEW_SECTION_KEYS = ("概览", "统计", "overview", "指标")

    def _overview_variants_for(self, template_id):
        """返回模板登记的 overviewVariants（无则 None）。"""
        template = self._effective_template(template_id) or {}
        variants = template.get("overviewVariants")
        return variants if isinstance(variants, dict) else None

    def _page_overview_blocks(self, page):
        """收集页面的概览区块：type/title 命中概览语义，或声明了 overviewStyle/overviewMetrics 的区块。"""
        blocks = []
        for i, section in enumerate(page.get("sections") or []):
            if not isinstance(section, dict):
                continue
            type_text = str(section.get("type") or "").lower()
            title_text = str(section.get("title") or "").lower()
            hit = (any(k.lower() in type_text for k in self.OVERVIEW_SECTION_KEYS)
                   or any(k.lower() in title_text for k in self.OVERVIEW_SECTION_KEYS)
                   or section.get("overviewStyle") or section.get("overviewMetrics"))
            if hit:
                blocks.append((i, section))
        return blocks

    def check_overview_style(self):
        """RULE-69 概览区形态还原闭环（条件式）：
        页面 templateId 命中注册表含 overviewVariants 的模板（概览表格页/概览左树表格页），
        或 regions 含 overview 区域时启用。概览区块必须声明 overviewStyle（注册表形态 id）
        与 overviewMetrics（指标数组），线框图按形态绘制痕迹。"""
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.34 概览区形态还原闭环（RULE-69）"
        for page, ppath in self.all_pages:
            if self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
            if self._page_override_enabled(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            variants = self._overview_variants_for(tid)
            wf = self.page_wireframe(page)
            regions = (wf or {}).get("regions") or [] if isinstance(wf, dict) else []
            region_triggered = any(
                isinstance(r, dict) and str(r.get("templateRegion") or "") == "overview"
                for r in regions)
            if not variants and not region_triggered:
                continue
            blocks = self._page_overview_blocks(page)
            declared_styles = []
            has_overview_block = bool(blocks)
            for bi, block in blocks:
                style = str(block.get("overviewStyle") or "").strip()
                metrics = block.get("overviewMetrics") or []
                exempt = page.get("overviewStyleExempt")
                if style:
                    style_ids = {str(s.get("id") or "").strip()
                                 for s in (variants or {}).get("styles", []) if isinstance(s, dict)}
                    if not style_ids or style not in style_ids:
                        valid = "、".join(sorted(v for v in style_ids if v)) or "该模板未登记 overviewVariants（禁止声明形态值）"
                        self.add_error(pid, "OVERVIEW_STYLE_INVALID", "error",
                                       f"{ppath}.sections[{bi}].overviewStyle",
                                       f"概览区块声明的 overviewStyle「{style}」不在模板 {tid} 登记的形态枚举内",
                                       f"形态枚举（以精读 Common Design 模板原文为准）：{valid}",
                                       f"声明值 {style}",
                                       source_ref=src_ref,
                                       fix=f"将 overviewStyle 改为模板 {tid} overviewVariants.styles 中登记的形态 id，形态枚举以精读 Common Design 模板文档原文为准，禁止凭经验新增")
                    else:
                        declared_styles.append((bi, style, block))
                else:
                    declared_styles.append((bi, "", block))
                # overviewMetrics 项审计
                if isinstance(metrics, list):
                    for mi, metric in enumerate(metrics):
                        if not isinstance(metric, dict):
                            self.add_error(pid, "OVERVIEW_METRIC_COMPONENT_MISSING", "warning",
                                           f"{ppath}.sections[{bi}].overviewMetrics[{mi}]",
                                           "overviewMetrics 项必须是对象（含 name/iduxComponent/description）",
                                           "对象：指标名+展示形式+组件+说明", f"实际值类型 {type(metric).__name__}",
                                           source_ref=src_ref,
                                           fix="为指标项补齐 name/display/iduxComponent/description 字段")
                            continue
                        missing = [k for k in ("name", "iduxComponent", "description") if not str(metric.get(k) or "").strip()]
                        if missing:
                            self.add_error(pid, "OVERVIEW_METRIC_COMPONENT_MISSING", "warning",
                                           f"{ppath}.sections[{bi}].overviewMetrics[{mi}]",
                                           f"概览指标「{str(metric.get('name') or '未命名')[:20]}」缺 {('、'.join(missing))} 声明",
                                           "每项指标声明 name/display/iduxComponent/description（图表形态须声明维度与图例）",
                                           f"缺失字段：{'、'.join(missing)}",
                                           source_ref=src_ref,
                                           fix="补齐指标组件与说明；图表组件名以已读取 Common Design 组件映射表为准，本 Skill 不保存组件映射清单")
            # 图表形态痕迹校验：声明 chart 形态但 ascii 检索不到形态名
            if wf and isinstance(wf, dict):
                ascii_text = str(wf.get("ascii") or "")
                variants_ascii = " ".join(str((v or {}).get("ascii") or "") for v in (wf.get("variants") or []) if isinstance(v, dict))
                ascii_blob = ascii_text + " " + variants_ascii
                style_meta = {str(s.get("id") or "").strip(): s
                              for s in (variants or {}).get("styles", []) if isinstance(s, dict)}
                for bi, style, block in declared_styles:
                    meta = style_meta.get(style) or {}
                    if str(meta.get("drawKind") or "") != "chart":
                        continue
                    style_name = str(meta.get("name") or "").strip()
                    if not style_name:
                        continue
                    if style_name not in ascii_blob:
                        self.add_error(pid, "OVERVIEW_CHART_STYLE_NOT_DRAWN", "warning",
                                       f"{ppath}.wireframe.ascii",
                                       f"概览区块声明了图表形态「{style_name}」，但线框图概览区未绘制该形态痕迹",
                                       f"概览区画图表占位框并标注形态（如 [{style_name}：维度名]），占位提示：{str(meta.get('drawHint') or '')[:60]}",
                                       f"ascii 概览区未出现「{style_name}」标注",
                                       source_ref=src_ref,
                                       fix=f"在线框图概览区绘制 [{style_name}：维度名] 图表占位框（或补充形态标注文字）")
            # 形态缺失告警：启用页面存在概览区块但均未声明 overviewStyle
            if has_overview_block and not page.get("overviewStyleExempt"):
                if all(not str(b.get("overviewStyle") or "").strip() for _, b in blocks):
                    self.add_error(pid, "OVERVIEW_STYLE_MISSING", "warning",
                                   f"{ppath}.sections",
                                   "概览页面的概览区块均未声明 overviewStyle（概览形态信息缺失）",
                                   "概览区块声明 overviewStyle（stat-number/pie-chart/line-chart/bar-chart 等注册表登记形态）与 overviewMetrics，供 AI Coding 还原 Common Design 概览样式",
                                   "无任何概览形态声明，AI Coding 只能自绘通用卡片",
                                   source_ref=src_ref,
                                   fix="为概览区块补充 overviewStyle 与 overviewMetrics（形态枚举取注册表 overviewVariants.styles 的 id，以精读 Common Design 模板原文为准）；确不适用时在页面 overviewStyleExempt 声明理由")

    @staticmethod
    def _page_prosearch_filter(page):
        """判断页面筛选组件是否声明为高级搜索（IxProSearch/高级搜索）。"""
        texts = []
        cc = (page.get("templateContract") or {}).get("componentContract") or {}
        texts.extend(walk_text(cc.get("patternComponents") or []))
        for item in (page.get("codingGuide") or {}).get("pageItems") or []:
            if isinstance(item, dict) and str(item.get("scope", "")) == "filter":
                texts.append(str(item.get("name", "")))
                texts.append(str(item.get("description", "")))
        for section in page.get("sections") or []:
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", ""))
            if "筛选" in title or "搜索" in title or "查询" in title:
                texts.append(title)
                texts.append(str(section.get("componentName", "")))
                texts.append(str(section.get("component", "")))
                texts.append(str(section.get("informationPurpose", "")))
                texts.append(str(section.get("description", "")))
        blob = " ".join(texts).lower()
        return any(m in blob for m in PROSEARCH_MARKERS)

    def check_section_wireframe_consistency(self):
        for page in self.data.get("pages", []):
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._wireframe_shared_with(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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
            if not tid or not tid.startswith(("page-table", "list-")):
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
            if self._page_reuse_business(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._wireframe_shared_with(page):
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
            if self._page_reuse_business(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            if self._wireframe_shared_with(page):
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
            if tid.startswith("list-") and not has_semantic(regions, ["object", "上下文", "对象"]):
                self.add_error(pid, "DRAWER_OBJECT_CONTEXT_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "列表抽屉缺少对象上下文", "包含对象上下文", "缺失",
                               fix="在 wireframe 中补充 object-context 区域")
            if not has_semantic(regions, ["close", "关闭", "取消"]):
                self.add_error(pid, "DRAWER_CLOSE_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "抽屉类页面缺少关闭入口", "包含关闭入口", "缺失",
                               fix="在 wireframe 中补充关闭入口")
            if tid.startswith("list-") and not has_semantic(regions, ["table", "表格", "列表"]):
                self.add_error(pid, "DRAWER_LIST_MISSING", "error",
                               f"$.pages[{self._idx(page)}].wireframe.regions",
                               "列表抽屉缺少列表主体", "包含列表主体", "缺失",
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
            template = self._effective_template(tid)
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
            if self._page_reuse_business(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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
            if self._page_reuse_business(page):
                continue
            if page.get("id") in self._legacy_page_ids:
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid)
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
            if self._wireframe_shared_with(page):
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
            if self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
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
            template = self._effective_template(tid) or {}
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
            if self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
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
            if self._wireframe_shared_with(page):
                continue
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
        """RULE-36 字段完整性闭环：需求/规范明确要求的字段必须落入对应字段数组（表格列/表单项/筛选项/详情描述字段）、
        excludedFields 排除声明，或 mergedFields 合并承载声明（覆盖是包含关系而非一一对应：
        需求配置项可经设计手法合并承载，如地理位置级联、执行周期复合配置）。"""
        for page in self.data.get("pages", []):
            pid = page.get("id", "")
            required = page.get("requirementFieldNames") or []
            if not required:
                continue
            excluded = page.get("excludedFields") or {}
            merged = page.get("mergedFields") if isinstance(page.get("mergedFields"), dict) else {}
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
                # mergedFields 合并承载声明：into（字符串或字符串数组）须全部命中真实落位字段
                entry = merged.get(n)
                if isinstance(entry, dict) and str(entry.get("note", "")).strip():
                    raw_into = entry.get("into")
                    if isinstance(raw_into, str):
                        into_list = [raw_into.strip()] if raw_into.strip() else []
                    elif isinstance(raw_into, (list, tuple)):
                        into_list = [str(x).strip() for x in raw_into if str(x).strip()]
                    else:
                        into_list = []
                    if into_list and all(t in covered for t in into_list):
                        continue  # 合并目标全部真实落位，覆盖成立
                    self.add_error(
                        pid, "MERGED_FIELD_TARGET_MISSING", "warning",
                        f"$.pages[{self._idx(page)}].mergedFields.{n}.into",
                        f"字段 {n} 的 mergedFields 合并声明无效：into 目标 "
                        f"{'、'.join(into_list) if into_list else '缺失或为空'}"
                        f"未全部命中本页面实际落位字段数组（{'、'.join(sorted(covered)) or '无任何落位字段'}）",
                        "into 指向的字段必须真实出现在本页面 tableFields/formFields/filterFields/cardFields/fields/detailFields 中，且不指向 excludedFields 排除的字段",
                        f"声明的 into：{'、'.join(into_list) if into_list else '（空）'}",
                        fix="修正 into 为实际落位字段名（合并目标须真实存在），或拆回独立配置项落入字段数组，或确属不展示时改用 excludedFields 并说明原因")
                missing.append(n)
            if missing:
                self.add_error(pid, "REQUIRED_FIELD_MISSING", "error",
                               f"$.pages[{self._idx(page)}].requirementFieldNames",
                               f"需求明确要求的字段未落入设计说明书：{'、'.join(missing)}",
                               "需求/规范明确列出的每个字段都出现在对应区块的字段数组（表格列/表单项/筛选项/详情字段）中，或写入 excludedFields 并说明排除原因",
                               f"缺失字段：{'、'.join(missing)}",
                               fix="将缺失字段补充到对应区块的字段数组（tableFields/formFields/filterFields/cardFields/fields等），字段经设计手法合并承载时（如地理位置级联、执行周期复合配置）在页面 mergedFields 登记合并声明（into 指向实际落位字段 + note 说明手法，覆盖为包含关系无需一一对应），若该页面确实不展示则写入 excludedFields 并说明原因")

    def _collect_option_fields(self, page):
        """收集页面各字段数组中的字段，返回 [(name, array_key, field_dict)]。"""
        index = []
        arrays = ("formFields", "filterFields", "tableFields", "columns",
                  "cardFields", "fields", "detailFields")

        def collect(container):
            for key in arrays:
                for field in container.get(key) or []:
                    if isinstance(field, dict) and field.get("name"):
                        index.append((str(field["name"]).strip(), key, field))

        for section in self.page_sections(page):
            if isinstance(section, dict):
                collect(section)
        collect(page)
        return index

    @staticmethod
    def _match_option_fields(index, field_name):
        """按字段名匹配字段（精确或双向包含，避免命名略有差异时漏配）。"""
        target = norm(field_name)
        matched = []
        for name, key, field in index:
            current = norm(name)
            if current == target or (
                len(target) >= 2 and len(current) >= 2
                and (target in current or current in target)
            ):
                matched.append((key, field))
        return matched

    @staticmethod
    def _normalize_options(value):
        """把选项声明归一化为字符串列表（字符串按常见分隔符拆分）。"""
        if value is None:
            return []
        if isinstance(value, str):
            return [p.strip() for p in re.split(r"[/、,，;；\n]+", value) if p.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(v).strip() for v in value if str(v).strip()]
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def _option_cell_text(matched):
        """取字段渲染出的选项单元格文本（表单 rules/tips，筛选 options/description）。"""
        parts = []
        for key, field in matched:
            for cell_key in OPTION_CELL_KEYS.get(key, DEFAULT_OPTION_CELL_KEYS):
                value = field.get(cell_key)
                if not _has_text_value(value):
                    continue
                if isinstance(value, (list, tuple, set)):
                    parts.extend(str(v) for v in value)
                else:
                    parts.append(str(value))
        return "\n".join(parts)

    def _option_dimension(self, item):
        """声明项的有效维度：显式 dimension 优先；否则 sourceColumns >=2 列视为 group；缺省 flat。"""
        raw = str(item.get("dimension") or "").strip().lower()
        dim = OPTION_DIMENSION_SYNONYMS.get(raw, "")
        if dim:
            return dim
        cols = item.get("sourceColumns")
        if isinstance(cols, str):
            cols = [c for c in re.split(r"[、,，/;；|]", cols) if c.strip()]
        if isinstance(cols, (list, tuple)) and len([c for c in cols if str(c).strip()]) >= 2:
            return "group"
        return "flat"

    def _has_option_dimension_trait(self, text):
        """选项单元格是否保留了分组/层级维度痕迹（弱校验，仅用结构痕迹，不做形态名映射）。"""
        raw = str(text or "")
        if not raw.strip():
            return False
        cleaned = re.sub(r"^\s*(选项|可选值|选项范围|取值范围|枚举值)\s*[:：]\s*", "", raw)
        if any(marker in cleaned for marker in OPTION_DIMENSION_MARKERS):
            return True
        if re.search(OPTION_DIMENSION_ARROW_PATTERN, cleaned):
            return True
        if re.search(OPTION_DIMENSION_GROUP_PATTERN, cleaned):
            return True
        if len([ln for ln in cleaned.splitlines() if re.search(r"[:：]", ln)]) >= 2:
            return True
        return False

    def check_option_completeness(self):
        """RULE-48 下拉选项完整性（条件式，页面声明 requirementOptionSets 时启用）。

        - 声明的每个固定选项必须逐项出现在该字段的选项单元格（表单 rules / 筛选 options）；
          缺失阻断（REQUIRED_OPTION_MISSING），声明字段不存在阻断（OPTION_FIELD_NOT_FOUND）。
        - 未声明选项集的选择类字段，选项单元格出现 等/例如/如：/… 截断指纹时告警
          （OPTION_TRUNCATION_MARKER），提示"可能只举例未列全"。
        """
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            index = self._collect_option_fields(page)
            declared = page.get("requirementOptionSets") or []
            covered = set()
            for oi, item in enumerate(declared):
                opath = f"{path}.requirementOptionSets[{oi}]"
                if not isinstance(item, dict):
                    self.add_error(pid, "OPTION_SET_INVALID", "warning", opath,
                                   "选项集声明项必须是对象（{field, options}）",
                                   "对象", type(item).__name__,
                                   source_ref=RULE48_SOURCE,
                                   fix="改为 {\"field\": \"字段名\", \"options\": [\"选项1\", \"选项2\"]}")
                    continue
                fname = str(item.get("field") or item.get("name") or "").strip()
                options = self._normalize_options(item.get("options"))
                if not fname or not options:
                    self.add_error(pid, "OPTION_SET_INCOMPLETE", "warning", opath,
                                   "选项集声明缺少 field 或 options",
                                   "field 与 options 均非空",
                                   f"field={fname!r}, options={options}",
                                   source_ref=RULE48_SOURCE,
                                   fix="补齐字段名与完整选项列表（options 为数组）")
                    continue
                matched = self._match_option_fields(index, fname)
                if not matched:
                    self.add_error(pid, "OPTION_FIELD_NOT_FOUND", "error", opath,
                                   f"选项集声明的字段未出现在页面任何字段数组：{fname}",
                                   "字段出现在 formFields/filterFields 等字段数组中",
                                   "未找到",
                                   source_ref=RULE48_SOURCE,
                                   fix="将字段补入对应区块字段数组，或修正字段名")
                    continue
                covered.add(norm(fname))
                tokens = option_tokens(self._option_cell_text(matched))
                missing = [o for o in options if norm(o) and norm(o) not in tokens]
                if missing:
                    self.add_error(pid, "REQUIRED_OPTION_MISSING", "error", opath,
                                   f"字段「{fname}」的固定选项未完整落入选项单元格：{'、'.join(missing)}",
                                   "声明选项全部逐项出现在表单选项/规则(rules)或筛选选项范围(options)单元格中",
                                   f"缺失选项：{'、'.join(missing)}",
                                   source_ref=RULE48_SOURCE,
                                   fix="把缺失选项逐项补进该字段的 rules（表单）或 options（筛选）单元格，完整列出，禁止只举例")
                # 维度保留（RULE-48）：源枚举表含分组/层级列时，选项单元格必须保留该维度，禁止压平
                dim = self._option_dimension(item)
                if dim != "flat":
                    cell = self._option_cell_text(matched)
                    if not self._has_option_dimension_trait(cell):
                        dim_label = "分组" if dim == "group" else "层级"
                        self.add_error(pid, "OPTION_DIMENSION_LOST", "warning", opath,
                                       f"字段「{fname}」的选项集声明了「{dim_label}」维度（dimension={dim}），但选项单元格被压成单层列表，未保留该维度",
                                       "选项单元格保留分组/层级结构痕迹（如“组名：选项A/选项B”或“父级 → 子级”）",
                                       cell.strip()[:80],
                                       source_ref=RULE48_SOURCE,
                                       fix="按需求源枚举表保留维度：分组写成“组名：选项A/选项B/…”，层级写成“父级 → 子级”或用分组标签表达；承载该维度的控件形态按 RULE-54 由 Common Design widget patterns 判定并登记依据，禁止把分组/层级压平为单层列表")
            self._check_option_truncation(pid, path, index, covered)

    def _check_option_truncation(self, pid, path, index, covered):
        """未声明选项集的选择类字段：选项单元格命中截断指纹时告警。"""
        seen = set()
        for name, key, field in index:
            if key not in ("formFields", "filterFields"):
                continue
            if norm(name) in covered:
                continue
            comp = " ".join(str(field.get(k, "")) for k in ("component", "iduxComponent")).lower()
            if not any(token in comp for token in SELECT_COMPONENT_KEYS):
                continue
            cell = self._option_cell_text([(key, field)])
            if not cell:
                continue
            for pattern in OPTION_TRUNCATION_PATTERNS:
                if re.search(pattern, cell, re.MULTILINE):
                    marker = name + "\u0000" + cell
                    if marker in seen:
                        break
                    seen.add(marker)
                    self.add_error(pid, "OPTION_TRUNCATION_MARKER", "warning",
                                   f"{path}.sections[].{key}",
                                   f"字段「{name}」的固定选项疑似只举例未列全（命中截断标记：{pattern}）",
                                   "固定选项型字段需逐项完整列出，禁止使用 等/例如/如：/… 等截断表达",
                                   cell,
                                   source_ref=RULE48_SOURCE,
                                   fix="把全部选项逐项写进选项单元格，或在 requirementOptionSets 中声明该字段的完整选项集")
                    break

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
            if (tid and "detail" in tid.lower()) or "详情" in ptype:
                ids.append(cid)
        return ids

    # ---- 详情页字段去重（RULE-49，条件式，仅详情类页面）----
    def _is_detail_page(self, page):
        """详情类页面判定：type 含“详情”或 templateId 含 detail。"""
        t = str(page.get("type", ""))
        tid = self.page_template(page) or ""
        return ("详情" in t) or ("detail" in tid.lower())

    @staticmethod
    def _classify_detail_section(section):
        """区块归类：'skip'（历史/日志/记录，优先）/ 'description'（字段展示列表）/ 'summary'（对象摘要/摘要卡片）/ None。"""
        traw = str(section.get("type", "")).strip().lower()
        title = str(section.get("title", "")).strip().lower()
        combos = [h for h in (traw, title) if h]
        for h in combos:
            if any(kw in h for kw in DETAIL_DEDUP_SKIP_SECTION_TYPES):
                return "skip"
        for h in combos:
            if any(kw in h for kw in DETAIL_DESCRIPTION_SECTION_TYPES):
                return "description"
        for h in combos:
            if any(kw in h for kw in DETAIL_SUMMARY_SECTION_TYPES):
                return "summary"
        return None

    @staticmethod
    def _detail_field_name(item):
        """从字段项取字段名：dict 取 name；字符串取冒号前的名称部分。"""
        if isinstance(item, dict):
            nm = item.get("name")
            return str(nm).strip() if nm else ""
        if isinstance(item, str):
            s = item.strip()
            for sep in ("：", ":"):
                if sep in s:
                    s = s.split(sep, 1)[0].strip()
                    break
            return s
        return ""

    def _detail_section_names(self, section, keys):
        names = []
        for k in keys:
            for item in section.get(k) or []:
                nm = self._detail_field_name(item)
                if nm:
                    names.append(nm)
        return names

    def _detail_name_list(self, value):
        names = []
        if isinstance(value, (list, tuple, set)):
            for v in value:
                nm = self._detail_field_name(v)
                if nm:
                    names.append(nm)
        elif value is not None:
            nm = self._detail_field_name(value)
            if nm:
                names.append(nm)
        return names

    def _detail_exempt_names(self, page):
        exempt = set()
        for src in (page.get("excludedFields"), page.get("detailDedupExempt")):
            if isinstance(src, dict):
                exempt.update(norm(k) for k in src.keys())
            elif isinstance(src, (list, tuple, set)):
                exempt.update(norm(str(k)) for k in src)
        return exempt

    def check_detail_field_dedup(self):
        """RULE-49 详情页字段去重（条件式，仅详情类页面）。

        - 概览卡片/对象摘要已展示字段不应在详情描述列表重复：
          声明 detailSummaryFields 时以其为准，未声明时以 cardFields 与摘要型区块兜底；
          命中即 warning DETAIL_FIELD_DUPLICATE。
        - 同一详情描述列表区块内字段名重复：error DETAIL_FIELD_DUPLICATED_IN_LIST。
        - 豁免：excludedFields 与页面级 detailDedupExempt；历史/日志/记录类区块与表格字段不参与。
        """
        for page, path in self.all_pages:
            if not self._is_detail_page(page):
                continue
            pid = str(page.get("id", ""))
            sections = self.page_sections(page)
            exempt = self._detail_exempt_names(page)

            # ---- Zone B：详情描述列表字段（并检测同一描述列表内重复）----
            zone_b = {}
            for si, section in enumerate(sections):
                if not isinstance(section, dict):
                    continue
                if self._classify_detail_section(section) != "description":
                    continue
                counts = {}
                for nm in self._detail_section_names(section, DETAIL_FIELD_ARRAYS):
                    n = norm(nm)
                    if not n or n in exempt:
                        continue
                    counts.setdefault(n, []).append(nm)
                    zone_b.setdefault(n, nm)
                for n, lst in counts.items():
                    if len(lst) > 1:
                        self.add_error(pid, "DETAIL_FIELD_DUPLICATED_IN_LIST", "error",
                                       f"{path}.sections[{si}]",
                                       f"详情描述列表内字段「{lst[0]}」重复出现 {len(lst)} 次",
                                       "同一详情描述列表内字段名唯一",
                                       f"重复 {len(lst)} 次",
                                       source_ref=RULE49_SOURCE,
                                       fix="删除描述列表中重复的字段项，同一字段只保留一项")
            for item in page.get("detailFields") or []:
                nm = self._detail_field_name(item)
                n = norm(nm)
                if n and n not in exempt:
                    zone_b.setdefault(n, nm)
            if not zone_b:
                continue

            # ---- Zone A：概览卡片/对象摘要字段（declared detailSummaryFields 优先，cardFields 兜底）----
            declared = self._detail_name_list(page.get("detailSummaryFields"))
            zone_a = []
            if declared:
                zone_a = [d for d in declared if norm(d) not in exempt]
            else:
                for item in page.get("cardFields") or []:
                    nm = self._detail_field_name(item)
                    if nm and norm(nm) not in exempt:
                        zone_a.append(nm)
                for section in sections:
                    if not isinstance(section, dict):
                        continue
                    for nm in self._detail_section_names(section, ("cardFields",)):
                        if norm(nm) not in exempt:
                            zone_a.append(nm)
                    if self._classify_detail_section(section) == "summary":
                        for nm in self._detail_section_names(section, ("fields", "detailFields")):
                            if norm(nm) not in exempt:
                                zone_a.append(nm)

            if not zone_a:
                continue

            # ---- 求交集：概览卡片字段在描述列表重复出现 ----
            reported = set()
            for nm in zone_a:
                n = norm(nm)
                if n and n in zone_b and n not in reported:
                    reported.add(n)
                    self.add_error(pid, "DETAIL_FIELD_DUPLICATE", "warning",
                                   f"{path}.detailSummaryFields",
                                   f"概览卡片/对象摘要已展示字段「{nm}」在详情描述列表重复出现",
                                   "概览卡片/对象摘要已展示的字段不在详情描述列表重复",
                                   f"字段：{nm}",
                                   source_ref=RULE49_SOURCE,
                                   fix="从详情描述列表移除该字段（概览卡片已承载）；若确为有意重复，写入 page.detailDedupExempt 并说明原因")

    # ---- 按钮/可点击操作表（RULE-50）----
    def _action_rules_for(self, page):
        """合并 spec 级与页面级 actionRules 配置（高影响操作/关键词/豁免，均为扩展）。"""
        merged = {"highImpactActions": [], "highImpactKeywords": [], "exempt": []}
        sources = []
        if isinstance(self.data, dict):
            sources.append(self.data.get("actionRules"))
        sources.append(page.get("actionRules"))
        for spec in sources:
            if isinstance(spec, dict):
                for key in merged:
                    value = spec.get(key)
                    if isinstance(value, (list, tuple)):
                        merged[key].extend(str(v) for v in value)
        return merged

    @staticmethod
    def _action_text(value):
        if isinstance(value, (list, tuple)):
            return "；".join(str(v) for v in value)
        return str(value or "")

    def _is_high_impact_action(self, name, row, rules):
        if str(row.get("impact", "")).strip().lower() == "high" or row.get("confirm") is True:
            return True
        if name in set(DEFAULT_HIGH_IMPACT_ACTIONS) | set(rules["highImpactActions"]):
            return True
        keywords = list(DEFAULT_HIGH_IMPACT_KEYWORDS) + list(rules["highImpactKeywords"])
        return any(kw and kw in name for kw in keywords)

    def check_action_table(self):
        """RULE-50 按钮/可点击操作表（条件式）。

        高影响操作 / 二次确认 / 局部面板须写清触发方式、组件与文案或字段：
        - 高影响操作（自动识别 + actionRules 可配置）缺文案 -> error（ACTION_CONFIRM_TEXT_MISSING）；
        - 涉及二次确认/局部面板但缺组件、或声明组件却既无文案也无字段 -> warning；
        - 提供组件/文案但未标注来源、标为 ai-fill、来源锚点缺失或取值非法 -> warning（ACTION_SOURCE_NOT_TRACED），
          组件与文案须取自 Product Design 或 Common Design 的 pattern，Product Design 优先，禁止 AI 自拟；
        - 旧字符串写法（actions 为字符串列表）保持兼容，不参与本规则。
        """
        for page, path in self.all_pages:
            pid = str(page.get("id", ""))
            rules = self._action_rules_for(page)
            exempt = {norm(x) for x in rules["exempt"]}
            for si, section in enumerate(self.page_sections(page)):
                if not isinstance(section, dict):
                    continue
                actions = section.get("actions")
                if not isinstance(actions, (list, tuple)):
                    continue
                for ai, item in enumerate(actions):
                    if not isinstance(item, dict):
                        continue
                    self._check_action_row(pid, path, si, ai, item, rules, exempt)

    def _check_action_row(self, pid, path, si, ai, row, rules, exempt):
        loc = f"{path}.sections[{si}].actions[{ai}]"
        name = str(row.get("name") or row.get("action") or row.get("label") or "").strip()
        if not name:
            self.add_error(pid, "ACTION_NAME_MISSING", "warning", loc,
                           "按钮/可点击操作行缺少操作名称",
                           "每行须写明操作名称（如 删除/禁用/移动）",
                           "name 为空", source_ref=RULE50_SOURCE,
                           fix="补写操作名称")
            return
        if norm(name) in exempt:
            return
        trigger = str(row.get("trigger") or row.get("confirmType") or row.get("mode") or "")
        component = str(row.get("component") or row.get("iduxComponent") or row.get("componentName") or "").strip()
        text = str(row.get("text") or row.get("copy") or "").strip()
        fields = self._action_text(row.get("fields")).strip()
        high = self._is_high_impact_action(name, row, rules)
        need_confirm = high or bool(component) or bool(fields) or any(k in trigger for k in ACTION_CONFIRM_TRIGGER_KEYWORDS)
        if high and not text:
            self.add_error(pid, "ACTION_CONFIRM_TEXT_MISSING", "error", loc,
                           f"高影响操作「{name}」缺少二次确认文案（标题+正文）",
                           "高影响操作必须写明确认弹窗/面板文案，且文案优先取 Product Design、其次 Common Design，禁止 AI 自拟",
                           "文案为空", source_ref=RULE50_SOURCE,
                           fix="补充确认文案（如“确认删除吗？删除后，数据不可恢复，请谨慎操作。”）并标注来源")
        if need_confirm and not component:
            self.add_error(pid, "ACTION_COMPONENT_MISSING", "warning", loc,
                           f"操作「{name}」涉及二次确认或局部面板但未写明使用组件",
                           "写明组件名（标准确认弹窗/自定义弹窗/局部面板等），组件优先取 Product Design、其次 Common Design",
                           "组件为空", source_ref=RULE50_SOURCE,
                           fix="补充使用组件；组件来源优先 Product Design，未定义时回退 Common Design")
        if component and not text and not fields:
            self.add_error(pid, "ACTION_CONTENT_MISSING", "warning", loc,
                           f"操作「{name}」声明了弹窗/面板组件，但既无文案也未列字段",
                           "写明弹窗/面板的确认文案，或列出其中字段/组件（如“选择框 + 之前/之后 下拉框”）",
                           "文案与字段均为空", source_ref=RULE50_SOURCE,
                           fix="补充文案或面板/弹窗内的字段与组件")
        if component or text or fields:
            self._check_action_source(pid, loc, name, row)

    def _check_action_source(self, pid, loc, name, row):
        source = str(row.get("source") or row.get("designSource") or "").strip()
        if not source:
            self.add_error(pid, "ACTION_SOURCE_NOT_TRACED", "warning", loc,
                           f"操作「{name}」的组件/文案未标注设计来源",
                           "组件与文案必须取自 Product Design 或 Common Design 的 pattern（Product Design 优先），禁止 AI 自拟",
                           "source 为空", source_ref=RULE50_SOURCE,
                           fix="标注 source（product-design/common-design/requirement/code）并在来源文档中定位组件与文案")
        elif source == "ai-fill":
            self.add_error(pid, "ACTION_SOURCE_NOT_TRACED", "warning", loc,
                           f"操作「{name}」的组件/文案标注为 ai-fill",
                           "组件与文案不得由 AI 自拟，须取自 Product Design 或 Common Design 的 pattern（Product Design 优先）",
                           "source=ai-fill", source_ref=RULE50_SOURCE,
                           fix="改为 Product Design / Common Design 来源并登记锚点；确认设计库无覆盖时再保留 ai-fill 并转待确认问题")
        elif source not in SOURCE_LABELS:
            self.add_error(pid, "ACTION_SOURCE_NOT_TRACED", "warning", loc,
                           f"操作「{name}」的设计来源取值非法：{source}",
                           "来源取值限 requirement / product-design / common-design / code / ai-fill",
                           f"source={source}", source_ref=RULE50_SOURCE,
                           fix="改用合法来源标记")
        elif source in ("common-design", "product-design") and not str(row.get("sourceRef") or "").strip():
            self.add_error(pid, "ACTION_SOURCE_NOT_TRACED", "warning", loc,
                           f"操作「{name}」声明了设计来源但未给出可定位锚点",
                           f"{source} 来源须给出可定位引用（格式：<文档路径>#<章节/模板条目>）",
                           "sourceRef 为空", source_ref=RULE50_SOURCE,
                           fix="补写 sourceRef 指向来源文档原文锚点（Product Design 优先于 Common Design）")

    # ---- 表格区按钮位置（RULE-51，线框图）----
    def check_table_button_placement(self):
        """RULE-51 表格区按钮位置（线框图，warning）：表格关联按钮（批量操作、子功能入口等）
        必须统一置于表格区左上角工具栏；绘制在表格框下方或表格工具栏之外的区域时提示。"""
        for page, path in self.all_pages:
            if self._wireframe_shared_with(page):
                continue
            pid = str(page.get("id", ""))
            wf = page.get("wireframe")
            if not isinstance(wf, dict):
                continue
            ascii_sources = [(f"{path}.wireframe.ascii", str(wf.get("ascii") or ""))]
            for vi, variant in enumerate(wf.get("variants") or []):
                if isinstance(variant, dict) and variant.get("ascii"):
                    ascii_sources.append((f"{path}.wireframe.variants[{vi}].ascii", str(variant["ascii"])))
            for apath, text in ascii_sources:
                if len(text.strip()) < 8:
                    continue
                lines = text.splitlines()
                box = _find_ascii_table_box(lines)
                if not box:
                    continue
                top, bottom = box
                # 1) 表格关联按钮绘制在表格框下方（列设置/列配置属组件自带功能，交由判定3统一提示）
                for idx in range(bottom + 1, len(lines)):
                    raw = lines[idx]
                    if any(kw in raw for kw in COLUMN_SETTING_DRAWN_KEYWORDS):
                        continue
                    hits = _table_button_keywords_in(raw)
                    if not hits:
                        continue
                    if _ascii_line_is_pagination_or_footer(raw, True):
                        continue
                    self.add_error(pid, "TABLE_BUTTON_MISPLACED", "warning", apath,
                                   f"表格关联按钮绘制在表格框下方：{'、'.join(hits)}",
                                   "表格区按钮统一置于表格区左上角（工具栏），不得绘制在表格下方",
                                   raw.strip(), source_ref=RULE51_SOURCE,
                                   fix="将表格关联按钮（批量操作/子功能入口等）移到表格左上角工具栏区域")
                # 2) 表格批量操作按钮不在工具栏区域（紧邻表格框上方一行 / 表格框内）
                for idx, raw in enumerate(lines):
                    if top - 1 <= idx <= bottom:
                        continue
                    hits = [kw for kw in _table_button_keywords_in(raw) if "批量" in kw]
                    if not hits or _ascii_line_is_pagination_or_footer(raw, True):
                        continue
                    self.add_error(pid, "TABLE_ACTION_NOT_IN_TOOLBAR", "warning", apath,
                                   f"表格批量操作按钮未置于表格区左上角：{'、'.join(hits)}",
                                   "表格批量操作按钮必须置于表格区左上角工具栏",
                                   raw.strip(), source_ref=RULE51_SOURCE,
                                   fix="将批量操作按钮移到表格左上角工具栏区域")
                # 3) 列设置/列配置画为独立按钮：表格组件自带功能，线框图不得绘制
                for idx, raw in enumerate(lines):
                    hits = [kw for kw in COLUMN_SETTING_DRAWN_KEYWORDS if kw in raw]
                    if not hits:
                        continue
                    self.add_error(pid, "WIREFRAME_COLUMN_SETTING_DRAWN", "warning", apath,
                                   f"线框图将列设置绘制为独立按钮：{'、'.join(hits)}",
                                   "列设置为表格组件自带功能，线框图不绘制，Coding 时由表格组件自带能力提供",
                                   raw.strip(), source_ref=RULE51_SOURCE,
                                   fix="删除线框图中的列设置按钮：筛选与列定义落在字段表，列设置为表格组件自带能力，无需独立按钮")

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
    # RULE-67 小i提示痕迹词：tips 值含这些标记视为“字段声明了小i提示图标”
    TOOLTIP_HINT_MARKERS = ("[i]", "(i)", "提示图标", "小i", "小 i", "小i提示", "小 i 提示", "小i图标", "小 i 图标", "i图标", "i 图标", "tooltip", "tooltip提示", "hover提示", "悬浮提示")
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

    def check_tooltip_content(self):
        """RULE-67 小i提示内容义务（条件式）：字段声明了小i提示图标，必须写明提示内容。

        触发口径（键声明才启用，历史 JSON 不误伤）：字段对象显式声明提示图标
        —— tips/tooltip/hint 键值含小i痕迹标记（TOOLTIP_HINT_MARKERS），
        或字段 name 附近线框/ascii 含图标痕迹；仅"图标存在、内容缺失"时告警。

        检查项（warning，不阻断 code）：
        - FORM_TIP_PLACEHOLDER：formFields/表单区块 fields 中字段 tips 值仅为
          占位空话（"有"/"需要"/"待补充"/"是"/"小i提示"/"见原型"等）或为空，
          未写明提示内容本身——配置项有小i时，提示内容是设计交付物的一部分，
          必须写明具体文案（如"用于实例鉴权，创建后不可修改"），禁止只画图标不给内容。
        - FORM_TIP_AMBIGUOUS：tips 存在但仅写"小i提示"/"提示图标"等痕迹词本身，
          无法区分提示内容与图标声明。
        豁免：tips 内容含具体文案（长度>=6 且非纯痕迹词）视为已履行义务。
        范围：仅表单字段（formFields 与含"表单/form"区块的 fields），表格/筛选
        字段的 description 列语义不同，不在本规则内。
        """
        for page, path in self.all_pages:
            pid = page.get("id", "")
            sections = page.get("sections")
            section_list = sections if isinstance(sections, list) else []
            self._audit_tooltip_content(
                pid, page.get("formFields"), f"{path}.formFields", section_list)
            for si, section in enumerate(section_list):
                if not isinstance(section, dict):
                    continue
                block_type = f"{section.get('type', '')} {section.get('title', '')}"
                if "表单" not in block_type and "form" not in block_type.lower():
                    continue
                self._audit_tooltip_content(
                    pid, section.get("formFields"),
                    f"{path}.sections[{si}].formFields", section_list)
                legacy = section.get("fields")
                if isinstance(legacy, list):
                    self._audit_tooltip_content(
                        pid, legacy, f"{path}.sections[{si}].fields", section_list)

    def _audit_tooltip_content(self, pid, fields, base_path, section_list):
        """对一组表单字段执行小i提示内容义务审计（RULE-67 单数组检查）。"""
        if not isinstance(fields, list):
            return
        trace_text = " ".join(
            self._page_trace_text(sec) for sec in section_list if isinstance(sec, dict))
        for i, field in enumerate(fields):
            if not isinstance(field, dict):
                continue
            fname = str(field.get("name", "")).strip()
            fpath = f"{base_path}[{i}]"
            raw_tip = field.get("tips")
            tip_text = raw_tip if isinstance(raw_tip, str) else ""
            stripped = tip_text.strip()
            if not stripped:
                continue
            marker_hit = [mk for mk in self.TOOLTIP_HINT_MARKERS if mk.lower() in stripped.lower()]
            if not marker_hit:
                continue
            # 去掉痕迹词后剩余文本 = 提示内容本体
            residue = stripped
            for m in sorted(marker_hit, key=len, reverse=True):
                residue = residue.replace(m, "").replace(m.lower(), "")
            residue = residue.strip("：: 　，,。；;·-—|")
            if len(residue) >= 6:
                continue  # 有具体文案，义务已履行
            if len(residue) > 0 and residue not in ("有", "需要", "是", "待补充", "见原型", "略"):
                # 残留短文本但非空话：给 warning 让人工复核（如"长度64"）
                self.add_error(
                    pid, "FORM_TIP_AMBIGUOUS", "warning", fpath,
                    f"字段「{fname}」的 tips 仅含小i痕迹词与极短残留「{residue}」，提示内容是否完整需人工复核",
                    "tips 写明小i提示的具体文案（如：用于实例鉴权，创建后不可修改）",
                    f"tips 原文：{stripped[:60]}",
                    fix="把小i提示的内容写进 tips（具体说明该配置项的含义/影响/限制），痕迹词本身不是提示内容",
                )
            else:
                self.add_error(
                    pid, "FORM_TIP_PLACEHOLDER", "warning", fpath,
                    f"字段「{fname}」声明了小i提示但 tips 未写明提示内容（仅占位：{stripped[:30]}）",
                    "tips 写明小i提示的具体文案（如：用于实例鉴权，创建后不可修改）",
                    f"tips 仅为占位：{stripped[:30]}",
                    fix="配置项有小i时必须写明提示内容本身——把具体说明文案写进 tips；若确实无提示内容则删除痕迹词",
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

    TEMPLATE_SYNC_FIELDS = ("footer.buttonOrder", "footer.alignment")

    def _template_sync_entries(self):
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return []
        entries = dc.get("templateSync")
        return entries if isinstance(entries, list) else []

    def _effective_template(self, tid):
        """返回合并 templateSync 差异后的模板契约副本（RULE-64）。

        注册表快照与 Common Design 原文不一致时，AI 以 Common Design 为准产出设计
        并登记 templateSync 条目；本方法把已登记条目的 commonDesignValue 覆盖到
        对应 footer 字段上，RULE-20/37/60 的判定真值随之切换。未声明或声明非法时
        返回注册表原值（纯函数、幂等，非法条目的覆盖不生效，合法性由 check_template_sync 校验）。
        """
        templates = self.registry.get("templates") or {}
        template = templates.get(tid)
        if not isinstance(template, dict):
            return template
        entries = [e for e in self._template_sync_entries()
                   if isinstance(e, dict) and str(e.get("templateId", "")).strip() == tid]
        if not entries:
            return template
        merged = json.loads(json.dumps(template, ensure_ascii=False))
        footer = dict(merged.get("footer") or {})
        for entry in entries:
            field = str(entry.get("field", "")).strip()
            value = entry.get("commonDesignValue")
            if field == "footer.buttonOrder" and isinstance(value, list) and value:
                footer["buttonOrder"] = [str(k).strip() for k in value]
            elif field == "footer.alignment" and isinstance(value, str) and value.strip().lower() in ("left", "right"):
                footer["alignment"] = value.strip().lower()
        merged["footer"] = footer
        return merged

    CARRIER_SWEEP_REVIEW_SIGNALS = ("第三方", "对接", "厂商", "平台", "连接状态", "对接进度", "同步进度")

    def check_carrier_sweep(self):
        """RULE-65 承载形式分流闭环（两部分）。

        其一：条目对账（designContext.carrierSweep 键显式声明时启用，含空 list）——
        CD 存在承载形式分流决策链（如多实例配置内容：表格承载 vs 多卡片承载）时，
        逐页登记 { pageId, contextRef, dataTraits, decision, templateRef, reason }；
        校验字段完整性、pageId/templateRef 存在性、账实一致（templateRef == 页面
        templateId）、contextRef 锚点级精读；注册表 carrierTraceRequired=true 的
        特化承载模板被使用时必须有对应条目（CD 明文"仅判为对应承载形式时使用"）。
        其二：可疑信号复核（始终启用，warning 级）——页面文本含第三方对接特征词
        而未留痕时提示复核，防止该选卡片承载却回落表格基线。
        判定语义始终以 CD 分流链原文为准，本校验只做账实一致与留痕完整性。
        """
        dc = self.data.get("designContext")
        dc_dict = dc if isinstance(dc, dict) else {}
        raw_sweep = dc_dict.get("carrierSweep")
        declared = isinstance(dc, dict) and isinstance(raw_sweep, list)
        entries = raw_sweep if isinstance(raw_sweep, list) else []
        ledger = self._build_ledger(dc_dict.get("readLedger"))
        templates = self.registry.get("templates") or {}
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.30 承载形式分流闭环（RULE-65）"
        pages_by_id = {}
        for page, _ in self.all_pages:
            pid = str(page.get("id", "")).strip()
            if pid:
                pages_by_id[pid] = page
        swept = set()
        if declared:
            for i, entry in enumerate(entries):
                base = f"$.designContext.carrierSweep[{i}]"
                if not isinstance(entry, dict):
                    self.add_error("-", "CARRIER_SWEEP_ENTRY_INVALID", "error", base,
                                   "carrierSweep 条目必须为对象",
                                   "含 pageId/contextRef/dataTraits/decision/templateRef/reason 的对象",
                                   type(entry).__name__, source_ref=src_ref,
                                   fix="按 11.30 条目结构登记承载形式分流判定")
                    continue
                page_id = str(entry.get("pageId", "")).strip()
                context_ref = str(entry.get("contextRef", "")).strip()
                data_traits = entry.get("dataTraits")
                decision = str(entry.get("decision", "")).strip()
                template_ref = str(entry.get("templateRef", "")).strip()
                reason = str(entry.get("reason", "")).strip()
                invalid = []
                if not page_id:
                    invalid.append("pageId")
                if "#" not in context_ref:
                    invalid.append("contextRef（须含 # 锚点）")
                if not (isinstance(data_traits, dict) and data_traits):
                    invalid.append("dataTraits（须为非空对象，逐特征判定留痕）")
                if not decision:
                    invalid.append("decision")
                if not template_ref:
                    invalid.append("templateRef")
                if not reason:
                    invalid.append("reason")
                if invalid:
                    self.add_error("-", "CARRIER_SWEEP_ENTRY_INVALID", "error", base,
                                   f"carrierSweep 条目字段缺失或非法：{'、'.join(invalid)}",
                                   "pageId 非空、contextRef 含 # 锚点、dataTraits 为非空对象、decision/templateRef/reason 非空",
                                   "；".join(invalid), source_ref=src_ref,
                                   fix="按 11.30 条目结构补齐后重新校验")
                else:
                    if page_id not in pages_by_id:
                        self.add_error("-", "CARRIER_SWEEP_TARGET_MISSING", "error", base,
                                       f"carrierSweep 条目的 pageId {page_id} 不存在于 pages",
                                       "pageId 须为 pages 中已有页面", page_id,
                                       source_ref=src_ref, fix="核对页面 ID 后修正条目")
                    elif template_ref not in templates:
                        self.add_error("-", "CARRIER_SWEEP_TARGET_MISSING", "error", base,
                                       f"carrierSweep 条目的 templateRef {template_ref} 不在模板注册表中",
                                       "templateRef 须为注册表已有模板", template_ref,
                                       source_ref=src_ref, fix="核对模板 ID 后修正条目")
                    else:
                        actual = self.page_template(pages_by_id[page_id])
                        if template_ref != actual:
                            self.add_error("-", "CARRIER_SWEEP_MISMATCH", "error", base,
                                           f"承载形式判定与实际选型不一致：条目判定 {template_ref}，页面实际 {actual}",
                                           "decision 落地的 templateRef 须与页面 templateId 一致",
                                           f"{template_ref} != {actual}", source_ref=src_ref,
                                           fix="按 CD 分流链重新判定，或修正页面模板/条目使账实一致")
                        swept.add(page_id)
                    if "#" in context_ref:
                        doc, anchor = self._norm_ref(context_ref)
                        if not (ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"):
                            self.add_error("-", "CARRIER_SWEEP_BASIS_UNREAD", "warning", base + ".contextRef",
                                           f"承载形式分流的依据 {context_ref} 未在 readLedger 中精读命中（status=read）",
                                           "readLedger 中 status=read 且锚点匹配", context_ref,
                                           source_ref=src_ref,
                                           fix="精读 CD 该分流章节原文并登记 readLedger 为 read")
            for page, _ in self.all_pages:
                pid = str(page.get("id", "")).strip()
                tid = self.page_template(page)
                if not pid or not tid or pid in swept:
                    continue
                if (templates.get(tid) or {}).get("carrierTraceRequired"):
                    self.add_error("-", "CARRIER_SWEEP_CARD_TRACE_MISSING", "error",
                                   f"$.pages[{self._idx(page)}].templateContract.templateId",
                                   f"页面 {pid} 使用了承载形式特化模板 {tid}（CD 明文：仅判为对应承载形式时使用），"
                                   "但 designContext.carrierSweep 中没有该页的分流判定条目",
                                   "使用特化承载模板须在 carrierSweep 留痕（contextRef/dataTraits/decision/reason）",
                                   "无对应条目", source_ref=src_ref,
                                   fix="补 carrierSweep 条目回溯分流判定，或改用默认承载模板")
        for page, _ in self.all_pages:
            pid = str(page.get("id", "")).strip()
            if not pid or pid in swept:
                continue
            text = self._page_trace_text(page)
            hits = [w for w in self.CARRIER_SWEEP_REVIEW_SIGNALS if w in text]
            if hits:
                self.add_error(pid, "CARRIER_SWEEP_SIGNAL_REVIEW", "warning",
                               f"$.pages[{self._idx(page)}]",
                               f"页面含承载形式分流特征词（{'、'.join(hits[:3])}）但未在 carrierSweep 留痕，"
                               "请复核 Common Design 承载形式分流判定（如多实例配置内容：表格承载 vs 多卡片承载）",
                               "涉及承载形式选择的页面应有 carrierSweep 分流判定留痕",
                               "无条目", source_ref=src_ref,
                               fix="按 CD 分流章节逐特征判定并在 designContext.carrierSweep 落账")

    def check_template_sync(self):
        """RULE-64 模板契约差异同步闭环（条件式，designContext.templateSync 非空 list 时启用）。

        注册表快照与 Common Design 原文不一致时，以 Common Design 为准产出设计并把差异
        登记到 designContext.templateSync；登记完整性与依据精读在此校验，覆盖消费在
        _effective_template（RULE-20/37/60 判定前合并）。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return
        entries = dc.get("templateSync")
        if not (isinstance(entries, list) and entries):
            return
        ledger = self._build_ledger(dc.get("readLedger"))
        templates = self.registry.get("templates") or {}
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.29 模板契约差异同步闭环（RULE-64）"
        for i, entry in enumerate(entries):
            base = f"$.designContext.templateSync[{i}]"
            if not isinstance(entry, dict):
                self.add_error("-", "TEMPLATE_SYNC_ENTRY_INVALID", "error", base,
                               "templateSync 条目必须为对象",
                               "含 templateId/field/registryValue/commonDesignValue/ref 的对象",
                               type(entry).__name__, source_ref=src_ref,
                               fix="按 11.29 条目结构登记差异")
                continue
            template_id = str(entry.get("templateId", "")).strip()
            field = str(entry.get("field", "")).strip()
            ref = str(entry.get("ref", "")).strip()
            value = entry.get("commonDesignValue")
            invalid = []
            if not template_id:
                invalid.append("templateId")
            if field not in self.TEMPLATE_SYNC_FIELDS:
                invalid.append("field（须为 footer.buttonOrder / footer.alignment）")
            if value is None or value == "" or value == []:
                invalid.append("commonDesignValue")
            if field == "footer.buttonOrder" and value is not None and not isinstance(value, list):
                invalid.append("commonDesignValue（footer.buttonOrder 须为按钮 kind 数组）")
            if field == "footer.alignment" and isinstance(value, str) and value.strip().lower() not in ("left", "right"):
                invalid.append("commonDesignValue（footer.alignment 须为 left/right）")
            if "#" not in ref:
                invalid.append("ref（须含 # 锚点）")
            if invalid:
                self.add_error("-", "TEMPLATE_SYNC_ENTRY_INVALID", "error", base,
                               f"templateSync 条目字段缺失或非法：{'、'.join(invalid)}",
                               "templateId 非空、field 为 footer.buttonOrder/footer.alignment、commonDesignValue 类型正确且非空、ref 含 # 锚点",
                               "；".join(invalid), source_ref=src_ref,
                               fix="按 11.29 条目结构补齐后重新校验")
            elif template_id not in templates:
                self.add_error("-", "TEMPLATE_SYNC_TARGET_MISSING", "error", base,
                               f"templateSync 条目的 templateId {template_id} 不在模板注册表中",
                               "templateId 须为注册表已有模板", template_id,
                               source_ref=src_ref,
                               fix="核对模板 ID（模板 ID 以注册表为准）后修正条目")
            if ref and "#" in ref:
                doc, anchor = self._norm_ref(ref)
                if not (ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"):
                    self.add_error("-", "TEMPLATE_SYNC_BASIS_UNREAD", "warning", base + ".ref",
                                   f"templateSync 条目的依据 {ref} 未在 readLedger 中精读命中（status=read）",
                                   "readLedger 中 status=read 且锚点匹配", ref,
                                   source_ref=src_ref,
                                   fix="精读 Common Design 该模板条目原文并登记 readLedger 为 read")

    def check_footer_ascii_order(self):
        """RULE-37 线框图底部按钮：ascii 必须按模板 buttonOrder 绘制（主操作在左、次操作在右），
        按钮文案须落在模板允许集合（缺主操作/顺序错=error，缺次要按钮=warning），自定义按钮需 override 声明。"""
        for page in self.data.get("pages", []):
            if self._wireframe_shared_with(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid) or {}
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

    def check_footer_ascii_alignment(self):
        """RULE-60 线框图底部按钮水平位置闭环（error 级）：
        Common Design 模板声明 footer.alignment（right/left）时，ascii 底部操作区的按钮
        必须画在对应一侧——"声明 right 画到左边"是真实的视觉还原漂移，此前 RULE-20 只对账
        JSON 层 alignment 声明、RULE-37 只查按钮出现顺序，水平位置零校验。

        判定口径：以底部操作区上边框线（最后一条内部分隔线）的显示宽度为容器参照 W，
        取每行按钮 span（模板按钮文案 + 自定义按钮）整体距左/距右留白，明显偏向另一侧
        （超出容差 max(4, W*12%)）时报错。无法可靠判定时静默跳过（无结构线、无按钮 span、
        顺序已错、override、PD 模板页），不引入新误报。"""
        for page in self.data.get("pages", []):
            if self._wireframe_shared_with(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            template = self._effective_template(tid) or {}
            footer = template.get("footer") or {}
            expected = str(footer.get("alignment") or "").strip().lower()
            if expected not in ("left", "right"):
                continue
            wf = self.page_wireframe(page)
            if not isinstance(wf, dict):
                continue
            ascii_text = str(wf.get("ascii") or "")
            if not ascii_text.strip():
                continue
            tc = page.get("templateContract") or {}
            if bool((tc.get("override") or {}).get("enabled")):
                continue
            path = f"$.pages[{self._idx(page)}].wireframe.ascii"
            tpl = template.get("source", "")
            # 与 RULE-37 同口径重算按钮出现顺序：顺序已错或缺按钮时跳过对齐判定，避免叠加报错
            expected_order = footer.get("buttonOrder") or []
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
            if not pos or actual_order != [k for k in expected_order if k in actual_order]:
                continue
            footer_text = self._footer_region_text(ascii_text)
            if not footer_text:
                continue
            lines = [l.rstrip() for l in footer_text.splitlines() if l.strip()]
            # 容器参照：全文结构框线（含底部操作区上边线）的最大显示宽度，减去两端框字符
            struct_lines = [l for l in (x.strip() for x in ascii_text.splitlines())
                            if re.fullmatch(r"[+\-─│┌┐└┘├┤┬┴┼ ]+", l) and re.search(r"[─\-]", l)]
            widths = [_disp_width(l) for l in struct_lines]
            if not widths:
                continue
            inner_w = max(widths) - 2
            if inner_w < 20:
                continue
            tol = max(4, int(inner_w * 0.12))
            for line in lines:
                spans = [m for m in re.finditer(r"[【\[]([^】\]\n]{1,24})[】\]]", line)]
                if not spans:
                    continue
                start_gap = _disp_width(line[: spans[0].start()])
                end_gap = inner_w - _disp_width(line[: spans[-1].end()])
                actual = "left" if start_gap <= end_gap else "right"
                if expected == "right" and start_gap < end_gap - tol:
                    self.add_error(pid, "FOOTER_ASCII_ALIGNMENT_MISMATCH", "error", path,
                                   "线框图底部按钮水平位置与模板对齐要求不符：模板要求右对齐，实际画在左侧",
                                   "底部操作区按钮按 Common Design 模板 alignment 贴右侧绘制",
                                   f"按钮距左 {start_gap} 列、距右 {end_gap} 列（偏左）",
                                   source_ref=tpl,
                                   fix="重画 ascii 底部操作区，把按钮整体移到右侧贴边（模板要求 right 对齐）")
                    break
                if expected == "left" and end_gap < start_gap - tol:
                    self.add_error(pid, "FOOTER_ASCII_ALIGNMENT_MISMATCH", "error", path,
                                   "线框图底部按钮水平位置与模板对齐要求不符：模板要求左对齐，实际画在右侧",
                                   "底部操作区按钮按 Common Design 模板 alignment 贴左侧绘制",
                                   f"按钮距左 {start_gap} 列、距右 {end_gap} 列（偏右）",
                                   source_ref=tpl,
                                   fix="重画 ascii 底部操作区，把按钮整体移到左侧贴边（模板要求 left 对齐）")
                    break

    def check_wireframe_column_alignment(self):
        """RULE-47 线框图列对齐一致性（warning）：内容行右边界（右竖线）应在同一列，
        出现明显错位时提示，用于捕捉"两列结构断裂"。"""
        for page in self.data.get("pages", []):
            if self._wireframe_shared_with(page):
                continue
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
        # 2) 模板覆盖落地：PD 声明 override 的页面模板视为注册表新增模板，命中页面必须直接采用
        #    （templateId=PD 定义的页面模板 ID），不得仍使用 Common Design 模板 ID
        if pd_matched:
            overrides = self._pd_template_override_entries()
            if overrides:
                for page, path in self.all_pages:
                    pid = page.get("id", "")
                    tid = self.page_template(page)
                    entry = self._pd_template_for_page(page, tid)
                    if entry is None:
                        continue
                    tc = page.get("templateContract") or {}
                    base = str(tc.get("templateBase", "")).strip().lower()
                    pref = str(tc.get("productTemplateRef", "")).strip()
                    adopted = tid in self.pd_templates or (
                        tid and tid not in self.registry.get("templates", {})
                        and base == "product")
                    if not adopted or base != "product" or not pref:
                        pd_tid = (str(entry.get("templateId") or entry.get("pdTemplateId") or "").strip()
                                  or tid)
                        pd_name = self._pd_template_name(entry)
                        hint = f"（模板名：{pd_name}）" if pd_name else ""
                        self.add_error(pid, "TEMPLATE_OVERRIDE_NOT_APPLIED", "error",
                                       f"{path}.templateContract.templateId",
                                       "Product Design 声明模板覆盖，但页面未直接采用 Product Design 页面模板"
                                       "（仍使用 Common Design 模板或未按 PD 模板 ID 登记）",
                                       f"templateId=<PD 页面模板 ID>{hint}，templateBase=product，productTemplateRef 非空",
                                       f"templateId={tid or '空'}，templateBase={base or '空'}",
                                       fix="将 templateId 直接改为 Product Design 定义的页面模板 ID"
                                           "（PD override 模板视为注册表新增模板，不再保留 Common Design 底层 ID），"
                                           "type 同步 PD 模板中文名，并在 productTemplateRef 登记其文档锚点")
                    elif tid in self.pd_templates and tid not in self.registry.get("templates", {}):
                        if not self._page_has_pd_template_basis_read(page, entry):
                            self.add_error(pid, "PD_TEMPLATE_BASIS_UNREAD", "warning",
                                           f"{path}.codingGuide.designReferences",
                                           "采用 Product Design 页面模板，但模板文档依据未在 readLedger 精读（status=read）",
                                           "PD 模板文档锚点已精读（readLedger status=read）",
                                           "未精读",
                                           fix="精读 productTemplateRef 指向的 PD 模板文档原文后更新 readLedger；"
                                               "PD 模板页的骨架/区域/组件契约以该文档为真值源")
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
                applies = {normalize_template_id(t) for t in (cov.get("appliesTo") or [])}
                for page, path in self.all_pages:
                    pid = page.get("id", "")
                    tid = self.page_template(page)
                    if applies and pid not in applies and normalize_template_id(tid) not in applies:
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

    # ---- 需求入口落位闭环（RULE-52）----
    ENTRY_SCOPES = ("in-scope", "out-of-scope")

    def _page_design_text(self, page):
        """页面设计对象的序列化文本（排除 children 引用，避免子页面干扰落位判定）。"""
        return json.dumps({k: v for k, v in page.items() if k != "children"},
                          ensure_ascii=False, sort_keys=True)

    def _entry_landing_in_page(self, page, entry):
        """in-scope：宿主页面是否承载该入口（触发元素 / 打开容器 / 宿主位置）。"""
        text = self._page_design_text(page)
        container = str(entry.get("container") or "").strip()
        trigger = str(entry.get("trigger") or "").strip()
        location = str(entry.get("location") or "").strip()
        if container and container in text:
            return True
        if trigger and trigger in text:
            return True
        for op in page.get("operations") or []:
            if not isinstance(op, dict):
                continue
            if container and str(op.get("targetPageId") or "").strip() == container:
                return True
            blob = " ".join(str(op.get(k) or "") for k in ("label", "name", "trigger", "action", "description"))
            if (trigger and trigger in blob) or (location and location in blob):
                return True
        for section in self.page_sections(page):
            if not isinstance(section, dict):
                continue
            blob = f"{section.get('title') or ''} {section.get('type') or ''} " \
                   f"{json.dumps(section.get('actions') or [], ensure_ascii=False)}"
            if (trigger and trigger in blob) or (location and location in blob) or (container and container in blob):
                return True
        return False

    def _entry_drawn_in_wireframe(self, page, entry):
        """宿主页面线框图是否绘制了入口痕迹（触发文案 / 打开容器 / 显式入口标记）。"""
        wf = page.get("wireframe")
        ascii_text = ""
        if isinstance(wf, dict):
            ascii_text = wf.get("ascii") or ""
        elif isinstance(wf, str):
            ascii_text = wf
        if not ascii_text:
            return False
        trigger = str(entry.get("trigger") or "").strip()
        container = str(entry.get("container") or "").strip()
        if trigger and trigger in ascii_text:
            return True
        if container and container in ascii_text:
            return True
        return "入口" in ascii_text

    def check_requirement_entry_points(self):
        """RULE-52 需求入口落位闭环（条件式，顶层声明 requirementEntryPoints 时启用）。

        PRD 点名的每个入口挂载点必须有落点，否则编码阶段会凭"识别到入口"的空壳设计漏做：
        - in-scope 宿主：宿主页面 sections/actions 或 operations 中须出现该触发元素/打开容器；
        - out-of-scope 宿主：必须在 entryHosts 登记（含 Tier1 精读与对应开发项）；
        - 宿主线框图无入口绘制痕迹：warning；
        - 入口声明缺必需字段或 hostScope 非法：阻断。
        """
        entries = self.data.get("requirementEntryPoints")
        if not isinstance(entries, list) or not entries:
            return
        hosts = self.data.get("entryHosts")
        hosts = hosts if isinstance(hosts, list) else []
        by_id = {str(p.get("id", "")).strip(): p for p, _ in self.all_pages if p.get("id")}
        by_name = {str(p.get("name", "")).strip(): p for p, _ in self.all_pages if p.get("name")}
        all_item_ids = set()
        for page, _ in self.all_pages:
            for item in (page.get("codingGuide") or {}).get("pageItems") or []:
                if isinstance(item, dict) and item.get("id"):
                    all_item_ids.add(str(item["id"]).strip())
        host_index = {}
        for h in hosts:
            if isinstance(h, dict):
                key = str(h.get("id") or h.get("name") or "").strip()
                if key:
                    host_index[key] = h
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.17 需求入口落位闭环（RULE-52）"

        for i, entry in enumerate(entries):
            epath = f"$.requirementEntryPoints[{i}]"
            if not isinstance(entry, dict):
                self.add_error("-", "ENTRY_POINT_INCOMPLETE", "error", epath,
                               "入口挂载点声明必须是对象", "对象", type(entry).__name__,
                               source_ref=src_ref,
                               fix="按 01-output-templates.md 定义补全入口挂载点字段")
                continue
            eid = str(entry.get("id") or f"EP{i + 1}")
            missing = [k for k in ("host", "hostScope", "location", "trigger", "container")
                       if not _has_text_value(entry.get(k))]
            if missing:
                self.add_error(eid, "ENTRY_POINT_INCOMPLETE", "error", epath,
                               f"入口挂载点 {eid} 缺少必需字段：{'、'.join(missing)}",
                               "host / hostScope / location / trigger / container 均非空",
                               f"缺失 {missing}", source_ref=src_ref,
                               fix="补全宿主、宿主范围、宿主位置、触发元素与打开容器")
                continue
            scope = str(entry.get("hostScope")).strip()
            if scope not in self.ENTRY_SCOPES:
                self.add_error(eid, "ENTRY_POINT_INCOMPLETE", "error", f"{epath}.hostScope",
                               f"入口挂载点 {eid} 的 hostScope 非法：{scope}",
                               "in-scope / out-of-scope", scope, source_ref=src_ref,
                               fix="将 hostScope 修正为 in-scope 或 out-of-scope")
                continue
            host = str(entry.get("host")).strip()
            if scope == "in-scope":
                page = by_id.get(host) or by_name.get(host)
                if page is None:
                    self.add_error(eid, "ENTRY_POINT_NOT_PLACED", "error", f"{epath}.host",
                                   f"入口挂载点 {eid} 的 in-scope 宿主「{host}」不存在于 pages",
                                   "宿主页面存在于 pages 并在其中落位入口",
                                   f"pages 中未找到宿主 {host}", source_ref=src_ref,
                                   fix="在 pages 补充宿主页面；若宿主不在本次范围，将 hostScope 改为 out-of-scope 并登记 entryHosts")
                    continue
                if not self._entry_landing_in_page(page, entry):
                    self.add_error(eid, "ENTRY_POINT_NOT_PLACED", "error", epath,
                                   f"入口挂载点 {eid} 未在宿主「{host}」落位：宿主 sections/actions 与 operations 中均未见触发元素或打开容器",
                                   "宿主相应区块的 actions 或 operations 中承载该入口（触发元素 + 打开容器）",
                                   "未找到入口落点", source_ref=src_ref,
                                   fix="在宿主页面相应区块的 actions/operations 中声明该入口（open-container/targetPageId 或 actions 行）")
                if not self._entry_drawn_in_wireframe(page, entry):
                    self.add_error(eid, "ENTRY_NOT_DRAWN", "warning", epath,
                                   f"入口挂载点 {eid} 在宿主「{host}」的线框图中没有绘制痕迹（未见触发文案/入口标记/容器）",
                                   "宿主线框图绘制入口触发元素（如【新增入口】）与打开容器关系",
                                   "线框图无入口痕迹",
                                   source_ref="references/01-workflow/04-demo-output-spec.md 11.6 线框图绘制规范 / 11.17",
                                   fix="在线框图中绘制宿主页面结构并显式标注入口位置与打开后的容器")
            else:
                h = host_index.get(host)
                if h is None:
                    self.add_error(eid, "ENTRY_HOST_UNREGISTERED", "error", f"{epath}.host",
                                   f"入口挂载点 {eid} 的 out-of-scope 宿主「{host}」未在 entryHosts 登记",
                                   "范围外宿主必须在 entryHosts 登记（含 Tier1 精读与对应开发项）",
                                   "entryHosts 缺失该宿主", source_ref=src_ref,
                                   fix="在顶层 entryHosts 登记该宿主（id/name、readTier=tier1、devItem）并完成精读")
                    continue
                read_ok = (str(h.get("read")).strip().lower() in ("true", "1", "yes", "y")
                           or str(h.get("readTier") or "").strip().lower() in ("tier1", "tier-1", "1"))
                if not read_ok:
                    self.add_error(eid, "ENTRY_HOST_UNREGISTERED", "error", f"$.entryHosts[{host}]",
                                   f"范围外宿主「{host}」未完成 Tier1 精读（readTier 非 tier1 且 read 未置真）",
                                   "read=true 或 readTier=tier1",
                                   f"read={h.get('read')} / readTier={h.get('readTier')}", source_ref=src_ref,
                                   fix="对范围外宿主做 Tier1 精读（宿主页面级结构：Tab 集合、区块构成、操作列现状）")
                dev = str(h.get("devItem") or "").strip()
                if not dev:
                    self.add_error(eid, "ENTRY_HOST_UNREGISTERED", "error", f"$.entryHosts[{host}].devItem",
                                   f"范围外宿主「{host}」没有对应开发项（devItem 为空），编码阶段将漏做该入口",
                                   "入口开发项 ID（挂在打开容器的 codingGuide 下）", "空", source_ref=src_ref,
                                   fix="为入口建立开发项（scope=entry-point），并把其 ID 登记到 entryHosts[].devItem")
                elif dev not in all_item_ids:
                    self.add_error(eid, "ENTRY_HOST_UNREGISTERED", "error", f"$.entryHosts[{host}].devItem",
                                   f"范围外宿主「{host}」的开发项 {dev} 不存在于任何页面 codingGuide.pageItems",
                                   f"开发项 {dev} 已定义", f"未找到 {dev}", source_ref=src_ref,
                                   fix="在打开容器页面的 codingGuide.pageItems 中补充该开发项，或修正 devItem 引用")
                wf_text = str(h.get("wireframe") or "").strip()
                if not wf_text:
                    self.add_error(eid, "ENTRY_NOT_DRAWN", "warning", f"$.entryHosts[{host}].wireframe",
                                   f"范围外宿主「{host}」未登记宿主落位说明（entryHosts[].wireframe 为空），编码阶段将遗漏入口落位信息",
                                   "宿主落位说明：宿主内位置 + 触发元素 + 打开容器 + 编码要求（一行文字即可，无需绘制宿主完整线框图）",
                                   "空", source_ref="references/01-workflow/04-demo-output-spec.md 11.17 需求入口落位闭环（RULE-52）",
                                   fix="补写宿主落位说明（如「告警列表操作列新增【加入行为白名单】按钮，点击打开行为白名单表单抽屉，编码要求见 P003-E01」）")
                else:
                    trigger_text = str(entry.get("trigger") or "").strip()
                    hit = bool(trigger_text and trigger_text in wf_text) or any(k in wf_text for k in self.ENTRY_HOST_PLACE_HINTS)
                    if not hit:
                        self.add_error(eid, "ENTRY_NOT_DRAWN", "warning", f"$.entryHosts[{host}].wireframe",
                                       f"范围外宿主「{host}」的落位说明未写清入口在宿主内的位置或触发元素，编码阶段无法据此定位",
                                       "宿主落位说明须包含宿主内位置（操作列/工具栏/按钮区等）与触发元素",
                                       f"说明「{wf_text[:30]}」未含位置或触发元素",
                                       source_ref="references/01-workflow/04-demo-output-spec.md 11.17 需求入口落位闭环（RULE-52）",
                                       fix="在落位说明中补写入口在宿主内的位置与触发元素（如「xx列表操作列」），编码阶段才能准确定位落点")

    # ---- 共用线框差异描述闭环（RULE-62）----
    ENTRY_HOST_PLACE_HINTS = ("位置", "操作列", "工具栏", "按钮区", "按钮", "页头", "头部", "行内", "菜单", "标签页", "Tab", "列头", "栏", "入口")

    def check_wireframe_shared(self):
        """RULE-62 共用线框差异描述闭环（条件式，页面声明 wireframeSharedWith 时启用）。

        相同 UI 的页面（如同一对象的新增/编辑共用同一弹窗布局、仅数据不同）以主页面完整绘制，
        从页面不再重复绘制线框图，只描述差异：
        - wireframeSharedWith 指向的主页面不存在 -> error WIREFRAME_SHARED_TARGET_MISSING；
        - 主页面模板 ID 或页面类型与从页面不一致（UI 不同/对象不同不得共用）-> error WIREFRAME_SHARED_TARGET_MISMATCH；
        - 主页面自身也声明共用（链式共享）或主页面未完整绘制 ascii -> error WIREFRAME_SHARED_HOST_NOT_DRAWN；
        - wireframeDiff 缺失或为空 -> warning WIREFRAME_SHARED_DIFF_MISSING。
        声明共用的页面跳过全部线框结构类校验（骨架/区域/绘制质量/footer/表格/表单布局等）。
        """
        pages_by_id = {}
        for page, _ in self.all_pages:
            pid_key = str(page.get("id", "")).strip()
            if pid_key:
                pages_by_id[pid_key] = page
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.27 共用线框差异描述闭环（RULE-62）"
        for page, ppath in self.all_pages:
            host_id = self._wireframe_shared_with(page)
            if not host_id:
                continue
            pid = str(page.get("id", "")).strip() or ppath
            host_page = pages_by_id.get(host_id)
            if host_page is None:
                self.add_error(pid, "WIREFRAME_SHARED_TARGET_MISSING", "error", f"{ppath}.wireframeSharedWith",
                               f"页面 {pid} 声明共用线框的主页面「{host_id}」不存在于 pages",
                               "wireframeSharedWith 指向本次范围内已完整绘制线框的主页面",
                               f"未找到主页面 {host_id}", source_ref=src_ref,
                               fix="修正 wireframeSharedWith 为主页面页面 ID；若两页 UI 并不相同，删除共用声明并完整绘制本页线框")
                continue
            my_tpl = self.page_template(page)
            host_tpl = self.page_template(host_page)
            my_type = str(page.get("type") or "").strip()
            host_type = str(host_page.get("type") or "").strip()
            mismatch = []
            if my_tpl and host_tpl and my_tpl != host_tpl:
                mismatch.append(f"模板 ID（{my_tpl} vs {host_tpl}）")
            if my_type and host_type and my_type != host_type:
                mismatch.append(f"页面类型（{my_type} vs {host_type}）")
            if mismatch:
                self.add_error(pid, "WIREFRAME_SHARED_TARGET_MISMATCH", "error", f"{ppath}.wireframeSharedWith",
                               f"页面 {pid} 与主页面 {host_id} 的 {'、'.join(mismatch)} 不一致，UI 不同不得共用线框",
                               "共用线框仅限两页 UI 完全一样（同模板、同容器类型、同布局），差异只在数据",
                               "；".join(mismatch), source_ref=src_ref,
                               fix="UI 不同的页面必须各自完整绘制线框（新增/编辑对象不同即属此类）；仅同对象同布局时才允许共用")
                continue
            if self._wireframe_shared_with(host_page):
                self.add_error(pid, "WIREFRAME_SHARED_HOST_NOT_DRAWN", "error", f"{ppath}.wireframeSharedWith",
                               f"共用链路非法：主页面 {host_id} 自身也声明共用其他页面线框（链式共享）",
                               "主页面必须完整绘制线框，从页面直接声明共用该主页面",
                               f"{host_id} 的 wireframeSharedWith={self._wireframe_shared_with(host_page)}",
                               source_ref=src_ref,
                               fix="取消链式共用：主页面完整绘制线框，其他页面直接共用该主页面")
                continue
            host_wf = self.page_wireframe(host_page)
            host_ascii = str((host_wf or {}).get("ascii") or "").strip() if isinstance(host_wf, dict) else ""
            if len(host_ascii) < 8:
                self.add_error(pid, "WIREFRAME_SHARED_HOST_NOT_DRAWN", "error", f"{ppath}.wireframeSharedWith",
                               f"主页面 {host_id} 未完整绘制线框，无法作为共用基准",
                               "主页面 wireframe.ascii 完整绘制后，从页面才可声明共用",
                               f"主页面 ascii 长度 {len(host_ascii)}", source_ref=src_ref,
                               fix="先为主页面绘制完整线框图，或删除本页的共用声明并自行绘制线框")
                continue
            diff = str(page.get("wireframeDiff") or "").strip()
            if not diff:
                self.add_error(pid, "WIREFRAME_SHARED_DIFF_MISSING", "warning", f"{ppath}.wireframeDiff",
                               f"页面 {pid} 与 {host_id} 共用线框但未描述差异（wireframeDiff 为空），无法说明两页区别",
                               "wireframeDiff 描述本页与主页面的差异（标题/数据/字段/默认值等）",
                               "空", source_ref=src_ref,
                               fix="补写 wireframeDiff：说明本页与主页面共用同一布局，差异仅在某处（如标题改为编辑、表单回填既有数据）")

    # ---- 页面定位证据闭环（RULE-53）----
    STRONG_MATCH_TOKENS = {
        "route", "router", "menu", "menupath", "menu_path", "tab", "tabs",
        "title", "navpath", "nav_path", "breadcrumb", "component", "export",
        "sidebar", "路由", "菜单", "页签", "标签页", "标题", "面包屑", "组件", "侧边栏", "导航",
    }
    WEAK_MATCH_TOKENS = {
        "filename", "file", "dir", "directory", "filepath", "path",
        "文件名", "目录名", "文件", "目录", "源文件", "文件路径", "目录路径",
    }

    def _norm_tokens(self, values):
        out = []
        if isinstance(values, list):
            for v in values:
                if isinstance(v, str) and v.strip():
                    out.append(v.strip().lower())
        elif isinstance(values, str) and values.strip():
            out = [t.strip().lower() for t in values.replace(";", ",").split(",") if t.strip()]
        return out

    def _check_identity_evidence(self, ev, epath, label):
        """校验单个"页面身份证据"对象：三证合一 + 禁止文件名定位 + 候选消歧 + 与 PRD 路径对证。"""
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.18 页面定位证据闭环（RULE-53）"
        if not isinstance(ev, dict):
            self.add_error(label, "HOST_IDENTITY_UNVERIFIED", "error", epath,
                           f"{label} 缺少页面身份证据（hostEvidence）：无法证明定位到的就是目标页面",
                           "hostEvidence{navPath, route/menu, title, codeRefs, matchedBy}",
                           "缺失", source_ref=src_ref,
                           fix="补充身份证据：逐级导航路径、路由/菜单标识、页面标题、命中代码实体与命中依据（禁止仅凭文件名）")
            return
        navpath = ev.get("navPath")
        nav_tokens = [str(x).strip() for x in navpath] if isinstance(navpath, list) else []
        nav_tokens = [x for x in nav_tokens if x]
        route = str(ev.get("route") or ev.get("menu") or ev.get("menuPath") or "").strip()
        title = str(ev.get("title") or "").strip()
        tabs = ev.get("tabs")
        tabs = [str(x).strip() for x in tabs if str(x).strip()] if isinstance(tabs, list) else []
        code_refs = ev.get("codeRefs")
        code_refs = [str(x).strip() for x in code_refs if str(x).strip()] if isinstance(code_refs, list) else []
        matched = self._norm_tokens(ev.get("matchedBy"))
        source = str(ev.get("identitySource") or "").strip().lower()
        if source not in ("code", "degraded"):
            source = "code" if code_refs else "degraded"

        if not nav_tokens:
            self.add_error(label, "HOST_IDENTITY_UNVERIFIED", "error", f"{epath}.navPath",
                           f"{label} 的身份证据缺少逐级导航路径（navPath）",
                           "非空导航路径，如 [\"安全事件\",\"事件详情\",\"告警列表\"]",
                           "空", source_ref=src_ref,
                           fix="按 PRD 逐级填写导航路径，禁止跳级或用近似名称代替")
        if source == "code":
            if not route:
                self.add_error(label, "HOST_IDENTITY_UNVERIFIED", "error", f"{epath}.route",
                               f"{label} 为代码模式但缺少路由/菜单标识（route/menu/menuPath）",
                               "稳定身份源：路由或菜单配置标识", "空", source_ref=src_ref,
                               fix="从路由/菜单配置中填入定位页面的一级/二级标识")
            if not code_refs:
                self.add_error(label, "HOST_IDENTITY_UNVERIFIED", "error", f"{epath}.codeRefs",
                               f"{label} 为代码模式但缺少命中代码实体（codeRefs）",
                               "实际对证命中的页面路由文件/组件路径", "空", source_ref=src_ref,
                               fix="登记实际打开确认过的代码实体路径（严禁以文件名匹配代替内容对证）")
        else:
            if not title and not tabs:
                self.add_error(label, "HOST_IDENTITY_UNVERIFIED", "error", epath,
                               f"{label} 为退化模式（环境无完整代码）但缺少标题/组件导出名与侧边栏或 Tab 文案",
                               "title + (tabs 或 navPath) 对证", "空", source_ref=src_ref,
                               fix="无代码可读时，以页面标题/组件导出名 + 侧边栏/Tab 文案逐级对证目标页面")

        if not matched:
            self.add_error(label, "HOST_IDENTITY_FILENAME_ONLY", "error", f"{epath}.matchedBy",
                           f"{label} 未给出命中依据（matchedBy）",
                           "命中依据须含 route/menu/tab/title/component 等强锚点，禁止 filename/dir",
                           "空", source_ref=src_ref,
                           fix="填写命中依据，且不得包含文件名或目录名")
        else:
            weak_hit = [t for t in matched if t in self.WEAK_MATCH_TOKENS]
            strong_hit = [t for t in matched if t in self.STRONG_MATCH_TOKENS]
            if weak_hit:
                self.add_error(label, "HOST_IDENTITY_FILENAME_ONLY", "error", f"{epath}.matchedBy",
                               f"{label} 的命中依据包含文件名/目录名（{weak_hit}）——文件名不得作为定位依据",
                               "仅使用 route/menu/tab/title/component 等强锚点",
                               f"命中依据 {matched}", source_ref=src_ref,
                               fix="移除 matchedBy 中的文件名/目录名，改用路由/菜单/Tab/标题/组件等强锚点对证")
            if not strong_hit:
                self.add_error(label, "HOST_IDENTITY_FILENAME_ONLY", "error", f"{epath}.matchedBy",
                               f"{label} 的命中依据不含任何强身份锚点（route/menu/tab/title）",
                               "至少一个强锚点", f"命中依据 {matched}", source_ref=src_ref,
                               fix="以路由/菜单/Tab/标题等强锚点作为命中依据")

        cand = ev.get("candidates")
        cand = [str(x) for x in cand if str(x).strip()] if isinstance(cand, list) else []
        rejected = ev.get("rejected")
        rejected = [x for x in rejected if x] if isinstance(rejected, list) else []
        if len(cand) > 1 and not rejected:
            self.add_error(label, "HOST_IDENTITY_AMBIGUOUS", "warning", f"{epath}.candidates",
                           f"{label} 存在多个形近/近义候选（{cand}）但未记录排除理由",
                           "逐条记录被排除候选及理由",
                           f"候选 {cand} / 未记录排除", source_ref=src_ref,
                           fix="枚举全部形近候选（如 alert-list/alarm-list），逐个对证并记录排除理由")

        prd = ev.get("prdNavPath")
        prd_tokens = [str(x).strip() for x in prd if str(x).strip()] if isinstance(prd, list) else []
        if prd_tokens and nav_tokens:
            last_prd = prd_tokens[-1].lower()
            host_norm = [t.lower() for t in nav_tokens]
            if not any(last_prd in h or h in last_prd for h in host_norm):
                self.add_error(label, "HOST_NAVPATH_MISMATCH", "error", f"{epath}.navPath",
                               f"{label} 的代码导航路径末级（{nav_tokens[-1]}）与 PRD 声明路径末级（{prd_tokens[-1]}）对不上，疑似张冠李戴",
                               "代码导航路径末级与 PRD 声明一致",
                               f"PRD={prd_tokens} / code={nav_tokens}", source_ref=src_ref,
                               fix="回到路由/菜单/Tab 逐级复核，确认定位到的页面就是 PRD 点名的页面")

    def check_page_identity(self):
        """RULE-53 页面定位证据闭环（条件式：声明 requirementEntryPoints 或 pageIdentityRefs 时启用）。

        - out-of-scope 入口宿主必须有 hostEvidence 并通过强锚点对证（缺/弱则阻断）；
        - in-scope 宿主仅在显式提供 hostEvidence 时校验（本需求页面的身份由页面拆解覆盖）；
        - pageIdentityRefs（复用/相似页面定位）逐项校验。
        """
        entries = self.data.get("requirementEntryPoints")
        refs = self.data.get("pageIdentityRefs")
        entries = entries if isinstance(entries, list) else []
        refs = refs if isinstance(refs, list) else []
        if not entries and not refs:
            return
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("hostScope", "")).strip() != "out-of-scope" \
                    and not isinstance(entry.get("hostEvidence"), dict):
                continue
            eid = str(entry.get("id") or i)
            self._check_identity_evidence(entry.get("hostEvidence"),
                                          f"$.requirementEntryPoints[{i}].hostEvidence",
                                          f"入口挂载点 {eid} 宿主")
        for i, ref in enumerate(refs):
            if not isinstance(ref, dict):
                continue
            rid = str(ref.get("id") or ref.get("name") or i)
            self._check_identity_evidence(ref.get("evidence"),
                                          f"$.pageIdentityRefs[{i}].evidence",
                                          f"定位页面 {rid}")

    # ---- 表格/表单字段选择类控件的组件形态闭环（RULE-54）----
    @staticmethod
    def _split_candidates(value):
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            raw = value.replace("、", ",").replace("；", ",").replace(";", ",")
            return [t.strip() for t in raw.split(",") if t.strip()]
        return []

    def check_component_form(self):
        """RULE-54 组件形态描述闭环（条件式：字段声明 >1 个形态候选 formCandidates 时启用）。

        组件存在多种形态（如 IxTag 的多种标签样式、IxSelect 下拉面板的搜索/新增/树/分组、
        单选/多选的 radio/卡片）时，必须在 iduxComponentForm 写明选用哪一种形态：
        - 声明多形态候选却未选形态 -> COMPONENT_FORM_MISSING（warning）；
        - 选用形态不在候选内 -> COMPONENT_FORM_UNKNOWN（warning）；
          iduxComponentForm 支持 Common Design"形态 + 增强项"两段式写法（如"级联（可搜索）"、
          "平铺+搜索"），按最长候选子串匹配形态主值，主值在候选内即通过；
        - 已选形态但未写 formDecision 判定结论 -> FORM_DECISION_MISSING（warning）；
        - formDecision 未引用所选形态 -> FORM_DECISION_MISMATCH（warning）。
        仅校验声明了 formCandidates 的字段，单形态组件零负担；
        形态清单与命名口径以 Common Design 组件映射为准，本 Skill 不内置形态目录。
        HTML 生成器会把 iduxComponentForm 并入既有“iDux组件名称”列展示，不新增列。

        形态来源分两层，并各自要求“已读证据”（没有证据的形态等于自造）：
        - 命名/枚举真值：Common Design 组件映射（`05-components/idux-component-map.md` 的组件锚点）；
        - 选择依据真值：Common Design widget patterns（`03-patterns/03-widget-patterns/` 的判定小节锚点），
          按“目录级索引 + 命中文件精读”读取，Product Design 侧 pattern 文档同样可作为选择依据。
        声明多形态候选却未登记组件映射依据、或依据未精读 -> COMPONENT_FORM_SOURCE_UNREAD（warning）；
        声明多形态候选却未登记 widget pattern 选择依据、或依据未精读 -> COMPONENT_FORM_RULE_UNREAD（warning）。
        """
        comp_map_hints = ("idux-component-map", "component-map", "05-components")
        widget_pattern_hints = ("widget-patterns", "03-widget-patterns")
        dc = self.data.get("designContext")
        dc = dc if isinstance(dc, dict) else {}
        ledger = self._build_ledger(dc.get("readLedger"))

        def _evidence_read(ref):
            if "#" not in str(ref or ""):
                return False
            doc, anchor = self._norm_ref(ref)
            return ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"

        def _basis_state(host, hints, allow_pd_pattern=False):
            """返回 (是否登记了该层依据, 是否精读命中)。"""
            found = False
            refs = (host.get("codingGuide") or {}).get("designReferences")
            for ref in refs if isinstance(refs, list) else []:
                if not isinstance(ref, dict):
                    continue
                src = str(ref.get("source", "")).strip()
                if src not in ("common-design", "product-design"):
                    continue
                rf = str(ref.get("ref", "")).strip()
                doc = self._norm_ref(rf)[0]
                hit = any(h in doc for h in hints)
                if not hit and allow_pd_pattern and src == "product-design" and "pattern" in doc:
                    hit = True
                if not hit:
                    continue
                found = True
                if _evidence_read(rf):
                    return True, True
            return found, False

        for page, path in self.all_pages:
            pid = page.get("id", "")
            flagged = []
            targets = []
            for key in ("tableFields", "columns", "formFields", "filterFields"):
                fields = page.get(key)
                if isinstance(fields, list):
                    targets.append((f"{path}.{key}", fields))
            sections = page.get("sections")
            if isinstance(sections, list):
                for si, section in enumerate(sections):
                    if not isinstance(section, dict):
                        continue
                    spath = f"{path}.sections[{si}]"
                    for key in ("tableFields", "columns", "formFields", "filterFields"):
                        fields = section.get(key)
                        if isinstance(fields, list):
                            targets.append((f"{spath}.{key}", fields))
            for base_path, fields in targets:
                for i, field in enumerate(fields):
                    if not isinstance(field, dict):
                        continue
                    candidates = self._split_candidates(field.get("formCandidates"))
                    if len(candidates) <= 1:
                        continue
                    fname = str(field.get("name") or field.get("label") or i)
                    fpath = f"{base_path}[{i}]"
                    flagged.append((fpath, fname))
                    # 样式变体编号（Common Design 组件表新增编号，如 IxTag 深色标签 -> IxTag_Filled）：
                    # 编号必须挂在形态上展示（IxTag（深色标签 · IxTag_Filled）），只写编号不写形态名会丢失可读性。
                    if str(field.get("iduxComponentVariantId") or "").strip() and not str(field.get("iduxComponentForm") or "").strip():
                        self.add_error(
                            pid, "COMPONENT_VARIANT_WITHOUT_FORM", "warning", fpath,
                            f"字段“{fname}”声明了样式变体编号 iduxComponentVariantId，但未写 iduxComponentForm 形态名——编号必须与形态名成对出现，否则展示层丢失可读性",
                            "iduxComponentForm 写明形态中文名（如“深色标签”），iduxComponentVariantId 填对应变体编号（如“IxTag_Filled”）",
                            "iduxComponentForm 缺失",
                            fix="按 Common Design 组件映射补写形态中文名到 iduxComponentForm；映射表未登记编号时 iduxComponentVariantId 留空即可",
                        )
                    chosen = str(field.get("iduxComponentForm") or "").strip()
                    comp = str(field.get("iduxComponent") or field.get("component") or "").strip()
                    # 样式变体编号漏填/不一致检查（启发式，warning）：校验器不知道 CD 映射表哪些形态登记了编号，
                    # 但 formDecision/form 中若已出现本组件前缀的编号 token（如 IxTag_Filled），即可判定“编号已在判定链中产生却未落字段”。
                    if chosen:
                        variant_id = str(field.get("iduxComponentVariantId") or "").strip()
                        decision_text = str(field.get("formDecision") or "") + " " + chosen
                        base = re.split(r"[\s（(]", comp)[0] if comp else ""
                        tokens = re.findall(r"\bIx[A-Za-z0-9]+_[A-Za-z0-9]+\b", decision_text)
                        related = [t for t in tokens if base and t.split("_")[0] == base]
                        if related and not variant_id:
                            self.add_error(
                                pid, "COMPONENT_VARIANT_MISSING", "warning", fpath,
                                f"字段“{fname}”的判定说明中已出现本组件的样式变体编号（{', '.join(related)}），但 iduxComponentVariantId 未填写——编号已在判定链中产生却未落到字段，HTML 展示将停留在“{comp}（{chosen}）”",
                                "iduxComponentVariantId 填写判定说明中引用的变体编号",
                                "iduxComponentVariantId 缺失",
                                fix="把判定说明中的编号填入 iduxComponentVariantId；若该形态确认无编号登记，将 formDecision 中的编号移除或写明“该形态无变体编号登记”",
                            )
                        elif related and variant_id and variant_id not in related:
                            self.add_error(
                                pid, "COMPONENT_VARIANT_MISMATCH", "warning", fpath,
                                f"字段“{fname}”的 iduxComponentVariantId（{variant_id}）与判定说明中引用的编号（{', '.join(related)}）不一致——编号与判定结论脱节，编码侧将引用错误变体",
                                f"iduxComponentVariantId 与判定说明引用的编号一致（{related[0]}）",
                                variant_id,
                                fix="以 Common Design 组件映射为准统一编号：修正 iduxComponentVariantId 或 formDecision，两者必须指向同一变体",
                            )
                    if not chosen:
                        self.add_error(
                            pid, "COMPONENT_FORM_MISSING", "warning", fpath,
                            f"字段“{fname}”的组件 {comp or '（未标注）'} 在 Common Design 中有多种形态（候选：{candidates}），但未在 iduxComponentForm 写明选用哪一种",
                            f"填写 iduxComponentForm（形态命名以 Common Design 组件映射为准）并同步写入 formDecision 判定结论",
                            "iduxComponentForm 缺失",
                            fix="读取 widget patterns 判定小节，从候选形态中选定一种写入 iduxComponentForm，并把判定结论（含所选形态名）写入 formDecision",
                        )
                        continue
                    primary = _form_primary_form(chosen, candidates)
                    if primary is None:
                        self.add_error(
                            pid, "COMPONENT_FORM_UNKNOWN", "warning", fpath,
                            f"字段“{fname}”选用的组件形态“{chosen}”不在声明的候选 {candidates} 内",
                            f"iduxComponentForm 主值须属于 {candidates}（增强项可后缀补充，如“深色标签（支持新增）”）",
                            f"取值为 {chosen}",
                            fix="修正 iduxComponentForm 使其主值与 Common Design 登记的候选形态一致（支持“形态+增强项”两段式），或补齐 formCandidates",
                        )
                        continue
                    # 结论留痕对账：读了判定小节就必须把结论写下来（含所选形态名），
                    # 倒逼判定链被执行；机器只校验存在性与包含关系，语义结论由留痕暴露。
                    decision = str(field.get("formDecision") or "").strip()
                    if not decision:
                        self.add_error(
                            pid, "FORM_DECISION_MISSING", "warning", fpath,
                            f"字段“{fname}”声明了多形态候选且已选“{primary}”，但未在 formDecision 写明判定结论——形态判定链读了却未留痕，无法证明是按 Common Design 判定规则选出的",
                            f"formDecision 写一句话判定结论（引用判定小节锚点依据，含所选形态名“{primary}”）；如按 PRD 特殊要求偏离判定链，需在结论中写明来源",
                            "formDecision 缺失",
                            fix="把 widget patterns 判定小节的结论写入 formDecision（例如“省市区层级选择按判定小节采用级联形态”）；判定结论缺失即视为判定链未执行",
                        )
                    elif primary not in decision and chosen not in decision:
                        self.add_error(
                            pid, "FORM_DECISION_MISMATCH", "warning", fpath,
                            f"字段“{fname}”的 formDecision 未引用所选形态“{primary}”，判定结论与所选形态对不上",
                            f"formDecision 须包含所选形态名（“{primary}”）以形成结论与选择的对账",
                            decision[:60],
                            fix="改写 formDecision 使其包含所选形态名，并核对判定小节结论；若结论指向其他形态，应同步修正 iduxComponentForm",
                        )
            if not flagged:
                continue
            sample_field = flagged[0][1]
            refs_path = f"{path}.codingGuide.designReferences"
            found, read = _basis_state(page, comp_map_hints)
            if not found:
                self.add_error(pid, "COMPONENT_FORM_SOURCE_UNREAD", "warning", refs_path,
                               f"字段“{sample_field}”等 {len(flagged)} 个字段声明了多形态候选，但页面未登记 Common Design 组件映射依据，形态候选无法溯源（等于自造形态）",
                               "codingGuide.designReferences 含 Common Design 组件映射锚点（如 .../05-components/idux-component-map.md#<组件>）且 readLedger 命中 read",
                               "缺失",
                               fix="读取 Common Design 组件映射对应组件条目，登记锚点级 designReferences 与 readLedger")
            elif not read:
                self.add_error(pid, "COMPONENT_FORM_SOURCE_UNREAD", "warning", refs_path,
                               f"字段“{sample_field}”等 {len(flagged)} 个字段的形态候选，其 Common Design 组件映射依据未精读命中（status 非 read 或缺锚点）",
                               "锚点级命中 readLedger status=read 的组件映射依据",
                               "未精读",
                               fix="补读组件映射对应锚点原文并登记 readLedger 为 read")
            found, read = _basis_state(page, widget_pattern_hints, allow_pd_pattern=True)
            if not found:
                self.add_error(pid, "COMPONENT_FORM_RULE_UNREAD", "warning", refs_path,
                               f"字段“{sample_field}”等 {len(flagged)} 个字段声明了多形态候选，但未登记形态选择依据（Common Design widget patterns），无法证明形态是按判定规则选出的",
                               "codingGuide.designReferences 含 03-patterns/03-widget-patterns 的判定小节锚点且 readLedger 命中 read",
                               "缺失",
                               fix="先按目录级索引定位命中控件对应的 widget pattern 文件，精读判定小节后登记锚点级 designReferences 与 readLedger")
            elif not read:
                self.add_error(pid, "COMPONENT_FORM_RULE_UNREAD", "warning", refs_path,
                               f"字段“{sample_field}”等 {len(flagged)} 个字段的形态选择依据（widget patterns）未精读命中（status 非 read 或缺锚点）",
                               "锚点级命中 readLedger status=read 的 widget pattern 依据",
                               "未精读",
                               fix="补读对应 widget pattern 判定小节原文并登记 readLedger 为 read")

    # ---- 能力发现完整性（RULE-55） ----
    def check_capability_sweep(self):
        """RULE-55：能力发现完整性（条件式，声明 designContext.productDesign.coverage 时启用）。

        针对“Product Design 未读完就输出、该用 PD 的组件用成 Common Design”的典型漏读：
        - PD 声明的每个能力都必须在 capabilitySweep 中被显式判定“命中/未命中”（未命中同样要留痕），
          漏项或判定非法 → ABILITY_NOT_SWEPT（warning）；
        - 判定为“命中”的能力必须附 evidenceRef 且锚点级命中 readLedger 的 status=read，
          否则 ABILITY_HIT_NOT_READ（warning）。
        以 Product Design 自身声明的 coverage 为真值，不硬编码任何产品/文档路径。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return
        pd = dc.get("productDesign") or {}
        if not bool(pd.get("matched")):
            return
        coverage = pd.get("coverage")
        if not isinstance(coverage, list) or not coverage:
            return
        caps = []
        for c in coverage:
            if isinstance(c, dict):
                cap = str(c.get("capability", "")).strip()
                if cap:
                    caps.append(cap)
        if not caps:
            return
        sweep = pd.get("capabilitySweep")
        sweep = sweep if isinstance(sweep, list) else []
        swept = {}
        for i, s in enumerate(sweep):
            if isinstance(s, dict) and str(s.get("capability", "")).strip():
                swept[str(s["capability"]).strip().lower()] = (i, s)
        ledger = self._build_ledger(dc.get("readLedger"))

        def _ledger_read(ref):
            if "#" not in str(ref or ""):
                return False
            doc, anchor = self._norm_ref(ref)
            return ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"

        for cap in caps:
            if cap.lower() not in swept:
                self.add_error("-", "ABILITY_NOT_SWEPT", "warning",
                               "$.designContext.productDesign.capabilitySweep",
                               f"Product Design 声明的能力 {cap} 未做能力发现全扫（未显式判定 命中/未命中），"
                               "存在“该读的没读、该用 PD 的组件退回 Common Design”的风险",
                               f"capabilitySweep 含 capability={cap} 的判定（命中/未命中均需留痕）",
                               "缺失",
                               fix=f"在 capabilitySweep 补 capability={cap} 的判定（decision=hit/not-hit + reason）")
        for _key, (i, s) in swept.items():
            cap = str(s.get("capability", "")).strip()
            base = f"$.designContext.productDesign.capabilitySweep[{i}]"
            decision = str(s.get("decision", "")).strip().lower()
            if decision not in ("hit", "not-hit", "not_hit", "命中", "未命中"):
                self.add_error("-", "ABILITY_NOT_SWEPT", "warning", base + ".decision",
                               f"能力 {cap} 的判定缺失或非法：{decision or '空'}（须为 hit / not-hit）",
                               "hit 或 not-hit", decision or "空",
                               fix="将 decision 明确为 hit（命中）或 not-hit（未命中）")
                continue
            if decision in ("hit", "命中"):
                ref = str(s.get("evidenceRef", "")).strip()
                if not ref:
                    self.add_error("-", "ABILITY_HIT_NOT_READ", "warning", base + ".evidenceRef",
                                   f"能力 {cap} 判定为命中但未附精读证据 evidenceRef，无法证明已读对应 Product Design",
                                   "锚点级命中 readLedger status=read 的 evidenceRef", "缺失",
                                   fix="补 evidenceRef（<product-design 文档路径>#<章节锚点>）并确保 readLedger 中该锚点为 read")
                elif not _ledger_read(ref):
                    self.add_error("-", "ABILITY_HIT_NOT_READ", "warning", base + ".evidenceRef",
                                   f"能力 {cap} 的 evidenceRef {ref} 未在 readLedger 中精读命中（status=read）",
                                   "readLedger 中 status=read 且锚点匹配", ref,
                                   fix="补读该锚点原文并登记 readLedger 为 read")

    # ---- 设计规范补齐落位闭环（RULE-63，条件式）----
    COMPLETENESS_SOURCES = ("product-design", "common-design")
    COMPLETENESS_DECISIONS = ("included", "excluded")

    @staticmethod
    def _trace_strings(value, out):
        """递归收集 JSON 结构中的所有字符串，用于落点痕迹检索。"""
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                Validator._trace_strings(v, out)
        elif isinstance(value, list):
            for v in value:
                Validator._trace_strings(v, out)

    def _page_trace_text(self, page):
        """把页面 JSON 的全部文本串成可检索的痕迹文本（小写）。"""
        buf = []
        self._trace_strings(page, buf)
        return " ".join(buf).lower()

    def check_design_completeness(self):
        """RULE-63：设计规范补齐落位闭环（条件式，designContext 声明 designCompleteness 时启用）。

        设计规范补齐项（Product Design / Common Design 声明为需求已建设对象/页面类型固有、必备、
        默认存在或成对约束能力，需求未提及但默认纳入）不能只在对话框说了，必须落进 demo-spec：
        - 条目字段缺失或非法（capability/appliesTo/ref 含#/source/decision）→ error COMPLETENESS_ENTRY_INVALID；
        - included 条目必须有本次设计落点 landingRef（开发项 ID 或 <页面ID>#<操作/区块名>），
          缺失/指向不存在/落点处检索不到补齐能力痕迹 → error COMPLETENESS_ITEM_NOT_LANDED；
        - excluded 条目缺排除原因 → error COMPLETENESS_EXCLUSION_REASON_MISSING；
        - ref 未在 readLedger 锚点级精读命中 → warning COMPLETENESS_BASIS_UNREAD。
        兼容旧字段 productDesignCompleteness（历史产物）；两个声明均缺失或为空时整条规则跳过，
        历史 JSON 不误伤。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return
        declared_key = ""
        completeness = dc.get("designCompleteness")
        if isinstance(completeness, list) and completeness:
            declared_key = "designCompleteness"
        else:
            completeness = dc.get("productDesignCompleteness")
            if isinstance(completeness, list) and completeness:
                declared_key = "productDesignCompleteness"
        if not declared_key:
            return
        ledger = self._build_ledger(dc.get("readLedger"))
        pages_by_id = {}
        for page, _ in self.all_pages:
            pid_key = str(page.get("id", "")).strip()
            if pid_key:
                pages_by_id[pid_key] = page
        # 开发项 ID 索引
        dev_item_ids = set()
        for page, _ in self.all_pages:
            cg = page.get("codingGuide") or {}
            items = cg.get("pageItems") or []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        iid = str(it.get("id", "")).strip()
                        if iid:
                            dev_item_ids.add(iid)
        page_traces = {}
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.28 设计规范补齐落位闭环（RULE-63）"
        for i, item in enumerate(completeness):
            base = f"$.designContext.{declared_key}[{i}]"
            if not isinstance(item, dict):
                self.add_error("-", "COMPLETENESS_ENTRY_INVALID", "error", base,
                               "设计规范补齐条目必须为对象",
                               "含 capability/appliesTo/ref/source/decision/reason/landingRef 的对象",
                               type(item).__name__, source_ref=src_ref,
                               fix="按 11.28 条目结构改写为对象")
                continue
            capability = str(item.get("capability", "")).strip()
            applies_to = str(item.get("appliesTo", "")).strip()
            ref = str(item.get("ref", "")).strip()
            source = str(item.get("source", "")).strip().lower()
            decision = str(item.get("decision", "") or "included").strip().lower()
            cap_label = capability or "(capability 缺失)"
            invalid = []
            if not capability:
                invalid.append("capability 缺失")
            if not applies_to:
                invalid.append("appliesTo 缺失")
            if "#" not in ref:
                invalid.append("ref 缺失或不含 # 锚点")
            if source not in self.COMPLETENESS_SOURCES:
                invalid.append(f"source 非法：{source or '空'}（须为 product-design / common-design）")
            if decision not in self.COMPLETENESS_DECISIONS:
                invalid.append(f"decision 非法：{decision or '空'}（须为 included / excluded）")
            if invalid:
                self.add_error("-", "COMPLETENESS_ENTRY_INVALID", "error", base,
                               f"补齐能力 {cap_label} 的条目字段缺失或非法：{'；'.join(invalid)}",
                               "capability/appliesTo 非空、ref 含 # 锚点、source 为 product-design/common-design、decision 为 included/excluded",
                               "；".join(invalid), source_ref=src_ref,
                               fix="按 11.28 条目结构补齐 capability/appliesTo/ref/source/decision")
            # 设计依据须锚点级精读命中 readLedger（excluded 条目同样需要已读依据支撑）
            if "#" in ref:
                doc, anchor = self._norm_ref(ref)
                if not (ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"):
                    self.add_error("-", "COMPLETENESS_BASIS_UNREAD", "warning", base + ".ref",
                                   f"补齐能力 {cap_label} 的依据 {ref} 未在 readLedger 中精读命中（status=read）",
                                   "readLedger 中 status=read 且锚点匹配", ref,
                                   source_ref=src_ref,
                                   fix="补读该锚点原文并登记 readLedger 为 read")
            if decision == "excluded":
                # 排除仅限“用户明确不做”或“与需求业务事实冲突”，且必须写明原因
                reason = str(item.get("reason", "")).strip()
                if not reason:
                    self.add_error("-", "COMPLETENESS_EXCLUSION_REASON_MISSING", "error", base + ".reason",
                                   f"补齐能力 {cap_label} 声明为 excluded 但缺少排除原因",
                                   "excluded 须写明排除原因（仅限用户明确不做或与需求业务事实冲突）", "缺失",
                                   source_ref=src_ref,
                                   fix="补 reason 说明为何剔除该设计规范固有能力；无正当理由时默认纳入")
                continue
            # included：必须有落点 landingRef
            landing = str(item.get("landingRef", "")).strip()
            if not landing:
                self.add_error("-", "COMPLETENESS_ITEM_NOT_LANDED", "error", base + ".landingRef",
                               f"补齐能力 {cap_label} 为 included 但缺少本次设计落点 landingRef，可能在页面设计与开发项中被静默遗漏",
                               "included 补齐项须写 landingRef（开发项 ID 或 <页面ID>#<操作/区块名>）", "缺失",
                               source_ref=src_ref,
                               fix="把补齐能力落进页面操作/区块/开发项，并回填 landingRef")
                continue
            if "#" in landing:
                pid, _, point = landing.partition("#")
                pid, point = pid.strip(), point.strip()
                page = pages_by_id.get(pid)
                if page is None:
                    self.add_error("-", "COMPLETENESS_ITEM_NOT_LANDED", "error", base + ".landingRef",
                                   f"补齐能力 {cap_label} 的落点 landingRef「{landing}」指向的页面 {pid} 不存在于 pages",
                                   "landingRef 的页面 ID 须存在于 pages", f"未找到页面 {pid}",
                                   source_ref=src_ref,
                                   fix="修正 landingRef 为实际承载补齐能力的页面；或先把补齐能力落进对应页面")
                    continue
                trace = page_traces.get(pid)
                if trace is None:
                    trace = self._page_trace_text(page)
                    page_traces[pid] = trace
                probes = [point]
                if capability:
                    probes.extend(w for w in re.split(r"[\s/，,、()（）\-]+", capability) if len(w) >= 2)
                hit = any(p and p.lower() in trace for p in probes)
                if not hit:
                    self.add_error("-", "COMPLETENESS_ITEM_NOT_LANDED", "error", base + ".landingRef",
                                   f"补齐能力 {cap_label} 的落点「{landing}」处检索不到补齐能力痕迹，补齐项未实际落位",
                                   "落点页面在 operations/sections.actions/区块标题/字段名中可检索到补齐能力（操作或区块）点名",
                                   f"页面 {pid} 中未找到「{point}」或能力关键词", source_ref=src_ref,
                                   fix="把补齐能力落进页面操作/区块/字段（如操作列的删除入口）或将 landingRef 修正为真实落点")
            else:
                # 开发项 ID 落点
                if landing not in dev_item_ids:
                    self.add_error("-", "COMPLETENESS_ITEM_NOT_LANDED", "error", base + ".landingRef",
                                   f"补齐能力 {cap_label} 的落点 landingRef「{landing}」指向的开发项不存在于 codingGuide.pageItems",
                                   "landingRef 须为某页面 codingGuide.pageItems[].id 或 <页面ID>#<操作/区块名>",
                                   f"未找到开发项 {landing}", source_ref=src_ref,
                                   fix="修正 landingRef 为实际承载补齐能力的开发项；或先在页面开发项中补齐该能力")

    # ---- 关联改动同步闭环（RULE-66，条件式）：已有功能上新增/修改字段时，关联视图同步或显式豁免 ----
    CHANGE_SYNC_VIEW_TYPES = ("form", "table", "filter", "detail", "card")

    def check_change_sync(self):
        """RULE-66 关联改动同步闭环（条件式，designContext.changeSync 声明时启用）。

        场景：需求在已有功能上修改（如已有表单新增一个配置项）。同一业务对象的关联视图
        （表格汇总列/筛选搜索项/详情展示/卡片等）须同步呈现该字段——或逐项写明豁免理由，
        禁止静默遗漏。只针对本次需求新增/修改的字段，存量字段历史差异不属本规则范围：
        - 条目字段缺失或 view 取值非法 -> error CHANGE_SYNC_ENTRY_INVALID
        - pageId 不存在于 pages -> error CHANGE_SYNC_TARGET_MISSING
        - sourceField 不在该页 sections 任何字段数组中（触发字段本身未落位，先按 RULE-36 落字段）
          -> error CHANGE_SYNC_SOURCE_NOT_LANDED
        - synced 落点指向不存在页面/开发项或落点处检索不到字段痕迹 -> error CHANGE_SYNC_NOT_LANDED
        - excluded 缺豁免理由 -> error CHANGE_SYNC_EXEMPTION_REASON_MISSING
          （豁免是专业判断：如密码字段不进表格列、时间戳不值得做搜索项、超长描述不进筛选条件
          但可进关键词搜索；无理由豁免视为遗漏）
        - views 枚举的关联视图未被 synced/excluded 覆盖 -> error CHANGE_SYNC_VIEW_UNCOVERED
        反向复核（warning，changeSync 键声明时启用，对未被条目触碰的页面生效）：同页面表单字段均未出现在表格列与
        筛选项时提示人工复核——机器只认字段名交集，字段别名/派生列（状态列、操作列、聚合列）
        属正常差异，故仅 warning；完整对账以 changeSync 条目为准。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return
        entries = dc.get("changeSync")
        if "changeSync" not in dc or not isinstance(entries, list):
            return
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.31 关联改动同步闭环（RULE-66）"
        pages_by_id = {}
        for page, _ in self.all_pages:
            pid_key = str(page.get("id", "")).strip()
            if pid_key:
                pages_by_id[pid_key] = page
        dev_item_ids = set()
        for page, _ in self.all_pages:
            items = (page.get("codingGuide") or {}).get("pageItems") or []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and str(it.get("id", "")).strip():
                        dev_item_ids.add(str(it.get("id")).strip())
        page_traces = {}

        def _section_field_names(page):
            names = set()
            for section in self.page_sections(page):
                if not isinstance(section, dict):
                    continue
                for key in ("tableFields", "formFields", "cardFields", "filterFields", "detailFields"):
                    for f in section.get(key) or []:
                        if isinstance(f, dict) and str(f.get("name", "")).strip():
                            names.add(str(f.get("name")).strip())
            return names

        name_cache = {}
        touched_pages = set()
        for i, entry in enumerate(entries):
            base = f"$.designContext.changeSync[{i}]"
            if not isinstance(entry, dict):
                self.add_error("-", "CHANGE_SYNC_ENTRY_INVALID", "error", base,
                               "changeSync 条目必须为对象",
                               "含 sourceField/pageId/views/synced/excluded 的对象",
                               type(entry).__name__, source_ref=src_ref,
                               fix="按 11.31 条目结构登记关联改动同步判定")
                continue
            source_field = str(entry.get("sourceField", "")).strip()
            page_id = str(entry.get("pageId", "")).strip()
            views = entry.get("views")
            synced = entry.get("synced")
            excluded = entry.get("excluded")
            invalid = []
            if not source_field:
                invalid.append("sourceField")
            if not page_id:
                invalid.append("pageId")
            if not (isinstance(views, list) and views):
                invalid.append("views（须为非空数组，枚举对象关联视图）")
            if not isinstance(synced, list):
                invalid.append("synced（须为数组，可为空）")
            if not isinstance(excluded, list):
                invalid.append("excluded（须为数组，可为空）")
            if invalid:
                self.add_error("-", "CHANGE_SYNC_ENTRY_INVALID", "error", base,
                               f"changeSync 条目字段缺失或非法：{'；'.join(invalid)}",
                               "sourceField/pageId 非空、views 非空数组、synced/excluded 为数组",
                               "；".join(invalid), source_ref=src_ref,
                               fix="按 11.31 条目结构补齐后重新校验")
                continue
            page = pages_by_id.get(page_id)
            if page is None:
                self.add_error("-", "CHANGE_SYNC_TARGET_MISSING", "error", base,
                               f"changeSync 条目的 pageId {page_id} 不存在于 pages",
                               "pageId 须为 pages 中已有页面", page_id, source_ref=src_ref,
                               fix="核对页面 ID 后修正条目")
                continue
            if page_id not in name_cache:
                name_cache[page_id] = _section_field_names(page)
            if source_field not in name_cache[page_id]:
                self.add_error("-", "CHANGE_SYNC_SOURCE_NOT_LANDED", "error", base,
                               f"触发字段「{source_field}」未在页面 {page_id} 的 sections 字段中落位——触发字段本身尚未落地，关联同步无从谈起",
                               "sourceField 须为该页 sections（表单/表格/筛选/详情/卡片）中已存在的字段",
                               f"页面 {page_id} 中未找到字段「{source_field}」", source_ref=src_ref,
                               fix="先按 RULE-36 把触发字段落进页面字段数组，再登记关联同步")
                continue
            swept_views = set()
            for j, item in enumerate(synced):
                sbase = f"{base}.synced[{j}]"
                if not isinstance(item, dict):
                    self.add_error("-", "CHANGE_SYNC_ENTRY_INVALID", "error", sbase,
                                   "synced 视图项必须为对象", "含 view/landingRef 的对象",
                                   type(item).__name__, source_ref=src_ref,
                                   fix="按 11.31 视图项结构改写为对象")
                    continue
                view = str(item.get("view", "")).strip()
                landing = str(item.get("landingRef", "")).strip()
                bad = []
                if not view:
                    bad.append("view")
                elif view not in self.CHANGE_SYNC_VIEW_TYPES:
                    bad.append(f"view 取值非法：{view}（须为 form/table/filter/detail/card）")
                if not landing:
                    bad.append("landingRef")
                if bad:
                    self.add_error("-", "CHANGE_SYNC_ENTRY_INVALID", "error", sbase,
                                   f"synced 视图项字段缺失或非法：{'；'.join(bad)}",
                                   "view 取 form/table/filter/detail/card、landingRef 非空",
                                   "；".join(bad), source_ref=src_ref,
                                   fix="补齐或修正 synced 视图项")
                    continue
                swept_views.add(view)
                if "#" in landing:
                    lpid, _, point = landing.partition("#")
                    lpid, point = lpid.strip(), point.strip()
                    lpage = pages_by_id.get(lpid)
                    if lpage is None:
                        self.add_error("-", "CHANGE_SYNC_NOT_LANDED", "error", sbase + ".landingRef",
                                       f"字段「{source_field}」同步视图 {view} 的落点 landingRef「{landing}」指向的页面 {lpid} 不存在于 pages",
                                       "landingRef 的页面 ID 须存在于 pages", f"未找到页面 {lpid}",
                                       source_ref=src_ref, fix="修正 landingRef 为实际承载同步的页面；或先补该页同步内容")
                        continue
                    trace = page_traces.get(lpid)
                    if trace is None:
                        trace = self._page_trace_text(lpage)
                        page_traces[lpid] = trace
                    if not point or point.lower() not in trace:
                        self.add_error("-", "CHANGE_SYNC_NOT_LANDED", "error", sbase + ".landingRef",
                                       f"字段「{source_field}」同步视图 {view} 的落点「{landing}」处检索不到字段痕迹，同步未实际落位",
                                       "落点页面可检索到同步视图区块或字段名", f"页面 {lpid} 中未找到「{point}」",
                                       source_ref=src_ref,
                                       fix=f"在落点页面的 {view} 视图中补上字段「{source_field}」，或将 landingRef 修正为真实落点")
                elif landing not in dev_item_ids:
                    self.add_error("-", "CHANGE_SYNC_NOT_LANDED", "error", sbase + ".landingRef",
                                   f"字段「{source_field}」同步视图 {view} 的落点 landingRef「{landing}」指向的开发项不存在",
                                   "landingRef 须为某页面 codingGuide.pageItems[].id 或 <页面ID>#<区块/字段名>",
                                   f"未找到开发项 {landing}", source_ref=src_ref,
                                   fix="修正 landingRef 为实际承载同步的开发项或页面落点")
            for j, item in enumerate(excluded):
                sbase = f"{base}.excluded[{j}]"
                if not isinstance(item, dict):
                    self.add_error("-", "CHANGE_SYNC_ENTRY_INVALID", "error", sbase,
                                   "excluded 视图项必须为对象", "含 view/reason 的对象",
                                   type(item).__name__, source_ref=src_ref,
                                   fix="按 11.31 视图项结构改写为对象")
                    continue
                view = str(item.get("view", "")).strip()
                reason = str(item.get("reason", "")).strip()
                if not view or view not in self.CHANGE_SYNC_VIEW_TYPES:
                    self.add_error("-", "CHANGE_SYNC_ENTRY_INVALID", "error", sbase,
                                   f"excluded 视图项 view 缺失或非法：{view or '空'}（须为 form/table/filter/detail/card）",
                                   "view 取 form/table/filter/detail/card", view, source_ref=src_ref,
                                   fix="补齐或修正 excluded 视图项 view")
                    continue
                swept_views.add(view)
                if not reason:
                    self.add_error("-", "CHANGE_SYNC_EXEMPTION_REASON_MISSING", "error", sbase + ".reason",
                                   f"字段「{source_field}」对视图 {view} 声明豁免但缺少豁免理由——无理由豁免视为遗漏",
                                   "excluded 须写明专业豁免理由（如密码字段不进表格列、时间戳不值得做搜索项、超长描述不进筛选条件但可进关键词搜索）",
                                   "缺失", source_ref=src_ref,
                                   fix="补 reason 说明为何该视图不同步；无正当理由时补同步内容")
            uncovered = [str(v).strip() for v in views if str(v).strip() and str(v).strip() not in swept_views]
            if uncovered:
                self.add_error("-", "CHANGE_SYNC_VIEW_UNCOVERED", "error", base + ".views",
                               f"字段「{source_field}」枚举的关联视图 {'、'.join(uncovered)} 既未在 synced 登记同步、也未在 excluded 登记豁免",
                               "views 枚举的每个视图须在 synced（同步）或 excluded（豁免+理由）中出现其一",
                               f"未覆盖：{'、'.join(uncovered)}", source_ref=src_ref,
                               fix="为遗漏视图补 synced 落点或 excluded 豁免理由；视图枚举本身有误则修正 views")
            touched_pages.add(page_id)
        # 反向复核（warning）：同页面表单字段均未出现在表格列与筛选项时提示人工复核
        for page, _ in self.all_pages:
            pid = page.get("id", "")
            if not pid or pid in touched_pages:
                continue
            form_names, list_names = set(), set()
            for section in self.page_sections(page):
                if not isinstance(section, dict):
                    continue
                for f in section.get("formFields") or []:
                    if isinstance(f, dict) and str(f.get("name", "")).strip():
                        form_names.add(str(f.get("name")).strip())
                for key in ("tableFields", "filterFields"):
                    for f in section.get(key) or []:
                        if isinstance(f, dict) and str(f.get("name", "")).strip():
                            list_names.add(str(f.get("name")).strip())
            if not form_names or not list_names:
                continue
            gap = sorted(n for n in form_names if n not in list_names)
            if gap:
                self.add_error(pid, "CHANGE_SYNC_REVIEW", "warning",
                               f"$.pages[{self._idx(page)}].sections",
                               f"同页面表单字段 {'、'.join(gap[:3])} 等 {len(gap)} 个字段未出现在表格列与筛选项中，请复核是否为本次改动的关联视图遗漏",
                               "新增/修改字段在关联视图（表格列/筛选项）同步呈现，或在 designContext.changeSync 逐项豁免并写明理由",
                               f"{len(gap)} 个字段仅存在于表单视图", source_ref=src_ref,
                               fix="确属本次改动遗漏 -> 补表格列/筛选项或登记 changeSync；属存量差异或专业豁免（如密码不进表格、时间戳不值得做搜索项、超长描述不进筛选但可进关键词搜索）-> 登记 changeSync 豁免留痕")

    # ---- Feature 契约落位闭环（RULE-68，条件式）：CD Feature 功能契约的保留/调整/禁止三级约束留痕对账 ----
    def check_feature_contract(self):
        """RULE-68 Feature 契约落位闭环（条件式，designContext.featureContract 声明时启用）。

        场景：Common Design Feature 业务功能层文档声明了功能契约——哪些结构必须保留、
        哪些可按业务调整、哪些禁止出现。设计命中该功能时，CD 是约束而非参考，契约条款必须落进设计：
        - 条目 source 缺失或不含 # 锚点 / appliedTo 非非空数组 / appliedTo 项缺 pageId/item/landingRef /
          adjustments 项缺 item/from/to / forbidden 项缺 pattern / reason 缺失
          -> error FEATURE_CONTRACT_ENTRY_INVALID
        - appliedTo 项 pageId 不存在于 pages -> error FEATURE_TARGET_MISSING
        - appliedTo 项 landingRef 指向不存在页面/开发项、与 pageId 不一致，或落点处检索不到 item 痕迹
          -> error FEATURE_PRESERVE_MISSING（必须保留的契约结构未落位）
        - adjustments 项缺 reason -> error FEATURE_ADJUSTMENT_UNREASONED（可按业务调整的部分调整须留痕：
          CD 原结构 -> 本设计调整 -> 业务理由，无理由调整视为静默偏离）
        - forbidden 声明的禁止模式（词元）出现在任一页面文本 -> error FEATURE_FORBIDDEN_PATTERN
          （禁止模式由 AI 从契约原文声明为数据，校验器只做文本检索，不硬编码任何 CD 词汇）
        - source 未在 readLedger 锚点级精读命中 -> warning FEATURE_BASIS_UNREAD
        机制通用：不绑定任何具体功能词，CD 新增 Feature 文档零改动；未声明 featureContract 键的
        历史 JSON 不启用，不误伤。
        """
        dc = self.data.get("designContext")
        if not isinstance(dc, dict):
            return
        entries = dc.get("featureContract")
        if "featureContract" not in dc or not isinstance(entries, list):
            return
        src_ref = "references/01-workflow/04-demo-output-spec.md 11.33 Feature 契约落位闭环（RULE-68）"
        ledger = self._build_ledger(dc.get("readLedger"))
        pages_by_id = {}
        for page, _ in self.all_pages:
            pid_key = str(page.get("id", "")).strip()
            if pid_key:
                pages_by_id[pid_key] = page
        dev_item_ids = set()
        for page, _ in self.all_pages:
            items = (page.get("codingGuide") or {}).get("pageItems") or []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and str(it.get("id", "")).strip():
                        dev_item_ids.add(str(it.get("id")).strip())
        page_traces = {}
        all_traces = []
        for page, _ in self.all_pages:
            pid = str(page.get("id", "")).strip()
            trace = self._page_trace_text(page)
            page_traces[pid] = trace
            all_traces.append((pid, trace))
        for i, entry in enumerate(entries):
            base = f"$.designContext.featureContract[{i}]"
            if not isinstance(entry, dict):
                self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", base,
                               "featureContract 条目必须为对象",
                               "含 source/appliedTo/adjustments/forbidden/reason 的对象",
                               type(entry).__name__, source_ref=src_ref,
                               fix="按 11.33 条目结构登记 Feature 契约对账")
                continue
            source = str(entry.get("source", "")).strip()
            applied_to = entry.get("appliedTo")
            adjustments = entry.get("adjustments")
            forbidden = entry.get("forbidden")
            reason = str(entry.get("reason", "")).strip()
            invalid = []
            if not source or "#" not in source:
                invalid.append("source（须为 <Feature文档路径>#<契约章节锚点>）")
            if not (isinstance(applied_to, list) and applied_to):
                invalid.append("appliedTo（须为非空数组，逐项登记契约条款落点）")
            if adjustments is not None and not isinstance(adjustments, list):
                invalid.append("adjustments（须为数组，可为空）")
            if forbidden is not None and not isinstance(forbidden, list):
                invalid.append("forbidden（须为数组，可为空）")
            if not reason:
                invalid.append("reason（须写明该 Feature 契约为何适用本需求）")
            if invalid:
                self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", base,
                               f"featureContract 条目字段缺失或非法：{'；'.join(invalid)}",
                               "source 含 # 锚点、appliedTo 非空数组、adjustments/forbidden 为数组（可空）、reason 非空",
                               "；".join(invalid), source_ref=src_ref,
                               fix="按 11.33 条目结构补齐后重新校验")
                continue
            doc, anchor = self._norm_ref(source)
            if not (ledger.get((doc, anchor)) == "read" or ledger.get((doc, "*")) == "read"):
                self.add_error("-", "FEATURE_BASIS_UNREAD", "warning", base + ".source",
                               f"Feature 契约依据 {source} 未在 readLedger 中精读命中（status=read）",
                               "readLedger 中 status=read 且锚点匹配", source,
                               source_ref=src_ref,
                               fix="精读该 Feature 契约章节原文并登记 readLedger 为 read")
            for j, item in enumerate(applied_to or []):
                abase = f"{base}.appliedTo[{j}]"
                if not isinstance(item, dict):
                    self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", abase,
                                   "appliedTo 落点项必须为对象", "含 pageId/item/landingRef 的对象",
                                   type(item).__name__, source_ref=src_ref,
                                   fix="按 11.33 appliedTo 项结构改写为对象")
                    continue
                page_id = str(item.get("pageId", "")).strip()
                item_name = str(item.get("item", "")).strip()
                landing = str(item.get("landingRef", "")).strip()
                bad = []
                if not page_id:
                    bad.append("pageId")
                if not item_name:
                    bad.append("item")
                if not landing:
                    bad.append("landingRef")
                if bad:
                    self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", abase,
                                   f"appliedTo 落点项字段缺失：{'、'.join(bad)}",
                                   "pageId/item/landingRef 非空", "、".join(bad), source_ref=src_ref,
                                   fix="补齐 appliedTo 落点项字段")
                    continue
                page = pages_by_id.get(page_id)
                if page is None:
                    self.add_error("-", "FEATURE_TARGET_MISSING", "error", abase + ".pageId",
                                   f"契约条款「{item_name}」的落点页 pageId {page_id} 不存在于 pages",
                                   "pageId 须为 pages 中已有页面", page_id, source_ref=src_ref,
                                   fix="核对页面 ID；契约要求保留的结构须有页面承载")
                    continue
                if "#" in landing:
                    lpid, _, point = landing.partition("#")
                    lpid, point = lpid.strip(), point.strip()
                    if lpid != page_id:
                        self.add_error("-", "FEATURE_PRESERVE_MISSING", "error", abase + ".landingRef",
                                       f"契约条款「{item_name}」的 landingRef「{landing}」与声明页面 {page_id} 不一致",
                                       f"landingRef 页面 ID 须与 pageId 一致（{page_id}）", lpid,
                                       source_ref=src_ref, fix="修正 landingRef 为该页面内的实际落点")
                        continue
                    trace = page_traces.get(lpid) or ""
                    probes = [point] if point else []
                    probes.extend(w for w in re.split(r"[\s/，,、()（）\-]+", item_name) if len(w) >= 2)
                    if not any(p.lower() in trace for p in probes if p):
                        self.add_error("-", "FEATURE_PRESERVE_MISSING", "error", abase + ".landingRef",
                                       f"契约要求保留的「{item_name}」在落点「{landing}」处检索不到痕迹——必须保留的契约结构未落位",
                                       "落点页面可检索到该契约结构（区块标题/字段名/线框文本）",
                                       f"页面 {page_id} 中未找到「{point or item_name}」", source_ref=src_ref,
                                       fix=f"在页面 {page_id} 落位契约要求保留的结构，或将 landingRef 修正为真实落点")
                else:
                    if landing not in dev_item_ids:
                        self.add_error("-", "FEATURE_PRESERVE_MISSING", "error", abase + ".landingRef",
                                       f"契约条款「{item_name}」的落点 landingRef「{landing}」指向的开发项不存在",
                                       "landingRef 须为某页面 codingGuide.pageItems[].id 或 <页面ID>#<区块/字段名>",
                                       f"未找到开发项 {landing}", source_ref=src_ref,
                                       fix="修正 landingRef 为实际承载契约结构的开发项或页面落点")
            for j, adj in enumerate(adjustments or []):
                abase = f"{base}.adjustments[{j}]"
                if not isinstance(adj, dict):
                    self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", abase,
                                   "adjustments 调整项必须为对象", "含 item/from/to/reason 的对象",
                                   type(adj).__name__, source_ref=src_ref,
                                   fix="按 11.33 adjustments 项结构改写为对象")
                    continue
                adj_item = str(adj.get("item", "")).strip()
                adj_from = str(adj.get("from", "")).strip()
                adj_to = str(adj.get("to", "")).strip()
                missing = [k for k, v in (("item", adj_item), ("from", adj_from), ("to", adj_to)) if not v]
                if missing:
                    self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", abase,
                                   f"adjustments 调整项字段缺失：{'、'.join(missing)}",
                                   "item/from/to 非空（CD 原结构 -> 本设计调整）", "、".join(missing),
                                   source_ref=src_ref, fix="补齐调整项的 item/from/to")
                    continue
                if not str(adj.get("reason", "")).strip():
                    self.add_error("-", "FEATURE_ADJUSTMENT_UNREASONED", "error", abase + ".reason",
                                   f"契约条款「{adj_item}」声明为按业务调整但缺少调整理由——无理由调整视为静默偏离契约",
                                   "reason 须写明业务事实（为何本需求无法沿用 CD 原结构）", "缺失",
                                   source_ref=src_ref,
                                   fix="补 reason；结构调整偏离契约时须在确认点向用户呈现并确认")
            for j, fb in enumerate(forbidden or []):
                fbase = f"{base}.forbidden[{j}]"
                if not isinstance(fb, dict):
                    self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", fbase,
                                   "forbidden 禁止项必须为对象", "含 pattern 的对象",
                                   type(fb).__name__, source_ref=src_ref,
                                   fix="按 11.33 forbidden 项结构改写为对象")
                    continue
                pattern = str(fb.get("pattern", "")).strip()
                if not pattern:
                    self.add_error("-", "FEATURE_CONTRACT_ENTRY_INVALID", "error", fbase + ".pattern",
                                   "forbidden 禁止项缺少 pattern（契约禁止出现的结构/模式描述）",
                                   "pattern 非空（取自契约原文）", "缺失", source_ref=src_ref,
                                   fix="补 pattern（从契约原文逐条抄录禁止模式）")
                    continue
                tokens = [w for w in re.split(r"[\s/，,、()（）\-]+", pattern) if len(w) >= 2]
                for pid, trace in all_traces:
                    hit = next((w for w in tokens if w.lower() in trace), "")
                    if hit:
                        self.add_error("-", "FEATURE_FORBIDDEN_PATTERN", "error", fbase + ".pattern",
                                       f"契约禁止模式「{pattern}」在页面 {pid} 中命中（词元「{hit}」）——禁止出现的结构不得出现在设计中",
                                       "声明为 forbidden 的禁止模式不出现在任何页面（线框/区块/字段/操作）",
                                       f"页面 {pid} 含「{hit}」", source_ref=src_ref,
                                       fix="移除页面中违反契约的结构；若 pattern 抄录有误则修正 forbidden 声明")
                        break
            ui_blueprint = entry.get("uiBlueprint")
            if ui_blueprint is None:
                continue
            if not isinstance(ui_blueprint, list):
                self.add_error("-", "FEATURE_UI_BLUEPRINT_INVALID", "error", base + ".uiBlueprint",
                               "uiBlueprint 界面蓝图对账数组非法（Feature 文档含分步线框图时必须逐界面登记，禁止选择性登记）",
                               "数组，每个元素对应 Feature 线框图中的一个界面",
                               type(ui_blueprint).__name__, source_ref=src_ref,
                               fix="按 11.33 uiBlueprint 条目结构逐界面登记（每个界面含 screen/pageId/structuralElements）")
                continue
            for j, bp in enumerate(ui_blueprint):
                bbase = f"{base}.uiBlueprint[{j}]"
                if not isinstance(bp, dict):
                    self.add_error("-", "FEATURE_UI_BLUEPRINT_INVALID", "error", bbase,
                                   "uiBlueprint 界面条目必须为对象", "含 screen/pageId/structuralElements 的对象",
                                   type(bp).__name__, source_ref=src_ref,
                                   fix="按 11.33 uiBlueprint 条目结构改写为对象")
                    continue
                screen = str(bp.get("screen", "")).strip()
                bp_page = str(bp.get("pageId", "")).strip()
                elements = bp.get("structuralElements")
                bad = []
                if not screen:
                    bad.append("screen（界面名，对应 Feature 线框图中的一个界面/步骤）")
                if not bp_page:
                    bad.append("pageId（该界面落位页面）")
                if not (isinstance(elements, list) and elements):
                    bad.append("structuralElements（非空数组：该界面的结构元素清单）")
                if bad:
                    self.add_error("-", "FEATURE_UI_BLUEPRINT_INVALID", "error", bbase,
                                   f"uiBlueprint 界面条目字段缺失或非法：{'；'.join(bad)}",
                                   "screen 非空、pageId 非空、structuralElements 为非空数组", "；".join(bad),
                                   source_ref=src_ref,
                                   fix="精读 Feature 线框图，把该界面拆成结构元素清单（步骤条/列表/进度条/操作列等）后补齐")
                    continue
                target_page = pages_by_id.get(bp_page)
                if target_page is None:
                    self.add_error("-", "FEATURE_TARGET_MISSING", "error", bbase + ".pageId",
                                   f"界面「{screen}」的落点页 pageId {bp_page} 不存在于 pages",
                                   "pageId 须为 pages 中已有页面", bp_page, source_ref=src_ref,
                                   fix="核对页面 ID；Feature 线框图的每个界面须有页面承载")
                    continue
                wf = target_page.get("wireframe") if isinstance(target_page.get("wireframe"), dict) else {}
                ascii_parts = []
                if wf:
                    main_ascii = str(wf.get("ascii", "") or "").strip()
                    if main_ascii:
                        ascii_parts.append(main_ascii.lower())
                    for variant in wf.get("variants") or []:
                        if isinstance(variant, dict):
                            v_ascii = str(variant.get("ascii", "") or "").strip()
                            if v_ascii:
                                ascii_parts.append(v_ascii.lower())
                ascii_text = " ".join(ascii_parts)
                shared_with = str(target_page.get("wireframeSharedWith", "") or "").strip()
                if not ascii_parts and not shared_with:
                    self.add_error("-", "FEATURE_UI_BLUEPRINT_NOT_DRAWN", "warning", bbase + ".pageId",
                                   f"界面「{screen}」落位页 {bp_page} 未绘制线框图（无 wireframe.ascii 也未声明共用线框）——Feature 界面蓝图须画进线框",
                                   "页面 wireframe.ascii 完整绘制该界面结构", "页面无线框图",
                                   source_ref=src_ref,
                                   fix="补绘该页面线框图，把 structuralElements 画进 ascii")
                    continue
                for k, element in enumerate(elements):
                    if not isinstance(element, str) or not str(element).strip():
                        self.add_error("-", "FEATURE_UI_BLUEPRINT_INVALID", "error", bbase + f".structuralElements[{k}]",
                                       "结构元素必须为非空字符串", "取自 Feature 线框图的结构元素描述",
                                       type(element).__name__ if not isinstance(element, str) else "空字符串",
                                       source_ref=src_ref, fix="补结构元素描述（步骤条/列表/进度条/操作列等）")
                        continue
                    element_text = str(element).strip()
                    tokens = [w for w in re.split(r"[\s/，,、()（）\-]+", element_text) if len(w) >= 2]
                    trace = page_traces.get(bp_page) or ""
                    if any(w.lower() in ascii_text for w in tokens):
                        continue
                    if any(w.lower() in trace for w in tokens):
                        self.add_error("-", "FEATURE_UI_BLUEPRINT_NOT_IN_WIREFRAME", "warning", bbase + f".structuralElements[{k}]",
                                       f"界面「{screen}」的结构元素「{element_text}」未画进线框图 ascii，仅出现在页面文本中——疑似只是文字提及未按 Feature 原图绘制",
                                       f"结构元素「{element_text}」在线框图 ascii 中有绘制痕迹", "ascii 未命中、页面文本命中",
                                       source_ref=src_ref,
                                       fix="把该结构元素画进线框图（区块标题/线框文本），而非只在字段说明提及")
                    else:
                        self.add_error("-", "FEATURE_UI_BLUEPRINT_ELEMENT_MISSING", "error", bbase + f".structuralElements[{k}]",
                                       f"界面「{screen}」的结构元素「{element_text}」在页面 {bp_page} 全文检索不到——Feature 线框结构未落位",
                                       f"页面（线框/区块/字段）可检索到结构元素「{element_text}」", f"页面 {bp_page} 未找到",
                                       source_ref=src_ref,
                                       fix="按 Feature 原图在该页面落位该结构元素并画进线框图；若登记有误则修正 structuralElements")

    # ---- 模板 ID 一致性与覆盖兜底（RULE-56，条件式）----
    def check_template_id_consistency(self):
        """模板 ID 一致性与覆盖兜底（warning 级）：
        1) coverage / capabilitySweep 声明了 appliesTo 却未命中任何页面（模板 ID 更名后 Product Design 侧沿用旧 ID
           会让覆盖落地校验被静默跳过，这里兜住"声明了却谁也不管"的情况）；
        2) templateSource / layoutSource / 组件来源等自由文本引用已废弃的旧模板 ID。
        appliesTo 匹配对旧 ID 自动归一为当前注册表 ID（兼容识别），归一后仍无法命中才判定为未命中。
        """
        dc = self.data.get("designContext") or {}
        pd = dc.get("productDesign") if isinstance(dc, dict) else None
        pd = pd if isinstance(pd, dict) else {}

        declared = []
        for key in ("coverage", "capabilitySweep"):
            for i, item in enumerate(pd.get(key) or []):
                if isinstance(item, dict):
                    declared.append((f"$.designContext.productDesign.{key}[{i}].appliesTo", item))

        text_refs = []
        for page, path in self.all_pages:
            tc = page.get("templateContract") or {}
            wf = page.get("wireframe") or {}
            rr = page.get("restoreRequirement") or {}
            if isinstance(tc, dict) and str(tc.get("templateSource", "")).strip():
                text_refs.append((str(tc.get("templateSource", "")),
                                  f"{path}.templateContract.templateSource", "模板来源说明"))
            if isinstance(wf, dict) and str(wf.get("layoutSource", "")).strip():
                text_refs.append((str(wf.get("layoutSource", "")),
                                  f"{path}.wireframe.layoutSource", "线框布局来源"))
            for i, comp in enumerate(rr.get("components") or []):
                if isinstance(comp, dict) and str(comp.get("source", "")).strip():
                    text_refs.append((str(comp.get("source", "")),
                                      f"{path}.restoreRequirement.components[{i}].source", "组件来源"))

        if not declared and not text_refs:
            return

        # 1) appliesTo 未命中任何页面（模板类条目只按模板口径命中：templateId / 页面类型中文名 / PD 模板名）
        page_ids = set()
        template_hits = set()
        for page, _path in self.all_pages:
            pid = str(page.get("id", "")).strip()
            if pid:
                page_ids.add(pid)
            tid = normalize_template_id(self.page_template(page))
            if tid:
                template_hits.add(tid)
            ptype = str(page.get("type", "")).strip()
            if ptype:
                template_hits.add(ptype)
        template_hits |= {k for k in self.pd_templates}
        template_hits |= {v.get("name") for v in self.pd_templates.values() if v.get("name")}
        for path, item in declared:
            targets = [str(t).strip() for t in (item.get("appliesTo") or []) if str(t).strip()]
            if not targets:
                continue
            cap = str(item.get("capability", "")).strip()
            if is_template_capability(cap):
                if any(normalize_template_id(t) in template_hits for t in targets):
                    continue
            elif any(normalize_template_id(t) in template_hits or t in page_ids
                     for t in targets):
                continue
            self.add_error("-", "TEMPLATE_COVERAGE_UNAPPLIED", "warning", path,
                           f"声明了 appliesTo（{', '.join(targets)}）却没有任何页面命中"
                           + (f"，能力/模板 {cap} 的覆盖落地校验会被静默跳过" if cap else "，覆盖落地校验会被静默跳过")
                           + "（模板 ID 更名后 Product Design 侧沿用旧 ID 的典型情形）",
                           "appliesTo 命中至少一个页面（页面 ID 或当前注册表 templateId）",
                           ", ".join(targets),
                           fix="核对 appliesTo：Product Design 若仍使用更名前的旧模板 ID，请更新为当前注册表 ID"
                               "（校验器已对旧 ID 自动归一）；确无适用页面时删除该 appliesTo 声明")

        # 2) 自由文本引用已废弃旧模板 ID
        for text, path, label in text_refs:
            old = legacy_template_id_in(text)
            if not old:
                continue
            self.add_error("-", "LEGACY_TEMPLATE_ID_REF", "warning", path,
                           f"{label} 引用了已废弃的旧模板 ID {old}，模板引用只允许使用当前注册表 ID",
                           f"当前注册表 ID（{LEGACY_TEMPLATE_ID_ALIASES[old]}）", old,
                           fix=f"把 {old} 更新为 {LEGACY_TEMPLATE_ID_ALIASES[old]}")

    # ---- 表单单列布局闭环（RULE-57）----
    def _form_field_names(self, page):
        """页面表单配置项的字段名（sections 中 formFields + 页面级 formFields）。"""
        names = []
        for section in self.page_sections(page):
            for field in section.get("formFields") or []:
                if isinstance(field, dict) and str(field.get("name", "")).strip():
                    names.append(str(field["name"]).strip())
                elif isinstance(field, str) and field.strip():
                    names.append(field.strip())
        for field in page.get("formFields") or []:
            if isinstance(field, dict) and str(field.get("name", "")).strip():
                names.append(str(field["name"]).strip())
            elif isinstance(field, str) and field.strip():
                names.append(field.strip())
        ordered = []
        for n in names:
            if n not in ordered:
                ordered.append(n)
        return ordered

    def _has_form_section(self, page):
        """页面是否含表单配置区块（用于非表单类模板页面）。"""
        for section in self.page_sections(page):
            if section.get("formFields"):
                return True
            blob = " ".join(str(section.get(k, "")) for k in ("title", "name", "type", "blockType"))
            lowered = blob.lower()
            if any(k in lowered for k in FORM_SECTION_KEYWORDS):
                return True
        return False

    def _page_ascii_texts(self, page):
        """页面所有线框 ascii（主结构图 + 各变体图），返回 [(标签, 文本)]。"""
        wf = self.page_wireframe(page)
        if isinstance(wf, str):
            return []
        texts = []
        main = str((wf or {}).get("ascii") or "")
        if main.strip():
            texts.append(("wireframe.ascii", main))
        for i, variant in enumerate((wf or {}).get("variants") or []):
            if not isinstance(variant, dict):
                continue
            text = str(variant.get("ascii") or "")
            if text.strip():
                label = str(variant.get("id") or variant.get("name") or (i + 1))
                texts.append((f"wireframe.variants[{label}].ascii", text))
        return texts

    def _form_list_field_names(self, page):
        """声明为动态表单列表的区块内的字段名集合（RULE-57 豁免口径）。
        区块声明 formList: true，或页面 formListBlocks 列表包含该区块 name/title 时，
        该区块的 formFields/filterFields 按"一行一个对象、一行多列"的动态列表对待。"""
        blocks = page.get("formListBlocks")
        block_names = {str(b).strip() for b in blocks if str(b or "").strip()} if isinstance(blocks, list) else set()
        names = []
        for section in self.page_sections(page):
            declared = bool(section.get("formList"))
            if not declared:
                title = str(section.get("name") or section.get("title") or "").strip()
                declared = bool(title and title in block_names)
            if not declared:
                continue
            for key in ("formFields", "filterFields"):
                for field in section.get(key) or []:
                    if isinstance(field, dict):
                        nm = str(field.get("name") or field.get("label") or "").strip()
                        if nm:
                            names.append(nm)
                    elif isinstance(field, str) and field.strip():
                        names.append(field.strip())
        return set(names)

    def _form_ascii_issues(self, text, field_names, form_list_names=None):
        """返回 (多列命中, label 换行命中)。多列 = 同一行出现 >=2 个已声明表单字段；
        label 换行 = 某行仅有字段名且无控件占位，而下一行有控件占位且无字段名。
        RULE-57 分流豁免：命中字段全部属于动态表单列表区块（formList 声明），或该行带
        行内删除/移除标记（一行一个对象、一行多列的动态列表画法），不计为多列错误。"""
        form_list_names = form_list_names or set()
        lines = str(text or "").splitlines()
        multi = []
        label_split = []
        for idx, line in enumerate(lines):
            hits = [n for n in field_names if n and n in line and n not in form_list_names]
            has_control = bool(re.search(CONTROL_PLACEHOLDER_PATTERN, line))
            if len(hits) >= 2:
                if FORM_LIST_INLINE_DELETE_PATTERN.search(line):
                    continue
                multi.append((hits, line.strip()))
                continue
            if len(hits) == 1 and not has_control:
                nxt = lines[idx + 1] if idx + 1 < len(lines) else ""
                nxt_hits = [n for n in field_names if n and n in nxt and n not in form_list_names]
                if re.search(CONTROL_PLACEHOLDER_PATTERN, nxt) and not nxt_hits:
                    label_split.append((hits[0], line.strip(), nxt.strip()))
        return multi, label_split

    def check_form_layout(self):
        """RULE-57 表单单列布局闭环（warning 级，条件式）：
        1) 表单承载页的 ascii（含 variants）同一行出现 >=2 个已声明表单字段 -> FORM_LAYOUT_MULTI_COLUMN；
        2) 字段名与其控件不在同一行（label 独占一行、控件在下一行）-> FORM_LAYOUT_LABEL_NOT_INLINE；
        3) 表单布局依据（Common Design 表单规范）未按锚点登记到 designReferences 或未在 readLedger 精读 ->
           FORM_LAYOUT_BASIS_UNREAD。表单布局以已读取的 Common Design 表单规范为准，本 Skill 不内置布局真值。

        动态表单列表分流（RULE-57 豁免口径）：绑定条件、映射规则、审批流条件等"一行一个对象、
        一行多列"的动态列表/行内可编辑表格（IxProFormList）不适用单列口径——
        区块声明 formList: true（或页面 formListBlocks 登记区块名）后，其字段同行多列不告警；
        未声明时，同行多字段且带行内删除/移除标记的行同样按动态列表行豁免（自动兜底）。
        """
        for page, ppath in self.all_pages:
            if self._page_reuse_business(page):
                continue
            if self._wireframe_shared_with(page):
                continue
            pid = page.get("id", "")
            tid = self.page_template(page)
            field_names = self._form_field_names(page)
            form_list_names = self._form_list_field_names(page)
            is_form_page = (tid in FORM_LAYOUT_TEMPLATE_IDS) or bool(field_names) or self._has_form_section(page)
            if not is_form_page:
                continue
            for label, text in self._page_ascii_texts(page):
                multi, label_split = self._form_ascii_issues(text, field_names, form_list_names) if field_names else ([], [])
                if multi:
                    hits, line = multi[0]
                    self.add_error(pid, "FORM_LAYOUT_MULTI_COLUMN", "warning",
                                   f"{ppath}.{label}",
                                   f"表单配置线框出现一行多配置项（同一行检测到 {len(hits)} 个字段：{'、'.join(hits)}），"
                                   f"表单单列是本 Skill 强制口径",
                                   "每行一个配置项（label 在左、控件在右，水平同一行）",
                                   line[:80], source_ref=RULE57_SOURCE,
                                   fix="把同一行的配置项拆成多行，每行只保留一个 label + 控件；"
                                       "表单单列口径见 04-demo-output-spec.md 11.22（RULE-57）与 03-demo-page-decomposition.md 4.3")
                if label_split:
                    fname, line, nxt = label_split[0]
                    self.add_error(pid, "FORM_LAYOUT_LABEL_NOT_INLINE", "warning",
                                   f"{ppath}.{label}",
                                   f"表单配置项「{fname}」的 label 与控件不在同一行（label 独占一行、控件在下一行）",
                                   "label 与控件在同一行，水平排列（label 左、控件右）",
                                   f"{line[:60]} / {nxt[:60]}", source_ref=RULE57_SOURCE,
                                   fix="把 label 与其控件画在同一行，例如：字段名    [控件占位]")
            # 表单布局依据（Common Design 表单规范）读取证据
            refs = (page.get("codingGuide") or {}).get("designReferences") or []
            ledger = getattr(self, "_design_ledger", None)
            if ledger is None:
                dc = self.data.get("designContext") or {}
                ledger = self._build_ledger(dc.get("readLedger")) if isinstance(dc, dict) else {}
                self._design_ledger = ledger
            solved = False
            for ref in refs:
                if not isinstance(ref, dict):
                    continue
                rf = str(ref.get("ref", "")).strip()
                doc, anchor = self._norm_ref(rf)
                if not any(h in doc.lower() for h in FORM_LAYOUT_BASIS_HINTS):
                    continue
                if not anchor:
                    continue
                status = ledger.get((doc, anchor)) or ledger.get((doc, "*"))
                if status == "read":
                    solved = True
                    break
            if not solved:
                self.add_error(pid, "FORM_LAYOUT_BASIS_UNREAD", "warning",
                               f"{ppath}.codingGuide.designReferences",
                               "表单承载页未按锚点登记 Common Design 表单规范作为表单布局依据，"
                               "或该依据未在 readLedger 命中 status=read",
                               "designReferences 含表单规范锚点（如 <Common Design 表单规范>#<章节>）且 readLedger 为 read",
                               "", source_ref=RULE57_SOURCE,
                               fix="读取 Common Design 表单规范并登记锚点级依据（表单布局：单列、label 与控件水平同一行），"
                                   "使表单布局结论可溯源；单列口径见 04-demo-output-spec.md 11.22（RULE-57）")

    # ---- 执行 ----
    # ---- RULE-58 详情页操作去重 ----
    @staticmethod
    def _action_row_name(item):
        """从操作行取操作名：dict 取 name/action/label；字符串取原值。"""
        if isinstance(item, dict):
            for k in ("name", "action", "label", "title"):
                v = str(item.get(k) or "").strip()
                if v:
                    return v
            return ""
        if isinstance(item, str):
            return item.strip()
        return ""

    def _detail_action_exempt_names(self, page, section=None):
        """操作去重豁免：页面级 detailActionDedupExempt + （区块级 excludedActions / actionExempt）。"""
        exempt = set()
        for k in ("detailActionDedupExempt", "detailActionExempt"):
            for nm in self._detail_name_list(page.get(k)):
                exempt.add(normalize_action_name(nm))
                exempt.add(norm(nm))
        if isinstance(section, dict):
            for k in ("excludedActions", "actionExempt"):
                for nm in self._detail_name_list(section.get(k)):
                    exempt.add(normalize_action_name(nm))
                    exempt.add(norm(nm))
        return exempt

    def check_detail_action_dedup(self):
        """RULE-58 详情页操作去重（条件式）。

        概览卡片/对象摘要（Zone A）已承载的对象级操作（编辑/重启/删除等）不应在底部按钮栏
        （footerActions）重复出现；按操作名同义归一比较，命中即 warning DETAIL_SUMMARY_ACTION_DUPLICATE。
        豁免：页面级 detailActionDedupExempt 与区块级 excludedActions/actionExempt。
        """
        for page, path in self.all_pages:
            footer = self.page_footer_actions(page)
            if not isinstance(footer, (list, tuple)) or not footer:
                continue
            pid = str(page.get("id", ""))
            summary_names = {}
            for si, section in enumerate(self.page_sections(page)):
                if not isinstance(section, dict):
                    continue
                if self._classify_detail_section(section) != "summary":
                    continue
                exempt = self._detail_action_exempt_names(page, section)
                for item in section.get("actions") or []:
                    nm = self._action_row_name(item)
                    if not nm:
                        continue
                    key = normalize_action_name(nm)
                    if key in exempt or norm(nm) in exempt:
                        continue
                    summary_names.setdefault(key, nm)
            if not summary_names:
                continue
            page_exempt = self._detail_action_exempt_names(page)
            for fi, act in enumerate(footer):
                nm = self._action_row_name(act)
                if not nm:
                    continue
                key = normalize_action_name(nm)
                if key in page_exempt or norm(nm) in page_exempt:
                    continue
                if key in summary_names:
                    self.add_error(
                        pid, "DETAIL_SUMMARY_ACTION_DUPLICATE", "warning",
                        f"{path}.footerActions[{fi}]",
                        f"操作「{nm}」已由顶部概览卡片承载（概览卡片操作「{summary_names[key]}」），不应在底部按钮栏重复出现",
                        "底部按钮栏只保留页面级动作（关闭/上一个/下一个/取消/确定）；编辑/重启/删除等对象级操作只在概览卡片承载",
                        nm, source_ref=RULE58_SOURCE,
                        fix="从 footerActions 移除该操作（保留概览卡片承载），或删除概览卡片操作只留底部；若确需两处重复，写入 detailActionDedupExempt 并说明原因")

    # ---- RULE-59 复用业务组件容器 ----
    def _reuse_basis_state(self, page):
        """返回 (basis, 是否满足依据要求, 说明)。"""
        decl = self._page_reuse_business(page) or {}
        basis = str(decl.get("basis") or "").strip().lower()
        refs = [r for r in ((page.get("codingGuide") or {}).get("designReferences") or [])
                if isinstance(r, dict)]
        dc = self.data.get("designContext") or {}
        ledger = self._build_ledger(dc.get("readLedger") if isinstance(dc, dict) else None)
        if basis in ("product-design", "product", "pd", "产品设计"):
            target = str(decl.get("componentRef") or "").strip()
            doc, _anchor = self._norm_ref(target)
            for r in refs:
                try:
                    if str(r.get("source") or "").strip() != "product-design":
                        continue
                except Exception:
                    continue
                rdoc, ranchor = self._norm_ref(str(r.get("ref") or ""))
                if doc and rdoc == doc:
                    if not ranchor:
                        return (basis, False, f"依据 {r.get('ref')} 未使用锚点级引用")
                    status = ledger.get((rdoc, ranchor))
                    if status is None:
                        status = ledger.get((rdoc, "*"))
                    if status != "read":
                        return (basis, False, f"依据 {r.get('ref')} 未精读命中（readLedger 无 status=read）")
                    return (basis, True, str(r.get("ref")))
            return (basis, False, "未在 codingGuide.designReferences 登记 Product Design 组件依据")
        if basis in ("code", "代码"):
            ev = str(decl.get("codeEvidence") or "").strip()
            if not ev:
                return (basis, False, "basis=code 但未填写 codeEvidence（形如 src/xxx#Symbol）")
            return (basis, True, ev)
        return (basis or "(未填写)", False, "basis 必须为 product-design 或 code")

    def check_business_reuse(self):
        """RULE-59 复用业务组件容器闭环（条件式）。

        需求延伸容器（按钮点击/表格字段点击/详情字段点击/行操作/导入/导出）命中 Product Design 业务封装组件，
        或代码识别已知业务封装组件时：不单独绘制线框与页面内容说明，只在宿主页面简要交代复用的组件。
        声明复用 -> 校验"未过度描述 / 依据实读 / 范围合法 / 宿主有交代"；未声明但命中 PD 业务组件候选 -> 反向提示。
        """
        pages = list(self.all_pages)
        all_page_dicts = [pg for pg, _ in pages]
        by_id = {}
        for page, path in pages:
            pid = str(page.get("id", ""))
            if pid:
                by_id.setdefault(pid, (page, path))

        for page, path in pages:
            pid = str(page.get("id", ""))
            decl = self._page_reuse_business(page)

            if not decl:
                # 反向候选：容器 + 有宿主入口 + 已引用 Product Design 组件依据，但未声明复用
                tid = str(self.page_template(page) or "").lower()
                if "modal" not in tid and "drawer" not in tid:
                    continue
                refs = [r for r in ((page.get("codingGuide") or {}).get("designReferences") or [])
                        if isinstance(r, dict)]
                has_pd_component = any(
                    str(r.get("source") or "").strip() == "product-design"
                    and ("component" in str(r.get("ref") or "").lower() or "组件" in str(r.get("ref") or ""))
                    for r in refs)
                if has_pd_component and self._container_has_entry(page, all_page_dicts):
                    self.add_error(
                        pid, "REUSE_CANDIDATE_UNMARKED", "warning",
                        f"{path}.reuseBusinessComponent",
                        f"页面「{page.get('name', pid)}」是宿主页面动作延伸出来的容器，且已引用 Product Design 业务封装组件，但未声明复用，疑似应直接复用业务组件而非自绘",
                        "若该容器就是 Product Design 定义的业务封装功能，声明 reuseBusinessComponent（decision=reuse + componentRef + hostPageId + trigger + basis）；确需自绘则补充说明",
                        "未声明 reuseBusinessComponent", source_ref=RULE59_SOURCE,
                        fix="命中业务封装组件时不要自绘样式：声明 reuseBusinessComponent.decision=reuse，并删除该页面的线框与页面内容区块，只在宿主页面简要交代复用的组件")
                continue

            # 1) 过度描述（声明复用却仍自绘）
            over = []
            wf = self.page_wireframe(page) or {}
            if str(wf.get("ascii") or "").strip():
                over.append("wireframe.ascii")
            if wf.get("regions"):
                over.append("wireframe.regions")
            for si, section in enumerate(self.page_sections(page)):
                if not isinstance(section, dict):
                    continue
                for k in REUSE_SECTION_FIELD_KEYS:
                    if section.get(k):
                        over.append(f"sections[{si}].{k}")
            if self.page_footer_actions(page):
                over.append("footerActions")
            if over:
                self.add_error(
                    pid, "REUSE_CONTAINER_OVER_DESCRIBED", "error",
                    f"{path}",
                    f"页面「{page.get('name', pid)}」已声明复用业务组件，但仍单独绘制/描述了：{'、'.join(over)}；复用容器的样式以业务实现为准，自绘会误导编码",
                    "复用业务组件容器不产出 wireframe.ascii / wireframe.regions / 区块字段（formFields/tableFields/detailFields/cardFields/filterFields）/ footerActions",
                    "、".join(over), source_ref=RULE59_SOURCE,
                    fix="删除该页面的线框、区块字段与底部按钮栏配置，只在宿主页面写一行「点击 X 打开 Y（复用 Product Design 组件 Z，不单独绘制）」；codingGuide 保留一条 mode=reuse 的开发项指向该组件")

            # 2) 依据实读
            basis, ok, detail = self._reuse_basis_state(page)
            if not ok:
                self.add_error(
                    pid, "REUSE_BASIS_UNREAD", "warning",
                    f"{path}.reuseBusinessComponent.basis",
                    f"复用依据不可用：{detail}",
                    "basis=product-design 时需在 codingGuide.designReferences 锚点级登记并在 readLedger 命中 status=read；basis=code 时需填写 codeEvidence",
                    f"basis={basis}; {detail}", source_ref=RULE59_SOURCE,
                    fix="补齐 Product Design 组件依据（锚点级 + 实读留痕）或代码证据，禁止凭印象声明复用")

            # 3) 适用范围
            scope_problems = []
            trigger = str(decl.get("trigger") or "").strip()
            if trigger not in REUSE_ALLOWED_TRIGGERS:
                scope_problems.append(
                    f"trigger「{trigger or '(未填写)'}」不在允许枚举内（{'/'.join(REUSE_ALLOWED_TRIGGERS)}）")
            host_id = str(decl.get("hostPageId") or "").strip()
            host_entry = by_id.get(host_id)
            if not host_id or host_entry is None:
                scope_problems.append(f"hostPageId「{host_id or '(未填写)'}」缺失或不在本次需求范围内")
            if not self._container_has_entry(page, all_page_dicts):
                scope_problems.append("未识别到宿主页面入口（独立页面不允许声明复用，需求直接点名的页面必须完整产出）")
            if scope_problems:
                self.add_error(
                    pid, "REUSE_SCOPE_INVALID", "warning",
                    f"{path}.reuseBusinessComponent",
                    f"复用声明超出允许范围：{'；'.join(scope_problems)}",
                    "复用仅适用于需求延伸容器：由宿主页面的按钮点击/表格字段点击/详情字段点击/行操作/导入导出触发，且宿主在本次范围内",
                    "；".join(scope_problems), source_ref=RULE59_SOURCE,
                    fix="补齐 hostPageId 与合法 trigger，或确认该页面是需求主页面（主页面不允许复用，需完整绘制线框与内容说明）")

            # 4) 宿主交代
            if host_entry is not None:
                host_page = host_entry[0]
                blob = page_text_blob(host_page)
                cname = str(page.get("name") or "")
                tokens = [cname, pid]
                cref = str(decl.get("componentRef") or "")
                if "#" in cref:
                    tokens.append(cref.split("#")[-1])
                has_name = any(t and len(t) >= 2 and t in blob for t in tokens)
                has_marker = any(mk in blob for mk in REUSE_HOST_NOTE_MARKERS)
                if not (has_name and has_marker):
                    self.add_error(
                        pid, "REUSE_HOST_NOTE_MISSING", "warning",
                        f"{path}.reuseBusinessComponent.hostPageId",
                        f"宿主页面「{host_page.get('name', host_id)}」未交代「打开 {cname or pid}（复用业务组件，不单独绘制）」",
                        f"宿主页面文本中同时出现容器名/ID（{cname or pid}）与复用标记（{'/'.join(REUSE_HOST_NOTE_MARKERS)} 之一）",
                        f"has_name={has_name}; has_marker={has_marker}", source_ref=RULE59_SOURCE,
                        fix="在宿主页面的线框或内容说明里补一行：点击[触发元素] -> 打开 <容器名>，复用 Product Design 组件 <组件名>，不单独绘制")

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
        self.check_wireframe_flat_filter_order()
        # ---- 概览区形态还原闭环（RULE-69）：概览区块形态声明与线框痕迹对账（条件式，概览模板/概览区域启用）----
        self.check_overview_style()
        # ---- 区域规范精读闭环（RULE-70）：表格/概览/树区块存在时对应规范文档必须已精读（存在性触发）----
        self.check_region_basis_reading()
        # ---- 表格行内操作收纳检验（RULE-71）：行内操作超阈值未收纳提醒 ----
        self.check_action_column_overflow()
        # ---- 线框图列对齐一致性（RULE-47）：右边界错位/两列结构断裂提示 ----
        self.check_wireframe_column_alignment()
        # ---- 页面平铺闭环（RULE-35）：children 禁止内嵌完整页面设计对象 ----
        self.check_child_page_flattened()
        # ---- 字段完整性闭环（RULE-36）：需求明确字段必须落位或排除 ----
        self.check_requirement_fields()
        # ---- 字段形态键契约（RULE-41）：内容必须写在渲染器实际渲染的键上，跨形态套键阻断 ----
        self.check_field_key_contract()
        self.check_tooltip_content()
        # ---- 下拉选项完整性（RULE-48）：固定选项型下拉须完整列出选项，缺项阻断/截断指纹告警 ----
        self.check_option_completeness()
        # ---- 表格与详情字段一致性闭环（RULE-38）：表格展示字段必须在对应详情容器中存在 ----
        self.check_table_detail_field_consistency()
        # ---- 详情页字段去重（RULE-49）：概览卡片/对象摘要已展示字段不应在描述列表重复 ----
        self.check_detail_field_dedup()
        # ---- 按钮/可点击操作表（RULE-50）：高影响/二次确认/局部面板须写清组件与文案，来源优先 PD>CD ----
        self.check_action_table()

        # ---- 表格区按钮位置（RULE-51）：表格关联按钮须统一置于表格区左上角工具栏 ----
        self.check_table_button_placement()
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
        # ---- 需求入口落位闭环（RULE-52）：PRD 点名入口必须有落点（条件式，声明 requirementEntryPoints 时启用）----
        self.check_requirement_entry_points()
        # ---- 页面定位证据闭环（RULE-53）：被定位的既有页面须携带可核验身份证据（禁止文件名定位）----
        self.check_page_identity()
        # ---- 组件形态描述闭环（RULE-54）：多形态组件须写明选用形态（条件式，字段声明 formCandidates 时启用）----
        self.check_component_form()
        # ---- 能力发现完整性（RULE-55）：PD 声明的能力须全扫并判定命中/未命中（条件式，声明 coverage 时启用）----
        self.check_capability_sweep()
        # ---- 模板 ID 一致性与覆盖兜底（RULE-56）：appliesTo 未命中/自由文本引用旧 ID（旧 ID 自动归一）----
        self.check_template_id_consistency()
        # ---- 表单单列布局闭环（RULE-57）：表单承载页线框必须单列 + 表单布局依据须实读 ----
        self.check_form_layout()
        self.check_detail_action_dedup()
        self.check_business_reuse()
        self.check_template_sync()
        self.check_carrier_sweep()
        self.check_change_sync()
        # ---- Feature 契约落位闭环（RULE-68）：CD Feature 功能契约保留/调整/禁止三级约束对账（条件式）----
        self.check_feature_contract()
        self.check_footer_ascii_order()
        self.check_footer_ascii_alignment()
        # ---- 共用线框差异描述闭环（RULE-62）：相同 UI 页面共用主页面线框，从页面只描述差异 ----
        self.check_wireframe_shared()
        # ---- 设计规范补齐落位闭环（RULE-63）：设计规范补齐项须落进 demo-spec 并有落点（条件式）----
        self.check_design_completeness()

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

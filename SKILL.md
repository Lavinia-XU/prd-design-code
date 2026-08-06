---
name: prd-design-code
description: 将B端需求转为可视化Demo设计说明和AI Coding指导，覆盖页面结构、交互逻辑、边界状态与Mock数据；当用户需要根据PRD、截图、代码或想法生成可实现的Demo方案、HTML说明书或编码提示词时使用
metadata:
  frieren.tags: "需求设计开发"
---

# 需求 Demo 设计与 Coding 指导助手

## 任务目标

- 本 Skill 用于：将B端产品需求、PRD、截图、Demo代码或原型资料，转化为可直观看到页面效果的Demo设计说明和可直接指导AI Coding的实现规格。
- 能力包含：确定Demo范围、精简需求理解、输出页面总览、生成HTML设计说明书、补充交互逻辑与边界状态、形成AI Coding提示词，并在用户确认后按页面执行Coding计划。
- 触发条件：用户需要把需求做成Demo、希望AI直接生成页面、需要页面设计说明书、需要补充搜索筛选/二次确认/空状态/极端情况等交互逻辑，或希望基于设计说明书立即开发Demo。

## 核心工作流程

### 第一步：确定需求输入与 Demo 范围

- 如果用户提供PRD、截图、原型、录屏、Demo代码、业务说明或字段清单，直接提取需求内容并进入Demo范围判断。
- 如果用户只说“帮我分析需求”“帮我做Demo”但没有提供任何资料，先要求用户补充需求内容、Demo范围、代码范围或相关文档，禁止自行发挥。
- 如果资料较大，先做范围过滤：区分平台内操作、平台内展示、线下流程、外部系统、技术实现、商业/运营背景，只将平台内可展示、可操作、可演示的内容进入Demo设计。
- 如果当前存在Demo代码环境、用户指定代码范围、业务设计Skill提到相关参考模块，或用户自己提到某个已有模块，读取相关代码作为页面拆解、交互说明和Coding指导输入，重点关注路由、菜单、相似页面、组件组织、Mock数据和已有交互习惯。

### 第二步：提炼核心用户、场景与功能目标

只保留服务于页面设计和Coding的需求分析内容：

1. 需求概括：简要概述本需求要解决什么问题，不限制为一句话。
2. 体验目标：先读取 [体验目标撰写规范](references/01-workflow/02-experience-goal-writing.md)，直接基于需求分析内容输出3条体验目标和画面感。
3. 主要用户角色：围绕业务需求场景识别主要用户角色，输出1-2个不同岗位的真实使用者；如果只有1个岗位就只输出1个，如果超过2个且确实都是主要角色，可以输出3个，说明岗位职责、核心任务和Demo关注点。
4. 核心场景与功能映射：控制在3-5个重点场景，不输出边缘场景，不输出故事版和子场景未来旅程。

### 第三步：生成 Demo 页面总览

1. 先读取 [Demo设计规格](references/01-workflow/03-demo-design-spec.md)，执行Demo范围过滤、页面拆解和导航结构设计。
2. 页面拆解和导航结构设计后，如果存在业务设计Skill，必须优先查阅业务设计Skill中的产品介绍、页面导航结构、页面说明、页面设计规范和同类模块设计规则，校准菜单层级、命名、页面归属、容器选择、字段表达和弹窗/抽屉等交互方式。
3. 业务设计Skill识别方式：先通过Skill名称和描述判断；名称中包含深信服产品英文缩写 aTrust、ZTP、DSP、SASE、XDR、MSS、DR、aES，或描述中同时包含具体深信服产品名称、设计、业务设计规范等关键词时，可判定为业务设计Skill；例如“为深信服下一代端点安全产品路由策略类产品设计与前端交付需求”可作为业务设计Skill使用。
4. 只有业务设计Skill没有覆盖、没有说清楚，或用户没有提供业务设计Skill时，按需求命中的主题读取 [主题设计库](references/02-theme-patterns/)；主题模板仍未覆盖时，再按需读取 [功能点设计库](references/03-function-patterns/) 和 [基础设计库](references/04-design-basics/) 中的页面类型、布局、表单、表格、交互和状态规则，用通用B端设计规则补充页面类型、页面容器、表格、表单、详情、二次确认和多层级下钻设计。
5. 如果存在可用代码环境，读取相关模块代码并校准页面拆解：判断应复用已有页面、在已有菜单下新增页面、组合成Tab，还是使用弹窗/抽屉承载；同时参考已有代码中的组件、状态、Mock数据和交互实现方式。
6. 生成页面关键交互说明时，必须综合五类信息：需求资料中明确写出的操作、流程、状态和限制；业务设计Skill中的既有产品规范；可用Demo代码环境中的已有模块实现；通用设计库中的B端页面设计模式；AI基于业务目标、用户任务和页面容器类型做出的合理补齐。
6. 对话框主体只输出到“页面总览表”为止，禁止在对话框继续输出逐页设计说明、Demo交互与逻辑规则、Mock数据细节或AI Coding完整提示词。

对话框输出上限：需求与Demo范围、核心用户与场景、导航结构、页面总览表、待确认问题、HTML文件路径和简短说明。详细页面内容必须进入HTML。

### 第四步：输出待确认问题并等待用户确认

页面总览表输出后，必须先输出待确认问题，让用户判断影响方案准确性的关键事项。此步骤是生成HTML设计说明书前的强制卡点，禁止在同一轮直接继续生成完整HTML和AI Coding指导。

- 问题来源：对第三步页面总览、导航结构、页面容器、用户旅程闭环、关键业务规则、代码环境参考结果和业务设计Skill差异进行检查。
- 问题范围：只保留会影响整体设计、导航菜单结构、页面容器选择、核心操作闭环、状态流转、关键业务规则、权限边界或AI Coding实现方式的问题。
- 专业补齐：需求颗粒度不足时，先自动补齐能保证用户旅程、功能点、数据、操作、状态和页面层级闭环的设计；不要把字段命名、按钮文案、普通筛选项、常规表格字段等可合理补齐的细节全部抛给用户确认。
- 数量控制：最多10个，优先3-6个；不要询问颜色、按钮微调、普通文案等低影响问题。
- 输出要求：每个问题必须包含“待确认问题、影响范围、当前默认假设”；如果存在阻断Demo成立的问题，必须标记为“需确认后继续”。
- 对话策略：输出待确认问题后停止，等待用户确认或修正；用户确认后，再进入第五步生成HTML设计说明书。
- 例外情况：如果没有任何会影响方案准确性的待确认问题，明确写“暂无关键待确认问题，按当前页面总览继续生成HTML说明书”，然后可继续进入第五步。

### 第五步：生成 HTML 设计说明书与 AI Coding 指导

用户确认待确认问题后，先判断确认结果是否影响第三步已输出的导航结构和页面总览表；若有影响，必须先按用户确认后的内容重新输出更新版导航结构和页面总览表，再生成HTML说明书。页面总览之后的详细页面内容直接写入HTML说明书，不在对话框展开。待确认问题只放在对话框的页面总览表之后，不写入HTML说明书。

- 确认结果回写：用户对菜单层级、页面容器、页面增删、入口方式、关键业务规则或Coding方式的确认，必须同步更新导航结构、页面总览表和HTML输入JSON，禁止沿用确认前的旧总览。
- 逐页设计说明：页面类型、页面目标、页面布局、页面内容区块和底部操作。
- 页面级Demo交互与逻辑规则：搜索、筛选、重置、排序、分页、新增、编辑、查看、删除、处置、启用、禁用、二次确认、表单校验等规则必须整合到对应页面的区块说明或底部操作中，不单独生成页面内关键交互章节或页面交互规则章节。
- 状态与极端情况：状态值范围、空状态、搜索无结果、加载态、异常态、无权限态、长文本、0值、空字段、批量选择为空等，按影响对象整合到对应页面区块说明中。
- AI Coding指导：总结性的实现建议与完整提示词放在HTML总览页；针对单个页面的组件、Mock数据和前端逻辑要求放在对应页面里。

HTML生成方式：先将结构化内容保存为JSON文件，再调用脚本：`python scripts/generate_demo_spec_html.py --input ./demo-spec.json --output ./demo-design-spec.html`。

HTML标题使用“XX需求设计说明书”。左侧为目录结构，第一页为总览；后续按页面层级生成目录，点击左侧目录后右侧切换展示每个页面的内容和页面级Coding指导。页面交互说明、筛选范围、状态值、表单下拉选项和边界状态必须整合在页面内容区块说明里。目录需体现页面层级关系，例如：总览、一级页面、其下新增/编辑/详情等子页面，再到更深层子页面。

### 第六步：询问并执行 Coding 计划

HTML设计说明书生成后，先提醒用户查看HTML页面内容；如果HTML中有需要调整的页面结构、字段、交互、状态或说明内容，用户可以直接告知修改点。随后输出具体Coding计划并询问用户是否确认执行；只有用户明确同意后，才开始Coding执行。这里确认的是Coding相关内容，业务设计相关内容应已在第四步待确认问题中完成确认，不要在此重新展开业务方案讨论。若用户在确认Coding前提出HTML修改意见，先更新HTML设计说明书并重新生成一次最新HTML，再重新输出Coding计划确认。

- Coding计划必须说明：本次开发页面的导航路径，包括一级菜单、二级菜单、三级菜单、Tab或页面入口；若需要新增路由或复用已有菜单，也要明确写出。
- Coding计划必须区分：哪些页面由AI全新开发，哪些页面参考已有已开发页面的代码实现，并写明参考页面或模块名称。
- Coding计划必须列出：页面内哪些功能点会复用已有代码模块、组件、样式、Mock数据或交互逻辑，不重新开发；哪些功能点需要新增实现。
- HTML修改处理：如果用户在开始Coding前反馈HTML内容需要修改，先更新设计说明JSON并重新生成最新HTML，再基于最新HTML重新输出Coding计划；不得基于旧HTML直接开始开发。
- 执行拆分：按HTML左侧页面目录和页面层级拆分Coding任务，一个页面完成并自检后，再开始下一个页面；不要一次性跨多个页面无序开发。
- 页面开发顺序：优先开发父级主页面，再开发由主页面打开的新增、编辑、详情、弹窗或抽屉等子页面，确保入口和跳转链路可运行。
- 每页完成反馈：每完成一个页面，简要告知用户“已完成 <页面ID-页面名称> 的开发，接下来开发 <页面ID-页面名称>”，并说明已完成的关键界面、交互和状态。
- 全部完成反馈：所有页面开发完成后，告知用户“Demo已开发完毕，请告知有哪些需要调整的”，并提示用户可以从页面结构、字段、交互、状态、样式或Coding效果上提出修改。

## 使用示例

- 示例1：
  - 场景/输入：用户提供数据防泄密事件分析PRD，希望直接生成可Coding的Demo设计方案。
  - 对话框产出：Demo范围、核心用户与场景、导航结构、页面总览表、HTML设计说明书路径。
  - HTML产出：逐页设计说明、交互逻辑、Mock数据要求和AI Coding提示词；随后输出具体Coding计划并询问用户是否确认执行。

- 示例2：
  - 场景/输入：用户在AI编程环境中打开已有Demo代码，希望补齐交互逻辑和极端情况。
  - 对话框产出：已识别页面总览和HTML文件路径。
  - HTML产出：每个页面的内容说明、搜索筛选、二次确认、空状态、异常态、Mock数据覆盖规则和Coding指导。

- 示例3：
  - 场景/输入：用户提供一个小需求，已明确菜单、字段和操作。
  - 对话框产出：快速范围过滤、导航结构、页面总览表、HTML文件路径。
  - HTML产出：逐页页面内容与交互规则。

## 资源索引

- 脚本：见 [scripts/generate_demo_spec_html.py](scripts/generate_demo_spec_html.py)（用途与参数：读取结构化Demo设计JSON，生成带左侧目录和右侧切换内容的HTML说明书；参数为`--input`与`--output`）
- 资产：见 [assets/demo-spec-template.html](assets/demo-spec-template.html)（用途：HTML说明书模板，由脚本读取并注入设计数据）
- 工作流规范：见 [references/01-workflow/01-output-templates.md](references/01-workflow/01-output-templates.md)（何时读取：需要按标准结构输出对话框摘要、待确认问题、HTML生成后的说明和Coding执行提示时）
- 工作流规范：见 [references/01-workflow/02-experience-goal-writing.md](references/01-workflow/02-experience-goal-writing.md)（何时读取：提炼需求分析后撰写体验目标和画面感时）
- 工作流规范：见 [references/01-workflow/03-demo-design-spec.md](references/01-workflow/03-demo-design-spec.md)（何时读取：生成导航结构、页面总览、逐页设计说明和HTML输入JSON前）
- 工作流规范：见 [references/01-workflow/04-coding-guidelines.md](references/01-workflow/04-coding-guidelines.md)（何时读取：补充搜索筛选、二次确认、状态规则、Mock数据、AI Coding提示词和执行Coding计划时）
- 工作流规范：见 [references/01-workflow/05-quality-and-rules.md](references/01-workflow/05-quality-and-rules.md)（何时读取：输出前做质量自检或确认禁止事项时）
- 主题设计库：见 [references/02-theme-patterns/strategy-management.md](references/02-theme-patterns/strategy-management.md)（何时读取：需求涉及策略、规则、白名单、规则组时）
- 功能点设计库：见 [references/03-function-patterns/tag-management.md](references/03-function-patterns/tag-management.md)（何时读取：需求涉及标签、打标、标签筛选、标签关联对象时）
- 功能点设计库：见 [references/03-function-patterns/import.md](references/03-function-patterns/import.md)（何时读取：需求涉及批量导入、模板下载、文件解析、导入校验或失败明细时）
- 功能点设计库：见 [references/03-function-patterns/export.md](references/03-function-patterns/export.md)（何时读取：需求涉及批量导出、导出范围、导出字段、文件生成或文件下载时）
- 功能点设计库：见 [references/03-function-patterns/execution-cycle.md](references/03-function-patterns/execution-cycle.md)（何时读取：需求涉及执行周期、定时任务周期、每天每周每月联动选择或周期表单配置时）
- 功能点设计库：见 [references/03-function-patterns/priority-configuration.md](references/03-function-patterns/priority-configuration.md)（何时读取：需求涉及优先级、策略位置、规则位置、移动到某条数据之前或之后时）
- 基础设计库：见 [references/04-design-basics/01-page-types.md](references/04-design-basics/01-page-types.md)（何时读取：判断页面类型时）
- 基础设计库：见 [references/04-design-basics/02-table-patterns.md](references/04-design-basics/02-table-patterns.md)（何时读取：设计表格、工具栏、搜索筛选、分页排序和批量操作时）
- 基础设计库：见 [references/04-design-basics/03-form-patterns.md](references/04-design-basics/03-form-patterns.md)（何时读取：设计表单、配置项、步骤条、字段校验和未保存提醒时）
- 基础设计库：见 [references/04-design-basics/04-layout-patterns.md](references/04-design-basics/04-layout-patterns.md)（何时读取：设计详情页、Tab、页面层级和内容组织时）
- 基础设计库：见 [references/04-design-basics/05-interaction-patterns.md](references/04-design-basics/05-interaction-patterns.md)（何时读取：设计二次确认、高危操作、反馈和容器使用边界时）
- 基础设计库：见 [references/04-design-basics/06-state-patterns.md](references/04-design-basics/06-state-patterns.md)（何时读取：补充空状态、加载态、异常态、无权限和极端情况时）
- 示例：见 [references/05-examples/demo-design-examples.md](references/05-examples/demo-design-examples.md)（何时读取：需要参考HTML说明书输入JSON、页面说明颗粒度或完整输出示例时）

## 注意事项

- 对话框主体输出只到页面总览表；页面总览之后仅允许补充待确认问题、HTML路径和简短说明，逐页设计说明、Demo交互与逻辑规则、Mock数据细节和完整AI Coding提示词必须进入HTML。
- 输出目标是让用户能直观看到需求对应Demo，并让AI Coding工具能直接实现。
- 需求分析必须精简，只保留影响页面设计和Coding的信息；体验目标输出3条目标选项和画面感，作为需求分析中的小段内容。
- 页面设计必须包含页面区块、字段展示、按钮顺序、点击结果、状态变化和基础逻辑限制，但这些详细内容写入HTML。
- 页面关键交互说明不能只写“点击查看”“点击提交”，必须说明触发入口、打开容器、页面反馈、数据变化、校验规则、成功/失败反馈、状态联动和必要的边界状态。
- HTML说明书左侧目录只包含总览和按页面层级组织的页面目录；不包含待确认问题、全局交互规则页或独立Coding指导页。
- 生成HTML设计说明书后，必须先提醒用户查看HTML页面内容；如用户反馈HTML需要修改，先更新并重新生成最新HTML，再输出具体Coding计划并询问用户是否确认执行。Coding计划只确认导航路径、全新开发页面、参考已有页面、复用已有功能点、新增实现功能点和开发顺序，不重新确认业务设计内容。
- 不确定信息明确标记为待确认，不自行补全真实业务事实。
- 禁止使用开发语言和开发状态，页面文案、字段和状态必须使用用户语言。

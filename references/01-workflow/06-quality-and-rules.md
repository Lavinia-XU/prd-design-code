# 质量自检机制与规则

## 目录

1. [质量自检机制](#1-质量自检机制)
2. [禁止事项](#2-禁止事项)
3. [表达风格要求](#3-表达风格要求)
4. [Coding执行检查](#4-coding执行检查)

## 1. 质量自检机制

每次输出前必须完成以下检查。

### 1.1 对话框输出边界检查

- 对话框是否只输出到页面总览表。
- 阻塞性业务理解问题是否在页面拆解前提出并等待确认，是否没有拖到页面总览后才暴露业务模型理解错误。
- 页面总览表之后是否先输出待确认问题，并等待用户确认。
- 用户确认待确认问题前，是否没有直接生成HTML说明书、HTML文件路径或AI Coding完整指导。
- 是否没有在对话框展开逐页设计说明、页面区块、交互逻辑、状态规则、Mock数据细节或完整AI Coding提示词。
- 用户确认后，若确认内容影响导航结构或页面总览，是否先重新输出更新后的导航结构和页面总览表，再生成HTML说明书。
- 用户确认后，页面总览之后的详细内容是否已写入HTML说明书。
- 是否在输出页面导航结构前，已随主要用户与场景输出体验目标（3条目标选项与一段画面感），且体验目标只出现在对话框、未写入HTML说明书。

### 1.2 Demo范围检查

- 是否在无输入时先要求用户补充需求资料，而不是自行发挥。
- 是否先区分平台内操作、平台内展示、线下流程、外部系统、技术实现、商业/运营背景。
- 是否只把平台内可展示、可操作、可演示的内容进入Demo页面设计。
- 是否把线下流程、外部系统和技术实现仅作为背景、约束或待确认信息。
- 是否在拆页面前完成“功能交付项 vs 语境”切分，页面总览中的每个页面是否都能回溯到一条功能交付项。
- 匹配 Product Design 时，是否未因需求未提及而丢弃 PD 声明为需求已建设对象/页面类型固有能力的内容；此类内容是否已作为产品规范补齐项默认为范围来源（功能交付项来源之一）。
- 是否将客户交付旅程、验收语境或现场动作（如设备上架、拔线回接）错拆成功能页面；此类内容是否已改归背景或待确认。

### 1.3 需求精简检查

- 页面拆解前是否已把PRD/功能清单/Playbook/口述需求解析为结构化业务任务模型（角色/目标/业务对象/动作/判断信息/状态/结果/异常），是否形成 requirementUnderstanding 并写入 Design Context。
- 是否区分需求事实、设计推导、AI补齐、产品规范补齐和待确认项并按来源标记；AI补齐是否仅限展示层与常规交互，是否未补造业务对象、权限、状态流转、数量限制等业务事实；产品规范补齐项是否来自匹配 Product Design 且登记可定位锚点。
- 是否满足业务理解准出条件后才进入页面拆解（角色/业务对象/核心动作/关键判断信息明确，成功结果与主要异常明确，未决问题不改变业务模型或页面结构）。
- 是否只保留需求概括、主要用户角色和核心场景。
- 需求概括是否简明说明问题背景和要解决的问题，不强制限制为一句话。
- 用户角色是否是真实产品使用者，并围绕业务需求场景识别主要角色；通常输出1-2个不同岗位，只有1个岗位时只输出1个，超过2个且确实都是主要角色时最多输出3个。
- 核心场景是否控制在3-5个重点场景。
- 是否删除故事版和各子场景未来旅程输出。

### 1.4 页面总览检查

- 如果当前有Demo代码环境、用户指定代码范围、Product Design提到参考模块或用户提到已有模块，是否按“代码读取分层（Tier 0/1/2）”读取：设计阶段是否只做 Tier 0（定位：路由、菜单/Tab 归属、页面清单、相似页面入口、PRD 点名宿主页面的页面级结构定位——Tab 集合、区块构成、操作列现状）；Tier 2 的实现细节（组件导出名、Props、Events、数据结构、功能链路、Mock / 状态管理）是否留待 Coding 阶段且未被设计阶段重复读取。
- 是否已为当前任务标记代码可用状态（verified 已核验 / partial 部分可用 / unavailable 不可用）并写入 Design Context；是否逐页写入 `codingGuide.pageContext.codeAvailability`（缺省时校验器按 `unavailable` 处理）；项目目录存在但未实际读取验证的代码是否未被标记为 `verified`。
- 页面拆解和导航结构设计后，是否读取Common Design的页面类型模板和组件映射表；如果存在Product Design，是否优先参考Product Design的产品介绍、页面导航结构、页面说明和页面设计规范。
- 是否对照五层参考框架（Theme / Template / Feature / Pattern / Component）自查命中能力完整性：命中的能力是否已读取对应 Reference，未命中的层是否记录原因，是否存在静默遗漏。
- 设计说明书中声称引用 Design Skill 的决策，是否能在 `codingGuide.designReferences` 中找到对应来源登记；无来源的决策是否明确标记为 AI 补齐；引用页面模板文档的 ref 是否精确到原文锚点（`<文档路径>#<章节/模板条目>`），能否直达原文复核。
- `common-design` / `product-design` 依据所引用的文档，是否在顶层 `designContext.readLedger` 中登记为 `status: read`（仅登记过索引/摘要的 `index-only` 文档不得作为设计依据）。
- 是否仅在Product Design、Common Design和已有代码未覆盖时，再基于需求上下文与B端常见模式补齐必要设计。
- 匹配 Product Design 时，是否已识别并默认纳入产品规范补齐项（PD 声明为需求已建设对象/页面类型固有、必备或默认存在、需求未提及的能力），来源是否标记为 `product-design` 并登记可定位锚点，是否未以行业惯例冒充。
- 导航结构是否综合展示本次Demo覆盖范围，不按每个页面、弹窗或抽屉重复输出。
- 命中 4.6.0 需求线索触发清单（如“链接”“在…时提供”“可选择 N 个”“按…筛选”等）的功能点，是否均已输出对应的入口容器 / 入口归属 / 选择容器 / 筛选区承载结论，是否不存在只凭功能名称判断或静默跳过的漏项。
- 是否按 03-demo-page-decomposition.md 4.6.5 完成入口承载判定：PRD 点名“在既有页面/既有区块某位置加入口”时，是否判定宿主范围（in-scope / out-of-scope）并产出对应入口挂载点（requirementEntryPoints）；范围外宿主是否未只建打开容器而漏掉宿主落位，是否已登记 entryHosts 并完成精读。
- 页面总览表是否列清所有页面或容器，并标明初步复用方向；初步复用方向仅为“复用已有页面”“参考已有框架”“新增页面”或“待详细设计确认”，不得提前写死具体组件或开发方式。
- `partial` / `unavailable` 状态下，页面总览表是否未虚构真实文件路径或组件名称；真实代码对象是否标记为“Coding 阶段待核验”。
- `partial` / `unavailable` 状态下，字段表（tableFields / formFields / filterFields）与编码指导中是否未出现未核验的产品专有组件名（非 `Ix` 标准组件），此类名称是否以语义级能力描述表达或标注“Coding 阶段待核验”。
- 页面ID、页面名称、页面类型在总览表、HTML逐页说明和交互规则中是否一致。
- 页面总览表“页面类型”列是否使用 Common Design 中文页面类型名（如概览表格页、表单抽屉），是否误输出模板 ID（如 page-table-overview）；templateId 仅用于 HTML JSON 的 templateContract 字段。
- 页面总览表是否为 Step 4 已确认的**冻结基准清单**：`overview.pageOverview` 是否与之原样一致、`pages` 是否逐项一一对应展开（无遗漏、无合并、无弱化）；是否未在生成说明书时重新推导页面集合，是否存在“对话框已确认但说明书被遗漏或弱化”的页面/功能。
- 页面类型决策表是否在页面总览前形成，是否记录业务场景、PRD/用户约束、Product Design覆盖、Common Design候选模板、代码证据、最终类型、决策理由和未决问题。
- 页面类型是否来自已读取Common Design、匹配Product Design或已验证代码中的标准类型；业务描述是否未被当作页面类型；自定义类型是否说明继承模板、扩展内容和差异原因。
- PRD 中以“流程 / 步骤 / 容器”形式表达的页面设想（步骤数、每步内容、承载方式：页面 / 弹窗 / 抽屉），是否已与“同产品同类页面的既有承载”（命中的 Product Design 规则或已验证的同类页面）逐项核对；不一致时是否未默认接受 PRD 的步骤划分，而是作为设计决策待确认问题进入待确认出口。

### 1.5 待确认问题检查

- 是否区分业务理解问题与设计决策问题：业务理解问题（业务对象、动作范围、状态定义与流转）是否在页面拆解前提出，设计决策问题（页面组织、容器、交互方式）是否在页面总览后提出；是否没有等页面结构做完才发现业务模型理解错误。
- 页面拆解前是否存在未确认的阻塞性业务理解问题（blocking gap）；存在时是否已在页面拆解前输出并等待用户确认后才进入页面拆解。
- 是否在生成HTML设计说明书和AI Coding指导前生成待确认问题。
- 待确认问题是否最多10个，优先控制在3-6个。
- 是否只保留影响整体设计、导航结构、页面容器、用户旅程闭环、关键业务规则、权限边界、Coding实现或关键需求完整性的问题。
- 需求颗粒度不足时，是否先自动补齐能保证用户旅程、功能点、数据、操作、状态和页面层级闭环的设计，而不是把字段命名、按钮文案、普通筛选项、常规表格字段等可合理补齐的细节全部抛给用户确认。
- 每个问题是否包含影响范围和当前默认假设。
- 是否没有询问颜色、按钮位置、普通文案等低价值问题。
- 未确认内容是否没有被写成已确认事实。
- 如果代码、需求和Product Design存在冲突，是否列入待确认问题。
- 输出待确认问题后是否停止并等待用户确认；确认前是否没有直接生成HTML或完整AI Coding指导。
- 匹配 Product Design 时，产品规范补齐清单是否在页面总览后、待确认问题前输出，补齐项是否默认纳入且未被错误列为待确认问题。

### 1.6 HTML说明书检查

- HTML标题是否为“XX需求设计说明书”。
- 左侧目录是否只包含总览和按页面层级组织的页面目录，没有待确认问题、全局交互规则页或独立Coding指导页；页面目录名称是否带页面ID，格式为`页面ID-页面名称`。
- 点击左侧目录后右侧是否可切换展示对应内容。
- 第一页是否展示需求概括、导航结构、页面总览表和总结性AI Coding指导。
- 后续页面是否按页面层级结构组织目录，例如总览、父页面、子页面、孙页面。
- 每个页面是否用一列结构展示页面目标、页面基础信息、页面内容区块、底部操作和页面级AI Coding指导；页面类型是否与页面布局放在一起，而不是作为标题旁标签。
- HTML字号层级是否清晰：页面标题24号；一级小标题18号；二级小标题和页面内容区块名称16号；三级小标题14号；正文、列表和表格内容12号。
- 页面基础信息中的导航位置是否使用表头为“一级导航、二级导航、三级导航、Tab页面”的表格展示，避免只用`/`拼接路径导致AI Coding误把Tab页面当作菜单层级；新增、编辑、详情、弹窗、抽屉等非菜单页面是否继承所属主页面导航，禁止把功能子页面名称写进导航位置。
- 页面基础信息是否写明页面类型还原要求，并从Common Design页面模板中列出标题栏、Tab、筛选区、工具栏、表格、分页、弹窗、抽屉、底部操作等页面骨架组件。
- 页面区块是否继承页面类型的默认布局、区块顺序和组件组合。
- Wireframe / ASCII线框图是否按照页面类型定义绘制，而不是自由组合布局。
- Wireframe / ASCII线框图是否包含该页面类型必须出现的区块，例如搜索筛选、表格工具栏、分页、底部按钮、关闭入口或返回入口。
- Wireframe / ASCII线框图中的抽屉、弹窗、页面、详情页、左树表格、概览表格等容器是否绘制正确。
- Wireframe / ASCII线框图是否与页面内容区块描述一致，并与页面类型决策表、模板结构、layout、组件与交互、页面级AI Coding指导一致。
- 入口挂载点是否在线框图中可定位：宿主页面（含范围外宿主）线框图是否绘制了宿主页面结构与入口位置（以显式标记如 【入口】/【新增入口】 高亮），并画出点击后打开的容器关系；不得只绘制入口自身的容器而找不到其从何处打开（RULE-52 ENTRY_NOT_DRAWN）。
- 含底部操作区的页面、抽屉和弹窗是否已读取对应页面模板：匹配 Product Design 声明该页模板 override 时读取 Product Design 页面模板，否则读取 Common Design 页面模板；`wireframe`、`footerActions`和页面内容说明中的底部操作区位置、按钮顺序和布局规则是否与该模板来源一致，不存在无依据的左右分置或跨容器规则混用。
- 生成每页 HTML 前是否完成并登记该页页面模板来源判定：Design Context 是否记录 Product Design 是否 override 页面模板及判定依据；`templateContract` 是否登记 `templateBase`（common/product），`templateBase=product` 时 `productTemplateRef` 是否非空且可定位到 Product Design 模板文档原文（格式`<文档路径>#<章节/模板条目>`）；模板结构、必需区域、区域顺序与 footer 契约结论是否基于 Product Design / Common Design 模板文档原文精读得出，是否存在仅凭 Reference Index、摘要或他方转述下结构结论的情况。
- 页面区块是否具体到位置、内容、字段/指标、展示形式、取值范围、按钮、可点击操作和点击结果。
- 表格区是否包含工具栏、搜索筛选、字段、字段展示形式、状态值范围、排序、分页、行内操作和边界状态说明；筛选搜索方式是否优先采用Product Design或Common Design页面模板明确要求；HTML中筛选区是否展示筛选方式来源、筛选组件类型、一个`IxProSearch`高级搜索组件或多个独立组件组合说明，以及筛选字段表格（筛选字段表格不再单独标注iDux组件名称，由筛选区组件说明统一承载）；HTML中表格字段是否渲染为“字段名称、展示形式、组件名称、说明”的表格，非普通文本列是否标注组件名称。
- 表单区是否包含字段、组件、iDux组件名称、必填、默认值、选项、是否支持下拉搜索、校验、提示和联动；HTML中表单字段是否渲染为“字段名称、组件类型、iDux组件名称、必填、默认值、选项/规则、提示信息或联动关系”的表格，而不是普通列表。
- 详情区是否包含对象识别信息、描述列表、关联信息、操作入口和必要Tab。
- 设计说明书中的复用对象表达是否与代码可用状态一致：`verified` 时精确到真实页面文件、组件名称、文件路径、关键 Props / Events / Slots 和复用类型；`partial` / `unavailable` 时只写语义级描述并标记“Coding 阶段待核验”，未虚构真实代码对象。

### 1.7 页面目标闭环检查

- 是否执行页面目标闭环检查，避免只按需求字面翻译导致页面无法完成用户任务。
- 是否按两层检查并先业务后页面：先验证业务任务闭环（业务对象、动作、状态、结果是否成立），再验证页面目标闭环（页面能否承载上述业务任务），避免把业务缺口误判为页面缺口。
- 对象管理类页面是否具备支撑对象生命周期的基础承载能力；流程/任务类页面是否具备开始、执行、结果和异常反馈；分析/事件类页面是否具备发现、查看详情和处理路径。
- 当需求只描述局部操作时，是否判断该操作依赖的上下文能力，并从Product Design、已有代码或AI业务理解中按需补齐。
- 补齐内容是否标注为`基于页面目标闭环补齐`，且没有伪装成用户原始需求。
- 会明显影响页面结构、业务规则或用户旅程的补齐项是否进入待确认问题。
- 补齐内容是否仅用于确保页面可用、易用和Demo可演示，是否避免新增业务模块、复杂审批链路、跨系统联动或与需求目标无关的高级能力。

### 1.8 交互与Coding检查

- HTML中的搜索、筛选、重置、排序、分页是否整合到对应页面的表格区、工具栏或相关内容区块说明里，而不是放在独立全局规则页或页面独立交互章节。
- HTML中关键交互是否综合需求资料、Product Design、可用Demo代码环境和AI业务理解生成。
- HTML中新增、编辑、查看、删除、处置、启用、禁用、批量操作是否在对应页面的区块说明或底部操作中写清入口、触发方式、打开容器、页面反馈、数据变化、校验、成功反馈、失败反馈和状态联动。
- HTML中高影响操作是否包含二次确认，确认文案是否说明风险。
- HTML中表单提交是否有必填校验、格式校验、联动关系、提交中和提交失败反馈。
- HTML中空状态、搜索无结果、加载态、异常态、无权限态是否覆盖。
- HTML中极端情况是否覆盖长文本、0值、空字段、数据量大、批量选择为空、部分成功等。
- HTML中Mock数据是否覆盖主要状态、异常状态和边界数据。
- HTML中如果页面区块简要引用了Product Design或已有代码功能点，页面级AI Coding指导是否补充关联说明，写清命中的设计依据、使用位置、实现方式、建议复用组件或代码、Mock数据和边界状态。
- 对标记为“复用已有页面”或“参考已有框架”的页面，是否已完成代码参考验收，核对容器结构、步骤条、工具栏、底部按钮位置、关键交互和组件组织，并写清实际复用范围与新增差异。
- HTML中AI Coding提示词是否可直接复制使用。
- HTML总览AI Coding指导是否包含组件使用规则，要求严格按照页面区块、表格字段、表单字段和页面模板中标注的组件名称开发。
- HTML和AI Coding指导是否明确要求左侧目录不要使用URL hash定位锚点开发，应通过组件状态、路由状态或数据驱动选中态切换页面内容。

### 1.9 代码可用状态与复用表达检查

- 是否已为当前任务标记代码可用状态（verified 已核验 / partial 部分可用 / unavailable 不可用）并写入 Design Context。
- 项目目录存在但未实际读取验证的代码，是否未被标记为 `verified`。
- `verified` 状态下的复用对象是否精确到真实页面文件、组件名称、文件路径、关键 Props / Events / Slots 或使用方式、复用类型和相对已有实现的新增差异。
- `partial` / `unavailable` 状态下，是否只写语义级描述（如标准列表容器、业务策略列表框架、业务对象展示组件、标准状态切换组件、标准高风险确认链路），是否未虚构真实文件路径、组件路径、Props、Events 或调用方式。
- 设计阶段没有代码时，是否未阻断需求设计，并明确区分语义级描述与“Coding 阶段待核验”对象。
- 组件名来源是否按优先级确定：匹配 Product Design 且其 Component 层已登记该业务封装时以 Product Design 业务组件为准（登记 `source=product-design` + `ability`），未登记时才以 Common Design 组件映射表为准，是否未一律写死为 Common Design 通用组件。
- 是否区分“设计意图”与“实现名”位置：`componentContract`（含 `patternComponents`）、`implementationNotes`、`designReferences`（用 `ability`）可写业务组件的语义级能力名并标注待核验；字段级 `iduxComponent` / `component`、`target.component` / `target.components`、`restoreRequirement.components[].name` 不得写未核验的业务组件真实名。
- 匹配 Product Design 的 Pattern 层输出非空 `component_requirements` 且对应能力已登记时，页面是否已将组件结论回填到 `componentContract.patternComponents` 并登记对应 `ability` 依据，是否未遗留在 Pattern 层。
- 是否未通过硬编码产品名称或缩写确定产品身份；产品身份是否依据 Product Design 的 metadata、product_id（同一产品存在多个名称时是否按声明的多标识集合匹配，需求产品名命中任一标识即视为同一产品）或 Resolver 结果。

### 1.10 Implementation Mapping Gate 检查

- Implementation Mapping Gate 是否由 AI 自动执行，未把代码核验职责推给产品经理或设计师。
- 输出 Coding Plan 前是否已完成 Implementation Mapping Gate（无论设计阶段代码状态如何）。
- 是否输出了统一映射表（设计对象、是否必需复用、设计阶段表达、真实代码对象、实现方式、AI核验依据、与设计说明书的差异、映射结果）。
- 实现方式是否只使用“直接引用 / 复用框架 / 组件复用 / 全新开发”四类。
- 映射结果是否只能是“已验证 / 全新开发 / 不适用 / 阻塞”四态。
- 输出 Coding Plan 前，所有必需复用对象是否均为“已验证”；必需对象为“阻塞”时是否未继续输出 Coding Plan 或进入 Coding Execution。
- “待核验”是否只存在于 Gate 执行前，是否未作为 Gate 完成后的结果。
- 设计说明书与真实代码的差异是否已完成分级处理（实现层差异 / 设计层差异 / 业务事实缺失）。
- 是否未在映射阶段未完成时输出 Coding Plan 或进入页面 Coding。

### 1.11 视觉基线检查

- 当需求属于已有业务主题或已有页面体系时，是否把真实参考页面作为视觉和交互基线，而非只复用业务字段和数据模型。
- 视觉基线映射是否覆盖：页面容器、页面标题层级、Tab 结构、筛选区、工具栏、表格容器、表格字段展示、状态组件、操作列、按钮位置和顺序、间距边界和空状态、高风险确认链路。
- 改造既有页面（在既有页面加入口或改区块）时，是否已对宿主页面建立“既有形态基线”：入口所处模块的既有元素形态（操作列图标样式、区块头部操作排列等）与相邻操作的样式与排列；入口是否融入既有形态而非另起样式。
- 视觉基线结果是否写入 Design Context 和页面总览，并在 Coding 阶段落实。
- Implementation Mapping Gate 通过前，是否已完成视觉参考页面与视觉基线范围映射；属于已有页面体系但未完成时，是否未进入 Coding。
- Verification 是否包含视觉基线回归；未完成视觉回归时是否未宣称 Demo 完整交付。

### 1.12 开发项完整性检查

- 页面级 Coding 指导是否使用“编号、开发对象、开发方式、复用与代码映射、实现要求、完成判定”六列表格，开发项 JSON 是否使用固定字段（id/scope/name/mode/mappingRef/mappingStatus/target/requirements/acceptanceCriteria 等）。
- 页面 codingGuide 是否包含固定结构：pageContext、implementationRules、items、mockContract、stateContract、acceptanceCriteria、outOfScope。
- 开发项是否具有稳定 ID，Coding Plan、Coding Execution 和 Verification 是否使用相同 ID 追踪，是否存在改名、合并或遗漏。
- 每个开发项是否只对应一个可独立执行和验收的实现对象；是否明确了依赖顺序。
- 未经过代码核验的开发项，target.path 是否留空并标记 pending 或 blocked，未编造路径。
- 每个开发项是否包含完成判定（acceptanceCriteria）；缺少完成判定的开发项是否已补齐。
- 需求入口挂载点是否都有对应开发项并进入核销清单：in-scope 宿主入口是否落在宿主页面承载该入口的开发项下；out-of-scope 宿主入口的开发项是否挂在打开容器的 codingGuide 下（scope=entry-point，ID 可用 `<容器页ID>-E01` 或 `host:<宿主标识>-E01`），其 ID 是否登记到 entryHosts[].devItem，核销清单是否逐项包含 requirementEntryPoints。

### 1.13 模板契约与线框校验检查

- 每个页面是否绑定标准 templateId（page-table-basic / page-table-tree / page-table-overview / page-table-overview-tree / list-modal / list-drawer / page-detail-drilldown / detail-drawer / log-detail-drawer / page-form-config / page-form-stepper / form-modal / form-drawer / page-dashboard），或使用 custom 模板并填写 baseTemplateId、customReason、overrideSource、overrideJustification。（templateId 与中文页面类型名的对应关系以模板注册表 common-design-template-registry.json 的 name 字段为准，禁止使用已废弃的 page-list-* / page-detail-drawer / page-detail-log / page-form-modal / page-form-drawer 旧 ID；已废弃旧中文类型名"步骤条配置页""仪表盘页"分别以"下钻步骤条配置页""Dashboard"为准。）
- Product Design 自定义页面模板的 ID 口径：`templateId` 只允许"当前注册表标准模板 ID"或 `custom`（`templateId=custom` + `baseTemplateId` 填最接近的注册表标准模板 ID + `override.enabled=true` + `override.source/reason/affectedRules`，并同步 `templateBase=product` 与非空 `productTemplateRef`）；把 Product Design 自定义模板 ID 直接写入 `templateId`、或把其自定义页面类型名写入页面 `type`，均属违规（分别被 RULE-04 TEMPLATE_NOT_REGISTERED、RULE-06 UNREGISTERED_TYPE 阻断）。
- 页面 templateContract 是否登记 `templateBase`（common / product）；`templateBase=product` 时 `productTemplateRef` 是否非空且可定位到 Product Design 页面模板文档原文（格式`<文档路径>#<章节/模板条目>`）；模板来源判定是否在绘制线框与生成 HTML 前完成并写入 Design Context，页面结构是否与所选模板来源一致。
- 页面 type 是否与 templateId 一致，是否使用未注册页面类型名称。
- 页面类型命名（2026 更名）：中文页面类型名与 templateId 的对应关系唯一维护在模板注册表 `common-design-template-registry.json` 的 `name` 字段，校验器的 type↔templateId 映射由注册表派生，禁止在校验脚本中硬编码映射表。弹窗/抽屉不再称"页"——列表弹窗（list-modal）、列表抽屉（list-drawer）、详情抽屉（detail-drawer）、日志详情抽屉（log-detail-drawer）、表单弹窗（form-modal）、表单抽屉（form-drawer）；日志详情属抽屉形态（footer 左对齐，按钮上一个/下一个/关闭），不得按整页处理。旧 ID 与旧中文名仅用于兼容识别（RULE-43 覆盖判定自动归一、RULE-56 对模板引用文本中的旧 ID 告警），不得作为新产出。
- 每个需要区分导航的页面是否填写 navigationType（left-shaped / l-shaped）；无明确依据时是否填写 navigationTypeStatus=assumed、navigationTypeSource、navigationTypeNote。
- 页面是否填写 templateContract，且 templateId、layout、sections、wireframe、footerActions、componentContract、codingGuide 是否形成闭环；是否存在模板必需区域缺失、wireframe 区块无依据、sections 必需区块未出现在 wireframe。
- 结构化 wireframe 是否为唯一可信来源；多步骤/多 Tab 页面是否包含主结构图和每一步完整变体图，变体是否保留公共页面外壳。
- footerActions 对齐方式与按钮顺序是否与模板 footer 契约一致；底部操作区按钮是否与 `wireframe.ascii` 中绘制的按钮一致（缺主操作/顺序错阻断、缺次要按钮提示），出现模板外的业务自定义按钮是否已用 `templateContract.override` 声明；不一致时是否有 override 记录。
- 生成 HTML 前是否运行 validate_demo_spec.py 且 validationStatus=passed；校验失败时是否未生成 HTML、未进入 Implementation Mapping Gate、未输出 Coding Plan。

### 1.14 自动化校验规则登记表与扩展流程

所有 Demo JSON 自动校验规则统一登记在 `scripts/validate_demo_spec.py` 顶部的 `RULES` 表中，按固定流程扩展；禁止为单一校验另建脚本或独立文档。模板/数据类规则（requiredRegions、footer、variants、requiredComponents）直接维护 `references/02-template-contracts/common-design-template-registry.json`，无需改动校验代码。
| 规则 | 校验项 | 数据来源 | 测试覆盖 |
| --- | --- | --- | --- |
| RULE-01 | JSON schema 基础结构 | 01-output-templates.md 数据契约 | test_valid_table_basic_passes |
| RULE-02 | 页面 ID 唯一性 | 01-output-templates.md | — |
| RULE-03 | overview.pageOverview 与 pages 一致 | 01-output-templates.md | — |
| RULE-04 | templateId 已注册 | common-design-template-registry.json | test_unregistered_type_fails |
| RULE-05 | custom 模板 override 完整性 | SKILL.md 强制模板契约与线框校验 | test_custom_without_override_fails / test_valid_override_passes |
| RULE-06 | type 与 templateId 一致 | SKILL.md 强制模板契约与线框校验 | — |
| RULE-07 | 禁止未注册页面类型名称 | SKILL.md 强制模板契约与线框校验 | test_unregistered_type_fails |
| RULE-08 | navigationType 在模板支持范围 | common-design-template-registry.json | — |
| RULE-09 | 必需页面骨架区块存在 | common-design-template-registry.json | test_missing_title_bar_fails / test_missing_pagination_fails |
| RULE-10 | requiredRegions 全部出现在 wireframe.regions | 04-demo-output-spec.md 结构化线框契约 | test_missing_pagination_fails |
| RULE-11 | regionOrder 与模板顺序一致 | common-design-template-registry.json | — |
| RULE-12 | requiredComponents 已声明 | common-design-template-registry.json | test_stepper_uses_tabs_fails |
| RULE-13 | sections 与 wireframe.regions 双向一致 | SKILL.md 强制模板契约与线框校验 | test_section_wireframe_mismatch_fails |
| RULE-14 | table 页面含 Toolbar/Table/Pagination | common-design-template-registry.json | test_missing_pagination_fails / test_table_page_as_card_fails |
| RULE-15 | modal 页面含外壳/关闭入口/底部操作 | common-design-template-registry.json | test_modal_missing_close_fails |
| RULE-16 | drawer 页面含外壳/对象上下文/列表/关闭入口 | common-design-template-registry.json | test_drawer_footer_alignment_fails |
| RULE-17 | stepper 页面含 Stepper | common-design-template-registry.json | test_stepper_uses_tabs_fails |
| RULE-18 | 多步骤页面含主结构图与每步变体 | SKILL.md 强制模板契约与线框校验 | test_multi_step_missing_variants_fails |
| RULE-19 | 变体保留公共页面外壳 | SKILL.md 强制模板契约与线框校验 | test_multi_step_missing_variants_fails |
| RULE-20 | footerActions 与模板对齐规则一致 | common-design-template-registry.json | test_drawer_footer_alignment_fails / test_form_config_footer_right_fails |
| RULE-21 | footerActions 按钮顺序一致 | common-design-template-registry.json | test_form_config_footer_right_fails |
| RULE-22 | wireframe 与页面内容区块一致 | SKILL.md 强制模板契约与线框校验 | — |
| RULE-23 | codingGuide 含稳定开发项 ID | 05-interaction-coding-guidelines.md | — |
| RULE-24 | 代码可用状态：逐页读取 page / templateContract / codingGuide.pageContext.codeAvailability，缺省按 unavailable 处理（CODE_STATUS_UNDECLARED 提示，不再静默跳过）；partial/unavailable 时 target.path 必须为空 | SKILL.md 代码可用状态 / 04-demo-output-spec.md 11.11 | test_partial_path_not_empty_fails / test_code_status_undeclared_warns / test_code_status_in_page_context_fails |
| RULE-25 | 禁止 Vue3 专属绑定语法作为实现要求 | 05-interaction-coding-guidelines.md | — |
| RULE-26 | 非普通文本字段声明组件映射 | 04-demo-output-spec.md | — |
| RULE-27 | legacy 自由文本线框兼容模式 | SKILL.md 强制模板契约与线框校验（兼容模式） | test_legacy_wireframe_warning_non_strict |
| RULE-28 | 页面清单闭环：pageOverview(manifest) 与 pages 数组独立元素（弹窗/抽屉必须作为 pages 独立页面对象，children 仅允许写子容器 ID 字符串引用）的 ID/名称/类型/容器类型一致；页面遗漏、额外页面、重复页面、孤立容器 | 04-demo-output-spec.md 设计闭环自动校验 | test_manifest_page_missing_fails / test_manifest_metadata_mismatch_fails / test_orphan_container_fails |
| RULE-29 | 操作目标闭环：open-container 必须存在 targetPageId 且容器类型正确；高影响操作必须二次确认；未知操作类型 warning | 04-demo-output-spec.md 设计闭环自动校验 | test_operation_target_missing_fails / test_operation_confirm_missing_fails / test_operation_closure_passes / test_operation_other_info |
| RULE-30 | Tab 变体闭环（条件式）：页面显式声明 >=2 个内容 Tab 时，tabs/tabId 唯一、variants 数量与 tab 一一对应、variant 保留公共外壳且有内容区、sections 绑定 tabId | 04-demo-output-spec.md 设计闭环自动校验 | test_tabs_missing_variants_fails / test_tabs_variant_count_mismatch_fails / test_tabs_orphan_variant_fails / test_tabs_variant_no_shell_fails / test_tabs_variant_no_content_fails / test_tabs_section_invalid_fails / test_multitab_closure_passes |
| RULE-31 | 页面级 Coding 闭环：pageContext.pageId 与页面 ID 一致、每页至少一个 Coding item、无孤立 Coding item | 04-demo-output-spec.md 设计闭环自动校验 | test_coding_page_context_mismatch_fails / test_coding_no_items_fails |
| RULE-32 | 线框图绘制完整性：wireframe.ascii 必须按模板绘制，禁止一句话/几个字代替；ascii 过短或未覆盖模板必需区域即 error | 04-demo-output-spec.md 11.6 线框图绘制质量闭环 | test_wireframe_ascii_too_short_fails / test_wireframe_ascii_not_drawn_fails / test_wireframe_ascii_full_drawing_passes |
| RULE-33 | 绘制与 regions 一致性：regions 声明的内容性区域在 ascii 中必须有对应绘制痕迹（结构化字符画要求关键词落在带框线的一行内，避免整段文本偶发命中；纯文本线框按分隔符分段匹配）（warning） | 04-demo-output-spec.md 11.6 线框图绘制质量闭环 | test_wireframe_ascii_region_not_drawn_warns |
| RULE-34 | 线框图布局完整性：ascii 禁止区域标签罗列（每行一个"区域名：内容"），必须绘制为完整页面布局字符画；分隔行识别兼容 ASCII（`+---+`）与 box-drawing（`┌─┐`/`├─┤`/`└─┘`）两种风格 | 04-demo-output-spec.md 11.6 线框图绘制质量闭环 | test_wireframe_label_list_fails / test_wireframe_full_layout_passes |
| RULE-35 | 子容器平铺：children 中禁止内嵌完整页面对象，弹窗/抽屉必须作为 pages 数组独立元素，children 仅允许字符串 ID 引用 | 04-demo-output-spec.md 设计闭环自动校验 | test_child_page_not_flattened_fails / test_child_string_ref_passes |
| RULE-36 | 字段完整性闭环：需求/规范明确要求的字段（表格列、表单项、筛选项、详情字段、配置项）必须逐项落入对应字段数组，未落位且无 excludedFields 排除原因的字段阻断生成 | 01-output-templates.md 字段完整性 / 04-demo-output-spec.md 设计闭环自动校验 | test_requirement_field_missing_fails / test_requirement_field_all_covered_passes / test_requirement_field_excluded_passes |
| RULE-37 | 线框底部按钮：`wireframe.ascii` 底部操作区必须按模板 `footer.buttonOrder` 绘制按钮（缺主操作/顺序错 error，缺次要按钮 warning）；按钮文案须落在模板允许标签集合，出现模板外自定义按钮须 `templateContract.override` 声明（业务自定义按钮以业务为准） | common-design-template-registry.json footer.buttonOrder / 04-demo-output-spec.md 11.6 | test_footer_ascii_button_missing_fails / test_footer_ascii_order_mismatch_fails / test_footer_ascii_order_passes / test_footer_ascii_custom_button_without_override_fails / test_footer_ascii_custom_button_with_override_passes |
| RULE-38 | 表格与详情字段一致性：表格有详情容器时，表格页 tableFields 展示的每个字段必须在对应详情容器字段数组（detailFields/cardFields/fields/tableFields 等）中存在对应项（Common Design 表格与详情字段一致规则兜底） | Common Design 表格与详情字段一致规则 / 04-demo-output-spec.md 11.7 表格与详情字段一致性闭环 | test_table_detail_field_mismatch_fails / test_table_detail_field_consistent_passes / test_table_detail_without_detail_skips / test_table_detail_via_children_fails |
| RULE-39 | 表格标签使用约束：同一表格内标签总数 <= 5；深色/icon/点状标签各仅允许 1 次、浅色标签最多 2 次（超出 error）；样式未标注或中性描述字段（资产类型/IP/域名等）占用标签配额时 warning（Common Design 标签（IxTag）样式使用约束兜底） | Common Design 标签（IxTag）样式使用约束 / 04-demo-output-spec.md 11.8 表格标签使用约束闭环 | test_table_tag_count_exceeded_fails / test_table_tag_style_overused_fails / test_table_tag_style_unspecified_warns / test_table_tag_neutral_field_warns / test_table_tag_usage_passes |
| RULE-41 | 字段形态键契约：字段内容必须写在渲染器实际渲染的键上（表单字段 formFields 用 rules/tips；筛选字段 filterFields 用 options/description；表格字段 tableFields/columns 用 display/description）；内容写在异态键导致 HTML 对应列静默空白时阻断（error），内容已渲染但键写错位置时 warning | 04-demo-output-spec.md 字段形态键对照（RULE-41）/ 01-output-templates.md AI Coding指导输出格式 | test_form_field_options_not_rendered_fails / test_form_field_key_placed_wrong_warns / test_form_legacy_fields_options_not_rendered_fails / test_filter_field_rules_not_rendered_fails / test_table_field_rules_not_rendered_fails / test_field_key_contract_passes |
| RULE-42 | 需求理解与页面设计追溯（条件式启用）：requirementUnderstanding.status 非 resolved 阻断 HTML 生成；每个页面必须 taskRefs 关联业务任务；已建模任务必须有页面承载；任务缺核心动作或核心动作无结果反馈阻断；判断区块内字段缺 fieldRole、fieldRole/source 值非法给 warning；页面有 taskRefs 但顶层缺模型阻断 | 04-demo-output-spec.md 11.9 需求理解与页面设计追溯（RULE-42）/ SKILL.md Step 1.5 | test_requirement_status_not_resolved_fails / test_model_missing_but_task_ref_fails / test_page_without_task_ref_fails / test_task_not_bound_to_page_fails / test_task_without_outcome_fails / test_task_without_action_fails / test_judge_block_field_no_purpose_warns / test_invalid_source_marker_warns / test_invalid_field_role_warns / test_requirement_trace_passes / test_requirement_trace_skipped_without_model |
| RULE-40 | 设计依据可追溯：声称引用 Design Skill 的决策必须在页面 codingGuide.designReferences 登记来源；无来源的决策须标 ai-fill；声称引用 Product/Common Design 但无对应登记时阻断（error）；source/ref 格式问题给 warning | references/01-workflow/00-design-skill-resolver.md / SKILL.md 输出可追溯 | test_design_ref_missing_fails / test_design_ref_passes / test_design_ref_invalid_source_warns / test_design_ref_empty_ref_warns / test_design_ref_absent_no_claim_passes |
| RULE-43 | 设计依据一致性（条件式启用：声明顶层 designContext 时）：readLedger 为锚点粒度，designReferences 中 common-design/product-design 来源的 ref 必须锚点级命中 readLedger 的 status=read（未读引用、仅索引引用、引用同文档未精读章节均阻断）；Product Design 声明模板 override 的页面必须 templateBase=product 且 productTemplateRef 非空；采用 product 模板的页面必须反向登记 product-design 依据；coverage 声明 extend/override 的任意能力，其适用页面必须登记同 ability 的 product-design 依据 | 04-demo-output-spec.md 11.10 设计依据一致性（RULE-43）/ references/01-workflow/00-design-skill-resolver.md | test_design_context_absent_skips / test_design_context_unread_ref_fails / test_design_context_consistent_passes / test_design_context_anchor_unread_fails / test_design_context_whole_doc_read_passes / test_design_context_template_override_not_applied_fails / test_design_context_template_source_unregistered_fails / test_ability_source_not_registered_fails / test_ability_source_registered_passes |
| RULE-44 | 未核验实现细节隔离：partial/unavailable 时禁止把未核验的真实导出名、产品专有组件名（非 Ix 标准组件）、真实文件/组件路径或真实可视化基线页面当作已确认设计结论写入字段表/编码指导/复用映射 | 04-demo-output-spec.md 11.11 未核验实现细节隔离（RULE-44）/ 05-interaction-coding-guidelines.md 代码可用状态约束 | test_unverified_export_fails / test_unverified_component_name_fails / test_unverified_ix_component_passes / test_unverified_visual_baseline_fails |
| RULE-45 | 线框区域顺序一致性：`regions[].position` 的相对顺序必须与 `wireframe.ascii` 中区域标签首次出现的行序一致，不一致时提示（warning） | SKILL.md 强制模板契约与线框校验 / 04-demo-output-spec.md | test_wireframe_region_order_mismatch_warns / test_wireframe_region_order_consistent_passes |
| RULE-46 | 线框重复绘制：页面级单例控件（导出/刷新/查询/确定/取消等，见 `SINGULAR_CONTROLS`）在 `wireframe.ascii` 中同页重复绘制时提示；同一内容区域（步骤条/Tab/工具栏/筛选区/分页，见 `REGION_SINGLETON_KEYS`）在 ascii 中被绘制多次时提示（warning） | SKILL.md 强制模板契约与线框校验 / 04-demo-output-spec.md | test_wireframe_duplicate_control_warns / test_wireframe_duplicate_region_warns |
| RULE-47 | 线框列对齐一致性：`wireframe.ascii` 内容行右边界（右竖线）应在同一列，出现明显错位（疑似两列结构断裂）时提示（warning） | SKILL.md 强制模板契约与线框校验 / 04-demo-output-spec.md | test_wireframe_column_alignment_warns / test_wireframe_full_layout_passes |
| RULE-48 | 下拉选项完整性与维度保留（条件式启用：页面声明 `requirementOptionSets` 时）：固定选项型下拉（表单下拉/筛选下拉/单选/多选等）声明的完整选项必须逐项出现在表单 `rules`（选项/规则）或筛选 `options`（选项范围）单元格，缺失选项阻断（REQUIRED_OPTION_MISSING）、声明字段不存在阻断（OPTION_FIELD_NOT_FOUND）；未声明选项集的选择类字段选项单元格出现 等/例如/如：/… 截断指纹时告警（OPTION_TRUNCATION_MARKER）；声明项非法/不完整给 warning（OPTION_SET_INVALID / OPTION_SET_INCOMPLETE）；需求源枚举表含分组/层级列时（声明 `dimension=group/hierarchy`，或 `sourceColumns` 声明 >=2 列自动视为分组）选项单元格被压成单层列表、未保留该维度时告警（OPTION_DIMENSION_LOST）；是否保留维度属本规则职责，承载维度的控件形态由 RULE-54 依 widget patterns 判定，本规则不做形态名映射 | 04-demo-output-spec.md 11.13 下拉选项完整性与维度保留（RULE-48）/ 01-output-templates.md 4.2 | test_requirement_option_missing_fails / test_requirement_option_all_present_passes / test_option_set_field_not_found_fails / test_option_truncation_marker_warns / test_option_completeness_skips_without_declaration / test_option_dimension_lost_warns / test_option_dimension_kept_passes / test_option_dimension_inferred_from_columns_warns / test_option_dimension_flat_skips |
| RULE-49 | 详情页字段去重（条件式启用：仅详情类页面）：顶部概览卡片/对象摘要已展示字段（声明 `detailSummaryFields` 为准，未声明时以 `cardFields` 兜底）不得在其下方详情描述列表（概览/描述/detail 等区块的 fields/detailFields）重复展示，命中给 warning（DETAIL_FIELD_DUPLICATE）；同一详情描述列表区块内字段名重复出现给 error（DETAIL_FIELD_DUPLICATED_IN_LIST）；`excludedFields` 与页面级 `detailDedupExempt` 豁免，历史/日志/操作记录类区块与表格字段不参与；非详情页跳过 | 04-demo-output-spec.md 11.14 详情页字段去重（RULE-49）/ 01-output-templates.md 4.2 | test_detail_field_duplicate_warns / test_detail_summary_fields_declared_warns / test_detail_field_dedup_exempt_passes / test_detail_field_duplicated_in_list_fails / test_detail_field_dedup_skips_non_detail_page |
| RULE-50 | 按钮/可点击操作表（条件式启用：区块 `actions` 为对象数组时）：区块 `actions` 以表格输出（操作/触发方式/使用组件/文案或字段/Demo反馈/来源）；高影响操作（自动识别 name/`impact`/`confirm`，可用 `actionRules.highImpactActions`/`highImpactKeywords` 扩展、`exempt` 豁免）缺二次确认文案给 error（ACTION_CONFIRM_TEXT_MISSING）；涉及二次确认/局部面板缺组件给 warning（ACTION_COMPONENT_MISSING）、声明组件却无文案/字段给 warning（ACTION_CONTENT_MISSING）；组件/文案来源缺失、标为 ai-fill、缺锚点或取值非法给 warning（ACTION_SOURCE_NOT_TRACED，组件与文案须取自 Product Design 优先、其次 Common Design 的 pattern，禁止 AI 自拟）；操作行缺名称给 warning（ACTION_NAME_MISSING）；`actions` 旧字符串写法兼容不校验 | 04-demo-output-spec.md 11.15 按钮/可点击操作表（RULE-50）/ 01-output-templates.md 4.2 | test_action_high_impact_missing_text_fails / test_action_high_impact_complete_passes / test_action_source_ai_fill_warns / test_action_component_missing_warns / test_action_legacy_string_skipped / test_action_rules_configurable |
| RULE-51 | 表格区按钮位置（线框图，warning）：表格关联按钮（批量操作、其他子功能入口按钮，如新增/导入/导出/列设置等）必须统一绘制在表格区左上角工具栏；按钮出现在表格框下边界之下给 warning（TABLE_BUTTON_MISPLACED，分页行/底部操作区行/纯边框行除外）；`批量`类按钮出现在表格工具栏区域之外给 warning（TABLE_ACTION_NOT_IN_TOOLBAR，工具栏区域 = 紧邻表格框上方一行至表格框内部）；无 `\|` 分隔数据行的表格框的 ascii 自动跳过 | 04-demo-output-spec.md 11.16 表格区按钮位置（RULE-51） | test_table_button_below_table_warns / test_table_button_in_toolbar_passes / test_table_pagination_not_flagged / test_table_batch_action_outside_warns / test_table_button_check_skips_without_table |
| RULE-52 | 需求入口落位闭环（条件式启用：顶层声明 `requirementEntryPoints` 时）：PRD 点名的每个入口挂载点必须有落点——in-scope 宿主须在宿主页面 sections 操作或 operations 中承载触发元素与打开容器（缺失以 ENTRY_POINT_NOT_PLACED 阻断）；out-of-scope 宿主须在 entryHosts 登记且完成 Tier1 精读、含对应开发项（缺失以 ENTRY_HOST_UNREGISTERED 阻断）；入口声明缺必需字段或 hostScope 非法以 ENTRY_POINT_INCOMPLETE 阻断；宿主线框图未绘制入口痕迹以 ENTRY_NOT_DRAWN 告警 | 04-demo-output-spec.md 11.17 需求入口落位闭环（RULE-52）/ 01-output-templates.md 4.3 | test_entry_point_in_scope_placed_passes / test_entry_point_not_placed_fails / test_entry_point_out_of_scope_unregistered_fails / test_entry_point_out_of_scope_registered_passes / test_entry_point_out_of_scope_missing_dev_item_fails / test_entry_point_out_of_scope_dangling_dev_item_fails / test_entry_point_not_drawn_warns / test_entry_point_incomplete_fails / test_entry_point_skips_without_declaration |
| RULE-53 | 页面定位证据闭环（条件式启用：声明 `requirementEntryPoints`（out-of-scope 宿主）或顶层 `pageIdentityRefs`；in-scope 宿主仅在提供 hostEvidence 时校验）：定位到的既有页面必须给出身份证据——缺证据或证据不全（navPath 空 / 代码模式缺 route 或 codeRefs / 退化模式缺 title 与 tabs）以 HOST_IDENTITY_UNVERIFIED 阻断；`matchedBy` 含文件名/目录名或不含任何强锚点以 HOST_IDENTITY_FILENAME_ONLY 阻断；存在多个形近/近义候选（candidates > 1）但未记录排除理由（rejected 空）以 HOST_IDENTITY_AMBIGUOUS 告警；代码导航路径末级与 PRD 声明路径末级不一致以 HOST_NAVPATH_MISMATCH 阻断 | 04-demo-output-spec.md 11.18 页面定位证据闭环（RULE-53）/ 01-output-templates.md 4.4 / 03-demo-page-decomposition.md 4.6.6 | test_page_identity_ref_valid_passes / test_page_identity_missing_evidence_fails / test_host_identity_filename_only_fails / test_host_identity_navpath_mismatch_fails / test_host_identity_ambiguous_warns / test_host_identity_degraded_mode_passes / test_entry_point_out_of_scope_missing_evidence_fails |
| RULE-54 | 组件形态描述闭环（条件式启用：字段声明 >1 个形态候选 `formCandidates` 时）：组件在 Common Design 中登记多种形态（如 IxTag 多种标签样式、IxSelect 下拉面板的搜索/新增/树/分组、单选/多选的 radio/卡片）时，必须在 `iduxComponentForm` 写明选用的形态；声明多形态候选却未选形态给 warning（COMPONENT_FORM_MISSING）；选用形态不在候选内给 warning（COMPONENT_FORM_UNKNOWN）；形态来源分两层并各自要求"已读证据"——**命名/枚举真值**取 Common Design 组件映射（`common-design/references/05-components/idux-component-map.md` 的组件锚点），缺依据或依据未精读命中给 warning（COMPONENT_FORM_SOURCE_UNREAD）；**选择依据真值**取 Common Design widget patterns（`common-design/references/03-patterns/07-widget-patterns/` 的判定小节锚点，按“目录级索引 `#*` + 命中控件对应文件精读”读取，Product Design 侧 pattern 文档同等可用），缺依据或依据未精读命中给 warning（COMPONENT_FORM_RULE_UNREAD）；两层依据均须锚点级登记到页面 `codingGuide.designReferences` 并在 `readLedger` 命中 `status=read`（`index-only` 不算已读，同时触发 RULE-43 DESIGN_REF_UNREAD 阻断）；仅校验声明候选的字段，单形态组件零负担；形态候选与选用形态须取自组件映射的登记形态，本 Skill 不内置形态目录、禁止自造形态名；`iduxComponentForm` 并入既有“iDux组件名称”列展示，不新增列 | 04-demo-output-spec.md 11.19 组件形态描述（RULE-54）/ 01-output-templates.md 4.2 / 04-demo-output-spec.md 组件名来源规则 | test_component_form_missing_warns / test_component_form_unknown_warns / test_component_form_valid_passes / test_component_form_single_candidate_passes / test_component_form_source_unread_warns / test_component_form_rule_unread_warns / test_component_form_evidence_index_only_warns / test_component_form_evidence_complete_passes / test_component_form_single_candidate_skips_evidence |
| RULE-55 | 能力发现完整性（条件式启用：声明 `designContext.productDesign.coverage` 时）：以匹配到的 Product Design 自身声明的 `coverage` 为真值，要求对其声明的每项能力在 `capabilitySweep` 显式判定 命中/未命中（未命中同样留痕），漏项或判定非法给 warning（ABILITY_NOT_SWEPT）；判定为命中的能力须附 `evidenceRef` 且锚点级命中 `readLedger` 的 status=read，否则给 warning（ABILITY_HIT_NOT_READ）；用于兜住“Product Design 未读完就输出、该用 PD 的组件退回 Common Design”，不硬编码任何产品/文档路径，控件特征仅作复核信号 | 00-design-skill-resolver.md 能力识别参考框架（防漏清单）/ 04-demo-output-spec.md 11.20 能力发现完整性（RULE-55） | test_capability_sweep_complete_passes / test_capability_not_swept_warns / test_capability_hit_not_read_warns / test_capability_sweep_absent_warns |
| RULE-56 | 模板 ID 一致性与覆盖兜底（条件式启用：声明顶层 `designContext`，或页面携带 `templateSource`/`layoutSource` 等模板引用文本时）：页面类型更名后，旧模板 ID 在覆盖判定中自动归一为当前注册表 ID（`page-list-modal`→`list-modal`、`page-list-drawer`→`list-drawer`、`page-detail-drawer`→`detail-drawer`、`page-detail-log`→`log-detail-drawer`、`page-form-modal`→`form-modal`、`page-form-drawer`→`form-drawer`），保证 Product Design 声明即使滞后仍写旧 ID，模板覆盖仍被 RULE-43 强制而非静默跳过；`coverage[].appliesTo`/`capabilitySweep[].appliesTo` 声明了适用模板却归一后未命中本次任何页面给 warning（TEMPLATE_COVERAGE_UNAPPLIED）；`templateContract.templateSource`/`wireframe.layoutSource`/`restoreRequirement.components[].source` 等模板引用文本中出现已废弃旧 ID 给 warning（LEGACY_TEMPLATE_ID_REF）；归一仅用于兼容识别，旧 ID 不得作为新产出 | 04-demo-output-spec.md 11.21 模板 ID 一致性与覆盖兜底（RULE-56） | test_template_coverage_unapplied_warns / test_template_coverage_legacy_id_applied_passes / test_sweep_appliesTo_unapplied_warns / test_legacy_template_id_ref_warns / test_template_id_consistency_absent_skips |
| RULE-57 | 表单单列布局闭环（条件式启用：页面为表单承载页——templateId ∈ {page-form-config, page-form-stepper, form-modal, form-drawer}，或页面声明了表单配置字段、含表单配置区块）：表单配置一律单列——`wireframe.ascii`（含各 variant 的 ascii）中每行只允许一个配置项、label 在左控件在右且水平同一行；同一行检测到 ≥2 个已声明表单字段给 warning（FORM_LAYOUT_MULTI_COLUMN）；字段 label 独占一行、控件落在下一行给 warning（FORM_LAYOUT_LABEL_NOT_INLINE）；表单布局依据（Common Design 表单规范）未在 `codingGuide.designReferences` 锚点级登记，或未在 `readLedger` 命中 `status=read`（含 index-only）给 warning（FORM_LAYOUT_BASIS_UNREAD）；适配 Product Design 时同样需登记其表单规范依据；控件形态不在本规则内，按 RULE-54 依 widget patterns 判定；均为 warning，不阻断出图 | 04-demo-output-spec.md 11.22 表单单列布局闭环（RULE-57） | test_form_layout_single_column_passes / test_form_layout_multi_column_warns / test_form_layout_label_not_inline_warns / test_form_layout_basis_unread_warns / test_form_layout_basis_read_passes / test_form_layout_non_form_page_skips |
| RULE-58 | 详情页操作去重（条件式启用：页面 `footerActions` 非空且存在概览卡片/对象摘要区块并在该区块声明 `actions`）：概览卡片已承载的对象级操作（编辑/重启/删除等）不得在底部按钮栏重复出现，按操作名同义归一（编辑/修改、重启/重新启动、删除/移除等，词表见脚本 `DETAIL_ACTION_ALIASES`）比较，命中给 warning（DETAIL_SUMMARY_ACTION_DUPLICATE）；页面级 `detailActionDedupExempt` 与区块级 `excludedActions`/`actionExempt` 豁免；底部按钮栏只保留页面级动作（关闭/上一个/下一个/取消/确定）；与 RULE-49 同源（概览卡片已承载的内容不在别处重复堆叠） | Common Design 详情概览卡片与底部按钮栏操作去重规则 / 04-demo-output-spec.md 11.23 详情页操作去重（RULE-58） | test_detail_summary_action_duplicate_warns / test_detail_summary_action_alias_duplicate_warns / test_detail_summary_action_no_overlap_passes / test_detail_action_dedup_exempt_passes / test_detail_action_dedup_skips_without_summary_actions / test_detail_action_dedup_skips_without_footer |
| RULE-59 | 复用业务组件容器闭环（条件式启用：页面声明 `reuseBusinessComponent.decision=reuse`，或容器为宿主页面动作延伸且 `codingGuide.designReferences` 已引用 Product Design 业务封装组件依据）：命中 Product Design 业务封装组件（或代码识别已知业务封装）的**需求延伸容器**（trigger ∈ 按钮点击/表格字段点击/详情字段点击/行操作/导入/导出）不单独绘制与描述——不产出 `wireframe.ascii`、`wireframe.regions`、区块字段（formFields/tableFields/detailFields/cardFields/filterFields）与 `footerActions`，只在宿主页面交代"点击 X 打开 Y（复用 <组件名>，不单独绘制）"，容器仅保留一条 `mode=reuse` 开发项指向业务组件；声明复用却仍自绘给 **error**（REUSE_CONTAINER_OVER_DESCRIBED，阻断出图）；依据未锚点级登记或未在 `readLedger` 精读命中、`basis=code` 缺 `codeEvidence`、`basis` 取值非法给 warning（REUSE_BASIS_UNREAD）；宿主页面无线框痕迹或无复用标记（复用/不单独/业务封装/直接使用）给 warning（REUSE_HOST_NOTE_MISSING）；`trigger` 非法、`hostPageId` 缺失或不在本次范围、容器无宿主入口（独立页面不允许复用，需求主页面必须完整产出）给 warning（REUSE_SCOPE_INVALID）；容器（templateId 含 modal/drawer）已有宿主入口且已引用 Product Design 业务组件依据却未声明复用给 warning（REUSE_CANDIDATE_UNMARKED，反向提示）。豁免：必需区域/区域顺序/必需组件/弹窗抽屉外壳与底部/底部对齐与按钮顺序/线框绘制质量/线框区域绘制/表单单列布局在复用容器上不参与校验；模板契约（type↔templateId）与入口落位（ORPHAN_CONTAINER）仍生效 | Product Design 业务封装组件复用 / 04-demo-output-spec.md 11.24 复用业务组件容器闭环（RULE-59） | test_reuse_container_minimal_passes / test_reuse_container_over_described_fails / test_reuse_basis_unread_warns / test_reuse_basis_code_without_evidence_warns / test_reuse_host_note_missing_warns / test_reuse_scope_invalid_warns / test_reuse_candidate_unmarked_warns / test_reuse_absent_skips |

**override 影响范围**：`templateContract.override.enabled = true` 时，RULE-09/10（必需区域）、RULE-11（区域顺序）、RULE-12（必需组件）、RULE-14（表格语义）对该页自动放宽（校验器跳过对应结构断言），改由 Product Design 的页面模板定义兜底；RULE-20（footer 对齐）与 RULE-37（底部按钮文案/自定义按钮）本就读 override。放宽不代表不校验，仍需在 `templateContract.override.source` 中登记覆盖来源。

**注册表路径维护**：`common-design-template-registry.json` 的 `sourceBase` 与各模板 `source` 必须与 common-design 的实际目录（当前为 `references/02-template/`）保持一致；common-design 目录重命名或移动时，必须同步更新注册表、SKILL.md 及全部 references 中的路径引用，避免坏链导致 RULE-43 误判 `DESIGN_REF_UNREAD`。

新增校验规则的固定流程：

1. 在 `validate_demo_spec.py` 的 `RULES` 表登记一条（ruleId 唯一、来源文档、实现方法）；
2. 实现对应 `check_xxx` 方法，输出统一结构化错误（pageId/errorCode/severity/path/message/expected/actual/sourceRef/fixSuggestion）；
3. 在 `run()` 中按顺序注册调用；
4. 在 `tests/test_validate_demo_spec.py` 补充用例；
5. 在本登记表同步一条；
6. 若规则涉及 HTML 展示或门禁，同步更新 `generate_demo_spec_html.py` 与 SKILL.md Quality Gate。

### 1.15 设计闭环自动校验检查（RULE-28 ~ RULE-59）

生成 HTML 前必须完成以下设计闭环自检，任一 error 都会阻断 HTML 生成：

- 页面清单闭环：`overview.pageOverview` 中确认的每个页面/容器（含弹窗、抽屉）是否全部作为 `pages` 数组独立元素出现（`children` 仅允许字符串 ID 引用，内嵌对象会被 RULE-35 阻断）；是否存在额外页面、重复页面、ID/名称/类型/容器类型不一致；弹窗/抽屉是否至少有一个入口（open-container 操作或文本引用）。
- 操作目标闭环：`operations` 中的 `open-container` 操作是否都有存在的 `targetPageId` 且容器类型正确；`delete`/`batch-delete`/`disable`/`enable`/`revoke` 等操作是否带 `confirm: true` 与 `confirmConfig`。
- Tab 变体闭环（条件式）：页面显式声明 2 个及以上内容 Tab 时，每个 Tab 是否有唯一 `tabId`、对应完整 `wireframe.variants` 变体、变体是否保留公共页面外壳且有非空当前 Tab 内容区；`sections` 是否绑定 `tabId`。
- 页面级 Coding 闭环：每个页面 `codingGuide.pageContext.pageId` 是否等于页面 ID；每个页面是否至少有一个稳定 Coding item；Coding item 是否可追溯且无孤立项。
- 线框图绘制质量闭环：`wireframe.ascii` 是否按模板绘制（过短或未覆盖模板必需区域会阻断）；regions 声明的内容性区域在 ascii 中是否有绘制痕迹（缺失给 warning）；底部操作区按钮是否按模板 `footer.buttonOrder` 绘制（一个模板按钮都没画或顺序错会阻断，缺次要按钮给 warning，模板外自定义按钮须 override 声明）；同一内容区域（步骤条/Tab/工具栏/筛选区/分页）是否被重复绘制、内容行右边界是否对齐（warning）；HTML 生成前校验器拦截"只有几个字"的线框图。
- 字段完整性闭环：需求/规范明确列出的字段（表格列、表单项、筛选项、详情描述字段、配置项）是否逐项落入对应区块的字段数组（tableFields/formFields/filterFields/cardFields 等）；未落位且无 excludedFields 排除原因的字段会被 RULE-36 阻断，不得为了简洁过滤或合并需求明确字段。
- 表格与详情字段一致性闭环：表格有详情容器（open-container 指向详情类容器或 children 挂载的详情容器）时，表格页 tableFields 展示的每个字段是否都能在对应详情容器字段数组（detailFields/cardFields/fields/tableFields 等）中找到对应；缺失会被 RULE-38 阻断，表格无详情容器时不校验。
- 表格标签使用约束闭环：每个表格区块（sections 中带 tableFields 的区块 + 页面级 tableFields）内标签使用是否克制——标签总数是否 <= 5；深色/icon/点状标签是否各自仅 1 次、浅色标签是否 <= 2 次；超出会被 RULE-39 阻断；标签样式未标注（无法自动校验同一样式重复）或中性描述字段（资产类型/IP/域名等）占用标签配额时给出 warning，提示把配额留给风险等级、处置/启用禁用状态等重要业务字段。
- 字段形态键契约闭环：每个字段数组（formFields/filterFields/tableFields/columns，以及表单/表格区块自由fields中的字典字段）中字段对象的内容是否写在渲染器实际渲染的键上（表单字段rules/tips、筛选项options/description、表格字段display/description）；内容写在不渲染的异态键（如表单字段写options/description）会导致HTML对应列静默空白，会被RULE-41阻断；内容已渲染但键写错位置时给出warning。
- 下拉选项完整性与维度保留闭环（条件式）：页面声明 `requirementOptionSets` 时，固定选项型下拉（表单下拉/筛选下拉/单选/多选等）声明的完整选项是否逐项落入表单 `rules`（选项/规则）或筛选 `options`（选项范围）单元格（缺失选项被 RULE-48 以 REQUIRED_OPTION_MISSING 阻断，声明字段不存在以 OPTION_FIELD_NOT_FOUND 阻断）；未声明选项集的选择类字段选项单元格是否出现 等/例如/如：/… 截断标记（出现以 OPTION_TRUNCATION_MARKER 告警，提示只举例未列全）；需求源枚举表含分组/层级列时（`dimension=group/hierarchy`，或 `sourceColumns` >=2 列自动视为分组）选项单元格是否保留了该维度（压平为单层列表以 OPTION_DIMENSION_LOST 告警）。选型建议：选项单元格先列完整选项、再补其它规则说明，禁止用“等/例如/…”代替逐项枚举；分组写成“组名：选项A/选项B”，层级写成“父级 → 子级”；承载维度的控件形态不在本规则判定，按 RULE-54 依 Common Design widget patterns 判定并登记依据。
- 详情页字段去重闭环（条件式）：详情类页面（详情抽屉/下钻详情页/详情弹窗）顶部概览卡片/对象摘要已展示的字段（声明 `detailSummaryFields` 为准，未声明时以 `cardFields` 兜底），是否仍在其下方详情描述列表（概览/描述/detail 等区块的 fields/detailFields）重复展示（命中被 RULE-49 以 DETAIL_FIELD_DUPLICATE 告警，提示从描述列表移除或写入 `detailDedupExempt` 说明有意重复）；同一详情描述列表区块内字段名是否重复（重复以 DETAIL_FIELD_DUPLICATED_IN_LIST 阻断）；历史/日志/操作记录类区块与表格字段不参与去重，非详情页不校验。选型建议：概览卡片字段只落在 `cardFields` 或 `detailSummaryFields`，即满足 RULE-36 完整性，无需在描述列表重复堆叠。
- 详情页操作去重闭环（条件式）：页面 `footerActions` 非空且概览卡片/对象摘要区块声明了 `actions` 时，概览卡片已承载的对象级操作（编辑/重启/删除等）是否仍在底部按钮栏重复出现（同义归一比较，命中被 RULE-58 以 DETAIL_SUMMARY_ACTION_DUPLICATE 告警；`detailActionDedupExempt`/`excludedActions` 可豁免）；选型建议：对象级操作只写在概览卡片 `actions`，页面级动作只写在 `footerActions`，两边不重叠即通过。
- 复用业务组件容器闭环（条件式）：页面声明 `reuseBusinessComponent.decision=reuse` 时，是否已彻底降级为"只引用不自绘"（无 `wireframe.ascii`/`regions`、无区块字段、无 `footerActions`，被 REUSE_CONTAINER_OVER_DESCRIBED 阻断）？Product Design 依据是否锚点级登记并精读命中、`basis=code` 是否给了 `codeEvidence`（REUSE_BASIS_UNREAD 告警）？宿主页面是否写了容器名与复用标记（REUSE_HOST_NOTE_MISSING 告警）？`trigger` 与 `hostPageId` 是否合法且容器确有宿主入口（REUSE_SCOPE_INVALID 告警）？反向检查：容器已有宿主入口并引用了 Product Design 业务组件依据却没声明复用（REUSE_CANDIDATE_UNMARKED 告警）——选型建议：命中业务封装组件即声明复用、删除自绘内容，需求直接点名的页面不降级。
- 按钮/可点击操作表闭环（条件式）：区块 `actions` 是否以表格输出（操作/触发方式/使用组件/文案或字段/Demo反馈/来源）；高影响操作（自动识别 + `actionRules` 可配置）是否写清二次确认文案（缺失被 RULE-50 以 ACTION_CONFIRM_TEXT_MISSING 阻断）；涉及二次确认或局部面板的操作是否写清使用组件（缺组件以 ACTION_COMPONENT_MISSING 告警）、声明组件却无文案/字段是否补齐（ACTION_CONTENT_MISSING 告警）；组件与文案是否优先取自 Product Design（其次 Common Design）的 pattern 并登记 `source`/`sourceRef`、未由 AI 自拟（缺失或 ai-fill 以 ACTION_SOURCE_NOT_TRACED 告警）。选型建议：没有二次确认的操作只写交互行为，有二次确认或局部面板的必须写清组件与文案/字段。
- 表格区按钮位置闭环：线框图中表格关联按钮（批量操作、其他子功能入口按钮，如新增/导入/导出/列设置等）是否统一绘制在表格区左上角工具栏；按钮出现在表格框下边界之下（分页行/底部操作区行/纯边框行除外）被 RULE-51 以 TABLE_BUTTON_MISPLACED 告警；`批量`类按钮出现在表格工具栏区域之外被 TABLE_ACTION_NOT_IN_TOOLBAR 告警。选型建议：凡归属表格的按钮一律放在表格区左上角工具栏，禁止绘制在表格下方或其他区域。
- 需求入口落位闭环（条件式）：PRD 点名的每个入口挂载点是否有落点——in-scope 宿主是否在宿主页面区块操作或 operations 中承载触发元素与打开容器（缺失被 RULE-52 以 ENTRY_POINT_NOT_PLACED 阻断）；out-of-scope 宿主是否在 entryHosts 登记且完成 Tier1 精读、含对应开发项（缺失被 ENTRY_HOST_UNREGISTERED 阻断）；宿主线框图是否绘制入口痕迹（缺失以 ENTRY_NOT_DRAWN 告警）。选型建议：入口不能只建成打开容器，必须同时记录“宿主 + 宿主位置”，宿主在范围外时按 03-demo-page-decomposition.md 4.6.5 四条处置（登记 / 精读 / 绘制 / 开发项）。
- 页面定位证据闭环（条件式）：定位到的既有页面（out-of-scope 入口宿主、顶层 `pageIdentityRefs` 的复用/相似页面）是否给出身份证据（逐级导航路径 navPath + 路由/菜单标识 + 页面标题 + 命中代码实体 codeRefs + 命中依据 matchedBy）；缺证据或证据不全被 RULE-53 以 HOST_IDENTITY_UNVERIFIED 阻断；`matchedBy` 含文件名/目录名或不含任何强锚点被 HOST_IDENTITY_FILENAME_ONLY 阻断；存在形近/近义候选未记录排除理由以 HOST_IDENTITY_AMBIGUOUS 告警；代码导航路径末级与 PRD 声明路径末级不一致被 HOST_NAVPATH_MISMATCH 阻断。选型建议：定位必须逐级对证 PRD 导航路径（如“安全事件 → 事件详情 → 告警列表”），禁止以文件名/目录名近似匹配（`alert-list` 是告警链、`alarm-list` 才是告警列表），环境无代码时退化为以页面标题/组件导出名 + 侧边栏/Tab 文案对证。
- 组件形态描述闭环（条件式）：表格/表单字段中，凡在 Common Design 组件映射里登记了多种形态的组件（如 IxTag 标签样式、IxSelect 下拉面板形态、单选/多选的 radio/卡片），是否在声明 `formCandidates` 的同时用 `iduxComponentForm` 写明本页选用形态；声明多候选却未选形态（COMPONENT_FORM_MISSING）或所选形态不在候选内（COMPONENT_FORM_UNKNOWN）以 warning 提示（不阻断）。形态来源两层是否都有精读留痕：命名/枚举取 Common Design 组件映射（缺依据或依据未精读命中 COMPONENT_FORM_SOURCE_UNREAD），选择依据取 Common Design widget patterns `03-patterns/07-widget-patterns/`（目录级索引 `#*` + 命中控件对应文件精读；缺依据或依据未精读命中 COMPONENT_FORM_RULE_UNREAD），两层依据均须锚点级登记到页面 `codingGuide.designReferences` 并在 `readLedger` 命中 `status=read`（`index-only` 不算已读，并由 RULE-43 阻断）。单形态组件零负担；形态候选与选用形态须取自组件映射的登记形态，本 Skill 不内置形态目录、禁止自造形态名。
- 能力发现完整性闭环（条件式）：声明 `designContext.productDesign.coverage` 时，Product Design 声明的每项能力是否在 `capabilitySweep` 显式判定 命中/未命中（漏项或判定非法被 RULE-55 以 ABILITY_NOT_SWEPT 告警）；判定为命中的能力是否附 `evidenceRef` 且锚点级命中 `readLedger` 的 status=read（缺失或未读被 ABILITY_HIT_NOT_READ 告警，均为 warning）。选型建议：读取匹配到的 Product Design 后，对其 coverage 能力逐项做“命中/未命中 + 理由”留痕，命中项必须先精读；控件特征（资产选择/启禁用/数字范围/资产信息等）仅作复核信号，禁止据此静默跳过；能力清单以 Product Design 为准，本 Skill 不预置产品能力表。
- 模板 ID 一致性与覆盖兜底（条件式）：页面类型更名后，Product Design 的 `coverage`/`capabilitySweep` 或页面模板引用文本是否仍使用旧 ID——旧 ID 在覆盖判定中会被自动归一（`page-list-drawer`→`list-drawer` 等），确保该页仍被要求 `templateBase=product` + 非空 `productTemplateRef`（不一致被 RULE-43 以 TEMPLATE_OVERRIDE_NOT_APPLIED 阻断，不静默跳过）；声明的 `appliesTo` 归一后未命中本次任何页面（RULE-56 TEMPLATE_COVERAGE_UNAPPLIED 告警）；`templateSource`/`layoutSource`/组件来源等模板引用文本出现已废弃旧 ID（RULE-56 LEGACY_TEMPLATE_ID_REF 告警）。选型建议：模板引用一律写当前注册表 ID，历史 JSON 不兼容旧 ID，发现旧 ID 即改为当前 ID，不要依赖归一兜底。
- 表单单列布局闭环（条件式）：表单承载页（配置表单页、下钻步骤条配置页、表单弹窗、表单抽屉，或含表单配置区块）的线框 ascii（含 variants）是否每行只画一个配置项、label 与控件水平同一行（同一行多配置项 FORM_LAYOUT_MULTI_COLUMN 告警、label 与控件分离成两行 FORM_LAYOUT_LABEL_NOT_INLINE 告警）；表单布局依据是否锚点级登记并精读命中（未登记或仅索引 FORM_LAYOUT_BASIS_UNREAD 告警）；控件形态仍按 RULE-54 依 widget patterns 判定。
- 需求理解与页面设计追溯闭环：每个页面是否用 taskRefs 关联了至少一个业务任务；requirementUnderstanding 中每个已建模任务是否都有页面承载；核心动作是否有结果反馈（outcome）；判断区块（informationPurpose/decisionPoint）内字段是否说明用途（fieldRole）；AI 推导字段/来源标记是否合法；requirementUnderstanding.status 非 resolved 时不得生成 HTML（RULE-42 阻断）。
- 设计依据一致性闭环（条件式）：声明顶层 `designContext` 时，页面 `codingGuide.designReferences` 中 `common-design` / `product-design` 来源的 `ref` 是否为精确锚点，且对应**锚点**在 `readLedger` 中为 `status: read`（未读引用、仅索引引用、引用同文档未精读章节会被 RULE-43 阻断）；Product Design 声明 extend/override 的任意能力，其适用页面是否登记同 `ability` 的 product-design 依据（否则 `ABILITY_SOURCE_NOT_REGISTERED`）；Product Design 声明页面模板 override 的页面是否真正采用 `templateBase=product` 且 `productTemplateRef` 非空（否则 `TEMPLATE_OVERRIDE_NOT_APPLIED`），采用 product 模板的页面是否反向登记 `source=product-design` 依据（否则 `TEMPLATE_SOURCE_UNREGISTERED`）。
- 未核验实现细节隔离闭环：`partial` / `unavailable` 状态下，字段表、编码指导与复用映射中是否未出现未核验的真实导出名（EXPORT_WITHOUT_VERIFY）、产品专有组件名（非 `Ix` 标准组件，COMPONENT_WITHOUT_VERIFY）、真实文件/组件路径或真实可视化基线页面（VISUAL_BASELINE_WITHOUT_VERIFY）——由 RULE-44 在 HTML 生成前阻断。

### 1.16 需求理解检查

进入页面拆解前，对照以下清单检查需求理解质量（对应 SKILL.md Step 1.5 与 07-requirement-understanding.md）：

- 是否识别需求是功能清单还是叙事 Playbook（inputType），并据此选择提取方式；
- 是否从叙事/清单中提取角色、目标、业务对象、动作、判断信息和结果（requirementUnderstanding.tasks 结构化）；
- 是否区分平台功能与交付语境（前置切分，语境项不得直接拆为页面）；
- 是否把业务事实和设计推导分开（confirmedFacts / designInferences 分列，AI 补齐单独标 ai-fill）；
- 是否在页面拆解前暴露关键业务缺口（阻塞性业务理解问题须在页面拆解前提出并确认，不拖到页面总览后）；
- 是否每个页面都能回溯到业务任务（页面 taskRefs 与 requirementUnderstanding.tasks 相互绑定，RULE-42）；
- 是否每个核心任务都有完整的入口、执行动作和结果（action/outcome 齐备，核心动作无结果反馈会被 RULE-42 阻断）；
- 是否没有用 AI 补齐替代业务事实确认（AI 只能补展示层与常规交互，不得新增业务对象、状态流转、权限、审批、数量限制或核心动作）。

## 2. 禁止事项

1. 用户未提供任何资料就自行生成需求分析或Demo方案。
2. 输出长篇业务背景、故事版或各子场景未来旅程。
3. 把线下流程、外部系统操作、技术实现或商业背景直接拆成Demo页面。
4. 识别到Product Design但未优先参考产品介绍、页面导航结构、页面说明和页面设计规范。
5. 当前有Demo代码环境、用户指定参考模块或Product Design提到相关模块时，未读取代码就直接生成页面拆解和Coding指导。
6. 导航结构按每个页面重复书写，而不是综合展示覆盖范围。
7. 对话框在页面总览表之后继续展开逐页设计说明、交互逻辑、状态规则、Mock数据或完整AI Coding提示词。
8. 未输出待确认问题或未等待用户确认，就直接生成HTML设计说明书和AI Coding完整指导。
9. HTML中放入待确认问题、独立全局交互规则页、页面独立交互章节或独立Coding指导页。
10. HTML中只列页面名称，没有逐页设计说明。
11. HTML表格区只列字段，不说明搜索、筛选、按钮、字段展示形式、状态值范围、排序、分页和行内操作。
12. HTML表单区只列字段，不说明组件、必填、默认值、选项、校验、提示和联动。
13. 可点击统计数字、超链接文本、按钮、图标操作未说明点击结果。
14. 主要按钮没有交互结果或状态变化。
15. 关键交互只写“点击查看”“点击提交”等浅层描述，没有说明触发入口、打开容器、页面反馈、数据变化、校验、成功/失败反馈和状态联动。
16. Demo只有静态页面，没有搜索、筛选、重置、空状态、异常态、极端情况等基础逻辑。
17. Mock数据只填正常数据，没有覆盖异常、边界和空值情况。
18. 使用接口字段名、数据库字段名、开发枚举值或开发语言作为页面文案。
19. 页面类型只作为标签展示，没有还原对应页面类型的默认布局、区块顺序和组件组合。
20. 把基础表格页开发成随意表格，遗漏筛选/搜索、工具栏、分页或行内操作。
21. 把抽屉、弹窗开发成页面内普通卡片，或把页面内容误开发成弹窗/抽屉。
22. HTML线框图未先读取 已确认的页面类型结构，只画空白卡片、通用容器或与页面内容区块不一致的布局。
23. 忽略Product Design或已有代码中明确规定的组件习惯、筛选方式和页面容器。
24. HTML设计说明书未执行组件识别：页面骨架缺少组件映射，筛选区未说明`IxProSearch`或独立组件组合，表格非普通文本列未标注组件名称，表单项未标注iDux组件名称，操作列、状态列、反馈类交互未标注组件。
25. 在AI Coding提示词中要求实现真实后端、数据库或外部系统联调，除非用户明确要求。
26. 页面未绑定标准模板或 custom 模板（含 baseTemplateId 与 overrideJustification）就直接生成 HTML 或进入 Coding。
27. 页面 type 使用未注册页面类型名称，或页面 type 与 templateId 不一致。
28. 在 strict 模式下使用纯字符串 wireframe 静默通过校验，或校验失败后仍生成 HTML、进入 Implementation Mapping Gate、输出 Coding Plan。
29. 多步骤/多 Tab 页面只画一张总线框图，没有为每个步骤/Tab 输出完整变体图；或变体未保留公共页面外壳。
30. footerActions 对齐方式或按钮顺序与模板契约不一致时未记录 override 来源就继续开发。
26. 在 `partial` / `unavailable` 状态下虚构真实文件路径、组件路径、Props、Events 或调用方式，或把未实际读取的代码标记为 `verified`。
27. 未经 Implementation Mapping Gate 直接开始 Coding，或在共享页面外壳、公共组件、实现映射尚未冻结时并发开发多个页面。
28. 把实现层差异静默改为全新开发，或发现设计层差异后不修正 HTML 并重新确认就直接 Coding。
29. 未完成视觉基线回归就宣称 Demo 完整交付。
30. 在通用 Skill 内容中硬编码具体产线或产品名称、产品或产线专属的文档路径（如具体的 `product-design/references/...`），或通过产品名称缩写猜测 Product Design。Product Design 的目录结构随产品而异，其文档路径与章节锚点必须取自当前实际加载的 Product Design Skill。（Product Design 在 metadata 中显式声明的多产品标识（如 `product_id: aes, dr`）属合法标识声明，不属于本条所指的硬编码或缩写猜测。）
31. 命中 Product Design 声明页面模板 override 的页面，仍按 Common Design 模板结构登记与绘制，且未完成差异登记（`templateBase=product` / `productTemplateRef` / override 依据缺失即属未登记）。
32. 仅凭 Reference Index、摘要或他方转述确定页面模板结构、覆盖范围、必需区域、区域顺序或 footer 契约，未基于 Product Design / Common Design 模板文档原文精读并登记可定位引用。
33. 把未实际读取（或未精读所指章节）的 Common Design / Product Design 文档登记为设计依据（`readLedger` 中为 `index-only`、缺失或未锚点级命中），或引用未读文档/同文档未精读章节作为设计依据（RULE-43 阻断）。
34. 在 `partial` / `unavailable` 状态下，把未核验的产品专有组件名（非 `Ix` 标准组件）、真实导出名、真实文件/组件路径或真实可视化基线页面当作已确认设计结论写入字段表、编码指导或复用映射（RULE-44 阻断）。

## 3. 表达风格要求

输出内容应：

- 使用中文。
- 对话框简洁，主体内容止于页面总览表。
- 使用真实用户语言描述字段、状态和操作。
- 精简需求分析，重点放在页面总览和HTML说明书。
- 对不确定信息标记“待确认”。
- 避免空泛表达和过度包装。
- 页面总览之后的长内容放入HTML。

## 4. Coding执行检查

当HTML设计说明书生成后以及用户确认Coding计划后，执行前和执行中检查：

- 是否先提醒用户查看HTML页面内容，并说明如果HTML需要调整可直接告知修改点。
- 如果用户在开始Coding前反馈HTML修改意见，是否已先更新设计说明JSON并重新生成最新HTML，再重新执行 Implementation Mapping Gate，再输出最新Coding Plan并自动继续 Coding，未再次要求用户确认 Coding Plan。
- 是否在输出Coding Plan前完成 Implementation Mapping Gate 并输出统一映射表；映射表是否纳入 Coding Plan。
- 是否先输出具体Coding计划（导航路径、全新开发页面、参考已有页面、复用已有功能点、新增实现功能点和开发顺序），输出后即自动进入 Coding Execution；用户确认发生在阻塞性业务理解问题（存在时在页面拆解前确认）、待确认问题和 HTML 设计说明书三处。
- Coding Plan 是否只描述开发实现方式，未重新引入字段含义、业务规则、页面是否存在等业务设计确认（此类内容已在待确认问题和 HTML 确认阶段完成）。
- Coding输入是否综合HTML设计说明书、原始需求资料、待确认问题回复、Product Design和已有Demo代码，禁止把HTML当作唯一输入或机械执行稿。
- 是否按页面层级和页面依赖拆分开发顺序，优先完成可独立承载主旅程的页面，再实现其关联抽屉、弹窗和子页面。
- 进入 Coding Execution 前，是否完成 Step 7.5 编码 Skill 判定并记录结果：命中项目 `.frieren-design/workflows.json` 编码工作流时，是否已读取并严格按照 workflow 定义的顺序执行编码（未跳步、改序）；命中项目编码 Skill 声明或编码类 Skill 时，是否先向用户明示将调用的编码 Skill 名称与来源，是否执行桥接加载该编码 Skill（读取其 SKILL.md）并按其指导执行编码直至完成（本 Skill 未自行执行编码与编码结果检验、未代编码 Skill 选择调用顺序，编码未因命中而中断、未停在宣告处等待用户）；未命中时，是否向用户明示按默认流程执行后由本 Skill 执行编码并完成，未停止、挂起或虚构不存在的 Skill。
- 是否一个页面完成后再开始下一个页面，避免多页面同时改动导致上下文混乱；是否遵守并发开发限制：共享页面外壳、公共组件和实现映射冻结前未并行开发多个页面，父页面和子页面未同时 Coding。
- 每完成一个页面，是否告知用户“已完成哪个页面，接下来开发哪个页面”。
- 每个页面完成后是否做基础可运行校验、页面渲染校验、核心交互校验和视觉基线回归校验。
- 是否将声明为直接引用、组件复用或复用框架的对象擅自改为全新开发。
- 发现设计说明书与真实代码差异时，是否按实现层差异 / 设计层差异 / 业务事实缺失分级处理，未静默修改。
- 如果HTML与用户确认内容、Product Design或已有代码冲突，是否按更高优先级依据修正实现，并在开发进度说明中解释调整原因。
- 如果用户反馈Coding效果不好，是否先判断问题来源是需求理解、HTML设计说明、代码实现、业务规范还是组件复用策略，再决定修正HTML还是直接修正代码。
- 全部页面开发完成后，是否完成功能、交互、组件复用和视觉基线回归验证，再告知用户Demo已开发完毕，并请用户说明需要调整的页面、交互或视觉细节。

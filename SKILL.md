---
name: prd-design-code
description: 将B端产品需求转化为符合产品设计规范的Demo设计说明与AI Coding实现；负责识别产品、装配Common Design并在可用时叠加对应Product Design，完成页面拆解、HTML设计规格、Coding计划和代码实现
metadata:
  skill_type: workflow
  capability: prd-to-design-to-code
  frieren.tags: "需求设计开发"
---

# 任务目标

- 将B端产品需求、PRD、截图、Demo代码、原型资料或用户想法，编排为可审阅、可生成HTML、可指导AI Coding的Demo设计与开发计划。
- 输出可直观看到需求对应Demo的页面方案，覆盖页面导航、页面总览、逐页内容、交互逻辑、边界状态、Mock数据和Coding计划。
- 在Coding前形成Design Context和HTML说明书，帮助用户确认AI对需求、产品设计知识和代码复用对象的理解是否正确。

# 角色与职责

- A 是 Workflow Orchestrator：负责组织需求输入、Design Skill Resolver、页面拆解、待确认问题、HTML说明书、Implementation Mapping Gate、Coding Plan、Coding Execution和Verification。
- A 不维护具体设计规范：具体页面类型、业务主题、组件、导航、表格、表单、状态、术语等设计知识应来自 Common Design、Product Design、已有代码或用户输入。
- A 负责把设计知识装配成当前任务可执行的 Design Context，并确保后续页面设计、HTML说明书和Coding执行均基于该上下文。
- A 负责控制输出边界：对话框只展开到页面总览和待确认问题；逐页设计、交互细节、Mock数据和AI Coding详细指导写入HTML说明书。
- 职责边界：本 Skill 只负责发现、调用、装配和核验设计知识，不维护任何具体产线的业务模型、业务组件规范或仓库页面路径；产品身份必须通过 Product Design 的 metadata、product_id（同一产品存在多个名称时按声明的多标识集合判断，需求产品名命中任一标识即视为同一产品）或 Resolver 结果确定，禁止在本 Skill 内容中硬编码具体产线或产品名称，禁止用产品名称或缩写猜测 Product Design。

# 设计知识调用与优先级

- 先读取 [Design Skill Resolver](references/01-workflow/00-design-skill-resolver.md)，再开始页面设计。
- Design Skill必须通过当前环境的Skill查询能力实际发现并读取；未实际查询和读取的Skill一律视为不存在，禁止假设或虚构。
- 只有完成“查询 → 读取SKILL.md → metadata校验”的Design Skill，才允许进入当前任务的Design Context并作为设计依据。
- Common Design：优先识别声明`skill_type: common-design`的Skill，作为通用设计规则来源；若只有一个Common Design，直接使用。Common Design是进入正式页面设计阶段的必需依赖：未查询到Common Design，或查询到但无法成功读取其SKILL.md时，不得使用AI自身通用设计知识模拟Common Design；应停止进入正式页面设计，并提示缺少Common Design。读取Common Design时必须明确读取组件映射表和页面模板里的推荐组件，用于页面骨架、筛选区、表格字段、表单字段和反馈类组件映射。
- Product Design：作为可选增强依赖。先识别当前需求所属产品或需求中明确出现的产品名称，再寻找`skill_type: product-design`且需求产品名命中其任一产品标识的Skill；Product Design 通过 metadata 的 `product_id` 声明其服务的产品标识，同一产品存在多个名称（例如 AES 与 DR 为同一产品，需求资料可能显示为 DR 但需使用 AES 的 Product Design）时 `product_id` 允许声明逗号分隔的多个标识（如 `product_id: aes, dr`），需求产品名（主名或别名）与任一标识一致（忽略大小写与空白）即匹配并可调用，不得要求需求产品名必须与主标识一致；产品身份必须通过 Product Design 的 metadata、product_id（含多标识声明）或 Resolver 结果确定，禁止仅通过Skill名称中是否出现XDR、SASE、DSP等缩写判断，也禁止在本 Skill 内容中硬编码具体产线或产品名称。未找到匹配Product Design属于正常执行状态，不阻断流程、不作为待确认问题，进入Common Design模式继续执行，并结合当前代码环境和AI补齐。只有产品身份会影响导航、业务规则或Product Design选择，且无法根据现有输入确定时，才进入待确认问题；发现多个可能匹配的Product Design（含同一需求产品名命中多个Product Design的多标识声明）且无法判断选择对象时，也进入待确认问题。
- Product Design 组件映射处理：
  - 若 Product Design 已提供业务组件映射，prd-design-code 应读取并纳入 Design Context。
  - 若 Product Design 未提供某组件映射，设计阶段使用语义级描述；Coding 阶段通过 Implementation Mapping Gate 核验真实组件，将真实路径、Props、Events 和调用方式记录到当前任务的映射结果中；不把这些仓库级实现细节永久写入本 Skill。
- Resolver只决定设计知识来源，不负责具体页面设计；读取采用“索引优先、Reference按需”的方式：
  - Common Design：先读取SKILL.md及Design Capability Index / Reference Index；
  - Product Design：若存在匹配项，先读取SKILL.md、Coverage及Reference Index；
  - 再根据当前需求命中的Design Capability按需读取对应Reference；
  - 禁止递归或无差别读取Design Skill中的全部Reference。
- Inherit / Extend / Override：
  - `inherit`：产品完全继承Common Design，只读取对应Common Design Reference。
  - `extend`：先获得Common Design基础规则，再叠加Product Design补充规则。
  - `override`：以Product Design规则作为最终设计规则；仅当Product Design明确要求参考Common Design时，再读取对应Common Design细节。
- Design Context：页面拆解前必须形成当前任务Design Context，至少包含：
  - 已解析的Common Design；
  - 已读取的组件映射表、页面模板推荐组件和产品设计特殊组件；
  - 当前产品或当前可确认的产品范围；
  - 本需求命中的Design Capability；
  - 每项能力的实际知识来源；
  - 若存在Product Design，其Coverage及`inherit / extend / override`关系；
  - 当前任务代码可用状态（verified 已核验 / partial 部分可用 / unavailable 不可用）及当前代码中已验证的可复用对象；
  - AI合理补齐项；
  - 仍无明确规则的内容；
  - 关键冲突和待确认业务事实。
- 冲突原则：
  1. 用户本轮已经明确确认的设计决策；
  2. PRD中明确的业务事实、业务规则和业务约束；
  3. 匹配的Product Design中的产品设计规范；
  4. 当前明确要求复用且经过验证的代码实现；
  5. Common Design中的通用设计规范；
  6. AI合理补齐。
- PRD中的“业务事实”优先于Design Skill；PRD中的“设计表达”如果仅为需求撰写者的初步页面设想而非明确约束，则可结合Product Design和Common Design优化。
- Product Design与Common Design冲突时，按`override / extend / inherit`关系处理；代码与Design Skill冲突时，先判断代码代表历史实现还是当前明确要求复用的实现，不得仅因代码存在就推翻Product Design。
- AI自行合理补齐的内容必须明确标记为AI补齐，不得伪装或描述为Common Design、Product Design或已有代码中已明确规定的规则。

## Coding 实现与组件使用原则

本 Skill 负责确定页面最终采用何种 Coding 实现方式，但不自行维护具体通用组件的设计与使用规范。

生成页面级 AI Coding 指导前，必须结合以下信息确定最终实现方式（均须实际读取，仅作为信息收集来源，不作为优先级排序）：

1. 若存在匹配Product Design，读取其中明确的产品已有页面、业务模块、业务组件、产品专属组件和复用规则；
2. 当前代码环境中可验证的已有页面、组件、路由、交互和实现方式；
3. Common Design 中的页面模板推荐组件、标准组件映射与组件使用规范；
4. 前述信息无法满足需求时，才允许新增实现（全新开发）。

组件决策必须区分两个独立优先级，分别用于“设计语义来源”和“实际复用对象”，不得混用：

- 设计语义优先级（决定采用哪套设计知识）：Product Design 产品设计规范 > Common Design 通用设计规范 > AI 补齐。
- 具体实现优先级（决定 Coding 实际复用哪个实现）：用户或 HTML 明确要求复用的对象 > 当前代码环境中已验证的业务组件和页面框架 > Product Design 推荐的具体实现 > Common Design 推荐组件 > 通用 iDux 组件语义推断 > 全新开发。

若存在匹配Product Design，其用于说明产品中应优先复用什么（设计语义）；当前代码环境用于验证复用对象是否真实存在以及实际实现方式，且已验证的业务组件和页面框架在具体实现优先级中优先于 Product Design / Common Design 推荐组件；Common Design 用于提供标准基础组件和通用组件组合方式。不得因设计库推荐了通用组件，就跳过当前代码环境中真实可用的业务组件。未找到匹配Product Design时，按当前代码环境、Common Design和明确标记的AI补齐确定实现方式。

页面级 AI Coding 指导不得只写“使用按钮”“使用抽屉”“使用高级搜索”等泛化描述。涉及组件时，应尽可能明确：

- 具体组件名称；
- 关键使用方式或参数；
- 复用对象；
- 开发方式；
- 新增实现与已有实现的差异。

生成HTML说明书前必须完成组件识别与映射：每个页面都必须有页面骨架组件映射；筛选区必须说明使用一个`IxProSearch`高级搜索组件还是多个独立组件组合，多个独立组件也必须列出对应iDux组件名称；表格字段中非纯文本列必须标注组件名称；表单项必须标注控件组件；操作列、状态列、反馈类交互必须标注组件。

已有标准组件或已有业务组件能够满足需求时，禁止重新实现同类基础能力。

# 代码可用状态

设计阶段读取业务代码后，必须为当前任务的代码可用性标记唯一状态，并写入 Design Context：

- `verified`（已核验）：设计阶段已实际读取并验证相关业务代码，可明确真实页面、组件、路由、交互和数据结构。
- `partial`（部分可用）：只读取了部分代码，仍有页面、组件或交互未验证。
- `unavailable`（不可用）：设计阶段没有可用业务代码，或没有找到相关参考页面。

约束：

- 项目目录存在不代表代码已经读取；只有实际读取并验证过的页面、组件、路由、交互和数据结构，才能标记为 `verified`。
- `partial` 和 `unavailable` 状态下，禁止凭空生成真实文件路径、组件路径、Props、Events 或调用方式。
- 设计阶段没有代码时，不阻断需求设计，但必须明确区分：哪些内容是语义级描述、哪些内容需要 Coding 阶段核验。
- 产品身份不通过代码推断，也不得通过硬编码产品名称或缩写确定；必须依据 Product Design 的 metadata、product_id（同一产品存在多个名称时按声明的多标识集合判断，需求产品名命中任一标识即视为同一产品）或 Resolver 结果。

# 核心工作流程

## Step 1 输入与 Demo 范围

- 提取用户提供的PRD、截图、原型、录屏、Demo代码、字段清单、业务说明或口头需求。
- 若没有任何需求资料，先要求补充需求内容、Demo范围、代码范围或相关文档，禁止自行生成Demo方案。
- 过滤Demo范围：仅将平台内展示、平台内操作、可演示前端流程进入Demo设计；线下流程、外部系统、技术实现、商业背景仅作为背景或待确认信息。
- 若存在Demo代码环境、用户指定代码范围、Design Skill提到参考模块，或用户提到已有模块，读取相关代码作为输入，关注路由、菜单、相似页面、组件组织、Mock数据和已有交互习惯。
- 读取代码后，必须按“代码可用状态”标记当前任务的代码可用性（verified 已核验 / partial 部分可用 / unavailable 不可用）并写入 Design Context；项目目录存在但未实际读取验证的代码一律视为 `unavailable`。

## Step 2 产品识别 + Design Context

- 识别当前需求所属产品、业务域、页面所属模块和可能命中的设计能力；对照 [Design Skill Resolver](references/01-workflow/00-design-skill-resolver.md) 的能力识别参考框架（Theme 主题框架 / Template 页面模板 / Feature 业务功能 / Pattern 交互模式 / Component 组件映射）自查防漏：命中才读，未命中的层记录原因但不产生读取，禁止将五层当作全量读取清单。
- 调用Design Skill Resolver识别Common Design；若存在匹配Product Design，则同时识别并读取。
- 先读取Common Design的SKILL.md和Reference Index；若存在匹配Product Design，再读取其SKILL.md、Coverage和Reference Index；按需求命中的能力选择Reference，不递归读取所有Reference。
- Common Design解析成功后即可进入设计知识装配；必须读取组件映射表和页面模板里的推荐组件，形成当前任务的组件映射基线；若存在匹配Product Design，解析其Coverage中的`inherit / extend / override`关系，并读取产品设计里的特殊组件，明确每项设计能力和组件能力的最终知识来源。
- 未找到匹配Product Design时，使用Common Design、PRD、用户输入和当前代码环境继续设计；对于页面组织、通用交互、展示字段等可合理推导的设计细节允许AI补齐，但真实业务事实、权限、状态流转、数量限制、业务规则等不可从现有输入确认的信息不得自行编造，必要时进入待确认问题。
- 形成Design Context并在内部用于后续设计；Design Context 必须包含代码可用状态（verified 已核验 / partial 部分可用 / unavailable 不可用）、命中能力清单（每项能力及其知识来源）和未命中说明（未命中的层记录“未命中/不适用”及原因）；仅当产品无法确定、已发现的Product Design存在选择歧义、关键Reference缺失或规则冲突未明确时，进入待确认问题或停止页面拆解。

## Step 3 核心用户、场景、目标

- 简要概述需求要解决的问题，不强制限制为一句话。
- 输出需求概括和主要用户、场景，不再在HTML输出体验目标和Demo范围判断。
- 识别1-2个主要用户角色；如果只有1个岗位只输出1个，如果超过2个且确实都是主要角色，可最多输出3个。
- 提炼3-5个核心场景与功能映射，不输出故事版和各子场景未来旅程。

## Step 4 页面导航 + 页面总览

- 读取 [Demo页面拆解](references/01-workflow/03-demo-page-decomposition.md)，基于Design Context拆解页面导航和页面总览。
- 先判断功能属于独立业务旅程、菜单级能力、Tab级能力，还是依附于已有页面的轻量入口。
- 输出页面总览前，必须先为每个页面形成内部“页面类型决策表”，记录业务场景、PRD/用户约束、Product Design是否覆盖、Common Design候选模板、已验证代码证据、最终页面类型、决策理由和未决问题；页面类型不确定且会影响用户旅程或页面结构时，进入待确认问题。
- 页面总览表按导航层级列出一级菜单、二级菜单、三级菜单、Tab页面、详情页、弹窗、抽屉和必要下钻页面。
- 每个页面必须说明页面ID、页面名称、页面类型、导航路径、打开方式、页面目标、主要内容、关键操作和初步复用方向；初步复用方向仅可写复用已有页面、参考已有框架、新增页面或待详细设计确认。详细开发方式、具体组件和实现差异必须在HTML页面级AI Coding指导中确定。
- 页面类型必须使用已读取Common Design、匹配Product Design或已验证代码中真实存在的标准类型名称，页面总览表输出时必须使用 Common Design 中文页面类型名（如概览表格页、抽屉表单页），禁止输出模板 ID（如 page-table-overview）；业务描述不得直接充当页面类型。标准类型无法覆盖时，标记为“自定义页面类型”，并说明继承的基础模板、扩展内容和差异原因。
- 页面总览表即已确认页面/容器清单（manifest）：总览中出现的每个页面、弹窗、抽屉都必须作为 demo-spec.json `pages` 数组的独立页面对象完整呈现，页面 ID、名称、类型、容器类型保持一致；`children` 仅用于表达归属关系，只允许写子容器 ID（字符串），禁止在 `children` 中内嵌完整页面设计对象（生成器按 `pages` 数组逐项渲染，children 不展开；内嵌对象会被校验器以 RULE-35 阻断）。弹窗/抽屉必须通过 `operations` 的 open-container 操作或页面内容引用建立入口，禁止出现总览已确认但最终产物缺失的容器（详见 [Demo输出规格 - 设计闭环自动校验](references/01-workflow/04-demo-output-spec.md) 第 11 章）。
- 需求或规范中明确列出的字段（表格列、表单项、筛选项、详情描述字段、配置项等）必须逐项落入页面对象对应区块的字段数组（tableFields/formFields/filterFields/cardFields等），不得过滤、合并或仅简述；页面对象写入 requirementFieldNames（需求/规范明确要求的字段名数组）与 excludedFields（字段名到排除原因的映射），缺失的需求字段会被校验器以 RULE-36 阻断（详见 [Demo输出规格 - 设计闭环自动校验](references/01-workflow/04-demo-output-spec.md) 第 11 章）。
- 对话框主体只输出到页面总览表，禁止继续展开逐页设计、交互细节、Mock数据或完整AI Coding提示词。

## Step 5 待确认

- 页面总览表输出后，必须先输出待确认问题，并等待用户确认；这是生成HTML说明书前的强制卡点。
- 待确认问题来自Design Context、页面总览、导航结构、页面容器、用户旅程闭环、关键业务规则、代码环境和Design Skill冲突。
- 最多10个，优先3-6个；只保留影响整体设计、导航结构、页面容器、核心旅程、关键规则、权限边界或Coding实现的问题。
- 每个问题必须包含：待确认问题、影响范围、当前默认假设。
- 无关键待确认问题时，明确写“暂无关键待确认问题，按当前页面总览继续生成HTML说明书”，然后可继续Step 6。

## Step 6 HTML 说明书

- 用户确认待确认问题后，先判断确认结果是否影响Step 4的导航和页面总览；若影响，必须重新输出更新版导航结构和页面总览表。
- 生成HTML详细设计前，重新检查当前Design Context是否覆盖本阶段实际需要的设计能力，包括页面类型、表格、表单、交互、状态、文案术语、组件映射以及产品级业务组件和复用规则。
- 若页面总览确定后出现新的设计能力，通过Design Skill Resolver按需补充对应Common Design / Product Design Reference；禁止默认认为Step 2读取的Design Context已经覆盖详细设计阶段全部知识。
- HTML中的每项页面结构、内容区块、交互规则、状态规则、术语、组件选择和底部操作区布局，都必须可追溯到已读取的Common Design / Product Design Reference、PRD、用户确认、已验证代码或明确标记的AI补齐；不得仅因已识别Common Design就默认其所有规则已被使用。
- 绘制HTML线框图前，必须先选择已读取的页面类型模板，再从该页面类型对应的设计库模板文档读取模板结构与线框样式：匹配Product Design声明了页面模板时按Product Design定义的页面模板（按 00-design-skill-resolver 的覆盖关系），否则按Common Design页面模板文档（如 references/03-design-template/01-page-types.md 的对应模板条目）；线框图参考只来自这两个设计库，本Skill不保存任何页面模板线框图参考。不得根据页面名称或业务内容自由拼装结构。线框图必须继承所选页面模板的布局结构，并继承其中的底部操作区位置、按钮顺序和布局规则。底部操作区属于页面模板结构硬约束；除非PRD、用户确认或匹配Product Design明确覆盖，不得将同一操作区按钮拆分为左右两侧，也不得自行混用页面、抽屉、弹窗等不同容器的按钮位置规则。
- 生成HTML前，对每页执行“页面类型 → 模板结构 → layout → 页面骨架组件映射 → 内容区块 → 筛选/表格/表单字段组件映射 → wireframe → 组件与交互 → 页面级AI Coding指导”一致性校验；任一环节与已选模板不一致时，先修正页面设计或明确覆盖依据，不得直接生成HTML。
- 生成HTML前，将每页设计决策的知识来源登记到页面内`codingGuide.designReferences`（`source`取`common-design`/`product-design`/`code`/`ai-fill`，`ref`为来源标识）；声称引用 Product Design 或 Common Design 的决策必须有对应登记，无来源的决策须标记为 `ai-fill`，不得伪装成 Design Skill 规则（校验器以 RULE-40 提示，warning 级）。
- 生成HTML前必须运行设计闭环自动校验（`python scripts/validate_demo_spec.py --input demo-spec.json --template-registry references/02-template-contracts/common-design-template-registry.json --strict`）：页面清单闭环（RULE-28）、操作目标闭环（RULE-29）、Tab 变体闭环（RULE-30，仅多内容 Tab 页面强制）、页面级 Coding 闭环（RULE-31）、表格与详情字段一致性闭环（RULE-38，表格有详情容器时表格展示字段必须能在详情中找到）、表格标签使用约束闭环（RULE-39，同一表格内标签不超过 5 个，深色/icon/点状标签各仅允许 1 次、浅色标签最多 2 次，中性描述字段不占用标签配额）；error 级问题禁止生成HTML，warning 级不阻断，info 级仅提示待核验。
- 线框图必须绘制为严格继承所选模板布局结构的完整页面布局字符画：wireframe.ascii 按所选页面模板的标题栏、内容区、底部操作区等必需区域的位置关系与容器嵌套绘制，只允许替换文案并完善内容区中的具体内容，禁止调整模板布局结构、区块顺序、容器形态或新增模板不存在的区域；禁止用一句话或几个字代替线框图，禁止把线框图画成"每行一个区域名：内容"的标签罗列样式。ascii 过短或未覆盖模板必需区域会被校验器以 RULE-32 阻断，regions 声明的内容性区域在 ascii 中无绘制痕迹会以 RULE-33 提示，区域标签罗列会以 RULE-34 阻断。
- 设计说明书中的复用对象表达必须与代码可用状态一致：
  - `verified`：复用对象尽可能精确到真实页面文件、组件名称、文件路径、关键 Props / Events / Slots 或使用方式、复用类型（直接引用 / 复用框架 / 组件复用）、相对已有实现的新增字段与交互视觉差异、必须保留的页面结构和业务组件。
  - `partial` 或 `unavailable`：只描述设计语义和组件能力（如标准列表容器、业务策略列表框架、业务对象展示组件、标准状态切换组件、标准高风险确认链路），禁止虚构具体文件路径、组件路径、Props、Events 或调用方式；真实代码对象统一标记为“Coding 阶段待核验”。
- 生成页面级AI Coding指导前，读取 [Coding指导与执行规范](references/01-workflow/05-interaction-coding-guidelines.md) 中的Coding输出规则，并基于Design Context确定具体组件、复用对象和开发方式。
- 页面级AI Coding指导必须使用结构化开发项：HTML 展示“编号、开发对象、开发方式、复用与代码映射、实现要求、完成判定”六列表格，JSON 使用固定字段（id/scope/name/mode/mappingRef/mappingStatus/target/sourceRefs/dependencies/requirements/states/mockContract/acceptanceCriteria/prohibitedChanges），页面 codingGuide 固定为 pageContext + implementationRules + items + mockContract + stateContract + acceptanceCriteria + outOfScope，字段规范详见 [Coding指导与执行规范](references/01-workflow/05-interaction-coding-guidelines.md)；开发项须有稳定 ID，Coding Plan、Coding Execution 和 Verification 使用相同 ID 追踪，不得改名、合并或遗漏。不重复罗列字段级组件明细，但必须写明组件使用规则：严格按照页面区块、表格字段、表单字段中标注的组件名称开发，不得用原生HTML或其他组件替代；页面模板中已指定的标题栏、筛选区、表格、分页、弹窗、抽屉等组件，应按模板组件骨架实现；字段表中标注为标签、链接按钮、状态徽标、下拉选择、日期范围、开关等组件的内容，必须使用对应iDux或公司封装组件实现；未标注组件名称的普通文本/数字字段，可按常规文本渲染，如实现时发现交互含义，应回查Common Design组件映射表补齐。涉及已有页面、模块或业务组件时明确复用对象。
- 将逐页设计说明、页面内容区块、交互逻辑、状态规则、Mock数据和AI Coding指导整理为结构化JSON。
- 调用脚本生成HTML：`python scripts/generate_demo_spec_html.py --input ./demo-spec.json --output ./demo-design-spec.html --template-registry references/02-template-contracts/common-design-template-registry.json`。生成器默认 strict 模式，生成前自动执行模板契约校验，校验失败禁止写入 HTML；仅兼容旧 JSON 时使用 `--allow-legacy-wireframe`。
- 输出目录判定（HTML 与 demo-spec.json 同目录输出）：
  - 用户明确指定输出位置时，输出到用户指定位置；
  - 项目根目录存在 `.demo/design/` 且可确定对应 `{hash}` 子目录（`{hash}` 为真实存在的子目录名：优先取当前需求上下文确定的 hash，无法确定时若 `.demo/design/` 下仅有一个子目录则直接采用该子目录）时，输出到 `.demo/design/{hash}/`；
  - 找不到或无法确定 `.demo/design/{hash}/` 时，默认输出到项目根目录。
- 目录探测为只读静默检查，不创建、不修改目录；未找到 `.demo/design/{hash}/` 时直接按项目根目录输出，不得报错、中断或要求用户等待，不得因输出目录问题影响设计说明书生成。
- 输出目录仅限上述位置，禁止写入项目业务代码目录或已有功能文件夹。
- HTML标题使用“XX需求设计说明书”；左侧目录只包含总览和按页面层级组织的页面目录，不包含待确认问题。

## Step 6.5 Implementation Mapping Gate（代码实现映射阶段）

本阶段由 AI 自动执行，不要求产品经理或设计师读取、搜索或判断源代码。

- 位置：用户确认 HTML 说明书后、输出 Coding Plan 前；无论设计阶段代码状态如何，本阶段都必须执行，不得跳过直接开始 Coding。
- 情况 A（设计阶段代码状态为 `verified`）：重新验证 HTML 中写明的页面、组件、路径、参数和复用方式；确认设计说明书与当前代码实现是否一致；补充实际复用范围和新增差异。
- 情况 B（设计阶段为 `unavailable`，Coding 阶段发现代码）：读取当前代码环境；找到真实页面、组件、路由和交互；将设计说明书中的语义级组件映射到真实代码对象；必要时修正 HTML 中的 Coding 指导；不得绕过映射阶段直接开始 Coding。
- 情况 C（设计阶段为 `partial`）：保留已验证的映射；对未验证对象补充代码核验；必需复用对象必须在 Gate 内完成核验，非必需参考对象可标记为“不适用”。
- 本阶段必须输出统一映射表：

| 设计对象 | 是否必需复用 | 设计阶段表达 | 真实代码对象 | 实现方式 | AI核验依据 | 与设计说明书的差异 | 映射结果 | 视觉参考页面 | 视觉基线范围 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

- 必需复用对象判定：HTML、用户确认或 Product Design 明确要求复用的页面、组件或交互；会影响页面结构、视觉基线或核心交互的参考页面和组件；Coding 指导中明确写为“直接引用”“复用框架”或“组件复用”的对象。必需复用对象必须由 AI 完成真实代码核验，产品经理或设计师不承担代码核验职责。
- “实现方式”只能使用：直接引用 / 复用框架 / 组件复用 / 全新开发。
- “映射结果”只能使用：
  - `已验证`：AI 已找到真实代码对象，并确认路径、组件名称、关键 API 和使用方式；
  - `全新开发`：AI 已完成相关代码搜索，确认不存在满足需求的可复用对象；
  - `不适用`：该对象不是当前任务的实际实现对象，仅作为非阻塞性参考；
  - `阻塞`：设计要求复用，但 AI 无法访问代码、无法找到对象，或真实实现与设计存在无法自动解决的设计层差异。
- “待核验”只允许作为 Mapping Gate 执行前的临时状态，不能作为 Gate 完成后的必需对象结果；Gate 完成后，“Coding 阶段待核验”标记必须被映射结果替换并回填到 Coding Plan。
- Gate 通过条件：
  1. 所有必需复用对象均已标记为“已验证”；
  2. 不需要复用的对象已明确标记为“全新开发”或“不适用”；
  3. 没有未处理的设计层差异或业务事实缺失；
  4. 没有必需对象处于“阻塞”；
  5. 需求属于已有业务主题或页面体系时，已输出视觉参考页面与视觉基线范围映射且无未处理差异；全新页面体系可标记为“不适用（全新基线）”，不阻塞。
- 阻塞处理：若必需对象为“阻塞”，不得输出 Coding Plan，不得进入 Coding Execution；AI 应向用户说明阻塞原因，但只请求代码环境、访问条件或设计层确认，不要求用户自行查找代码。
- 如果没有可访问的代码且设计没有强制复用要求，AI 可以将对象标记为“全新开发”，按 Common Design、Product Design 和 HTML 设计执行，但不得声称复用了已有业务代码。
- 映射表输出后，将结果纳入 Coding Plan；未完成映射前不得输出 Coding Plan。

## Step 7 Coding Plan

- 用户确认点仅两处：Step 5 待确认问题和 Step 6 的 HTML 设计说明书；HTML 说明书生成后提醒用户查看，若用户反馈需调整，先更新 JSON 并重新生成 HTML，以最新确认的 HTML 作为基线。
- Step 6.5 Implementation Mapping Gate、本阶段 Coding Plan、Step 7.5 编码 Skill 声明识别与 Step 8 Coding Execution 均为自动执行环节：HTML 说明书确认后自动连续推进，Coding Plan 输出后无需等待用户确认即开始 Coding，Coding Plan 仅作为进度说明向用户展示。
- Coding Plan以最新HTML中的页面级AI Coding指导作为直接实现基线，不在本阶段重新设计页面结构、重新选择组件或重新改变开发方式。
- Coding Plan 以 Implementation Mapping Gate 输出的统一映射表为复用与差异基线，不再重复核验映射表中已确认的对象。
- 若映射阶段发现设计层差异，必须先修正结构化设计说明和 HTML 并重新获得用户确认，确认前不得输出 Coding Plan；业务事实缺失进入待确认问题；必需对象阻塞时按 Step 6.5 阻塞处理规则向用户说明。
- Coding Plan必须覆盖：输入来源、导航路径、全新开发页面、参考已有页面、复用对象、新增实现功能点、Mock策略、页面开发顺序和风险点。
- Coding Plan必须逐项映射HTML页面级AI Coding指导，不得遗漏、合并或自行改写开发项。

## Step 7.5 编码 Skill 声明识别（Coding 前置必做）

- 进入 Coding Execution 前，必须先主动查询当前项目文件中是否存在编码相关声明与编码类 Skill；该识别是编码前的必做动作，不得跳过，也不得因未找到而停止编码。
- 查询对象：
  - 项目根目录及约定的文档/配置目录中的声明与约定文件（如 README、AGENTS.md、CLAUDE.md、copilot-instructions、docs 下的项目说明或编码约定文档），查找其中关于“编码 / Coding / 开发实现应使用或遵循某 Skill”的明确声明；
  - 项目内实际存在的编码类 Skill 资源（如 skills/ 等目录下的 SKILL.md，其 metadata 或描述与 coding / 编码 / 开发实现相关）。
- 采用规则：声明或资源指向明确时，通过当前环境 Skill 查询能力实际查询并读取该 Skill 的 SKILL.md，确认其为编码相关后，将其规则作为 Coding Execution 的执行依据；未实际查询和读取的 Skill 一律视为不存在，禁止假设或虚构，禁止仅凭名称猜测其内容。
- 采用边界：项目声明的编码 Skill 约束 Coding Execution 的实现方式与执行细节（如框架约定、代码组织、命名、工具链、复用与新增策略），不得推翻已确认的 HTML 页面结构、组件映射、复用对象和开发项；其规则与 HTML / Coding Plan 冲突时，按“差异分级与处理规则”处理。
- 兜底：未找到项目声明的编码类 Skill、声明无法对应到可查询 Skill，或项目无编码相关声明时，按本 Skill 默认 Coding Execution 流程继续编码；不得因未找到而停止、挂起编码或要求用户等待，识别结果记入 Coding Execution 进度输出。

## Step 8 Coding Execution

- 开始逐页编码前，确认 Step 7.5 编码 Skill 声明识别已完成并明确其识别结果。
- 按HTML左侧页面目录和页面层级拆分Coding任务，一个页面完成并自检后，再开始下一个页面。
- 先开发父级主页面，再开发新增、编辑、详情、弹窗、抽屉或下钻页面，确保入口和跳转链路可运行。
- 每页开发前核对Design Context、HTML页面说明、页面级Coding指导、复用对象和Mock数据要求。
- 每页完成后告知用户已完成哪个页面、接下来开发哪个页面。
- 并发开发限制：
  - 允许并发：只读代码调研、Mock 数据整理、类型定义整理、不涉及共享页面骨架的准备工作。
  - 禁止并发：共享页面外壳尚未冻结时并行开发多个页面；父页面和子页面同时 Coding；共享工具栏、表格容器、表单容器或业务组件尚未确认时并行实现；多个 Agent 分别决定同一业务组件的替代实现；Implementation Mapping Gate 尚未完成时进入页面 Coding。
  - 仅当页面骨架、视觉基线、公共组件和实现映射已经冻结后，才允许并发开发完全独立的页面。
- 所有页面完成后，告知用户“Demo已开发完毕，请告知有哪些需要调整的”。

## Step 9 Verification

- 读取 [质量自检机制与规则](references/01-workflow/06-quality-and-rules.md)，执行输出边界、Design Context、页面总览、HTML说明书、Coding Plan和Coding结果检查。
- 验证HTML说明书输出目录是否符合输出目录判定规则（用户指定位置 / 可发现的 `.demo/design/{hash}/` / 默认项目根目录），且 demo-spec.json 与 HTML 位于同一输出目录；页面总览与HTML逐页说明是否一致、页面结构与Design Context是否一致。
- 验证Coding实现是否落实HTML页面级开发项、复用策略、页面结构、关键字段、操作、状态、边界和Mock数据。
- 验证视觉基线：属于已有业务主题或已有页面体系的需求，必须对照真实参考页面做视觉回归，覆盖页面容器、页面标题层级、Tab 结构、筛选区、工具栏、表格容器、表格字段展示、状态组件、操作列、按钮位置和顺序、间距边界和空状态、高风险确认链路；功能行为、组件复用、页面结构和视觉基线回归均通过后，才可宣称 Demo 完整交付。
- 若用户反馈Coding效果不好，先判断问题来源是需求理解、Design Context、HTML说明书、代码实现、业务规范还是组件复用策略，再决定回到对应步骤修正。

# 差异分级与处理规则

发现设计说明书与真实代码不一致时，不得静默修改，也不得把复用实现直接替换为全新开发。按以下分级处理：

- 实现层差异：仅影响具体组件名称、文件路径或调用方式，不影响页面结构、视觉基线、交互流程和业务规则。处理：记录到映射表和 Coding Plan，更新 Coding Plan 后继续开发。
- 设计层差异：影响页面容器、布局、表格结构、视觉层级、交互流程、状态规则或业务规则。处理：先修正结构化设计说明和 HTML，重新获得用户确认；确认前不得进入 Coding Execution。
- 业务事实缺失：权限、状态流转、数量限制、接口约束等无法从 PRD、用户确认、Product Design 或代码中确定。处理：进入待确认问题，不得用虚构业务逻辑替代。

# 视觉基线约束

当需求属于已有业务主题或已有页面体系时，必须把真实参考页面作为视觉和交互基线，不能只复用业务字段和数据模型而忽略已有页面的视觉结构。

视觉基线映射至少包括：

- 页面容器；
- 页面标题层级；
- Tab 结构；
- 筛选区；
- 工具栏；
- 表格容器；
- 表格字段展示；
- 状态组件；
- 操作列；
- 按钮位置和顺序；
- 间距、边界和空状态；
- 高风险确认链路。

视觉基线结果写入 Design Context 和页面总览；视觉参考页面与视觉基线范围必须在 Implementation Mapping Gate 中完成核验：属于已有页面体系但未完成映射时，Gate 不通过，不得进入 Coding。Coding 阶段必须对照该基线实现，Verification 必须包含视觉基线回归。

# 强制模板契约与线框校验

每个页面必须绑定标准页面模板，结构化 wireframe 是唯一可信来源；未通过模板契约校验不得生成 HTML，不得进入 Implementation Mapping Gate 和 Coding。

- 页面类型与模板绑定：
  - 每个页面必须绑定标准页面模板 templateId，禁止只写业务自定义名称。允许的 templateId 清单与模板定义以模板注册表为准（见 [common-design-template-registry.json](references/02-template-contracts/common-design-template-registry.json)），禁止凭 AI 经验新增或修改模板结构。
  - 需求无法匹配标准模板时，使用 `templateId: custom` + `baseTemplateId`（某个标准模板）+ `customReason` + `override.source`（用户确认 / PRD / Product Design / 已有代码）+ `override.affectedRules`（overrideJustification，说明覆盖了哪些模板约束）。不能仅通过 type 字段写“下钻配置表单页”这类未注册页面类型。
- 导航类型：每个需要区分导航的页面必须填写 navigationType（left-shaped / l-shaped）；没有明确依据时默认 left-shaped，但必须写 navigationTypeStatus: assumed、navigationTypeSource: AI 补齐、navigationTypeNote: 当前默认依据。
- 模板契约 templateContract：每个页面必须填写，至少包含 templateId、baseTemplateId、navigationType、templateSource、requiredRegions、optionalRegions、regionOrder、footerContract、componentContract、wireframeContract、override（enabled/source/reason/affectedRules）。字段规范与示例见 [HTML输出模板](references/01-workflow/01-output-templates.md) 与 [HTML逐页设计说明](references/01-workflow/04-demo-output-spec.md)。
- 闭环要求：页面类型、模板结构、layout、sections、wireframe、footerActions、组件映射、codingGuide 必须形成闭环。禁止以下情况：页面 type 与 templateId 不一致；基础表格页没有 Toolbar/Table/Pagination；弹窗列表页没有 Modal 外壳、关闭入口和列表主体；抽屉列表页没有 Drawer 外壳、对象上下文、Toolbar、Table；步骤条配置页没有 Stepper；多步骤页面只有一张总线框图；存在 footerActions 但 wireframe 没有底部操作区；wireframe 出现的区块没有 sections 或 templateContract 依据；sections 声明的必需区块没有出现在 wireframe；footer 对齐与模板不一致且无 override 记录。
- 生成门禁：HTML 生成前自动执行 [validate_demo_spec.py](scripts/validate_demo_spec.py) 模板契约校验；校验失败禁止写入 HTML；validationStatus 非 passed 时不得进入 Implementation Mapping Gate，wireframe 结构校验失败时不得输出 Coding Plan。校验规则与错误码由校验脚本输出，模板注册表见 [common-design-template-registry.json](references/02-template-contracts/common-design-template-registry.json)。
- legacy 兼容：纯字符串 wireframe 只允许作为 legacy 输入，必须进入兼容模式警告；strict 模式下不得生成 HTML，`--allow-legacy-wireframe` 仅用于兼容旧 JSON，且 HTML 顶部必须显示“本说明书使用旧版自由文本线框，未完成模板契约校验，不得作为 Coding 基线”。

# 输出 Contract

- 对话框输出：需求与Demo范围、核心用户与场景、Design Context摘要、导航结构、页面总览表、待确认问题、HTML文件路径、Coding Plan和Coding执行进度。
- HTML输出：总览页、导航结构、页面总览表、逐页页面目标、页面基础信息、页面内容区块、Wireframe / ASCII线框图（先展示完整线框图，下方补充线框说明与变体）、底部操作、页面级AI Coding指导（开头输出模板契约：templateId/templateSource/模板必需区域/区域顺序/底部操作契约）、Mock数据要求。
- Coding Plan输出：输入来源、Design Context使用方式、Implementation Mapping Gate映射结果、页面开发顺序、复用对象、新增开发项、风险点。
- Coding Execution输出：编码 Skill 声明识别结果（是否找到、采用的编码 Skill、未找到时的默认执行说明）、按页开发进度、页面级验证结论、下一页计划、最终完成说明。
- 禁止在对话框展开HTML逐页详情、完整交互规则、完整Mock数据和完整AI Coding提示词。

# Quality Gate

- Design Skill Resolver已执行，Common Design已识别；若存在匹配Product Design，其Coverage关系已识别。
- Common Design已完成“查询 → SKILL.md读取 → metadata校验”；不存在Common Design时未进入正式页面设计。
- Design Context已形成，且每项命中设计能力的知识来源明确。
- Design Context 包含代码可用状态（verified 已核验 / partial 部分可用 / unavailable 不可用）；`partial` / `unavailable` 状态下未虚构真实文件路径、组件路径、Props 或 Events。
- HTML中的页面级AI Coding指导已在生成HTML前完成组件映射和复用对象判断；Coding Plan未重新改变已确认HTML中的组件、复用对象和开发方式。
- HTML线框图已校验页面模板结构一致性；页面类型、模板结构、layout、内容区块、wireframe、组件与交互、页面级AI Coding指导均一致；含底部操作区的页面、抽屉、弹窗等容器均继承已读取Common Design中的按钮位置与顺序规则，不存在无依据的左右分置或跨容器规则混用。
- 每页均已形成页面类型决策记录；页面类型来自已读取的标准类型或已验证代码，自定义页面类型已说明继承模板与差异；声明复用已有页面或参考已有框架的页面已完成容器结构、步骤条、工具栏、底部按钮位置和关键交互的代码参考验收。
- 未使用未匹配产品的Product Design；Product Design 声明逗号分隔的多产品标识时，未因需求产品名与主标识不一致而漏用或误判其Product Design；未通过产品缩写或普通关键词猜测Product Design。
- 页面总览与HTML逐页说明中的页面ID、页面名称、页面类型、导航路径和入口方式一致。
- 待确认问题已在HTML前输出并等待用户确认；未把待确认问题写入HTML。
- HTML文件与 demo-spec.json 已按输出目录判定规则输出（用户指定位置 / 可发现的 `.demo/design/{hash}/` / 默认项目根目录），未写入项目业务代码目录或已有功能文件夹；未发现目标目录时已回退默认目录且未中断生成。
- HTML说明书覆盖逐页设计、交互逻辑、边界状态、Mock数据和AI Coding指导。
- Implementation Mapping Gate 由 AI 自动执行；输出 Coding Plan 前已输出统一映射表，所有必需复用对象均为“已验证”；必需对象为“阻塞”时未继续输出 Coding Plan；“待核验”只存在于 Gate 执行前，不作为 Gate 完成后的结果。
- 设计说明书与真实代码的差异已完成分级处理：实现层差异已记录并更新 Coding Plan，设计层差异已修正 HTML 并重新获得用户确认，业务事实缺失已进入待确认问题；未将实现层差异静默改为全新开发。
- 视觉基线已完成核对：属于已有业务主题或页面体系的需求已对照真实参考页面做视觉回归；功能、交互、组件复用和视觉回归均通过后，才宣称任务完成。
- 模板契约校验通过后才生成 HTML；HTML 生成成功不代表校验通过；校验通过时 HTML 顶部不显示校验横幅，校验失败（含 legacy 兼容模式）时 HTML 顶部显示失败提示横幅，validationStatus 非 passed 时未进入 Implementation Mapping Gate，wireframe 结构校验失败时未输出 Coding Plan。
- 每个页面已绑定标准 templateId 或 custom 模板（含 baseTemplateId、customReason 与 override.affectedRules）；navigationType 已声明或按 assumed + source 处理；未使用未注册页面类型名称；未在 strict 模式下静默通过 legacy 自由文本线框。
- Coding Plan逐项映射HTML页面级AI Coding指导；用户确认点仅 Step 5 待确认问题与 Step 6 HTML 设计说明书两处，HTML 确认后 Coding Plan 输出即自动进入 Coding Execution，无需再次确认。
- 进入 Coding Execution 前已完成 Step 7.5 项目编码 Skill 声明识别：存在明确声明时已按声明的编码 Skill 执行且未越界改变 HTML 已确认的页面结构与开发项；未找到或无法确认时已按默认流程继续编码，未虚构、未阻断。
- Coding Execution按页面顺序推进，每页完成后做页面级核对；未在共享页面骨架冻结前并发 Coding。

# 本 Skill 自有资源

- HTML generator：见 [scripts/generate_demo_spec_html.py](scripts/generate_demo_spec_html.py)，读取结构化Demo设计JSON并生成HTML说明书；参数为`--input`、`--output`和`--template-registry`，默认 strict 模式，生成前自动执行模板契约校验，校验失败禁止写入 HTML；`--allow-legacy-wireframe` 仅用于兼容旧 JSON。
- Template validator：见 [scripts/validate_demo_spec.py](scripts/validate_demo_spec.py)，校验模板契约与线框结构（40 项规则），输出结构化 JSON 错误与修复建议；参数为`--input`、`--template-registry`和`--strict`，校验失败返回非 0 exit code。
- Template registry：见 [references/02-template-contracts/common-design-template-registry.json](references/02-template-contracts/common-design-template-registry.json)，14 个标准页面模板的必需区域、必需组件、footer 契约与变体规则，规则来源于 Common Design。
- HTML template：见 [assets/demo-spec-template.html](assets/demo-spec-template.html)，HTML说明书模板，由脚本读取并注入设计数据。
- workflow/output schemas：
  - [references/01-workflow/00-design-skill-resolver.md](references/01-workflow/00-design-skill-resolver.md)：识别、选择和装配Common Design与Product Design。
  - [references/01-workflow/01-output-templates.md](references/01-workflow/01-output-templates.md)：对话框输出、HTML JSON和Coding计划模板。
  - [references/01-workflow/02-experience-goal-writing.md](references/01-workflow/02-experience-goal-writing.md)：已保留为历史参考，不再用于HTML输出生成。
  - [references/01-workflow/03-demo-page-decomposition.md](references/01-workflow/03-demo-page-decomposition.md)：页面拆解、页面总览和Demo范围过滤。
  - [references/01-workflow/04-demo-output-spec.md](references/01-workflow/04-demo-output-spec.md)：HTML逐页设计说明、说明书结构和设计闭环自动校验。
  - [references/01-workflow/05-interaction-coding-guidelines.md](references/01-workflow/05-interaction-coding-guidelines.md)：代码环境核验、Implementation Mapping Gate、Mock数据、Coding指导和逐页执行规则。
  - [references/01-workflow/06-quality-and-rules.md](references/01-workflow/06-quality-and-rules.md)：质量自检、禁止事项和Coding执行检查。
  - [references/05-examples/demo-design-examples.md](references/05-examples/demo-design-examples.md)：HTML说明书输入JSON与页面说明示例。
- Tests：见 [tests/test_validate_demo_spec.py](tests/test_validate_demo_spec.py)，模板契约校验器的 58 个回归用例（合法页面通过、缺分页/标题栏/关闭入口、footer 对齐、Stepper 组件、步骤变体、custom override、未注册类型、section 一致性、partial 路径、legacy 警告、设计闭环、表格详情一致性、表格标签使用约束、设计依据可追溯），运行方式 `python3 -m unittest discover -s tests`。

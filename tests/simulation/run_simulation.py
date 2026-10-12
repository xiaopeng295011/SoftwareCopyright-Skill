#!/usr/bin/env python3
"""Repeat fictional forward test. Simulated confirmations never authorize real materials."""
from pathlib import Path
import json
import subprocess
import sys
import importlib.util
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/fictitious-reagent'
BASE = ROOT / 'tests/simulation'
OUT = BASE / '软件著作权申请资料'
DRAFT = OUT / '草稿'
SCRIPTS = ROOT / 'software-copyright-materials/scripts'
NAME = '虚构青岚医院检验试剂管理软件'
NOTE = 'TEST_ONLY：用户授权的模拟测试确认；不代表真实用户确认，不得用于实际申请。'
logs = []
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def run(script, *args, expected=0):
    cmd = [sys.executable, str(SCRIPTS / script), *map(str, args)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    logs.append({'script': script, 'args': list(map(str, args)), 'exit_code': proc.returncode,
                 'stdout': proc.stdout, 'stderr': proc.stderr})
    if proc.returncode != expected:
        dump(BASE / 'execution.json', logs)
        raise RuntimeError(f'{script}: expected {expected}, got {proc.returncode}: {proc.stderr}{proc.stdout}')
    return proc

def confirm(stage, *extra):
    run('confirm_stage.py', '--workdir', OUT, '--stage', stage, '--note', NOTE, *extra)

modules = [
    {'title': '入库登记', 'purpose': '记录到库试剂的批次和数量，建立可供出库的库存。',
     'usage': '库管员收到试剂后，需要把包装上的标识、批号和有效期登记到库存。',
     'entry': '打开首页后，点击顶部的“入库登记”链接，页面跳转到入库区域。',
     'visible_elements': ['UDI输入框', '批号输入框', '有效期日期框', '数量输入框', '确认入库按钮'],
     'operation_steps': ['先核对包装上的UDI并输入14位数字，再填写批号。', '选择包装标注的有效期，数量填本次实际收到的盒数。', '点击“确认入库”，检查库存表中该批次的数量，并查看状态提示。'],
     'validation_rules': ['所有字段必填，UDI只能包含14位数字。', '数量必须为正整数，有效期应为有效日期。', '同UDI和批号已有记录时，新登记的有效期必须与原记录一致。'],
     'feedback': ['成功后页面显示“登记成功，库存和流水已更新”。', '首次登记会新增一行库存，后续同批次登记增加数量。', '出现有效期不一致提示时，核对包装并重新填写。'],
     'screenshot': '入库登记表单和登记成功后的库存'},
    {'title': '出库登记', 'purpose': '登记试剂领用数量，减少相应批次的库存。',
     'usage': '检验科领用试剂时，库管员按包装批号登记实际领用盒数。',
     'entry': '点击顶部“出库登记”链接，定位到出库表单。',
     'visible_elements': ['UDI输入框', '批号输入框', '数量输入框', '确认出库按钮'],
     'operation_steps': ['从库存表核对UDI和批号，填写到出库表单。', '填写本次领用数量，点击“确认出库”。', '返回库存表核对剩余数量，到流水区域确认新增出库记录。'],
     'validation_rules': ['出库数量必须大于零且不能超过该批次库存。', '不存在的批次无法出库。', '有效期早于当天的批次显示“过期批次不能出库”。'],
     'feedback': ['成功后库存减少相应数量，并出现一条出库流水。', '数量不符合条件时，状态区提示错误，库存保持原值。'],
     'screenshot': '出库表单、库存余额及错误提示'},
    {'title': '库存与效期', 'purpose': '查看已登记试剂的批次、有效期和当前库存。',
     'usage': '库管员准备发放试剂或核对账物时，先在表中查找相应批次。',
     'entry': '点击顶部“库存与效期”链接，页面定位到库存表。',
     'visible_elements': ['UDI列', '批号列', '有效期列', '库存数量列'],
     'operation_steps': ['根据包装UDI和批号在表中定位对应行。', '核对有效期和剩余数量，再决定是否登记出库。', '入出库完成后，检查表中数量变化是否与本次登记一致。'],
     'validation_rules': ['页面没有删除或直接改库存入口。', '无登记记录时表格只显示列标题。', '同UDI的不同批号分别显示。'],
     'feedback': ['表格显示本次服务期间的库存余额。', '服务重启后库存清空，应重新使用虚构批次测试。'],
     'screenshot': '包含两个虚构批次的库存表'},
    {'title': '流水追溯', 'purpose': '核对本次服务启动后的每笔入库和出库登记。',
     'usage': '数量发生变化时，库管员用流水确认登记方向、批号和数量。',
     'entry': '点击顶部“流水追溯”链接，页面定位到流水展示区。',
     'visible_elements': ['操作方向', 'UDI', '批号', '登记数量'],
     'operation_steps': ['查看流水区域的记录，按显示顺序核对登记。', '把记录中的UDI和批号与库存表对应起来。', '比较入库增加量和出库减少量，确认当前余额。'],
     'validation_rules': ['只展示成功登记，不记录被拒绝的操作。', '流水为只读内容，没有修改或删除按钮。', '服务重启后记录清空，不支持跨次追溯。'],
     'feedback': ['每次成功登记追加一条记录。', '没有登记时展示空记录数组。'],
     'screenshot': '一条入库和一条出库的虚构流水'},
]
modules[1]['usage'] += '例如本次入库十盒后领用三盒，完成登记时应剩余七盒。应填写包装对应的同一个批号，不能把不同批号的余额相加作为本次可领用数量。库存不足提示出现后先核对批次，页面不会替用户更换批次，也不会把拒绝的记录计入流水。'
modules[2]['usage'] += '核对时把实物包装标识、批号和有效期与同一行逐项对应。数量为零的批次仍可留在表中，表示该批次已经全部领用。同试剂不同批次不能只根据UDI判断余额，必须再核对批号。软件没有排序和筛选按钮，当前所有登记批次都在这张表中直接显示。'
modules[3]['usage'] += '例如先入库十盒再出库三盒，区域中应出现方向不同的两条记录，数量分别为十和三。这些数量是每次登记量，不是登记后的余额；余额需要到库存表查看。记录不含时间和经办人，也不能查看上一次启动服务时的记录，因此只能用于核对本轮虚构操作。'
for module in modules:
    module['evidence'] = ['app.py', 'README.md', '详细设计.md']
main_functions = '''软件供虚构医院检验科库管员登记试剂收货、领用和批次库存，页面包含入库登记、出库登记、库存与效期、流水追溯四个区域。顶部链接定位到相应区域，库管员在同一页面完成录入、核对余额和查看登记记录。软件不处理患者信息，所有试剂标识及批号均为迁移验证使用的模拟数据。入库登记需要填写14位数字UDI、批号、有效期和收到的数量。页面为有效期提供日期选择框，数量使用正整数输入。同UDI和批号第一次登记时建立库存行，再次登记时累计数量；已有批次的有效期与本次填写不一致时拒绝登记，并在页面状态区显示原因，原有库存不发生变化。出库登记接收UDI、批号和领用数量，按两项标识找到库存批次，核对剩余数量和有效期。数量为零、负数、超过余额或批次不存在时不扣减库存；过期批次不能出库。符合条件时减少库存数量并追加出库流水，状态区显示登记成功。库存与效期区域用表格呈现各批次的UDI、批号、有效期和当前数量。同UDI的不同批号分别列出，方便按包装批号核对账物。表格是只读内容，余额只能通过成功的入库或出库登记改变，没有直接修改或删除库存的入口。流水追溯按登记顺序展示操作方向、UDI、批号及数量，库管员可对照入库增加量、出库减少量和当前余额核查本次测试记录。被校验拒绝的操作不会新增流水。页面输入和结果展示使用中文，错误提示保留在登记区域上方；输出的动态数据经过转义后显示，避免包装批号中的特殊字符改变页面结构。试剂库存和流水仅保存在当前服务的内存中，关闭并重新启动服务后全部清空，不提供跨次保存、账号权限、患者查询、计费、数据导出或外部系统连接。'''
model = {
    'software_name': NAME, 'product_positioning': '用于虚构检验科入出库流程验证的本机浏览器软件。',
    'industry': '医疗机构检验科试剂库存管理（虚构测试）', 'target_users': ['虚构检验科库管员'],
    'core_value': '让同一批次的收货、领用、库存余额及登记记录可相互核对。',
    'business_features': [m['title'] for m in modules],
    'business_feature_details': {m['title']: m['purpose'] + m['usage'] + ''.join(m['feedback']) for m in modules},
    'operation_flow': ['启动本机服务并打开首页', '登记试剂入库', '核对批次有效期与余额', '登记出库', '核对库存和流水'],
    'application_purpose': '验证虚构检验科试剂入出库、效期核对及流水追溯流程。',
    'main_functions': main_functions, 'technical_characteristics': '本机浏览器表单处理，按UDI与批号定位库存，校验数量与有效期，中文结果展示及输出转义。',
    'manual_sections': [], 'manual_modules': modules,
    'system_requirements': [{'item': '系统与服务', 'minimum': 'Linux、Python 3.10+', 'recommended': 'Linux、Python 3.10+'}, {'item': '硬件（模拟设定）', 'minimum': '2核、2GB内存、100MB空间', 'recommended': '4核、4GB内存、100MB空间'}, {'item': '浏览器', 'minimum': '支持HTML表单的浏览器', 'recommended': '支持日期输入的浏览器'}],
    'faq': [{'question': '库存不足怎么办？', 'answer': '检查批号和数量，数量不得超过该批次库存。'}, {'question': '为什么过期批次不能出库？', 'answer': '软件比较有效期与当天日期，过期批次保留库存但拒绝领用登记。'}, {'question': '重启后记录为何消失？', 'answer': '该测试软件仅在当前服务内存保存数据，重启后需重新录入虚构批次。'}],
    'glossary': [{'term': 'UDI', 'definition': '本测试使用的14位数字试剂标识。'}, {'term': '批号', 'definition': '用于区分同一试剂不同生产批次的模拟标签。'}, {'term': '流水', 'definition': '成功入库及出库的登记记录。'}],
}
answers = {'软件全称': NAME, '软件简称': '青岚试剂（模拟）', '版本号': 'V1.0', '开发完成日期': '2026-10-12', '开发方式': '单独开发', '软件说明': '原创', '发表状态': '未发表', '首次发表日期': '不适用（未发表）', '著作权人': '中国/虚构省虚构市/法人/虚构青岚测试单位/测试证件/TEST-ONLY-NOT-VALID', '权利范围': '全部权利', '权利取得方式': '原始取得', '开发的硬件环境': '模拟：4核CPU、4GB内存、100MB空间', '运行的硬件环境': '模拟：2核CPU、2GB内存、100MB空间', '开发该软件的操作系统': 'Linux（模拟设定）', '软件开发环境 / 开发工具': '开发环境: Linux/开发工具: 文本编辑器', '该软件的运行平台 / 操作系统': 'Linux及支持HTML表单的浏览器', '软件运行支撑环境 / 支持软件': 'Python 3.10+、浏览器', '编程语言': 'Python、HTML'}

def main():
    with tempfile.TemporaryDirectory(prefix="softcopyright-gate-") as empty:
        rejected = run("build_docx_from_md.py", "--workdir", empty, "--software-name", NAME, "--txt-only", expected=2)
        assert "STOP_FOR_USER" in rejected.stdout
        assert not (Path(empty) / "正式资料/申请表信息.txt").exists()
    DRAFT.mkdir(parents=True, exist_ok=True)
    dump(BASE / 'model-context.json', model)
    dump(BASE / 'answers.json', answers)
    run('check_environment.py', '--out-dir', OUT)
    confirm('environment')
    analysis = OUT / 'analysis/project.json'
    run('analyze_project.py', '--project', FIXTURE, '--out', analysis)
    run('generate_business_context.py', '--project', FIXTURE, '--analysis', analysis, '--software-name', NAME, '--out-dir', DRAFT, '--model-context', BASE / 'model-context.json')
    confirm('business')
    run('propose_code_selection.py', '--project', FIXTURE, '--analysis', analysis, '--out-dir', DRAFT)
    selection = DRAFT / '代码文件选择.json'
    data = json.loads(selection.read_text())
    for item in data['files']:
        item['selected'] = item['path'] == 'app.py'
        item['model_reason'] = '完整最小程序包含四个页面区域及实际入出库校验；仅此文件属于业务源码。' if item['selected'] else '不是本测试业务源码。'
    dump(selection, data)
    confirm('code-selection')
    run('extract_code_material.py', '--project', FIXTURE, '--analysis', analysis, '--selection', selection, '--software-name', NAME, '--version', 'V1.0', '--out-dir', DRAFT)
    run('generate_application_info.py', '--analysis', analysis, '--code-manifest', DRAFT / '代码提取清单.json', '--business-context', DRAFT / '业务理解.json', '--software-name', NAME, '--version', 'V1.0', '--answers', BASE / 'answers.json', '--out-dir', DRAFT)
    confirm('application-fields')
    run('generate_manual_draft.py', '--analysis', analysis, '--business-context', DRAFT / '业务理解.json', '--software-name', NAME, '--version', 'V1.0', '--out-dir', DRAFT)
    sys.path.insert(0, str(SCRIPTS))
    # Model review of actual generated prose before simulated final confirmation.
    manual_path = DRAFT / '操作手册.md'
    prose = manual_path.read_text(encoding='utf-8')
    assert '账号进入、业务创建、过程查看、结果确认和资料管理' not in prose
    assert '本手册用于说明软件的用途' not in prose
    prose = prose.replace('用户先先核对', '用户先核对')
    manual_path.write_text(prose, encoding='utf-8')
    from generate_manual_draft import manual_quality_issues
    issues = manual_quality_issues(prose, modules)
    assert not issues, issues
    review_path = DRAFT / '操作手册自检记录.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    review['rounds'].append({'round': 4, 'action': '模型核对实际源码：断言无账号及资料管理套话，修正重复词，检查四个真实区域', 'issues': issues})
    dump(review_path, review)
    with (DRAFT / '操作手册自检记录.md').open('a', encoding='utf-8') as review_md:
        review_md.write('\n## 第4轮：模型逐章核对实际源码\n\n确认无账号和资料管理套话，修正重复词。四个实际区域的入口、表单、规则、反馈及截图占位一致。复核无问题。\n')
    confirm('screenshot-method', '--method', 'skip')
    confirm('markdown')
    sys.path.insert(0, str(SCRIPTS))
    from build_docx_from_md import confirmation_issues
    assert not confirmation_issues(OUT), confirmation_issues(OUT)
    run('build_docx_from_md.py', '--workdir', OUT, '--software-name', NAME, '--version', 'V1.0', '--txt-only')
    run('build_docx_from_md.py', '--workdir', OUT, '--software-name', NAME, '--version', 'V1.0', expected=1)
    txt = OUT / '正式资料/申请表信息.txt'
    warnings = []
    assert txt and txt.stat().st_size
    assert NAME in txt.read_text(encoding='utf-8')
    manual = (DRAFT / '操作手册.md').read_text(encoding='utf-8')
    assert manual.count('【截图预留：') == 4
    spec = importlib.util.spec_from_file_location('fixture_app', FIXTURE / 'app.py')
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app.receive('00000000000001', 'SIM-A', '2099-12-31', 10)
    app.issue('00000000000001', 'SIM-A', 3)
    assert app.stock[0]['quantity'] == 7 and len(app.ledger) == 2
    for fn, args in [(app.receive, ('INVALID', 'SIM-A', '2099-12-31', 1)), (app.issue, ('00000000000001', 'SIM-A', 8))]:
        try:
            fn(*args)
            raise AssertionError('invalid operation accepted')
        except ValueError:
            pass
    app.receive('00000000000002', 'SIM-B', '2000-01-01', 1)
    try:
        app.issue('00000000000002', 'SIM-B', 1)
        raise AssertionError('expired issue accepted')
    except ValueError:
        pass
    result = {'simulation_only': True, 'confirmation_note': NOTE, 'drafts': 'PASS', 'source_extraction': 'PASS: app.py complete file', 'application_txt': 'PASS', 'application_field_consistency': 'PASS', 'manual_placeholders': 'PASS: 4 visible placeholders', 'fixture_business_checks': 'PASS', 'docx': 'NOT_EXECUTED: OfficeCLI missing; no installation attempted', 'theme_fonts': 'NOT_EXECUTED', 'word_headers_and_pages': 'NOT_EXECUTED', 'word_code_pagination': 'NOT_EXECUTED', 'playwright_screenshots': 'NOT_EXECUTED: simulation uses explicit skip', 'warnings': warnings}
    dump(BASE / 'result.json', result)
    dump(BASE / 'execution.json', logs)
    (BASE / '结果.md').write_text('# 模拟测试结果\n\n仅测试，不可用于实际申请。所有确认均标记TEST_ONLY，不代表真实用户确认。\n\n实际完成环境检查、项目分析、业务理解、源码候选确认、完整app.py源码抽取、申请表及操作手册草稿、确认指纹校验、申请表TXT输出。入库10、出库3后余额7；非法UDI、超库存及过期出库校验通过。\n\nOfficeCLI不可用，未生成DOCX；中文Word显示、主题字体、页眉页码、真实分页均未执行。未运行Playwright CLI、未创建截图，四个操作章节保留可见截图占位。源码不足60页，输出全部代码草稿，草稿估算页数不代表Word实测页数。\n\n重跑：在仓库根目录执行 `python tests/simulation/run_simulation.py`。项目预览：`python tests/fixtures/fictitious-reagent/app.py`，打开 http://127.0.0.1:8765 。\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

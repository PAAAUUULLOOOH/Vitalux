"""Conservative source-dependency selection; uncertain/critical changes run all."""
import ast
from pathlib import Path

CRITICAL=('portable-runtime/','packaging/','requirements','.github/','assets/',
          'vitalux/__init__.py',
          'scripts/run-regressions.py','scripts/regression_selection.py',
          'vitalux/__main__.py','vitalux/settings.py','vitalux/profiles.py',
          'vitalux/lifecycle.py','vitalux/window_lifecycle.py','vitalux/window.py',
          'vitalux/telemetry.py','vitalux/renderer.py','vitalux/single_instance.py',
          'vitalux/window_appearance.py','vitalux/tray_controls.py','vitalux/widgets.py',
          'vitalux/charts.py','vitalux/page_base.py',
          'vitalux/restart_protocol.py','vitalux/startup.py','vitalux/theme.py','vitalux/ui_locale.py')
SMOKE={'test_core_behaviors.py','test_single_instance.py','test_update_catalog.py','test_versioning.py'}
DOC_CHECKS={'test_guide_locale.py','test_preferences_changelog.py','test_changelog_view.py',
            'test_info_credits.py','test_sculpt_design.py'}
DYNAMIC={'exec','eval','__import__','import_module','spec_from_file_location'}
PROCESS_CALLS={'run','Popen','call','check_call','check_output','getoutput','getstatusoutput'}


def select(root, changed):
    root=Path(root);tests=sorted((root/'tests').glob('test_*.py'))
    changed=set(changed)
    full=lambda reason:dict(full=True,reason=reason,selected=[p.name for p in tests],skipped=[])
    if any(path.startswith(CRITICAL) or path.endswith('.sh') for path in changed):return full('Runtime, shared UI, launcher or selection change')
    paths=[p for directory in ('vitalux','scripts','tests') for p in (root/directory).glob('*.py')]
    modules={str(p.relative_to(root)).removesuffix('.py').replace('/','.').removesuffix('.__init__'):p for p in paths}
    names={p.stem:p for p in paths if sum(q.stem==p.stem for q in paths)==1}
    modules.update(names)
    dependencies={};uncertain=set()
    for path in paths:
        relative=str(path.relative_to(root));found=set()
        try:tree=ast.parse(path.read_text())
        except (OSError,SyntaxError):return full('Dependency graph unavailable')
        process_modules={item.asname or item.name for node in ast.walk(tree) if isinstance(node,ast.Import)
                         for item in node.names if item.name=='subprocess'}
        process_functions={item.asname or item.name for node in ast.walk(tree)
                           if isinstance(node,ast.ImportFrom) and node.module=='subprocess'
                           for item in node.names if item.name in PROCESS_CALLS}
        package=path.relative_to(root).parent.parts
        for node in ast.walk(tree):
            candidates=[]
            if isinstance(node,ast.Import):candidates=[item.name for item in node.names]
            elif isinstance(node,ast.ImportFrom):
                prefix='.'.join(package[:len(package)-node.level+1]) if node.level else ''
                base='.'.join(part for part in (prefix,node.module) if part)
                candidates=[base,*[base+'.'+item.name for item in node.names]]
            elif isinstance(node,ast.Call):
                name=getattr(node.func,'id',getattr(node.func,'attr',''))
                # A spawned interpreter/launcher can import code inside a
                # string or shell script, outside the static Python graph.
                if (isinstance(node.func,ast.Name) and name in process_functions
                        or isinstance(node.func,ast.Attribute) and name in PROCESS_CALLS
                        and isinstance(node.func.value,ast.Name) and node.func.value.id in process_modules):
                    uncertain.add(relative)
                if name in ('__import__','import_module') and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
                    candidates=[node.args[0].value]
                elif name in DYNAMIC:uncertain.add(relative)
            for name in candidates:
                if name in modules:found.add(str(modules[name].relative_to(root)))
        dependencies[relative]=found
    meaningful={p for p in changed if not p.endswith('.md') and p!='vitalux/__init__.py'}
    docs=any(p.endswith('.md') for p in changed)
    if any(p not in dependencies for p in meaningful):return full('Unknown changed input')
    selected=[]
    for test in tests:
        pending=[str(test.relative_to(root))];seen=set()
        while pending:
            path=pending.pop()
            if path in seen:continue
            seen.add(path);pending.extend(dependencies.get(path,()))
        if (test.name in SMOKE or docs and test.name in DOC_CHECKS or seen & meaningful
                or meaningful and seen & uncertain):selected.append(test.name)
    return dict(full=False,reason='Direct/transitive dependencies, dynamic-import checks and smoke tests',
                selected=selected,skipped=[test.name for test in tests if test.name not in selected])

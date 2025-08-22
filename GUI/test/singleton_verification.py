"""
싱글톤 패턴 사용 검증 도구

프로젝트 내에서 MainMonitorTab 및 기타 클래스들이 
싱글톤 패턴을 올바르게 사용하고 있는지 검증합니다.
"""

import ast
import os
import sys
from typing import List, Dict, Tuple, Any
from pathlib import Path


class SingletonUsageAnalyzer(ast.NodeVisitor):
    """AST를 사용하여 싱글톤 패턴 사용을 분석하는 클래스"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.class_instantiations: List[Tuple[str, int, str]] = []  # (class_name, line_num, context)
        self.singleton_classes: List[Tuple[str, int]] = []  # (class_name, line_num)
        self.current_class = None
        self.current_function = None
        
    def visit_ClassDef(self, node):
        """클래스 정의 방문"""
        old_class = self.current_class
        self.current_class = node.name
        
        # 싱글톤 패턴 특성 확인
        has_instance_attr = False
        has_new_method = False
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '_instance':
                        has_instance_attr = True
            elif isinstance(item, ast.FunctionDef) and item.name == '__new__':
                has_new_method = True
        
        if has_instance_attr and has_new_method:
            self.singleton_classes.append((node.name, node.lineno))
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """함수 정의 방문"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node):
        """함수 호출 방문"""
        if isinstance(node.func, ast.Name):
            class_name = node.func.id
            if class_name.endswith('Tab') or class_name in ['SectorManager', 'MainMonitorTabSingleton']:
                context = f"in {self.current_class}.{self.current_function}" if self.current_class and self.current_function else "global"
                self.class_instantiations.append((class_name, node.lineno, context))
        
        self.generic_visit(node)


def analyze_file(file_path: str) -> SingletonUsageAnalyzer:
    """파일을 분석하여 싱글톤 사용 현황을 반환"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        analyzer = SingletonUsageAnalyzer(file_path)
        analyzer.visit(tree)
        return analyzer
        
    except Exception as e:
        print(f"파일 분석 중 오류 발생 {file_path}: {e}")
        return SingletonUsageAnalyzer(file_path)


def find_python_files(root_dir: str) -> List[str]:
    """프로젝트에서 Python 파일들을 찾아 반환"""
    python_files = []
    root_path = Path(root_dir)
    
    for py_file in root_path.rglob("*.py"):
        # __pycache__ 등 제외
        if "__pycache__" not in str(py_file):
            python_files.append(str(py_file))
    
    return python_files


def verify_singleton_usage(project_root: str) -> Dict[str, Any]:
    """프로젝트 전체에서 싱글톤 사용을 검증"""
    python_files = find_python_files(project_root)
    
    results = {
        'singleton_classes': {},  # 파일별 싱글톤 클래스들
        'instantiations': {},     # 파일별 클래스 인스턴스화
        'violations': [],         # 싱글톤 패턴 위반 사항들
        'recommendations': []     # 개선 권장사항들
    }
    
    # 각 파일 분석
    for file_path in python_files:
        analyzer = analyze_file(file_path)
        
        if analyzer.singleton_classes:
            results['singleton_classes'][file_path] = analyzer.singleton_classes
        
        if analyzer.class_instantiations:
            results['instantiations'][file_path] = analyzer.class_instantiations
    
    # 위반 사항 검사
    check_violations(results)
    
    return results


def check_violations(results: Dict[str, Any]) -> None:
    """싱글톤 패턴 위반 사항을 검사"""
    
    # MainMonitorTab 직접 인스턴스화 검사
    mainmonitortab_instantiations = []
    for file_path, instantiations in results['instantiations'].items():
        for class_name, line_num, context in instantiations:
            if class_name == 'MainMonitorTab':
                mainmonitortab_instantiations.append((file_path, line_num, context))
    
    # gui_main.py에서의 사용은 허용 (메인 애플리케이션)
    filtered_violations = []
    for file_path, line_num, context in mainmonitortab_instantiations:
        if not file_path.endswith('gui_main.py') and not file_path.endswith('main_monitor.py'):
            # 테스트 파일이나 업데이터는 제외
            if 'test' not in file_path.lower() and 'update' not in file_path.lower():
                filtered_violations.append({
                    'type': 'direct_instantiation',
                    'class': 'MainMonitorTab',
                    'file': file_path,
                    'line': line_num,
                    'context': context,
                    'message': 'MainMonitorTab을 직접 인스턴스화하고 있습니다. 싱글톤 패턴을 사용하세요.'
                })
    
    results['violations'].extend(filtered_violations)
    
    # 권장사항 생성
    if filtered_violations:
        results['recommendations'].append({
            'type': 'use_singleton',
            'message': 'MainMonitorTab 대신 get_main_monitor_tab() 함수를 사용하세요.',
            'example': 'from src.GUI.update.main_monitor_updater import get_main_monitor_tab\nmonitor = get_main_monitor_tab()'
        })
    
    # 싱글톤 클래스 수 확인
    singleton_count = sum(len(classes) for classes in results['singleton_classes'].values())
    if singleton_count > 0:
        results['recommendations'].append({
            'type': 'singleton_info',
            'message': f'프로젝트에서 {singleton_count}개의 싱글톤 클래스를 사용하고 있습니다.',
            'details': 'SectorManager, MainMonitorTabSingleton 등'
        })


def print_verification_report(results: Dict[str, Any]) -> None:
    """검증 결과를 출력"""
    print("=" * 60)
    print("🔍 싱글톤 패턴 사용 검증 보고서")
    print("=" * 60)
    
    # 싱글톤 클래스들
    print("\n 발견된 싱글톤 클래스들:")
    if results['singleton_classes']:
        for file_path, classes in results['singleton_classes'].items():
            print(f"\n  {os.path.basename(file_path)}:")
            for class_name, line_num in classes:
                print(f"    {class_name} (라인 {line_num})")
    else:
        print("  싱글톤 클래스를 찾을 수 없습니다.")
    
    # 클래스 인스턴스화 현황
    print("\n 클래스 인스턴스화 현황:")
    important_classes = ['MainMonitorTab', 'SectorManager', 'MainMonitorTabSingleton']
    
    for class_name in important_classes:
        print(f"\n  🔸 {class_name} 인스턴스화:")
        found = False
        for file_path, instantiations in results['instantiations'].items():
            class_instances = [(line, ctx) for cls, line, ctx in instantiations if cls == class_name]
            if class_instances:
                found = True
                print(f"     {os.path.basename(file_path)}:")
                for line_num, context in class_instances:
                    print(f"      - 라인 {line_num}: {context}")
        
        if not found:
            print("     인스턴스화를 찾을 수 없습니다.")
    
    # 위반 사항
    print(f"\n  싱글톤 패턴 위반 사항: {len(results['violations'])}개")
    if results['violations']:
        for i, violation in enumerate(results['violations'], 1):
            print(f"\n  {i}. {violation['type']}:")
            print(f"      파일: {os.path.basename(violation['file'])}")
            print(f"      라인: {violation['line']}")
            print(f"      컨텍스트: {violation['context']}")
            print(f"      메시지: {violation['message']}")
    else:
        print("   위반 사항이 없습니다!")
    
    # 권장사항
    print(f"\n 권장사항: {len(results['recommendations'])}개")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"\n  {i}. {rec['message']}")
        if 'example' in rec:
            print(f"     예시: {rec['example']}")
        if 'details' in rec:
            print(f"     세부사항: {rec['details']}")
    
    print("\n" + "=" * 60)
    print(" 검증 완료!")


def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # 현재 스크립트 위치에서 프로젝트 루트 추정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '../../..')
    
    project_root = os.path.abspath(project_root)
    print(f"프로젝트 루트: {project_root}")
    
    if not os.path.exists(project_root):
        print(f" 프로젝트 루트 디렉토리를 찾을 수 없습니다: {project_root}")
        return
    
    # 검증 실행
    results = verify_singleton_usage(project_root)
    
    # 결과 출력
    print_verification_report(results)
    
    # 위반 사항이 있으면 exit code 1 반환
    if results['violations']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
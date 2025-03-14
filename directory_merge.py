import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import multi_selector  # 우리가 만든 multi_selector 모듈
from datetime import datetime
import random

class FileNameTemplate:
    def __init__(self, template: str, original_name: str):
        self.template = template
        self.original_name = original_name
        self.original_name_without_ext, self.original_ext = os.path.splitext(original_name)

    def generate(self, count: int = 1):
        """
        주어진 count 값에 맞춰 <NUM>을 변경한 새로운 이름을 반환합니다.
        :param count: <NUM>에 들어갈 숫자 값
        :return: 변경된 이름
        """
        name = self.template
        name = self._apply_number(name, count)
        name = self._apply_date(name)
        name = self._apply_time(name)
        name = self._apply_random(name)
        name = self._apply_original(name)

        # 확장자가 있다면 무조건 마지막에 붙도록 처리
        if self.original_ext:
            name += self.original_ext

        return name

    def _apply_number(self, name: str, num: int):
        return name.replace("<NUM>", str(num))

    def _apply_date(self, name: str):
        if "<DATE>" in name:
            date_str = datetime.now().strftime("%Y%m%d")
            name = name.replace("<DATE>", date_str)
        return name

    def _apply_time(self, name: str):
        if "<TIME>" in name:
            time_str = datetime.now().strftime("%H%M%S")
            name = name.replace("<TIME>", time_str)
        return name

    def _apply_random(self, name: str):
        if "<RAND>" in name:
            rand_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
            name = name.replace("<RAND>", rand_str)
        return name

    def _apply_original(self, name: str):
        if "<ORIGINAL>" in name:
            name = name.replace("<ORIGINAL>", self.original_name_without_ext)
        return name


def check_for_duplicates(directories: list[Path], target_dir: Path, template: str, apply_template_to_non_duplicate: bool):
    """
    디렉토리 내 파일들을 모두 받아와서 중복 파일 이름을 체크하고,
    중복되는 파일에 대해 템플릿을 적용하여 이름을 생성합니다.
    """
    all_files = {}  # 중복 확인을 위한 딕셔너리
    file_name_templates = {}  # 원본 파일 -> 새 파일 이름 매핑
    name_counter = {}  # 각 원본 파일의 개수를 추적

    # 소스 디렉토리 내 모든 파일 확인
    for directory in sorted(directories):
        for file in directory.rglob('*'):
            original_name_without_ext, original_ext = os.path.splitext(file.name)

            # 같은 원본 이름을 가진 파일의 등장 횟수를 카운트
            if original_name_without_ext not in name_counter:
                name_counter[original_name_without_ext] = 1
            else:
                name_counter[original_name_without_ext] += 1

            count = name_counter[original_name_without_ext]  # 현재 파일의 순번
            filename_generator = FileNameTemplate(template, file.name)
            new_name = filename_generator.generate(count)

            # 중복 체크
            while new_name in all_files:
                count += 1
                new_name = filename_generator.generate(count)

            # 중복되지 않는 새 이름을 딕셔너리에 추가
            all_files[new_name] = file
            file_name_templates[file] = new_name

    return file_name_templates


def copy_files_to_target(directories: list[Path], target_dir: Path, template: str, apply_template_to_non_duplicate: bool):
    """
    여러 디렉토리에서 파일을 하나의 디렉토리로 복사하고,
    이름이 겹칠 경우 템플릿에 맞춰 이름을 변경하며,
    중복되지 않은 파일에도 템플릿을 적용할지 여부를 결정한다.
    """
    # 대상 디렉토리가 없으면 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 중복 체크 및 새 이름 생성
    file_name_templates = check_for_duplicates(directories, target_dir, template, apply_template_to_non_duplicate)
    
    for file, new_name in file_name_templates.items():
        # 새 파일 경로
        target_file = target_dir / new_name

        # 파일 복사
        shutil.copy(file, target_file)
        print(f"파일 복사됨: {file} -> {target_file}")

    messagebox.showinfo("완료", "파일 복사가 완료되었습니다.")


def select_source_directories():
    directories = multi_selector.ask_multi_directory(title="소스 디렉토리 선택")
    if not directories:
        messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
        return
    return directories


def select_target_directory():
    target_dir = Path(filedialog.askdirectory(title="대상 디렉토리 선택"))
    if not target_dir:
        messagebox.showwarning("경고", "대상 디렉토리를 선택하지 않았습니다.")
        return
    return target_dir


def start_copy_process(directories, target_dir, template, apply_template_to_non_duplicate):
    # 파일 복사 진행
    copy_files_to_target(directories, target_dir, template, apply_template_to_non_duplicate)


def main():
    root = tk.Tk()
    root.title("파일 이름 변경 및 합치기")

    source_directories = []
    target_directory = None

    # 소스 디렉토리 표시 라벨
    source_label = tk.Label(root, text="소스 디렉토리: 선택되지 않음", wraplength=400)
    source_label.pack(pady=5)

    # 대상 디렉토리 표시 라벨
    target_label = tk.Label(root, text="대상 디렉토리: 선택되지 않음", wraplength=400)
    target_label.pack(pady=5)

    # 소스 디렉토리 선택
    def on_select_source():
        nonlocal source_directories
        source_directories = multi_selector.ask_multi_directory(title="소스 디렉토리 선택")

        if not source_directories:
            messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
            return

        # 선택된 디렉토리 목록을 표시
        source_dirs_str = [str(dir) for dir in source_directories]

        if len(source_dirs_str) > 2:
            display_text = f"{source_dirs_str[0]}, {source_dirs_str[1]} ... (총 {len(source_dirs_str)}개)"
        else:
            display_text = ", ".join(source_dirs_str)

        source_label.config(text=f"소스 디렉토리: {display_text}")

    btn_select_source = tk.Button(root, text="소스 디렉토리 선택", command=on_select_source)
    btn_select_source.pack(pady=10)

    # 대상 디렉토리 선택
    def on_select_target():
        nonlocal target_directory
        target_directory = filedialog.askdirectory(title="대상 디렉토리 선택")

        if not target_directory:
            messagebox.showwarning("경고", "대상 디렉토리를 선택하지 않았습니다.")
            return

        target_label.config(text=f"대상 디렉토리: {target_directory}")

    btn_select_target = tk.Button(root, text="대상 디렉토리 선택", command=on_select_target)
    btn_select_target.pack(pady=10)

    # 템플릿 입력 창
    template_label = tk.Label(root, text="파일 이름 템플릿:")
    template_label.pack(pady=5)
    template_entry = tk.Entry(root, width=50)
    template_entry.insert(0, "<ORIGINAL>_<NUM>_<DATE>_<TIME>_<RAND>")
    template_entry.pack(pady=5)

    # 템플릿 설명
    template_description = tk.Label(root, text="템플릿 규칙\n<ORIGINAL> - 원본 이름\n<NUM> - 숫자\n<DATE> - 날짜\n<TIME> - 시간\n<RAND> - 랜덤")
    template_description.pack(pady=5)

    # 라디오 버튼 (중복된 파일에 템플릿 적용 여부)
    apply_template_var = tk.IntVar()
    apply_template_var.set(1)  # 기본값: 템플릿을 모든 파일에 적용

    apply_template_rb1 = tk.Radiobutton(root, text="중복된 파일에만 템플릿 적용", variable=apply_template_var, value=0)
    apply_template_rb1.pack(pady=5)
    apply_template_rb2 = tk.Radiobutton(root, text="모든 파일에 템플릿 적용", variable=apply_template_var, value=1)
    apply_template_rb2.pack(pady=5)

    # 파일 합치기 시작
    def on_start_copy():
        if not source_directories:
            messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
            return
        if not target_directory:
            messagebox.showwarning("경고", "대상 디렉토리를 선택하지 않았습니다.")
            return

        template = template_entry.get()
        apply_template_to_non_duplicate = apply_template_var.get() == 1

        copy_files_to_target([Path(dir) for dir in source_directories], Path(target_directory), template, apply_template_to_non_duplicate)

    btn_start = tk.Button(root, text="파일 합치기 시작", command=on_start_copy)
    btn_start.pack(pady=20)

    # 창 닫기 버튼 (프로세스 종료)
    def on_close():
        root.destroy()  # 창을 닫을 때 완전히 종료
        import sys
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()


if __name__ == "__main__":
    main()


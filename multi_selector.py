import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import multi_selector  # 우리가 만든 multi_selector 모듈
from datetime import datetime
import random
import glob  # glob 모듈 추가

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


def apply_template(directories: list[Path], template: str, apply_template_to_non_duplicate: bool, file_pattern: str):
    all_files = {}  # 중복 확인을 위한 딕셔너리
    file_name_templates = {}  # 원본 파일 -> 새 파일 이름 매핑
    name_counter = {}  # 각 원본 파일의 개수를 추적
    global_counter = {}  # 전체 파일에 대한 번호 카운터 (폴더 구분 없이 처리)

    for directory in sorted(directories):
        files = glob.glob(str(directory / file_pattern))

        for file_path in files:
            file = Path(file_path)
            original_name_without_ext, original_ext = os.path.splitext(file.name)

            # 원본 파일 등장 횟수 추적
            if original_name_without_ext not in name_counter:
                name_counter[original_name_without_ext] = 1
            else:
                name_counter[original_name_without_ext] += 1

            count = name_counter[original_name_without_ext]

            # 첫 번째 등장하는 경우, apply_template_to_non_duplicate=False이면 원래 이름 유지
            if not apply_template_to_non_duplicate and count == 1:
                new_name = file.name
            else:
                # 템플릿 적용을 위한 파일명 생성기
                filename_generator = FileNameTemplate(template, file.name)
                new_name = filename_generator.generate(count)

                # 중복된 이름이 있으면 <NUM>을 추가해 해결
                while new_name in all_files or new_name in global_counter:
                    global_counter[original_name_without_ext] = global_counter.get(original_name_without_ext, 0) + 1
                    count = global_counter[original_name_without_ext]
                    temp_template = template
                    if "<NUM>" not in template:
                        temp_template += "_<NUM>"
                    filename_generator = FileNameTemplate(temp_template, file.name)
                    new_name = filename_generator.generate(count)

            all_files[new_name] = file
            file_name_templates[file] = new_name

    return file_name_templates



def update_preview(source_directories, template, apply_template_to_non_duplicate, file_pattern, listbox_orig, listbox_new):
    # 소스 디렉토리만 선택된 경우에도 미리보기는 정상적으로 업데이트되도록 수정
    if not source_directories:
        return

    listbox_orig.delete(0, tk.END)
    listbox_new.delete(0, tk.END)

    # 타겟 디렉토리가 선택되지 않더라도 미리보기만 업데이트
    file_name_templates = apply_template(source_directories, template, apply_template_to_non_duplicate, file_pattern)

    for original_file, new_name in file_name_templates.items():
        listbox_orig.insert(tk.END, f"{original_file.parent.name}/{original_file.name}")
        listbox_new.insert(tk.END, new_name)




def copy_files_to_target(directories: list[Path], target_dir: Path, template: str, apply_template_to_non_duplicate: bool, file_pattern: str):
    # 타겟 디렉토리가 반드시 선택되어야 복사가 진행되도록 수정
    if not target_dir:
        messagebox.showwarning("경고", "대상 디렉토리를 선택하지 않았습니다.")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    file_name_templates = apply_template(directories, template, apply_template_to_non_duplicate, file_pattern)

    for file, new_name in file_name_templates.items():
        target_file = target_dir / new_name
        shutil.copy(file, target_file)
        print(f"파일 복사됨: {file} -> {target_file}")

    messagebox.showinfo("완료", "파일 복사가 완료되었습니다.")

def main():
    root = tk.Tk()
    root.title("파일 이름 변경 및 합치기")

    source_directories = []
    target_directory = None

    # source_label, target_label 등 위젯을 left_frame과 right_frame에 배치
    top_frame = tk.Frame(root)
    top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    bottom_frame = tk.Frame(root)
    bottom_frame.grid(row=1, column=0, sticky="ew", pady=10)

    left_frame = tk.Frame(top_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    right_frame = tk.Frame(top_frame)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    # 오른쪽 프레임을 위아래로 꽉 차게 만들기 위해
    top_frame.grid_rowconfigure(0, weight=1)
    top_frame.grid_columnconfigure(1, weight=1)

    # 왼쪽 프레임을 위아래로 꽉 차게 만들기 위해
    top_frame.grid_rowconfigure(0, weight=1)
    top_frame.grid_columnconfigure(0, weight=1)

    # 프레임 내 위젯 생성 (각각 해당하는 프레임에 배치)
    source_label = tk.Label(left_frame, text="소스 디렉토리: 선택되지 않음", wraplength=400)
    target_label = tk.Label(left_frame, text="대상 디렉토리: 선택되지 않음", wraplength=400)

    def on_select_source():
        nonlocal source_directories
        source_directories = multi_selector.ask_multi_directory(title="소스 디렉토리 선택")

        if not source_directories:
            messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
            return

        source_dirs_str = [str(dir) for dir in source_directories]
        if len(source_dirs_str) > 2:
            display_text = f"{source_dirs_str[0]}, {source_dirs_str[1]} ... (총 {len(source_dirs_str)}개)"
        else:
            display_text = ", ".join(source_dirs_str)

        source_label.config(text=f"소스 디렉토리: {display_text}")

        # 소스 디렉토리를 선택하면 미리보기 업데이트
        update_preview([Path(dir) for dir in source_directories], template_entry.get(), apply_template_var.get() == 1, pattern_entry.get(), listbox_orig, listbox_new)

    def on_select_target():
        nonlocal target_directory
        target_directory = filedialog.askdirectory(title="대상 디렉토리 선택")

        if target_directory:
            target_label.config(text=f"대상 디렉토리: {target_directory}")

        # 대상 디렉토리 선택 후 미리보기 업데이트
        update_preview([Path(dir) for dir in source_directories], template_entry.get(), apply_template_var.get() == 1, pattern_entry.get(), listbox_orig, listbox_new)

    btn_select_source = tk.Button(left_frame, text="소스 디렉토리 선택", command=on_select_source)
    btn_select_target = tk.Button(left_frame, text="대상 디렉토리 선택", command=on_select_target)

    template_label = tk.Label(left_frame, text="파일 이름 템플릿:")
    template_entry = tk.Entry(left_frame, width=50)
    template_entry.insert(0, "<ORIGINAL>_<NUM>_<DATE>_<TIME>_<RAND>")

    pattern_label = tk.Label(left_frame, text="파일 선택 와일드카드 패턴 (예: *.txt):")
    pattern_entry = tk.Entry(left_frame, width=50)
    pattern_entry.insert(0, "*.*")

    template_description = tk.Label(left_frame, text="템플릿 규칙\n<ORIGINAL> - 원본 이름\n<NUM> - 숫자\n<DATE> - 날짜\n<TIME> - 시간\n<RAND> - 랜덤")

    apply_template_var = tk.IntVar()
    apply_template_var.set(1)

    apply_template_rb1 = tk.Radiobutton(left_frame, text="중복된 파일에만 템플릿 적용", variable=apply_template_var, value=0)
    apply_template_rb2 = tk.Radiobutton(left_frame, text="모든 파일에 템플릿 적용", variable=apply_template_var, value=1)

    # 왼쪽 프레임에 위젯 배치
    source_label.grid(row=0, column=0, pady=5, sticky="ew")
    btn_select_source.grid(row=1, column=0, pady=10, sticky="ew")
    target_label.grid(row=2, column=0, pady=5, sticky="ew")
    btn_select_target.grid(row=3, column=0, pady=10, sticky="ew")
    template_label.grid(row=4, column=0, pady=5, sticky="ew")
    template_entry.grid(row=5, column=0, pady=5, sticky="ew")
    template_description.grid(row=6, column=0, pady=5, sticky="ew")
    pattern_label.grid(row=7, column=0, pady=5, sticky="ew")
    pattern_entry.grid(row=8, column=0, pady=5, sticky="ew")
    apply_template_rb1.grid(row=9, column=0, pady=5, sticky="ew")
    apply_template_rb2.grid(row=10, column=0, pady=5, sticky="ew")

    # Listbox와 Scrollbar를 동시에 연결하는 코드
    listbox_frame = tk.Frame(right_frame)
    listbox_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

    # Listbox 위젯
    listbox_orig = tk.Listbox(listbox_frame, width=50, height=15, selectmode=tk.SINGLE)
    listbox_orig.grid(row=0, column=0, padx=5, sticky="nsew")

    listbox_new = tk.Listbox(listbox_frame, width=50, height=15, selectmode=tk.SINGLE)
    listbox_new.grid(row=0, column=1, padx=5, sticky="nsew")

    # Scrollbar 연결: 두 Listbox에 대해 동일한 Scrollbar 사용
    scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
    scrollbar.grid(row=0, column=2, sticky="ns")

    # Listbox의 yscrollcommand와 Scrollbar의 set을 연결
    listbox_orig.config(yscrollcommand=scrollbar.set)
    listbox_new.config(yscrollcommand=scrollbar.set)
    def on_mouse_wheel(event):
        # Listbox에서 스크롤 시 두 개의 Listbox와 Scrollbar 모두 동기화
        listbox_orig.yview_scroll(int(-1*(event.delta/120)), "units")
        listbox_new.yview_scroll(int(-1*(event.delta/120)), "units")

    # Listbox에 마우스 휠 이벤트를 바인딩
    listbox_orig.bind("<MouseWheel>", on_mouse_wheel)
    listbox_new.bind("<MouseWheel>", on_mouse_wheel)

    # Scrollbar의 command와 Listbox의 yview를 연결
    scrollbar.config(command=lambda *args: [listbox_orig.yview(*args), listbox_new.yview(*args)])


    def on_start_copy():
        if not source_directories:
            messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
            return
        if not target_directory:
            messagebox.showinfo("알림", "대상 디렉토리가 선택되지 않았습니다. 복사는 진행되지 않습니다.")
            return

        template = template_entry.get()
        apply_template_to_non_duplicate = apply_template_var.get() == 1
        file_pattern = pattern_entry.get()

        copy_files_to_target([Path(dir) for dir in source_directories], Path(target_directory), template, apply_template_to_non_duplicate, file_pattern)

    # 아래쪽 프레임에 버튼 배치
    btn_start = tk.Button(bottom_frame, text="파일 합치기 시작", command=on_start_copy)
    btn_start.grid(row=0, column=0, pady=20, columnspan=2, sticky="ew")

    # 소스 디렉토리나 템플릿 등이 변경될 때마다 미리보기 업데이트
    def on_update_preview():
        update_preview([Path(dir) for dir in source_directories], template_entry.get(), apply_template_var.get() == 1, pattern_entry.get(), listbox_orig, listbox_new)

    template_entry.bind("<KeyRelease>", lambda e: on_update_preview())
    pattern_entry.bind("<KeyRelease>", lambda e: on_update_preview())
    apply_template_var.trace_add("write", lambda *args: on_update_preview())

    # 창 닫기 버튼 (프로세스 종료)
    def on_close():
        root.destroy()  # 창을 닫을 때 완전히 종료
        import sys
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
